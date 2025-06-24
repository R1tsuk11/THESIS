import math
import os
import json
from pyBKT.models import Model
import pandas as pd
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import subprocess
import pickle
import pymongo
import sys
from pymongo.errors import ConfigurationError
import types

uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

def reset_bkt_update_counters():
    """Reset any update counters to ensure parameters are recalculated"""
    global refit_counter
    refit_counter = 0
    print("[BKT] Reset update counters to force recalculation")

def connect_to_mongoDB():
    try:
        arami = pymongo.MongoClient(uri)["arami"]
        usercol = arami["users"]
        return usercol
    except ConfigurationError as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit("Terminating the program due to MongoDB connection failure.")

executor = ThreadPoolExecutor(max_workers=2)
TEMP_FILE = "temp_bkt_data.json"
PREDICTION_FILE = "bkt_predictions.json"
bkt_model = Model()
bkt_data = []
bkt_thread = None
bkt_thread_lock = threading.Lock()
uid = None
current_vocab_index = 0
current_vocab = None
questions_seen = set()  # Track IDs of questions already seen

def save_predictions_file():
    """Save the latest BKT predictions to a JSON file (legacy support)"""
    state = load_temp_state()
    predictions = state.get("predictions", {})
    
    # Save to the prediction file
    with open(PREDICTION_FILE, "w") as f:
        json.dump({"predictions": predictions}, f, indent=2)
        
    print(f"[BKT] Saved predictions to {PREDICTION_FILE}")

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
        
        # IMPORTANT: Return the actual mastery value - no normalization
        return mastery
    
    def get_vocabulary_in_order(self):
        """Get vocabulary ordered by mastery level (lowest first)"""
        if not self.vocab_parameters:
            return []  # Return empty list if no vocabulary
        
        # IMPORTANT: First populate order parameters if not present
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
        learn = params.get('learn', 0.15) * impact_scale
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
            if consecutive_correct > 1:  # Changed from >2 to >1
                guess_reduction = min(0.04, 0.015 * consecutive_correct)  # More reduction
                guess = max(0.05, guess - guess_reduction)
                slip = max(0.03, slip * 0.93)  # More reduction (was 0.95)
                
                # Log the parameter adjustments
                print(f"[BKT] After {consecutive_correct} consecutive correct answers for '{vocab}': " + 
                    f"reduced guess by {guess_reduction:.3f}, slip by {(old_slip - slip):.3f}")
        else:
            # P(mastered | incorrect)
            mastery = (mastery * slip) / (mastery * slip + (1 - mastery) * (1 - guess))
            
            # Increase slip probability for incorrect answers more aggressively
            slip_increase = min(0.05, slip * 0.08)  # More increase
            slip = min(0.35, slip + slip_increase)  # Higher max (was 0.25)
            
            # If high mastery but incorrect, even more likely a slip
            if mastery > 0.7:
                slip = min(0.40, slip + 0.05)  # Higher adjustment (was 0.02)
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
    
    def mark_vocabulary_reviewed(self, vocab):
        """Mark a vocabulary as reviewed in daily review context"""
        vocab = vocab.lower().strip()
        if vocab in self.vocab_parameters:
            # Update the reviewed flag and timestamp
            self.vocab_parameters[vocab]['reviewed'] = True
            self.vocab_parameters[vocab]['last_reviewed'] = int(time.time())
            
            # ENHANCED: Add to observations if this was a review
            if 'observations' not in self.vocab_parameters[vocab]:
                self.vocab_parameters[vocab]['observations'] = []
            
            # Add review observation
            self.vocab_parameters[vocab]['observations'].append({
                'timestamp': int(time.time()),
                'type': 'daily_review',
                'reviewed': True
            })
            
            print(f"[BKT] Marked '{vocab}' as reviewed with observation")
        else:
            # Initialize vocabulary if it doesn't exist
            import time
            self.vocab_parameters[vocab] = {
                'prior': 0.5,
                'guess': 0.25,
                'slip': 0.1,
                'learn': 0.15,
                'reviewed': True,
                'last_reviewed': int(time.time()),
                'observations': [{
                    'timestamp': int(time.time()),
                    'type': 'daily_review_init',
                    'reviewed': True
                }],
                'response_times': []
            }
            print(f"[BKT] Initialized and marked '{vocab}' as reviewed")

    def get_mastery(self, vocab):
        """Get current mastery for a vocabulary"""
        vocab = vocab.lower().strip()
        if vocab in self.vocab_parameters:
            return float(self.vocab_parameters[vocab].get('prior', 0.5))
        return 0.5

    def is_reviewed(self, vocab):
        """Check if vocabulary has been reviewed"""
        vocab = vocab.lower().strip()
        if vocab in self.vocab_parameters:
            return self.vocab_parameters[vocab].get('reviewed', False)
        return False

def get_custom_bkt_path(user_id=None):
    """Get path for user-specific custom BKT predictor"""
    if user_id and str(user_id).lower() != "none":
        return f"custom_bkt_predictor_{user_id}.pkl"
    return "custom_bkt_predictor.pkl"

def validate_bkt_data(custom_bkt):
    """Validate and repair BKT data structure"""
    if not custom_bkt or not hasattr(custom_bkt, 'vocab_parameters'):
        return
    
    fixed_count = 0
    for vocab, params in list(custom_bkt.vocab_parameters.items()):
        # Fix non-dictionary parameters
        if not isinstance(params, dict):
            custom_bkt.vocab_parameters[vocab] = {
                'learn': 0.15,
                'guess': 0.25,
                'slip': 0.1,
                'prior': 0.5,
                'observations': []
            }
            fixed_count += 1
            continue
        
        # Ensure required keys exist
        for key in ['learn', 'guess', 'slip', 'prior']:
            if key not in params or not isinstance(params[key], (int, float)):
                params[key] = {'learn': 0.15, 'guess': 0.25, 'slip': 0.1, 'prior': 0.5}[key]
                fixed_count += 1
        
        # Validate observations array
        if 'observations' not in params or not isinstance(params['observations'], list):
            params['observations'] = []
            fixed_count += 1
        else:
            # Check each observation
            valid_observations = []
            for obs in params['observations']:
                if isinstance(obs, dict):
                    valid_observations.append(obs)
            params['observations'] = valid_observations

        # Explicit numeric conversion for all numeric parameters
        for key in ['learn', 'guess', 'slip', 'prior']:
            if key in params and params[key] is not None:
                try:
                    params[key] = float(params[key])
                except (TypeError, ValueError):
                    params[key] = {'learn': 0.15, 'guess': 0.25, 'slip': 0.1, 'prior': 0.5}[key]
                    fixed_count += 1
    
    if fixed_count > 0:
        print(f"[BKT] Fixed {fixed_count} issues in BKT data structure")

def load_custom_bkt(user_id):
    """Ensure BKT predictor is properly loaded with data validation"""
    try:
        custom_bkt = None
        
        # Try binary file first
        file_path = f"custom_bkt_predictor_{user_id}.pkl"
        if os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    custom_bkt = pickle.load(f)
                    print(f"[BKT] Loaded custom predictor for user {user_id}")
            except Exception as e:
                print(f"[BKT] Error loading predictor from pickle: {e}")
                # If pickle is corrupted, delete it
                try:
                    os.remove(file_path)
                    print(f"[BKT] Removed corrupted predictor file: {file_path}")
                except:
                    pass
        
        # Try database as fallback if pickle didn't work
        if not custom_bkt:
            try:
                usercol = connect_to_mongoDB()
                user = usercol.find_one({"user_id": user_id})
                if user and "bkt_data" in user:
                    custom_bkt = CustomBKTPredictor()
                    
                    # CRITICAL FIX: Validate bkt_data before assigning
                    if isinstance(user["bkt_data"], dict):
                        # Clean the data before assigning - filter out non-dict values
                        valid_data = {}
                        for key, value in user["bkt_data"].items():
                            # Only include dictionary values and skip special keys
                            if isinstance(value, dict):
                                valid_data[key] = value
                            elif key not in ["fitted", "refit_counter", "predictions"]:
                                print(f"[BKT] Skipping invalid BKT data for '{key}': {type(value).__name__}")
                        
                        custom_bkt.vocab_parameters = valid_data
                        print(f"[BKT] Loaded BKT data from database for user {user_id}")
                    else:
                        print(f"[BKT] Invalid BKT data format in database: {type(user['bkt_data']).__name__}")
            except Exception as e:
                print(f"[BKT] Error loading from database: {e}")
        
        # Create new if needed
        if not custom_bkt:
            print(f"[BKT] No custom predictor found for user {user_id}, creating new one")
            custom_bkt = CustomBKTPredictor()
        
        # Final data validation to ensure all entries are valid
        validate_bkt_data(custom_bkt)
        
        return custom_bkt
        
    except Exception as e:
        print(f"[BKT] Error loading custom predictor: {e}")
        return CustomBKTPredictor()

def get_custom_bkt(user_id=None):
    """Get or create custom BKT predictor with proper user ID handling."""
    if user_id is None:
        # Try to get from global context
        global uid
        
        # Debug what's happening with IDs
        print(f"[BKT] get_custom_bkt called with no user_id, global uid={uid}")
        
        user_id = uid
        
        # Try to get from page.session if available
        if user_id is None:
            try:
                import flet as ft
                page = ft.app.get_current_page()
                if page and hasattr(page, 'session'):
                    session_user_id = page.session.get("user_id")
                    if session_user_id is not None:
                        user_id = session_user_id
                        print(f"[BKT] Retrieved user_id {user_id} from page session")
                        # Update global uid for future calls
                        uid = user_id
            except Exception as e:
                print(f"[BKT] Error retrieving user_id from session: {e}")
            
        # If still None, use a temporary ID
        if user_id is None:
            import time
            user_id = f"temp_{int(time.time())}"
            print(f"[BKT] Warning: Using temporary user ID {user_id}")

def save_custom_bkt(user_id, predictor):
    """Save the custom BKT predictor for a specific user"""
    try:
        # Check if arguments are swapped
        if hasattr(user_id, 'vocab_parameters') and not hasattr(predictor, 'vocab_parameters'):
            print("[BKT] Warning: Arguments appear to be in wrong order, swapping")
            user_id, predictor = predictor, user_id
        
        # Verify predictor is the right type
        if not hasattr(predictor, 'vocab_parameters'):
            print(f"[BKT] Error: Invalid predictor object: {type(predictor)}")
            return False
            
        # Get a valid filename
        if user_id is None:
            model_path = "custom_bkt_predictor.pkl"
        else:
            model_path = f"custom_bkt_predictor_{user_id}.pkl"
            
        with open(model_path, "wb") as f:
            pickle.dump(predictor, f)
        print(f"[BKT] Saved custom predictor to {model_path}")
        return True
        
    except Exception as e:
        print(f"[BKT] Error saving custom BKT predictor: {e}")
        return False

def create_user_bkt_predictor(user_id):
    """Create a user-specific BKT predictor by cloning the base model"""
    try:
        # First try to load the base custom predictor
        if os.path.exists("custom_bkt_predictor.pkl"):
            with open("custom_bkt_predictor.pkl", "rb") as f:
                base_predictor = pickle.load(f)
                
                # Clone the predictor (copy parameters)
                user_predictor = CustomBKTPredictor(base_predictor.vocab_parameters.copy())
                
                # Ensure the new predictor has the get_vocabulary_in_order method
                if not hasattr(user_predictor, 'get_vocabulary_in_order'):
                    def get_vocabulary_in_order(self):
                        """Return vocabulary items in their original qbank order"""
                        vocab_items = list(self.vocab_parameters.items())
                        # Sort by the 'order' parameter
                        vocab_items.sort(key=lambda x: x[1].get('order', 999999))
                        return [vocab for vocab, _ in vocab_items]
                    
                    # Bind the method to the instance
                    import types
                    user_predictor.get_vocabulary_in_order = types.MethodType(get_vocabulary_in_order, user_predictor)
                
                # Save the user-specific predictor
                save_custom_bkt(user_predictor, user_id)
                print(f"[BKT] Created user-specific predictor for {user_id}")
                return user_predictor
        else:
            print("[BKT] Base custom predictor not found")
            return None
    except Exception as e:
        print(f"[BKT] Error creating user BKT predictor: {e}")
        return None

# Add to bkt_engine.py
def get_vocab_mastery(vocab, default_for_new=0.4, user_performance=None, user_id=None):
    """Get current mastery level with custom BKT predictor"""
    # First try to use the state (for backward compatibility)
    state = load_temp_state(user_id)
    predictions = state.get("predictions", {})
    
    # If the vocab exists in predictions, return its mastery
    if vocab.lower() in predictions:
        return float(predictions[vocab.lower()].get("p_mastery", 0.5))
    
    # Try using the custom predictor
    custom_bkt = get_custom_bkt(user_id)
    if custom_bkt and vocab.lower() in custom_bkt.vocab_parameters:
        # Get this user's history with this vocabulary
        history = []
        if user_performance and vocab in user_performance:
            history = user_performance[vocab].get("answers", [])
        
        # Predict mastery using custom BKT
        mastery = custom_bkt.predict(vocab.lower(), history)
        return mastery
    
    # Fallback to default with adjustment based on performance
    if user_performance and isinstance(user_performance, dict):
        # Calculate average mastery across all known vocabularies
        known_masteries = [float(pred.get("p_mastery", 0.5)) for pred in predictions.values()]
        if known_masteries:
            avg_known_mastery = sum(known_masteries) / len(known_masteries)
            
            # Calculate user's recent accuracy across all words
            all_answers = []
            for data in user_performance.values():
                all_answers.extend(data.get("answers", []))
            
            # If user has consistently high accuracy, increase starting mastery
            if all_answers:
                recent_accuracy = sum(all_answers) / len(all_answers)
                # Scale default based on both existing masteries and recent accuracy
                default_adjustment = (avg_known_mastery * 0.5) + (recent_accuracy * 0.5)
                
                # Cap the adjustment to avoid too steep difficulty increases
                adjusted_default = min(0.65, default_for_new + (default_adjustment - 0.5))
                print(f"[BKT] Adjusting default mastery for '{vocab}' from {default_for_new} to {adjusted_default:.2f} based on performance")
                return adjusted_default
    
    return default_for_new

def get_vocabulary_from_question(question):
    """Extract vocabulary from question object"""
    if not question:
        return None
    
    # Try different attributes that might contain the vocabulary
    if hasattr(question, 'vocabulary'):
        return question.vocabulary
    elif hasattr(question, 'word_to_translate'):
        return question.word_to_translate
    elif isinstance(question, dict):
        return question.get('vocabulary') or question.get('word_to_translate')
    
    return None

def load_bkt_data_from_database(user_id):
    """Load BKT data from database with better validation"""
    try:
        arami = pymongo.MongoClient(uri)["arami"]
        user_doc = arami["users"].find_one({"user_id": int(user_id)})
        
        if not user_doc or "bkt_data" not in user_doc:
            print(f"[BKT] No BKT data found for user {user_id}")
            return {}
        
        bkt_data = user_doc["bkt_data"]
        
        # ENHANCED: Validate and clean BKT data structure
        cleaned_data = {}
        fixed_count = 0
        
        for vocab, data in bkt_data.items():
            if vocab in ['predictions', 'last_updated', 'fitted', 'refit_counter', 'source', 'force_update_id']:  # Skip metadata
                continue
                
            if not isinstance(data, dict):
                print(f"[BKT] Skipping invalid BKT data for '{vocab}': {type(data).__name__}")
                fixed_count += 1
                continue
                
            # Validate required fields
            required_fields = ['prior', 'guess', 'slip', 'learn']  # Updated field names
            valid_data = True
            
            for field in required_fields:
                if field not in data:
                    print(f"[BKT] Missing field '{field}' for vocab '{vocab}'")
                    valid_data = False
                    break
                    
                # Check if the value is a valid number
                value = data[field]
                if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                    print(f"[BKT] Invalid {field} value for '{vocab}': {value}")
                    valid_data = False
                    break
            
            if valid_data:
                cleaned_data[vocab] = data
            else:
                # Fix invalid data with defaults
                cleaned_data[vocab] = {
                    'prior': 0.5,
                    'guess': 0.25,
                    'slip': 0.1,
                    'learn': 0.15,
                    'observations': []
                }
                fixed_count += 1
                print(f"[BKT] Fixed invalid data for '{vocab}' with defaults")
                
        if fixed_count > 0:
            print(f"[BKT] Fixed {fixed_count} issues in BKT data structure")
            
        print(f"[BKT] Loaded BKT data from database for user {user_id}")
        return cleaned_data
        
    except Exception as e:
        print(f"[BKT] Error loading BKT data from database: {e}")
        return {}

def normalize_vocabulary_key(vocab):
    """Normalize vocabulary keys for consistent storage and retrieval"""
    if not vocab:
        return ""
    return str(vocab).lower().strip()

def normalize_vocabulary(vocab):
    """Normalize vocabulary for consistent database storage"""
    if not vocab:
        return None
        
    # Create a standard form - lowercase with proper spacing
    normalized = str(vocab).lower().strip()
    # Remove any multiple spaces
    normalized = ' '.join(normalized.split())
    return normalized

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

def select_adaptive_questions(questions_pool, user_performance=None, user_id=None, overall_proficiency=None):
    """
    Select adaptive questions based on vocabulary mastery AND overall user proficiency
    
    Args:
        questions_pool: Available questions grouped by vocabulary
        user_performance: Individual vocabulary performance data
        user_id: User identifier
        overall_proficiency: User's overall proficiency score (0.0-1.0)
    """
    print(f"[BKT] Starting adaptive question selection for user {user_id}")
    print(f"[BKT] Overall user proficiency: {overall_proficiency:.3f}" if overall_proficiency else "[BKT] No overall proficiency provided")
    
    # Group questions by vocabulary
    vocab_questions = {}
    questions_seen = set()
    
    for question in questions_pool:
        vocab = get_vocabulary_from_question(question)
        if not vocab:
            continue
        
        question_type = getattr(question, "type", "Unknown")
        
        if vocab not in vocab_questions:
            vocab_questions[vocab] = {
                "lesson": [],
                "pronunciation": [],
                "practice": []
            }
        
        # Categorize questions
        if question_type == "Lesson":
            vocab_questions[vocab]["lesson"].append(question)
        elif question_type == "Pronunciation":
            vocab_questions[vocab]["pronunciation"].append(question)
        else:
            vocab_questions[vocab]["practice"].append(question)
    
    # Get vocabularies in order of appearance in questions
    vocab_order = []
    for question in questions_pool:
        vocab = get_vocabulary_from_question(question)
        if vocab and vocab not in vocab_order:
            vocab_order.append(vocab)
    
    print(f"[BKT] Found {len(vocab_order)} vocabularies: {vocab_order}")
    
    # ENHANCED: Calculate global difficulty adjustment based on overall proficiency
    global_difficulty_adjustment = calculate_global_difficulty_adjustment(overall_proficiency)
    print(f"[BKT] Global difficulty adjustment: {global_difficulty_adjustment:.2f}")
    
    selected_questions = []
    previous_mastery = 0.5
    
    for vocab in vocab_order:
        if vocab not in vocab_questions:
            continue
            
        # Get individual vocabulary mastery
        vocab_mastery = get_vocab_mastery(vocab, user_id=user_id)
        
        # ENHANCED: Blend individual mastery with overall proficiency
        if overall_proficiency is not None:
            # Weight: 70% individual vocab mastery, 30% overall proficiency
            blended_mastery = (vocab_mastery * 0.7) + (overall_proficiency * 0.3)
            print(f"[BKT] Vocab '{vocab}': individual={vocab_mastery:.3f}, overall={overall_proficiency:.3f}, blended={blended_mastery:.3f}")
        else:
            blended_mastery = vocab_mastery
            print(f"[BKT] Vocab '{vocab}': using individual mastery={vocab_mastery:.3f}")
        
        # Apply mastery transfer from previous vocabulary
        if vocab != vocab_order[0]:
            blended_mastery = (blended_mastery * 0.8) + (previous_mastery * 0.2)
        
        q_sets = vocab_questions[vocab]
        
        # 1. Add lesson question if available and not seen
        if q_sets["lesson"]:
            lesson_q = q_sets["lesson"][0]
            selected_questions.append(lesson_q)
            questions_seen.add(getattr(lesson_q, "id", None))
            print(f"[BKT] Added lesson question for '{vocab}'")
        
        # 2. Add pronunciation question if available and not seen
        if q_sets["pronunciation"]:
            pron_q = q_sets["pronunciation"][0]
            selected_questions.append(pron_q)
            questions_seen.add(getattr(pron_q, "id", None))
            print(f"[BKT] Added pronunciation question for '{vocab}'")
        
        # 3. ENHANCED: Select practice questions with global difficulty adjustment
        remaining_slots = 3 - (1 if q_sets["pronunciation"] else 0)
        practice_questions = select_by_difficulty_with_global_adjustment(
            q_sets["practice"], 
            blended_mastery, 
            remaining_slots, 
            vocabulary=vocab, 
            user_id=user_id,
            global_adjustment=global_difficulty_adjustment
        )
        
        for q in practice_questions:
            selected_questions.append(q)
            questions_seen.add(getattr(q, "id", None))
            difficulty = getattr(q, "difficulty", "N/A")
            print(f"[BKT] Added {q.type} question for '{vocab}' (difficulty: {difficulty}, blended mastery: {blended_mastery:.3f})")
        
        previous_mastery = blended_mastery
    
    print(f"[BKT] Selected {len(selected_questions)} total questions")
    return selected_questions

def calculate_global_difficulty_adjustment(overall_proficiency):
    """
    Calculate global difficulty adjustment based on overall user proficiency
    
    Returns:
        float: Adjustment factor (-2 to +2)
               Negative = easier questions, Positive = harder questions
    """
    if overall_proficiency is None:
        return 0.0
    
    # Convert proficiency (0.0-1.0) to difficulty adjustment (-2 to +2)
    if overall_proficiency < 0.2:          # Very low proficiency (0-20%)
        adjustment = -2.0  # Much easier questions (difficulty 1-2)
    elif overall_proficiency < 0.4:       # Low proficiency (20-40%)
        adjustment = -1.0  # Easier questions (difficulty 1-3)
    elif overall_proficiency < 0.6:       # Medium proficiency (40-60%)
        adjustment = 0.0   # Standard difficulty (difficulty 2-4)
    elif overall_proficiency < 0.8:       # High proficiency (60-80%)
        adjustment = 1.0   # Harder questions (difficulty 3-5)
    else:                                  # Very high proficiency (80-100%)
        adjustment = 2.0   # Much harder questions (difficulty 4-5)
    
    print(f"[BKT] Proficiency {overall_proficiency:.3f} → Difficulty adjustment {adjustment}")
    return adjustment

def select_by_difficulty_with_global_adjustment(questions, mastery, count, vocabulary=None, user_id=None, global_adjustment=0.0):
    """
    Enhanced difficulty selection that considers both mastery and global proficiency
    """
    if not questions or count <= 0:
        return []
    
    # Group questions by difficulty
    by_difficulty = defaultdict(list)
    for q in questions:
        difficulty = getattr(q, "difficulty", 2)
        if difficulty is None or difficulty == 0:  # Lesson type
            difficulty = 2  # Default to medium
        by_difficulty[difficulty].append(q)
    
    # Get difficulty factor for this specific vocabulary
    custom_bkt = get_custom_bkt(user_id)
    difficulty_factor = 1.0
    if custom_bkt and vocabulary in custom_bkt.vocab_parameters:
        difficulty_factor = custom_bkt.vocab_parameters[vocabulary].get("difficulty_factor", 1.0)
    
    # ENHANCED: Combine individual difficulty factor with global adjustment
    combined_adjustment = (difficulty_factor - 1.0) * 2 + global_adjustment
    
    print(f"[BKT] Vocab '{vocabulary}': individual_factor={difficulty_factor:.2f}, global_adj={global_adjustment:.2f}, combined={combined_adjustment:.2f}")
    
    # UPDATED: Select target difficulties based on mastery + combined adjustment (1-5 range)
    base_difficulties = []
    if mastery < 0.3:          # Low mastery
        base_difficulties = [1, 2, 3]
    elif mastery < 0.7:        # Medium mastery  
        base_difficulties = [2, 3, 4]
    else:                      # High mastery
        base_difficulties = [3, 4, 5]
    
    # Apply combined adjustment to target difficulties
    target_difficulties = []
    for diff in base_difficulties:
        adjusted_diff = max(1, min(5, round(diff + combined_adjustment)))  # Cap between 1-5
        target_difficulties.append(adjusted_diff)
    
    print(f"[BKT] Base difficulties {base_difficulties} → Adjusted {target_difficulties} (mastery={mastery:.3f})")
    
    # Collect questions of target difficulties
    selected = []
    for diff in target_difficulties:
        if diff in by_difficulty:
            selected.extend(by_difficulty[diff])
    
    # If not enough questions, expand to adjacent difficulties
    if len(selected) < count:
        for diff in sorted(by_difficulty.keys()):
            if diff not in target_difficulties:
                selected.extend(by_difficulty[diff])
                if len(selected) >= count:
                    break
    
    # Shuffle and limit to requested count
    import random
    random.shuffle(selected)
    result = selected[:count]
    
    # Log final selections with difficulty info
    for q in result:
        diff = getattr(q, "difficulty", "N/A")
        q_type = getattr(q, 'type', 'Unknown')
        print(f"[BKT] SELECTED: {q_type} (difficulty {diff}) for '{vocabulary}' [mastery={mastery:.2f}, adj={combined_adjustment:.2f}]")
    
    return result

def update_current_vocab(completed_vocab, ordered_vocab_list):
    """Update the current vocabulary tracking based on completion with case-insensitive matching"""
    global current_vocab
    
    if not completed_vocab or not ordered_vocab_list:
        print("[BKT] Warning: Empty vocabulary or list provided")
        print(f"[BKT] Completed vocab: '{completed_vocab}', List length: {len(ordered_vocab_list) if ordered_vocab_list else 0}")
        if completed_vocab:  # Show some details about the completed vocab
            print(f"[BKT] Vocab type: {type(completed_vocab).__name__}, Length: {len(completed_vocab)}")
        return None
        
    try:
        # Case-insensitive match using normalize_vocabulary
        lower_ordered = [normalize_vocabulary(v) for v in ordered_vocab_list]
        lower_completed = normalize_vocabulary(completed_vocab)
        
        print(f"[BKT] Searching for normalized '{lower_completed}' in {len(lower_ordered)} vocabulary items")
        
        # Check for exact case before normalization to detect inconsistencies
        if completed_vocab in ordered_vocab_list:
            print(f"[BKT] Found exact case match for '{completed_vocab}'")
        else:
            # Check if case difference would be the only issue
            matching_vocab = find_vocabulary_in_list(completed_vocab, ordered_vocab_list)
            if matching_vocab:
                print(f"[BKT] Case difference detected: '{completed_vocab}' vs '{matching_vocab}'")
                
        if lower_completed in lower_ordered:
            current_index = lower_ordered.index(lower_completed)
            print(f"[BKT] Found '{completed_vocab}' at position {current_index+1}/{len(ordered_vocab_list)}")
            
            # Display some surrounding vocabulary for context
            start_idx = max(0, current_index-1)
            end_idx = min(len(ordered_vocab_list), current_index+2)
            context = ordered_vocab_list[start_idx:end_idx]
            print(f"[BKT] Vocabulary context: {', '.join(context)}")
            
            if current_index < len(ordered_vocab_list) - 1:
                next_vocab = ordered_vocab_list[current_index + 1]
                current_vocab = next_vocab
                print(f"[BKT] Advancing to next vocabulary: '{current_vocab}'")
                return next_vocab
            else:
                current_vocab = None
                print("[BKT] All vocabularies completed in this sequence")
                return None
        else:
            print(f"[BKT] Warning: Vocabulary '{completed_vocab}' not found in ordered list")
            # Try prefix matching as fallback
            matches = []
            for i, lower_vocab in enumerate(lower_ordered):
                if lower_completed and lower_vocab and (lower_vocab.startswith(lower_completed[:5]) or lower_completed.startswith(lower_vocab[:5])):
                    matches.append((i, ordered_vocab_list[i]))
                    
            if matches:
                for idx, match in matches:
                    print(f"[BKT] Found possible match: '{match}' at position {idx+1}")
                
                current_index = matches[0][0]
                next_vocab = ordered_vocab_list[current_index]
                print(f"[BKT] Using best match: '{next_vocab}'")
                
                if current_index < len(ordered_vocab_list) - 1:
                    next_vocab = ordered_vocab_list[current_index + 1]
                    current_vocab = next_vocab
                    print(f"[BKT] Advancing to next vocabulary: '{current_vocab}'")
                    return next_vocab
    except ValueError as e:
        print(f"[BKT] ValueError in update_current_vocab: {e}")
    except Exception as e:
        print(f"[BKT] Error in update_current_vocab: {e}")
        import traceback
        traceback.print_exc()
    
    # If we get here, we couldn't find a valid next vocabulary
    print("[BKT] Warning: Couldn't determine next vocabulary")
    return None

def check_vocab_completion(performance_data, vocab):
    """Check if a vocabulary item has been completed (all questions answered)"""
    if not vocab or not performance_data:
        return False
    
    # Normalize vocab for comparison
    normalized_vocab = normalize_vocabulary(vocab)
    
    # First try direct match
    if normalized_vocab in performance_data:
        data = performance_data[normalized_vocab]
        answers = data.get("answers", [])
        return len(answers) >= 4  # Consider vocab complete after 4 answers
    
    # Try case-insensitive match
    for perf_vocab, data in performance_data.items():
        if normalize_vocabulary(perf_vocab) == normalized_vocab:
            answers = data.get("answers", [])
            print(f"[BKT] Found case-variant completion data for '{vocab}' as '{perf_vocab}'")
            return len(answers) >= 4
    
    return False

def process_question_answer(question, is_correct, page):
    """Process a question answer and determine if rebatching is needed"""
    vocab = getattr(question, "vocabulary", None)
    if not vocab:
        return False  # No vocabulary to process
        
    # Get performance data - FIXED SESSION HANDLING
    user_id = page.session.get("user_id")
    
    # Properly handle session storage
    try:
        performance_data = page.session.get("user_performance")
    except Exception:
        performance_data = {}
    
    # Initialize if None
    if performance_data is None:
        performance_data = {}
    
    if vocab not in performance_data:
        performance_data[vocab] = {"answers": []}
    
    # Record answer (1 for correct, 0 for incorrect)
    performance_data[vocab]["answers"].append(1 if is_correct else 0)
    page.session.set("user_performance", performance_data)
    
    # Get ordered vocabulary list
    custom_bkt = get_custom_bkt(user_id)
    ordered_vocab = custom_bkt.get_vocabulary_in_order() if custom_bkt else []
    
    # Check if this vocabulary is complete
    is_vocab_complete = check_vocab_completion(performance_data, vocab)
    
    if is_vocab_complete:
        print(f"[BKT] Vocabulary '{vocab}' completed!")
        # Vocabulary complete, move to next vocabulary
        next_vocab = update_current_vocab(vocab, ordered_vocab)
        
        # Check if we need to rebatch for next vocabulary
        performance_summary = {}
        if vocab in performance_data:
            answers = performance_data[vocab].get("answers", [])
            if answers:
                performance_summary[vocab] = {
                    "correct": sum(answers),
                    "incorrect": len(answers) - sum(answers)
                }
                # Apply immediate difficulty adjustment
                adjust_difficulty_after_session(user_id, performance_summary, {})
                
        need_rebatch, rebatch_vocab = should_rebatch(performance_data, vocab, ordered_vocab)
        
        if need_rebatch:
            print(f"[BKT] Rebatching needed for next vocabulary '{rebatch_vocab}'")
            return True  # Signal that rebatching is needed
    
    return False  # No rebatching needed

def select_by_difficulty(questions, mastery, count, vocabulary=None, user_id=None):
    """Select questions with appropriate difficulty based on mastery level."""
    if not questions or count <= 0:
        return []
        
    # Log mastery and selection strategy
    print(f"[BKT] Selecting questions for mastery {mastery:.2f}")
    
    # Check for difficulty factor from BKT model for this vocabulary
    difficulty_factor = 1.0
    if vocabulary:
        custom_bkt = get_custom_bkt(user_id)
        if custom_bkt and vocabulary in custom_bkt.vocab_parameters:
            difficulty_factor = custom_bkt.vocab_parameters[vocabulary].get("difficulty_factor", 1.0)
            print(f"[BKT] Found difficulty factor {difficulty_factor:.2f} for vocabulary '{vocabulary}'")
    
    # Group questions by difficulty
    by_difficulty = {}
    for q in questions:
        difficulty = getattr(q, "difficulty", 1)
        if difficulty not in by_difficulty:
            by_difficulty[difficulty] = []
        by_difficulty[difficulty].append(q)
    
    # Apply difficulty factor to adjust target difficulties
    difficulty_offset = round((difficulty_factor - 1.0) * 2)  # Convert 0.5-2.0 range to -1 to +2 offset
    print(f"[BKT] Applying difficulty offset of {difficulty_offset} based on factor {difficulty_factor:.2f}")
    
    # Select appropriate difficulties based on mastery and difficulty factor
    if mastery < 0.3:  # Low mastery - easier questions
        target_difficulties = [max(1, 1 + difficulty_offset), 
                             max(1, 2 + difficulty_offset), 
                             max(1, 3 + difficulty_offset)]
        print(f"[BKT] Low mastery detected - selecting questions with difficulty {target_difficulties}")
    elif mastery < 0.7:  # Medium mastery - medium questions
        target_difficulties = [max(1, 2 + difficulty_offset), 
                             max(1, 3 + difficulty_offset), 
                             max(1, 4 + difficulty_offset)]
        print(f"[BKT] Medium mastery detected - selecting questions with difficulty {target_difficulties}")
    else:  # High mastery - harder questions
        target_difficulties = [max(1, 3 + difficulty_offset), 
                             max(1, 4 + difficulty_offset), 
                             min(5, 5 + difficulty_offset)]
        print(f"[BKT] High mastery detected - selecting questions with difficulty {target_difficulties}")
    
    # Cap difficulties at 5
    target_difficulties = [min(5, d) for d in target_difficulties]
    
    # Collect questions of target difficulties
    selected = []
    for diff in target_difficulties:
        selected.extend(by_difficulty.get(diff, []))
    
    # If not enough questions, take any available
    if len(selected) < count:
        for diff in sorted(by_difficulty.keys()):
            if diff not in target_difficulties:
                selected.extend(by_difficulty[diff])
    
    # Shuffle and limit to requested count
    import random
    random.shuffle(selected)
    result = selected[:count]
    
    # Log final selections
    for q in result:
        diff = getattr(q, "difficulty", "N/A")
        print(f"[BKT] Selected {getattr(q, 'type', 'Unknown')} question with difficulty {diff} for vocab '{vocabulary}' (mastery {mastery:.2f})")
    
    return result

def should_rebatch(performance_data, current_vocab, vocab_list, threshold=0.3):
    """Determine if rebatching is needed based on performance."""
    if not current_vocab or not vocab_list or current_vocab not in performance_data:
        return False, None
        
    # Get the index of the current vocab in the list (with case-insensitive matching)
    current_index = -1
    norm_current_vocab = current_vocab.lower().strip()
    for i, v in enumerate(vocab_list):
        if v.lower().strip() == norm_current_vocab:
            current_index = i
            break
            
    if current_index == -1:
        print(f"[BKT] Warning: Could not find '{current_vocab}' in vocabulary list")
        return False, None
        
    # If this was the last vocabulary, no need to rebatch
    if current_index >= len(vocab_list) - 1:
        return False, None
        
    # Calculate actual accuracy for the current vocabulary
    data = performance_data[current_vocab]
    actual_accuracy = sum(data.get("answers", [])) / len(data.get("answers", [1])) if data.get("answers") else 0.5
    
    # Get predicted mastery and expected accuracy  
    mastery = get_vocab_mastery(current_vocab)
    
    # Log the comparison between actual and predicted performance
    print(f"[BKT] Vocab '{current_vocab}' - Actual accuracy: {actual_accuracy:.2f}, Expected mastery: {mastery:.2f}")
    
    # Apply difficulty adjustment immediately here rather than waiting for adjust_difficulty_after_session
    custom_bkt = get_custom_bkt()
    
    next_vocab = vocab_list[current_index + 1] if current_index + 1 < len(vocab_list) else None
    if next_vocab and custom_bkt:
        if actual_accuracy > 0.8: # High accuracy
            # Apply difficulty increase for next vocab
            current_difficulty = 1.0
            if next_vocab in custom_bkt.vocab_parameters:
                current_difficulty = custom_bkt.vocab_parameters[next_vocab].get("difficulty_factor", 1.0)
            
            # Increase difficulty for next vocabulary
            new_difficulty = min(2.0, current_difficulty * 1.2)  # More aggressive increase
            
            if next_vocab not in custom_bkt.vocab_parameters:
                custom_bkt.vocab_parameters[next_vocab] = {}
                
            custom_bkt.vocab_parameters[next_vocab]["difficulty_factor"] = new_difficulty
            print(f"[BKT] IMMEDIATE TRANSFER: Increased difficulty for next vocab '{next_vocab}': {current_difficulty:.2f} → {new_difficulty:.2f}")
            save_custom_bkt(None, custom_bkt)
            
            return True, next_vocab
    
    return False, None

def threaded_update_bkt(user_id, correct_answers, incorrect_answers):
    """
    Runs update_bkt in a thread, waiting for any previous thread to finish.
    """
    global bkt_thread
    with bkt_thread_lock:
        if bkt_thread is not None and bkt_thread.is_alive():
            print("[threaded_update_bkt] Waiting for previous BKT thread to finish...")
            bkt_thread.join()
        
        # COMPLETE THE INCOMPLETE LINE: Check if we have a valid BKT predictor
        bkt_predictor = get_custom_bkt(user_id)
        if bkt_predictor and hasattr(bkt_predictor, 'vocab_parameters'):
            # Process BKT predictor logic here
            ordered_vocab = bkt_predictor.get_vocabulary_in_order()
            print(f"[BKT] Found BKT predictor with {len(ordered_vocab)} vocabulary items")
            
            # Start the update thread
            bkt_thread = threading.Thread(target=update_bkt, args=(user_id, correct_answers, incorrect_answers))
            bkt_thread.start()
        else:
            print("[BKT] No valid BKT predictor found, creating new thread anyway")
            bkt_thread = threading.Thread(target=update_bkt, args=(user_id, correct_answers, incorrect_answers))
            bkt_thread.start()

def get_user_library(user_id=None):
    """Get vocabulary library for a user"""
    try:
        # Try to load from temp file first
        if os.path.exists("temp_library.json"):
            with open("temp_library.json", "r") as f:
                return json.load(f)
                
        # If temp file doesn't exist and user_id is provided, get from database
        if user_id:
            uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"
            arami = pymongo.MongoClient(uri)["arami"]
            users_col = arami["users"]
            
            user = users_col.find_one({"user_id": int(user_id)})
            if user and "library" in user:
                return user["library"]
    except Exception as e:
        print(f"[BKT] Error getting user library: {e}")
    return []

def get_user_temp_file(user_id=None):
    """Get user-specific temp file path"""
    if user_id:
        return f"temp_state_{user_id}.json"
    return "temp_state.json"

# Update the load_temp_state function to include lesson data
def load_temp_state(user_id=None):
    """Load temp state WITHOUT lesson BKT data integration"""
    temp_file = f"temp_bkt_data_{user_id}.json" if user_id else TEMP_FILE
    
    try:
        if os.path.exists(temp_file):
            with open(temp_file, 'r') as f:
                state = json.load(f)
        else:
            state = {"predictions": {}, "history": {}}
        
        # REMOVED: Do not try to merge lesson BKT data automatically
        # This was causing the infinite loop
        
        return state
        
    except Exception as e:
        print(f"[BKT] Error loading temp state: {e}")
        return {"predictions": {}, "history": {}}

def save_temp_state(state, user_id=None):
    """Save temporary state to file with user-specific path support."""
    filepath = get_user_temp_file(user_id)
    with open(filepath, "w") as f:
        json.dump(state, f)

def get_all_p_masteries(user_id=None):
    """Get all mastery probabilities for all vocabulary items."""
    # First check if we have a pre-computed sequence
    sequence_file = 'bkt_sequence.json'
    if os.path.exists(sequence_file):
        try:
            with open(sequence_file, 'r') as f:
                sequence = json.load(f)
                if sequence and isinstance(sequence, list):
                    print(f"[DEBUG] Loaded BKT sequence from file: {len(sequence)} values")
                    return sequence
        except Exception as e:
            print(f"[DEBUG] Error loading BKT sequence from file: {e}")
    
    # Fall back to reconstructing from predictions
    try:
        with open('bkt_predictions.json', 'r') as f:
            predictions = json.load(f)
        
        # Get vocabulary in order
        custom_bkt = get_custom_bkt(user_id)
        if custom_bkt:
            try:
                # Get vocabulary in canonical order
                ordered_vocab = custom_bkt.get_vocabulary_in_order()
                
                # Build sequence in that order
                p_masteries = [float(predictions.get(vocab, {}).get('p_mastery', 0.5)) 
                            for vocab in ordered_vocab]
                
                print(f"[DEBUG] Extracted mastery sequence: {p_masteries}")
                return p_masteries
            except Exception as e:
                print(f"[DEBUG] Error getting ordered vocabulary: {e}")
        
        # Fall back to alphabetical order
        p_masteries = [float(pred.get('p_mastery', 0.5)) for pred in predictions.values()]
        print(f"[DEBUG] Extracted {len(p_masteries)} mastery values using alphabetical order")
        return p_masteries
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[DEBUG] Error loading BKT predictions: {e}")
        return []

def save_temp_state(state, user_id=None):
    with open(TEMP_FILE, "w") as f:
        json.dump(state, f, indent=4)

def calculate_bkt_confidence(mastery, guess, slip, vocab=None, params=None):
    """Calculate confidence based on BKT parameters with more dynamic weighting"""
    # Normalize input parameters
    mastery = min(0.99, max(0.01, mastery))
    guess = min(0.5, max(0.01, guess))
    slip = min(0.5, max(0.01, slip))
    
    # IMPROVED: Calculate certainty component - higher near 0 or 1, but with reduced weight
    certainty = 1.5 * abs(mastery - 0.5)  # Reduced from 2.0 to 1.5
    
    # Basic confidence starts at 0.5
    base_conf = 0.5
    
    # Mastery contributes at the extremes, but with a more logarithmic curve
    # This reduces the linear relationship between mastery and confidence
    if mastery > 0.5:
        mastery_contrib = 0.20 * math.log(1 + (mastery - 0.5) * 2) / math.log(3)
    else:
        mastery_contrib = 0.20 * math.log(1 + (0.5 - mastery) * 2) / math.log(3)
    
    # Lower guess rates increase confidence (less randomness)
    guess_contrib = 0.20 * (1.0 - (guess / 0.5))  # Increased weight from 0.15 to 0.20
    
    # Lower slip rates increase confidence (more consistency)
    slip_contrib = 0.15 * (1.0 - (slip / 0.5))  # Increased weight from 0.10 to 0.15
    
    # NEW: Add learning history factor if available
    history_contrib = 0.0
    if params and 'observations' in params:
        obs_count = len(params['observations'])
        # More observations increase confidence, but with diminishing returns
        history_contrib = 0.15 * min(1.0, math.log(1 + obs_count) / math.log(10))
        
        # But incorrect answers in recent history decrease confidence
        recent_obs = params['observations'][-5:] if len(params['observations']) > 5 else params['observations']
        incorrect_count = sum(1 for o in recent_obs if not o.get('correct', True))
        if incorrect_count > 0:
            history_contrib -= 0.05 * incorrect_count
    
    # Calculate confidence from components
    confidence = base_conf + mastery_contrib + guess_contrib + slip_contrib + history_contrib
    
    # Keep within reasonable bounds
    confidence = min(0.95, max(0.3, confidence))
    
    # Debug components with more detail
    print(f"[BKT] Confidence for {vocab or 'unknown'} (mastery={mastery:.3f}): {confidence:.3f}")
    print(f"[BKT]   Components: Base={base_conf:.2f}, Mastery={mastery_contrib:.2f}, " +
          f"Guess={guess_contrib:.2f}, Slip={slip_contrib:.2f}, History={history_contrib:.2f}")
    
    return confidence

def update_bkt(user_id, correct_answers, incorrect_answers, impact_scale=1.0, is_daily_review=False):
    """Update BKT model with new observations, with optional impact scaling."""
    try:
        reset_bkt_update_counters()
        
        # Store user_id for parameter initialization
        initialize_vocabulary_parameters.current_user_id = user_id
        
        # Start tracking revisions
        print(f"[update_bkt] Processing {len(correct_answers)} correct and {len(incorrect_answers)} incorrect answers")
        print(f"[BKT] Context: {'DAILY REVIEW' if is_daily_review else 'LESSON'}, impact_scale={impact_scale}")
        
        # Debug the actual vocabulary items being processed
        correct_vocab_list = [get_vocabulary_from_question(q) for q in correct_answers.values()]
        incorrect_vocab_list = [get_vocabulary_from_question(q) for q in incorrect_answers.values()]
        correct_vocab_list = [v for v in correct_vocab_list if v]  # Filter out None values
        incorrect_vocab_list = [v for v in incorrect_vocab_list if v]  # Filter out None values
        
        print(f"[BKT] Vocabulary being processed: {', '.join(correct_vocab_list + incorrect_vocab_list)}")
        
        # Get existing BKT state
        custom_bkt = get_custom_bkt(user_id)
        if not custom_bkt:
            print("[update_bkt] No custom BKT predictor found. Creating one.")
            custom_bkt = CustomBKTPredictor({})
        
        # Apply time decay before updates
        if custom_bkt:
            apply_time_decay(custom_bkt)
        
        # Load existing history
        state = load_temp_state(user_id)
        predictions = state.get("predictions", {})
        history = state.get("history", {})
        
        # CRITICAL FIX: Process vocabularies from the session answers
        vocabularies_processed = set()
        
        # Process correct answers
        for question_id, question_data in correct_answers.items():
            vocab = get_vocabulary_from_question(question_data)
            if vocab:
                vocab = normalize_vocabulary(vocab)
                vocabularies_processed.add(vocab)
                
                # Get difficulty
                difficulty = getattr(question_data, 'difficulty', 1)
                
                # Update BKT with correct answer
                print(f"[BKT] Processing correct answer for '{vocab}' (difficulty: {difficulty})")
                new_mastery = custom_bkt.observe_with_scale(vocab, True, impact_scale, difficulty)
                
                # CRITICAL: Mark as reviewed in daily review context
                if is_daily_review:
                    custom_bkt.mark_vocabulary_reviewed(vocab)
                    print(f"[BKT] Marked '{vocab}' as reviewed (daily review)")
                
                # Update history
                if vocab not in history:
                    history[vocab] = {"corrects": [], "incorrects": []}
                
                timestamp = int(time.time())
                history[vocab]["corrects"].append({
                    "timestamp": timestamp, 
                    "is_review": is_daily_review
                })
        
        # Process incorrect answers
        for question_id, question_data in incorrect_answers.items():
            vocab = get_vocabulary_from_question(question_data)
            if vocab:
                vocab = normalize_vocabulary(vocab)
                vocabularies_processed.add(vocab)
                
                # Get difficulty
                difficulty = getattr(question_data, 'difficulty', 1)
                
                # Update BKT with incorrect answer
                print(f"[BKT] Processing incorrect answer for '{vocab}' (difficulty: {difficulty})")
                new_mastery = custom_bkt.observe_with_scale(vocab, False, impact_scale, difficulty)
                
                # CRITICAL: Mark as reviewed in daily review context
                if is_daily_review:
                    custom_bkt.mark_vocabulary_reviewed(vocab)
                    print(f"[BKT] Marked '{vocab}' as reviewed (daily review)")
                
                # Update history
                if vocab not in history:
                    history[vocab] = {"corrects": [], "incorrects": []}
                
                timestamp = int(time.time())
                history[vocab]["incorrects"].append({
                    "timestamp": timestamp,
                    "is_review": is_daily_review
                })
        
        print(f"[BKT] Processed {len(vocabularies_processed)} unique vocabularies: {list(vocabularies_processed)}")
        
        # Update predictions with review status
        for vocab in vocabularies_processed:
            # Get latest parameters from custom_bkt
            latest_params = custom_bkt.vocab_parameters.get(vocab, {})
            latest_guess = float(latest_params.get('guess', 0.25))
            latest_slip = float(latest_params.get('slip', 0.1))
            latest_mastery = float(latest_params.get('prior', 0.5))
            
            # Calculate confidence using the enhanced function
            confidence = calculate_bkt_confidence(
                latest_mastery,
                latest_guess,
                latest_slip,
                vocab=vocab,
                params=latest_params
            )
            
            # CRITICAL FIX: Determine if this vocabulary was answered correctly in this session
            was_correct = 0  # Default
            for q_data in correct_answers.values():
                if get_vocabulary_from_question(q_data) == vocab:
                    was_correct = 1
                    break
            
            # If not found in correct answers, check incorrect answers
            if was_correct == 0:
                for q_data in incorrect_answers.values():
                    if get_vocabulary_from_question(q_data) == vocab:
                        was_correct = 0  # Explicitly set to 0 for incorrect
                        break
            
            # ENHANCED: Update the predictions dictionary with proper values
            predictions[vocab.lower()] = {
                'p_mastery': latest_mastery,
                'guess': latest_guess,
                'slip': latest_slip,
                'confidence': confidence,  # Now uses enhanced calculation
                'correct': was_correct,  # FIXED: Properly tracks last answer
                'reviewed': True if is_daily_review else False,
                'timestamp': int(time.time()),
                'difficulty_level': 1,
                'transferred_difficulty': 0,
                'observations': latest_params.get('observations', []),
                'response_times': latest_params.get('response_times', [])
            }
            
            print(f"[BKT] Updated prediction for '{vocab}': mastery={latest_mastery:.3f}, " +
                f"confidence={confidence:.3f}, correct={was_correct}")
        
        # Save updated state
        state["predictions"] = predictions
        state["history"] = history
        save_temp_state(state, user_id)
        
        # Save the BKT predictor
        save_custom_bkt(user_id, custom_bkt)
        
        # CRITICAL FIX: Save updated BKT data with review context
        success = save_bkt_data_to_database(user_id, custom_bkt, is_daily_review=is_daily_review)
        if success:
            print(f"[BKT] ✅ Successfully saved BKT data for user {user_id}")
        else:
            print(f"[BKT] ❌ Failed to save BKT data for user {user_id}")
        
        # FIXED: Apply difficulty adjustments BEFORE generating sequence
        adjust_difficulty_after_session(user_id, correct_answers, incorrect_answers)
        
        # FIXED: Generate sequence with comprehensive database integration
        try:
            # Get the most complete sequence using comprehensive database integration
            bkt_sequence = ensure_bkt_data_loaded(user_id, force_db_refresh=True)
            print(f"[BKT] Final comprehensive sequence: {len(bkt_sequence)} values")
            print(f"[BKT] Non-default values in final sequence: {sum(1 for x in bkt_sequence if abs(x - 0.5) > 0.01)}/{len(bkt_sequence)}")
            
            # CRITICAL: Save updated predictions with review status to temp file
            with open('bkt_predictions.json', 'w') as f:
                json.dump(predictions, f, indent=2)
            print(f"[BKT] Saved {len(predictions)} updated predictions with review status")
            
            # Return the enriched sequence
            return bkt_sequence
            
        except Exception as e:
            print(f"[BKT] Error in final sequence generation: {e}")
            # Fallback: Generate basic sequence from custom_bkt
            try:
                ordered_vocab = custom_bkt.get_vocabulary_in_order()
                fallback_sequence = [custom_bkt.get_mastery(vocab) for vocab in ordered_vocab]
                print(f"[BKT] Using fallback sequence with {len(fallback_sequence)} values")
                return fallback_sequence
            except Exception as fallback_error:
                print(f"[BKT] Fallback sequence generation failed: {fallback_error}")
                return []
        
    except Exception as e:
        print(f"[BKT] Critical error in update_bkt: {str(e)}")
        import traceback
        traceback.print_exc()
        return []  # Return empty sequence on error

def adjust_difficulty_after_session(user_id, correct_answers, incorrect_answers):
    """Adjust vocabulary difficulty based on session performance."""
    # Group answers by vocabulary
    vocab_performance = {}
    
    # Process correct answers
    for q in correct_answers.values():
        vocab = get_vocabulary_from_question(q)
        if vocab:
            if vocab not in vocab_performance:
                vocab_performance[vocab] = {"correct": 0, "incorrect": 0}
            vocab_performance[vocab]["correct"] += 1
    
    # Process incorrect answers
    for q in incorrect_answers.values():
        vocab = get_vocabulary_from_question(q)
        if vocab:
            if vocab not in vocab_performance:
                vocab_performance[vocab] = {"correct": 0, "incorrect": 0}
            vocab_performance[vocab]["incorrect"] += 1
    
    # Apply difficulty adjustments
    custom_bkt = get_custom_bkt(user_id) or CustomBKTPredictor()
    for vocab, perf in vocab_performance.items():
        total = perf["correct"] + perf["incorrect"]
        if total == 0:
            continue
            
        correct_rate = perf["correct"] / total
        
        # Get current difficulty factor
        current_difficulty = 1.0  # Default neutral difficulty
        if vocab in custom_bkt.vocab_parameters:
            current_difficulty = custom_bkt.vocab_parameters[vocab].get("difficulty_factor", 1.0)
        
        # Adjust based on performance
        if correct_rate > 0.9 and total >= 3:
            # Excellent performance, increase difficulty
            new_difficulty = min(2.0, current_difficulty * 1.1)
        elif correct_rate < 0.6 and total >= 2:
            # Poor performance, decrease difficulty
            new_difficulty = max(0.5, current_difficulty * 0.9)
        else:
            # No change needed
            new_difficulty = current_difficulty
            
        if new_difficulty != current_difficulty:
            print(f"[BKT] Adjusting difficulty for '{vocab}': {current_difficulty:.2f} → {new_difficulty:.2f}")
            if vocab not in custom_bkt.vocab_parameters:
                custom_bkt.vocab_parameters[vocab] = {}
            custom_bkt.vocab_parameters[vocab]["difficulty_factor"] = new_difficulty
    
    # Save the updated BKT model
    save_custom_bkt(user_id, custom_bkt)

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


def get_existing_parameters(vocab, user_id=None):
    """Try to find existing parameters for this vocabulary from various sources"""
    normalized_vocab = vocab.lower().strip()
    
    # Source 1: Check existing BKT predictor
    try:
        if user_id:
            custom_bkt = get_custom_bkt(user_id)
            if custom_bkt and normalized_vocab in custom_bkt.vocab_parameters:
                print(f"[BKT] Found existing parameters in user's BKT model")
                return custom_bkt.vocab_parameters[normalized_vocab]
    except Exception as e:
        print(f"[BKT] Error checking BKT predictor: {e}")
    
    # Source 2: Check predictions in state
    try:
        state = load_temp_state(user_id)
        predictions = state.get("predictions", {})
        
        if normalized_vocab in predictions:
            pred = predictions[normalized_vocab]
            # Convert prediction format to parameter format
            params = {
                'learn': 0.15,  # Default learning rate
                'guess': float(pred.get('guess', 0.25)),
                'slip': float(pred.get('slip', 0.1)),
                'prior': float(pred.get('p_mastery', 0.5)),
                'observations': []
            }
            print(f"[BKT] Converted existing prediction to parameters for '{vocab}'")
            return params
    except Exception as e:
        print(f"[BKT] Error checking state predictions: {e}")
    
    # Source 3: Check history in state
    try:
        state = load_temp_state(user_id)
        history = state.get("history", {})
        
        if normalized_vocab in history:
            # If we have history but no parameters, create parameters based on history
            vocab_history = history[normalized_vocab]
            corrects = len(vocab_history.get("corrects", []))
            incorrects = len(vocab_history.get("incorrects", []))
            
            if corrects + incorrects > 0:
                # Calculate a history-based prior
                accuracy = corrects / (corrects + incorrects) if corrects + incorrects > 0 else 0.5
                prior = 0.3 + (accuracy * 0.4)  # Scale between 0.3-0.7 based on accuracy
                
                params = {
                    'learn': 0.15,
                    'guess': max(0.15, 0.25 - (0.02 * corrects)),  # Reduce guess with more corrects
                    'slip': min(0.25, 0.1 + (0.02 * incorrects)),  # Increase slip with more incorrects
                    'prior': prior,
                    'observations': []
                }
                
                # Reconstruct observations from history
                for entry in vocab_history.get("corrects", []):
                    params['observations'].append({
                        'timestamp': entry.get('timestamp', int(time.time())),
                        'correct': True,
                        'impact_scale': 1.0
                    })
                for entry in vocab_history.get("incorrects", []):
                    params['observations'].append({
                        'timestamp': entry.get('timestamp', int(time.time())),
                        'correct': False,
                        'impact_scale': 1.0
                    })
                
                print(f"[BKT] Created parameters from history for '{vocab}' with {corrects}/{incorrects} correct/incorrect")
                return params
    except Exception as e:
        print(f"[BKT] Error checking history: {e}")
    
    # No existing parameters found
    return None

    # Add this to bkt_engine.py
def display_bkt_predictions(user_id, filter_vocab=None):
    """Display BKT predictions with daily review data integration"""
    # First try to load from daily review file if it exists
    daily_review_file = f"daily_review_bkt_{user_id}.json"
    predictions = {}
    
    if os.path.exists(daily_review_file):
        try:
            with open(daily_review_file, 'r') as f:
                daily_data = json.load(f)
                predictions = daily_data.get("predictions", {})
                print(f"[BKT] Loaded {len(predictions)} predictions from daily review file")
        except Exception as e:
            print(f"[BKT] Error loading daily review predictions: {e}")
    
    # Fall back to regular predictions file
    if not predictions:
        state = load_temp_state(user_id)
        predictions = state.get("predictions", {})
        
        if not predictions and os.path.exists('bkt_predictions.json'):
            try:
                with open('bkt_predictions.json', 'r') as f:
                    data = json.load(f)
                    predictions = data.get("predictions", data) if isinstance(data, dict) else {}
                    print(f"[BKT] Loaded {len(predictions)} predictions from file")
            except Exception as e:
                print(f"[BKT] Error loading predictions from file: {e}")
    
    # Filter if needed
    if filter_vocab:
        filtered_preds = {k: v for k, v in predictions.items() if k == filter_vocab.lower().strip()}
        if not filtered_preds:
            print(f"No BKT prediction found for '{filter_vocab}'")
            return 0
        predictions = filtered_preds
    
    if not predictions:
        print("\n┌─────────────────────────────────────────┐")
        print("│           BKT MODEL PREDICTIONS          │")
        print("├─────────────────────────────────────────┤")
        print("│ No predictions available                 │")
        print("└─────────────────────────────────────────┘")
        return 0
    
    # Count reviewed items
    reviewed_count = sum(1 for pred in predictions.values() if pred.get('reviewed', False))
    
    print(f"[BKT] Total vocabularies: {len(predictions)}, Reviewed: {reviewed_count}")
    
    # Print header with reviewed count
    print("\n┌────────────────────────────────────────────────────────────────────────────────────────┐")
    print(f"│                        BKT MODEL PREDICTIONS ({reviewed_count}/{len(predictions)} reviewed)                      │")
    print("├──────────────────────┬───────────┬──────────┬──────────┬──────────┬──────────┬────────┤")
    print("│ Vocabulary           │ Mastery   │ Guess    │ Slip     │ Conf     │ Correct  │ Review │")
    print("├──────────────────────┼───────────┼──────────┼──────────┼──────────┼──────────┼────────┤")
    
    # Sort by mastery descending
    try:
        sorted_items = sorted(predictions.items(), 
                            key=lambda x: float(x[1].get('p_mastery', 0)), 
                            reverse=True)
        print(f"[BKT] Successfully sorted {len(sorted_items)} items by mastery")
    except (ValueError, TypeError) as e:
        print(f"[BKT] Warning: Could not sort by mastery ({e}), using alphabetical order")
        sorted_items = sorted(predictions.items())
    
    # Print each vocabulary item
    for vocab, pred in sorted_items:
        try:
            p_mastery = float(pred.get('p_mastery', 0))
            guess = float(pred.get('guess', 0))
            slip = float(pred.get('slip', 0))
            conf = float(pred.get('confidence', 0))
        except (ValueError, TypeError) as e:
            print(f"[BKT] Warning: Invalid numeric data for '{vocab}': {e}, using defaults")
            p_mastery, guess, slip, conf = 0.0, 0.25, 0.1, 0.5
            
        correct = pred.get('correct', "-")
        reviewed = "Yes" if pred.get('reviewed', False) else "No"
        
        # Format vocab name (truncate if too long)
        vocab_display = vocab[:18] + '..' if len(vocab) > 20 else vocab.ljust(20)
        
        # Format values with color indicators using ASCII
        mastery_str = f"{p_mastery:.2f}" + ('*' if p_mastery > 0.85 else ' ')
        
        print(f"│ {vocab_display:<20} │ {mastery_str:^9} │ {guess:^8.2f} │ {slip:^8.2f} │ {conf:^8.2f} │ {correct:^8} │ {reviewed:^6} │")
    
    print("└──────────────────────┴───────────┴──────────┴──────────┴──────────┴──────────┴────────┘")
    print("* Mastery levels above 0.85 are considered 'mastered'")
    print(f"[BKT] Displayed {reviewed_count} vocabulary predictions from daily review")
    
    return reviewed_count

def debug_question_object(question, prefix=""):
    """Debug helper to print question object details"""
    if not question:
        print(f"{prefix}[BKT] Question object is None or empty")
        return
        
    print(f"{prefix}[BKT] Question object type: {type(question).__name__}")
    
    # Try to print relevant attributes
    for attr in ['vocabulary', 'word_to_translate', 'type', 'difficulty', 'correct', 'id']:
        if hasattr(question, attr):
            value = getattr(question, attr)
            print(f"{prefix}[BKT]   - {attr}: {value}")
    
    # For dictionary-style objects
    if isinstance(question, dict):
        for key in ['vocabulary', 'word_to_translate', 'type', 'difficulty', 'correct', 'id']:
            if key in question:
                print(f"{prefix}[BKT]   - {key}: {question[key]}")

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

def apply_time_decay(custom_bkt, max_mastery_decrease=0.3):
    """Apply time-based decay to mastery values that haven't been practiced recently"""
    now = int(time.time())
    updated_count = 0
    invalid_count = 0
    
    # Debug the vocab_parameters structure
    print(f"[BKT] Checking {len(custom_bkt.vocab_parameters)} vocabulary items for time decay")
    
    for vocab, params in list(custom_bkt.vocab_parameters.items()):
        # CRITICAL FIX: Check if params is actually a dictionary
        if not isinstance(params, dict):
            print(f"[BKT] WARNING: Invalid parameter type for '{vocab}': {type(params).__name__}")
            # Initialize with proper structure instead of causing an error
            custom_bkt.vocab_parameters[vocab] = {
                'learn': 0.15,
                'guess': 0.25,
                'slip': 0.1,
                'prior': 0.5,
                'observations': []
            }
            params = custom_bkt.vocab_parameters[vocab]
            invalid_count += 1
            
        if 'observations' not in params or not params['observations']:
            continue
            
        # Get last observation time
        last_obs = params['observations'][-1]
        
        # SAFETY CHECK: Make sure last_obs is a dictionary
        if not isinstance(last_obs, dict):
            print(f"[BKT] WARNING: Invalid observation format for '{vocab}'")
            params['observations'] = []
            continue
            
        last_time = last_obs.get('timestamp', 0)
        
        # Calculate days since last observation
        days_elapsed = (now - last_time) / (86400)  # seconds in a day
        
        # Don't decay if less than 2 days
        if days_elapsed < 2:
            continue
            
        # Calculate decay amount (1% per day after first 2 days, max 30%)
        decay_amount = min(max_mastery_decrease, (days_elapsed - 2) * 0.01)
        
        if decay_amount <= 0:
            continue
            
        # Apply decay
        old_mastery = params.get('prior', 0.5)
        min_mastery = 0.3  # Don't let mastery drop below this
        new_mastery = max(min_mastery, old_mastery * (1.0 - decay_amount))
        
        # Only update if significant change
        if old_mastery - new_mastery > 0.02:
            params['prior'] = new_mastery
            updated_count += 1
            print(f"[BKT] Applied {days_elapsed:.1f}-day decay to '{vocab}': {old_mastery:.3f} → {new_mastery:.3f}")
    
    if updated_count > 0:
        print(f"[BKT] Applied time decay to {updated_count} vocabulary items")
    if invalid_count > 0:
        print(f"[BKT] Fixed {invalid_count} invalid vocabulary parameter entries")
    
    return updated_count

def save_bkt_data_to_database(user_id, custom_bkt, is_daily_review=False):
    """Save BKT data to database with review context preservation"""
    try:
        print(f"[BKT] Saving BKT data to database for user {user_id}")
        
        # Connect to database
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": int(user_id)})
        
        if not user:
            print(f"[BKT] User {user_id} not found in database")
            return False
        
        # Get existing BKT data structure
        existing_bkt_data = user.get("bkt_data", {})
        if not isinstance(existing_bkt_data, dict):
            existing_bkt_data = {}
        
        # Ensure predictions structure exists
        if "predictions" not in existing_bkt_data:
            existing_bkt_data["predictions"] = {}
        
        existing_predictions = existing_bkt_data["predictions"]
        
        # CRITICAL FIX: Merge predictions properly without overwriting
        new_vocab_count = 0
        updated_vocab_count = 0
        
        # Process vocabulary parameters from custom_bkt
        for vocab, params in custom_bkt.vocab_parameters.items():
            if vocab in ["fitted", "refit_counter"]:
                continue
                
            # Create prediction entry with all necessary fields
            prediction_entry = {
                "p_mastery": float(params.get('prior', 0.5)),
                "guess": float(params.get('guess', 0.25)),
                "slip": float(params.get('slip', 0.1)),
                "confidence": float(params.get('confidence', 0.5)),
                "correct": int(params.get('correct', 0)),
                "reviewed": bool(params.get('reviewed', False)),  # CRITICAL: Preserve review status
                "timestamp": int(params.get('last_reviewed', time.time())),
                "difficulty_level": int(params.get('difficulty_level', 1)),
                "transferred_difficulty": float(params.get('transferred_difficulty', 0)),
                "observations": params.get('observations', []),
                "response_times": params.get('response_times', [])
            }
            
            # Check if this is new or updated vocabulary
            if vocab not in existing_predictions:
                new_vocab_count += 1
                print(f"[BKT] Adding NEW vocab '{vocab}': mastery={prediction_entry['p_mastery']:.6f}, reviewed={prediction_entry['reviewed']}")
            else:
                old_entry = existing_predictions[vocab]
                old_mastery = old_entry.get('p_mastery', 0.5)
                new_mastery = prediction_entry['p_mastery']
                old_reviewed = old_entry.get('reviewed', False)
                new_reviewed = prediction_entry['reviewed']
                
                if abs(old_mastery - new_mastery) > 0.001 or old_reviewed != new_reviewed:
                    updated_vocab_count += 1
                    print(f"[BKT] Updating vocab '{vocab}': mastery {old_mastery:.6f}→{new_mastery:.6f}, reviewed {old_reviewed}→{new_reviewed}")
            
            # Update the prediction
            existing_predictions[vocab] = prediction_entry
        
        # Update the main BKT data structure with metadata
        updated_bkt_data = {
            **existing_bkt_data,
            "predictions": existing_predictions,
            "last_update": int(time.time()),
            "last_update_type": "daily_review" if is_daily_review else "lesson",
            "vocab_count": len(existing_predictions)
        }
        
        # CRITICAL: Also save in old format for backward compatibility
        for vocab, prediction in existing_predictions.items():
            updated_bkt_data[vocab] = {
                'prior': prediction['p_mastery'],
                'guess': prediction['guess'],
                'slip': prediction['slip'],
                'learn': 0.15,
                'reviewed': prediction['reviewed'],
                'observations': prediction.get('observations', []),
                'timestamp': prediction['timestamp']
            }
        
        # Save to database
        update_result = usercol.update_one(
            {"user_id": int(user_id)},
            {"$set": {"bkt_data": updated_bkt_data}}
        )
        
        print(f"[BKT] Database update result: matched={update_result.matched_count}, modified={update_result.modified_count}")
        print(f"[BKT] Saving: {new_vocab_count} new vocabs, {updated_vocab_count} updated vocabs, {len(existing_predictions)} predictions")
        
        # CRITICAL: Update temp files for immediate access
        if update_result.modified_count > 0:
            try:
                # Update bkt_predictions.json for immediate use
                with open('bkt_predictions.json', 'w') as f:
                    json.dump(existing_predictions, f, indent=2)
                print(f"[BKT] Updated bkt_predictions.json with {len(existing_predictions)} predictions")
                
                # Create user-specific temp file for daily review processing
                if is_daily_review:
                    review_file = f"daily_review_bkt_{user_id}.json"
                    with open(review_file, 'w') as f:
                        json.dump({
                            "predictions": existing_predictions,
                            "timestamp": int(time.time()),
                            "reviewed_count": len([p for p in existing_predictions.values() if p.get('reviewed', False)])
                        }, f, indent=2)
                    print(f"[BKT] Created daily review BKT file: {review_file}")
                
            except Exception as e:
                print(f"[BKT] Error updating temp files: {e}")
            
            return True
        else:
            print(f"[BKT] No changes made to database")
            return False
            
    except Exception as e:
        print(f"[BKT] Error saving to database: {e}")
        import traceback
        traceback.print_exc()
        return False

def ensure_bkt_data_loaded(user_id, force_db_refresh=False):
    """Ensure BKT data is properly loaded from database and integrated with session data"""
    # Skip if no user_id provided
    if not user_id:
        print("[BKT] Cannot load BKT data: No user ID provided")
        return [0.5, 0.55, 0.6, 0.65, 0.7]  # Return default sequence instead of empty
    
    # Skip if we already have cached sequence and no forced refresh
    cache_key = f"bkt_sequence_{user_id}"
    if not force_db_refresh and os.path.exists(cache_key):
        try:
            with open(cache_key, 'r') as f:
                sequence = json.load(f)
                # CRITICAL FIX: Validate that sequence isn't empty
                if isinstance(sequence, list) and len(sequence) > 0:
                    print(f"[BKT] Using cached BKT sequence for user {user_id} with {len(sequence)} values")
                    return sequence
                else:
                    print(f"[BKT] Cached sequence is empty or invalid, rebuilding from database")
        except Exception as e:
            print(f"[BKT] Error loading cached sequence: {e}")
    
    print(f"[BKT] Loading complete BKT data for user {user_id}")
    
    try:
        # 1. Get custom BKT for ordered vocabulary list
        custom_bkt = get_custom_bkt(user_id)
        ordered_vocab = custom_bkt.get_vocabulary_in_order() if custom_bkt else []
        print(f"[BKT] Found {len(ordered_vocab)} vocabulary items in order")
        
        # If ordered_vocab is empty, try alternative methods to populate it
        if not ordered_vocab:
            try:
                # FIXED: Try multiple sources for vocabulary list
                
                # Method 1: Try to get from user's library
                user_library = get_user_library(user_id)
                if user_library:
                    ordered_vocab = []
                    for item in user_library:
                        if isinstance(item, dict):
                            vocab = item.get('vocabulary') or item.get('word')
                            if vocab:
                                ordered_vocab.append(vocab)
                        elif isinstance(item, str):
                            # If it's a string, just add it directly
                            ordered_vocab.append(item)
                    ordered_vocab = [v for v in ordered_vocab if v]  # Remove empty strings
                    print(f"[BKT] Using {len(ordered_vocab)} vocabulary items from user library")
                
                # Method 2: Try to get from lesson data in session
                if not ordered_vocab:
                    try:
                        # This is a fallback - try to get from any available source
                        state = load_temp_state(user_id)
                        predictions = state.get("predictions", {})
                        if predictions:
                            ordered_vocab = list(predictions.keys())
                            print(f"[BKT] Using {len(ordered_vocab)} vocabulary items from session predictions")
                    except Exception as e:
                        print(f"[BKT] Error getting vocabulary from session: {e}")
                
                # Method 3: Try to get from database directly
                if not ordered_vocab:
                    try:
                        arami = pymongo.MongoClient(uri)["arami"]
                        user_doc = arami["users"].find_one({"user_id": int(user_id)})
                        if user_doc and "bkt_data" in user_doc:
                            bkt_data = user_doc["bkt_data"]
                            
                            # Get vocabulary from predictions
                            if "predictions" in bkt_data and isinstance(bkt_data["predictions"], dict):
                                ordered_vocab = list(bkt_data["predictions"].keys())
                                print(f"[BKT] Using {len(ordered_vocab)} vocabulary items from database predictions")
                            
                            # Also check for direct vocabulary entries in bkt_data
                            if not ordered_vocab:
                                vocab_from_bkt = []
                                for key, value in bkt_data.items():
                                    if key not in ["fitted", "refit_counter", "predictions", "last_updated", "source", "force_update_id"] and isinstance(value, dict):
                                        vocab_from_bkt.append(key)
                                if vocab_from_bkt:
                                    ordered_vocab = vocab_from_bkt
                                    print(f"[BKT] Using {len(ordered_vocab)} vocabulary items from database BKT entries")
                    except Exception as e:
                        print(f"[BKT] Error getting vocabulary from database: {e}")
                
                # Method 4: Try to get from a hardcoded common vocabulary list (fallback)
                if not ordered_vocab:
                    print("[BKT] No vocabulary found from any source, using common vocabulary list")
                    ordered_vocab = [
                        "maupay", "diri", "it", "okay la ako", "salamat", "pakadto", 
                        "balay", "tubig", "kaon", "buhi", "maupay nga kulop"
                    ]
                    print(f"[BKT] Using {len(ordered_vocab)} default vocabulary items")
                    
            except Exception as e:
                print(f"[BKT] Error getting alternative vocabulary list: {e}")
        
        # 2. Get session predictions
        state = load_temp_state(user_id)
        session_predictions = state.get("predictions", {})
        print(f"[BKT] Loaded {len(session_predictions)} predictions from session")
        
        # 3. Get database predictions
        db_predictions = {}
        try:
            arami = pymongo.MongoClient(uri)["arami"]
            user_doc = arami["users"].find_one({"user_id": int(user_id)})
            if user_doc and "bkt_data" in user_doc:
                bkt_data = user_doc["bkt_data"]
                
                # Get predictions from standard location
                if "predictions" in bkt_data and isinstance(bkt_data["predictions"], dict):
                    db_predictions = bkt_data["predictions"]
                    print(f"[BKT] Loaded {len(db_predictions)} predictions from database")
                
                # Also check for legacy format
                for vocab, data in bkt_data.items():
                    # Skip special keys that aren't vocabulary items
                    if vocab in ["fitted", "refit_counter", "predictions", "last_updated", "source", "force_update_id"]:
                        continue
                        
                    # If it's a dict with prior, it's a valid vocabulary entry
                    if isinstance(data, dict) and "prior" in data:
                        # Add as prediction if not already present
                        if vocab not in db_predictions:
                            db_predictions[vocab] = {
                                "p_mastery": data.get("prior", 0.5),
                                "guess": data.get("guess", 0.25),
                                "slip": data.get("slip", 0.1)
                            }
        except Exception as e:
            print(f"[BKT] Error loading database predictions: {e}")
        
        # 4. Merge predictions with session taking precedence
        merged_predictions = {}
        
        # First add all database predictions
        for vocab, pred in db_predictions.items():
            if isinstance(pred, dict):
                merged_predictions[vocab] = pred
        
        # Then overwrite with session predictions
        for vocab, pred in session_predictions.items():
            if isinstance(pred, dict):
                merged_predictions[normalize_vocabulary_key(vocab)] = pred
            
        print(f"[BKT] Merged {len(session_predictions)} session and {len(db_predictions)} database predictions")
        print(f"[BKT] Total merged predictions: {len(merged_predictions)}")
        
        # 5. Generate final sequence based on ordered vocabulary
        final_sequence = []
        for vocab in ordered_vocab:
            norm_vocab = normalize_vocabulary_key(vocab)
            if norm_vocab in merged_predictions:
                try:
                    mastery = float(merged_predictions[norm_vocab].get('p_mastery', 0.5))
                    final_sequence.append(mastery)
                except (ValueError, TypeError):
                    final_sequence.append(0.5)  # Default if conversion fails
            else:
                final_sequence.append(0.5)  # Default for unknown vocabulary
                
        # CRITICAL FIX: If final_sequence is empty, use database predictions directly
        if not final_sequence and merged_predictions:
            print("[BKT] Ordered vocabulary is empty, building sequence from predictions")
            for vocab in sorted(merged_predictions.keys()):
                try:
                    mastery = float(merged_predictions[vocab].get('p_mastery', 0.5))
                    final_sequence.append(mastery)
                except (ValueError, TypeError):
                    pass
        
        # CRITICAL FIX: If still empty, provide default sequence
        if not final_sequence:
            print("[BKT] Could not generate sequence from any source, using default values")
            final_sequence = [0.5, 0.55, 0.6, 0.65, 0.7]
            
        # Only cache if sequence has actual values
        if final_sequence:
            try:
                with open(cache_key, 'w') as f:
                    json.dump(final_sequence, f)
                print(f"[BKT] Cached sequence with {len(final_sequence)} values")
            except Exception as e:
                print(f"[BKT] Error caching sequence: {e}")
                
        print(f"[BKT] Generated final sequence with {len(final_sequence)} values")
        print(f"[BKT] Sequence preview: {final_sequence[:5]}{'...' if len(final_sequence) > 5 else ''}")
        return final_sequence
        
    except Exception as e:
        print(f"[BKT] Error in ensure_bkt_data_loaded: {e}")
        import traceback
        traceback.print_exc()
        # Return default sequence even on error
        return [0.5, 0.55, 0.6, 0.65, 0.7]

def save_lesson_bkt_if_file_exists(user_id):
    """Simple approach: If lesson BKT predictions file exists, save its data to database"""
    try:
        # Check for the lesson BKT predictions file
        lesson_file = f"lesson_bkt_predictions_{user_id}.json"
        
        if not os.path.exists(lesson_file):
            print(f"[BKT] No lesson predictions file found for user {user_id}")
            return False
        
        print(f"[BKT] Found lesson predictions file for user {user_id}, processing...")
        
        # Load the lesson predictions data
        with open(lesson_file, 'r') as f:
            lesson_data = json.load(f)
        
        # Extract the predictions
        predictions = lesson_data.get('predictions', {})
        if not predictions:
            print(f"[BKT] No predictions found in lesson file for user {user_id}")
            return False
        
        print(f"[BKT] Found {len(predictions)} vocabulary predictions in lesson file")
        
        # Connect to database
        arami = pymongo.MongoClient(uri)["arami"]
        usercol = arami["users"]
        
        # Get user document
        user = usercol.find_one({"user_id": int(user_id)})
        if not user:
            print(f"[BKT] User {user_id} not found in database")
            return False
        
        # Get existing BKT data
        existing_bkt_data = user.get("bkt_data", {})
        
        # CLEAN APPROACH: Only add new vocabulary, don't duplicate existing ones
        timestamp = int(time.time())
        
        # Start with existing data or create fresh structure
        if isinstance(existing_bkt_data, dict):
            db_bkt_data = existing_bkt_data.copy()
        else:
            db_bkt_data = {}
        
        # Ensure basic structure exists
        if "predictions" not in db_bkt_data:
            db_bkt_data["predictions"] = {}
        
        # Update metadata
        db_bkt_data.update({
            "fitted": True,
            "refit_counter": db_bkt_data.get("refit_counter", 0) + 1,
            "last_updated": timestamp,
            "source": "lesson_predictions_file"
        })
        
        # Process each vocabulary from the lesson file
        new_vocab_count = 0
        updated_vocab_count = 0
        
        for vocab, pred_data in predictions.items():
            if isinstance(pred_data, dict):
                mastery = float(pred_data.get('p_mastery', 0.5))
                guess = float(pred_data.get('guess', 0.25))
                slip = float(pred_data.get('slip', 0.1))
                
                # Check if vocabulary already exists
                vocab_exists = vocab in db_bkt_data and vocab not in ["fitted", "refit_counter", "predictions", "last_updated", "source"]
                
                if not vocab_exists:
                    # Add new vocabulary parameters
                    db_bkt_data[vocab] = {
                        'prior': mastery,
                        'guess': guess,
                        'slip': slip,
                        'learn': 0.15,
                        'observations': [],
                        'timestamp': timestamp
                    }
                    new_vocab_count += 1
                    print(f"[BKT] Added NEW vocab '{vocab}' with mastery {mastery:.3f}")
                else:
                    # Update existing vocabulary mastery if significantly different
                    existing_mastery = db_bkt_data[vocab].get('prior', 0.5)
                    if abs(existing_mastery - mastery) > 0.01:  # Only update if mastery changed by more than 1%
                        db_bkt_data[vocab]['prior'] = mastery
                        db_bkt_data[vocab]['timestamp'] = timestamp
                        updated_vocab_count += 1
                        print(f"[BKT] Updated existing vocab '{vocab}': {existing_mastery:.3f} → {mastery:.3f}")
                    else:
                        print(f"[BKT] Skipped '{vocab}' - mastery unchanged ({existing_mastery:.3f})")
                
                # Always update predictions (these can change each session)
                db_bkt_data["predictions"][vocab] = {
                    'p_mastery': mastery,
                    'guess': guess,
                    'slip': slip,
                    'confidence': float(pred_data.get('confidence', 0.7)),
                    'correct': pred_data.get('correct', 1),
                    'reviewed': False,
                    'timestamp': pred_data.get('timestamp', timestamp)
                }
        
        print(f"[BKT] Summary: {new_vocab_count} new vocab, {updated_vocab_count} updated vocab")
        
        # Save to database with forced update
        db_bkt_data["force_update_id"] = f"{user_id}_{timestamp}"
        
        result = usercol.update_one(
            {"user_id": int(user_id)},
            {"$set": {"bkt_data": db_bkt_data}}
        )
        
        print(f"[BKT] Database save result: matched={result.matched_count}, modified={result.modified_count}")
        
        if result.matched_count > 0:
            # Verify the save worked
            verification = usercol.find_one({"user_id": int(user_id)})
            if (verification and 
                "bkt_data" in verification and 
                "force_update_id" in verification["bkt_data"] and
                verification["bkt_data"]["force_update_id"] == db_bkt_data["force_update_id"]):
                
                print(f"[BKT] Successfully saved lesson BKT data for user {user_id}")
                
                # FIXED: Delete the file instead of renaming to avoid conflicts
                try:
                    os.remove(lesson_file)
                    print(f"[BKT] Deleted processed file: {lesson_file}")
                except Exception as e:
                    print(f"[BKT] Could not delete file {lesson_file}: {e}")
                
                return True
            else:
                print(f"[BKT] Database save verification failed for user {user_id}")
                return False
        else:
            print(f"[BKT] No user document matched for user {user_id}")
            return False
        
    except Exception as e:
        print(f"[BKT] Error saving lesson BKT from file: {e}")
        import traceback
        traceback.print_exc()
        return False