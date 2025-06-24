"""
Base module for the BKT engine.
Contains shared functionality between the lesson and review engines.
"""

import math
import os
import json
import time
import pickle
import pymongo
from pymongo.errors import ConfigurationError
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

# MongoDB connection string
uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

# Global variables
executor = ThreadPoolExecutor(max_workers=2)
bkt_thread = None
bkt_thread_lock = threading.Lock()

def connect_to_mongoDB():
    """Connect to the MongoDB database"""
    try:
        arami = pymongo.MongoClient(uri)["arami"]
        usercol = arami["users"]
        return usercol
    except ConfigurationError as e:
        print(f"[BKT] Failed to connect to MongoDB: {e}")
        sys.exit("Terminating the program due to MongoDB connection failure.")

def normalize_vocabulary(vocab):
    """Normalize vocabulary for consistent database storage"""
    if not vocab:
        return None
        
    # Create a standard form - lowercase with proper spacing
    normalized = str(vocab).lower().strip()
    # Remove any multiple spaces
    normalized = ' '.join(normalized.split())
    return normalized

def normalize_vocabulary_key(vocab):
    """Normalize vocabulary key for dictionary consistency"""
    return normalize_vocabulary(vocab)

def find_vocabulary_in_list(vocab, vocab_list):
    """Find vocabulary in list, ignoring case and extra whitespace"""
    normalized_vocab = normalize_vocabulary(vocab)
    if not normalized_vocab:
        return None
        
    # First try exact match after normalization
    for v in vocab_list:
        if normalize_vocabulary(v) == normalized_vocab:
            return v
            
    # Then try prefix matching for partial matches
    for v in vocab_list:
        norm_v = normalize_vocabulary(v)
        if norm_v and normalized_vocab and (
            norm_v.startswith(normalized_vocab[:5]) or 
            normalized_vocab.startswith(norm_v[:5])
        ):
            print(f"[BKT] Found prefix match: '{normalized_vocab}' ≈ '{norm_v}'")
            return v
            
    return None

def get_vocabulary_from_question(question):
    """Extract vocabulary from question object consistently with normalized case"""
    if not question:
        return None
    
    vocab = None
    
    # Direct attribute
    if hasattr(question, 'vocabulary'):
        vocab = question.vocabulary
    elif isinstance(question, dict) and 'vocabulary' in question:
        vocab = question['vocabulary']
    
    # Alternative attributes
    elif hasattr(question, 'word_to_translate'):
        vocab = question.word_to_translate
    elif isinstance(question, dict) and 'word_to_translate' in question:
        vocab = question['word_to_translate']
    
    if vocab:
        # Apply normalization but preserve original case
        return vocab.strip()
    
    return None

def calculate_bkt_confidence(mastery, guess, slip, vocab=None, params=None):
    """Calculate confidence based on BKT parameters with more dynamic weighting"""
    # Normalize input parameters
    mastery = min(0.99, max(0.01, float(mastery)))
    guess = min(0.5, max(0.01, float(guess)))
    slip = min(0.5, max(0.01, float(slip)))
    
    # ENHANCED: Calculate certainty component - higher near 0 or 1
    certainty = 2.0 * abs(mastery - 0.5)  # 0.0 to 1.0 scale
    
    # Basic confidence starts at 0.3
    base_conf = 0.3
    
    # ENHANCED: Mastery contributes more significantly
    if mastery > 0.5:
        mastery_contrib = 0.35 * (mastery - 0.5) * 2  # 0 to 0.35
    else:
        mastery_contrib = 0.25 * (0.5 - mastery) * 2  # 0 to 0.25 (for low mastery)
    
    # ENHANCED: Lower guess rates increase confidence significantly
    guess_contrib = 0.25 * (1.0 - (guess / 0.5))  # Max 0.25 contribution
    
    # ENHANCED: Lower slip rates increase confidence significantly  
    slip_contrib = 0.20 * (1.0 - (slip / 0.5))  # Max 0.20 contribution
    
    # Add learning history factor if available
    history_contrib = 0.0
    if params and 'observations' in params:
        obs_count = len(params['observations'])
        # More observations increase confidence, but with diminishing returns
        history_contrib = 0.15 * min(1.0, math.log(1 + obs_count) / math.log(10))
        
        # Recent performance affects confidence
        recent_obs = params['observations'][-3:] if len(params['observations']) > 3 else params['observations']
        if recent_obs:
            recent_correct = sum(1 for o in recent_obs if o.get('correct', True))
            recent_ratio = recent_correct / len(recent_obs)
            if recent_ratio >= 0.67:  # 2/3 or better
                history_contrib += 0.10
            elif recent_ratio <= 0.33:  # 1/3 or worse
                history_contrib -= 0.05
    
    # Calculate confidence from components
    confidence = base_conf + mastery_contrib + guess_contrib + slip_contrib + history_contrib
    
    # Keep within reasonable bounds
    confidence = min(0.95, max(0.25, confidence))
    
    # Debug components with more detail
    if vocab:
        print(f"[BKT] Confidence for {vocab} (mastery={mastery:.3f}): {confidence:.3f}")
        print(f"[BKT]   Components: Base={base_conf:.2f}, Mastery={mastery_contrib:.2f}, " +
              f"Guess={guess_contrib:.2f}, Slip={slip_contrib:.2f}, History={history_contrib:.2f}")
    
    return confidence

def initialize_vocabulary_parameters(vocab, difficulty=None):
    """Initialize BKT parameters based on vocabulary characteristics"""
    # Calculate word complexity factors deterministically
    word_length = len(vocab)
    has_special_chars = any(c for c in vocab if not c.isalnum() and c != ' ')
    word_complexity = min(1.0, word_length / 25)  # Normalize by typical max length
    
    # Each word gets truly different parameters based on complexity 
    # Word length affects guess probability (shorter words are easier to guess)
    guess_prob = 0.25 - (0.10 * word_complexity)
    
    # Special characters and longer words increase slip probability
    slip_prob = 0.10 + (0.05 * word_complexity) + (0.02 * has_special_chars)
    
    # Learning rate is also affected by complexity
    learn_rate = 0.15 - (0.05 * word_complexity)
    
    # Initial mastery depends on word complexity
    prior_prob = 0.45 - (0.20 * word_complexity)
    
    # Adjust for difficulty if provided
    if difficulty and isinstance(difficulty, (int, float)):
        diff = float(difficulty)
        
        # Higher difficulty = lower learning rate and prior, higher slip
        learn_rate *= max(0.6, 1.0 - (diff * 0.08))
        guess_prob *= max(0.7, 1.0 - (diff * 0.06))
        slip_prob *= min(1.5, 1.0 + (diff * 0.10))
        prior_prob *= max(0.5, 1.0 - (diff * 0.12))
    
    # Ensure parameters are within reasonable bounds
    learn_rate = max(0.08, min(0.22, learn_rate))
    guess_prob = max(0.10, min(0.40, guess_prob))
    slip_prob = max(0.05, min(0.30, slip_prob))
    prior_prob = max(0.2, min(0.7, prior_prob))
    
    # Create final parameter dict
    params = {
        'learn': learn_rate,
        'guess': guess_prob,
        'slip': slip_prob,
        'prior': prior_prob,
        'observations': []
    }
    
    print(f"[BKT] Created diverse parameters for '{vocab}': " +
          f"learn={params['learn']:.3f}, guess={params['guess']:.3f}, " +
          f"slip={params['slip']:.3f}, prior={params['prior']:.3f}")
    
    return params

class CustomBKTPredictor:
    """Custom BKT predictor that directly uses the vocabulary parameters"""
    
    def __init__(self, vocab_parameters=None):
        """Initialize with optional vocab parameters"""
        # Initialize with empty parameters if none provided
        self.vocab_parameters = vocab_parameters or {}
        # Default BKT parameters for new vocabulary items
        self.default_params = {
            "p_init": 0.4,      # Initial probability of mastery
            "p_transit": 0.12,  # Probability of transitioning from not mastered to mastered
            "p_guess": 0.15,    # Probability of guessing correctly when not mastered
            "p_slip": 0.05      # Probability of answering incorrectly when mastered
        }
    
    def predict(self, vocab, sequence):
        """
        Return mastery prediction without artificial normalization
        """
        params = self.vocab_parameters.get(vocab, {})
        mastery = params.get('prior', 0.5)
        
        # Return the actual mastery value - no normalization
        return mastery
    
    def get_vocabulary_in_order(self):
        """Get vocabulary ordered by mastery level (lowest first)"""
        if not self.vocab_parameters:
            return []  # Return empty list if no vocabulary
        
        # First populate order parameters if not present
        # This ensures new vocabularies get properly ordered
        for vocab in self.vocab_parameters.keys():
            if 'order' not in self.vocab_parameters[vocab]:
                # Assign a high order number to new vocabulary items
                self.vocab_parameters[vocab]['order'] = len(self.vocab_parameters) * 10
            
        # Try to sort by specified order parameter first
        try:
            sorted_vocab = sorted(
                self.vocab_parameters.keys(),
                key=lambda v: self.vocab_parameters[v].get('order', 999999)
            )
            return sorted_vocab
        except Exception as e:
            print(f"[BKT] Error sorting vocabulary by order: {e}")
            # Fall back to mastery-based sort
            try:
                sorted_vocab = sorted(
                    self.vocab_parameters.keys(),
                    key=lambda v: float(self.vocab_parameters[v].get('prior', 0.5))
                )
                return sorted_vocab
            except Exception as e:
                print(f"[BKT] Error sorting vocabulary: {e}")
                # Last resort - simple alphabetical sort
                return sorted(self.vocab_parameters.keys())
    
    def observe_with_scale(self, vocab, correct, impact_scale=1.0, difficulty=None):
        """
        Update BKT parameters based on observation with adaptive learning
        but without random variations
        """
        vocab = vocab.lower().strip()

        # Initialize with diverse parameters if new vocabulary
        if vocab not in self.vocab_parameters:
            print(f"[BKT] Creating parameters for new vocabulary: '{vocab}'")
            self.vocab_parameters[vocab] = initialize_vocabulary_parameters(vocab, difficulty)
        
        # Get current parameters
        params = self.vocab_parameters[vocab]
        
        # Calculate time-based decay for mastery if previous observations exist
        if 'observations' in params and params['observations']:
            last_obs_time = params['observations'][-1].get('timestamp', 0)
            current_time = int(time.time())
            days_since_last = (current_time - last_obs_time) / (60 * 60 * 24)
            
            # Apply decay if more than 1 day has passed
            if days_since_last > 1:
                # Calculate decay factor (1.5% per day, max 40%)
                decay_factor = min(0.40, days_since_last * 0.015)
                old_mastery = params.get('prior', 0.5)
                decayed_mastery = max(0.2, old_mastery * (1 - decay_factor))
                
                # Only apply if significant decay occurred
                if old_mastery - decayed_mastery > 0.02:
                    params['prior'] = decayed_mastery
                    print(f"[BKT] Applied time decay to '{vocab}': {old_mastery:.3f} → {decayed_mastery:.3f} (after {days_since_last:.1f} days)")
        
        # Get observation history
        num_observations = len(params.get('observations', []))
        
        # Adjust learning rate based on multiple factors:
        # 1. Vocabulary difficulty (harder = learn slower)
        # 2. Number of previous observations (diminishing returns)
        # 3. Prior mastery level (harder to improve when already high)
        # 4. Daily review vs normal learning (impact_scale)
        
        # Base learning rate adjustment
        if difficulty and isinstance(difficulty, (int, float)):
            difficulty_factor = max(0.4, 1.0 - (float(difficulty) / 8.0))
        else:
            difficulty_factor = 0.8  # Default medium difficulty
        
        # Reduce learning rate for items with many observations (diminishing returns)
        history_factor = max(0.5, 1.5 - (num_observations * 0.05))
        
        # Harder to improve when mastery is already high
        mastery = params.get('prior', 0.5)
        mastery_factor = max(0.3, 1.0 - (mastery * 0.5))
        
        # Calculate final adaptive learning rate - no randomness
        learn = params.get('learn', 0.15) * impact_scale * difficulty_factor * history_factor * mastery_factor
        
        # Log the learning rate factors
        print(f"[BKT] Learning rate factors for '{vocab}': difficulty={difficulty_factor:.2f}, " +
            f"history={history_factor:.2f}, mastery={mastery_factor:.2f}")
        print(f"[BKT] Final learning rate: {learn:.3f}")
        
        consecutive_correct = 0
        if 'observations' in params:
            # Count consecutive correct answers from the end of history
            for obs in reversed(params.get('observations', [])):
                if isinstance(obs, dict) and obs.get('correct', False):
                    consecutive_correct += 1
                else:
                    break
                    
        # Add current observation to history if not already present
        current_time = int(time.time())
        if 'observations' not in params:
            params['observations'] = []
        
        # Add current observation
        params['observations'].append({
            'timestamp': current_time,
            'correct': correct,
            'impact_scale': impact_scale
        })

        # Get other parameters
        guess = params.get('guess', 0.25)
        slip = params.get('slip', 0.1)
        mastery = params.get('prior', 0.5)
        
        # Track original values for logging
        old_mastery = mastery
        old_guess = guess
        old_slip = slip
        
        # Apply BKT update formula with enhanced parameter dynamics
        if correct:
            # P(mastered | correct)
            mastery = (mastery * (1 - slip)) / (mastery * (1 - slip) + (1 - mastery) * guess)
            
            # Consecutive correct answers decrease guess & slip probabilities more aggressively
            if consecutive_correct > 1:
                guess_reduction = min(0.04, 0.015 * consecutive_correct)
                guess = max(0.05, guess - guess_reduction)
                slip = max(0.03, slip * 0.93)
                
                # Log the parameter adjustments
                print(f"[BKT] After {consecutive_correct} consecutive correct answers for '{vocab}': " + 
                    f"reduced guess by {guess_reduction:.3f}, slip by {(old_slip - slip):.3f}")
        else:
            # P(mastered | incorrect)
            mastery = (mastery * slip) / (mastery * slip + (1 - mastery) * (1 - guess))
            
            # Increase slip probability for incorrect answers more aggressively
            slip_increase = min(0.05, slip * 0.08)
            slip = min(0.35, slip + slip_increase)
            
            # If high mastery but incorrect, even more likely a slip
            if mastery > 0.7:
                slip = min(0.40, slip + 0.05)
                print(f"[BKT] High mastery but incorrect for '{vocab}': increasing slip to {slip:.3f}")
        
        # Update and save parameters
        params['prior'] = mastery
        params['guess'] = guess
        params['slip'] = slip
        self.vocab_parameters[vocab] = params
        
        # Enhanced logging
        param_changes = []
        if abs(mastery - old_mastery) > 0.001:
            param_changes.append(f"mastery: {old_mastery:.3f}→{mastery:.3f}")
        if abs(guess - old_guess) > 0.001:
            param_changes.append(f"guess: {old_guess:.3f}→{guess:.3f}")
        if abs(slip - old_slip) > 0.001:
            param_changes.append(f"slip: {old_slip:.3f}→{slip:.3f}")
            
        changes_str = ", ".join(param_changes)
        print(f"[BKT] Updated '{vocab}': {old_mastery:.3f} → {mastery:.3f} (correct={correct}, scale={impact_scale:.2f}, {changes_str})")
        
        return mastery
