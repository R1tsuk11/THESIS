"""
Lesson BKT Engine - Specialized BKT engine for lessons and chapter tests
This engine focuses on:
1. Session-based BKT tracking
2. Difficulty transfer between items
3. Smart merging with database data
"""

import json
import os
import time
from collections import defaultdict
import threading

# Import base functionality
from .base import CustomBKTPredictor, calculate_bkt_confidence, normalize_vocabulary

class LessonBKTEngine:
    """
    Specialized BKT engine for lesson and chapter test sessions
    Maintains in-session state and handles merging with database
    """
    def __init__(self, user_id):
        self.user_id = user_id
        self.session_id = f"lesson_{user_id}_{int(time.time())}"
        self.session_start = time.time()
        self.correct_answers = {}
        self.incorrect_answers = {}
        self.seen_vocabulary = set()
        self.difficulty_map = {}
        self.bkt_predictor = CustomBKTPredictor()
        self.db_predictions = {}
        self.session_predictions = {}
        self.merged_predictions = {}
        
        # Try to load existing parameters
        self._load_existing_parameters()
    
    def _load_existing_parameters(self):
        """Load existing parameters from database or file"""
        try:
            # Try to load from the standard predictions file first
            if os.path.exists('bkt_predictions.json'):
                with open('bkt_predictions.json', 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "predictions" in data:
                        self.db_predictions = data["predictions"]
                    elif isinstance(data, dict):
                        self.db_predictions = data
            
            # Initialize BKT predictor with existing parameters
            vocab_params = {}
            for vocab, pred in self.db_predictions.items():
                if isinstance(pred, dict):
                    vocab_params[vocab] = {
                        'prior': pred.get('p_mastery', 0.5),
                        'guess': pred.get('guess', 0.25),
                        'slip': pred.get('slip', 0.1),
                        'transit': 0.12,  # Default transition probability
                        'order': len(vocab_params)  # Maintain ordering
                    }
            
            self.bkt_predictor.vocab_parameters = vocab_params
        except Exception as e:
            print(f"[LessonBKTEngine] Error loading existing parameters: {str(e)}")
    
    def add_observation(self, question_key, question, is_correct):
        """Add an observation to the session"""
        # Extract vocabulary
        vocab = self._extract_vocab_from_question(question)
        if not vocab:
            return False
        
        # Store answer
        if is_correct:
            self.correct_answers[question_key] = question
        else:
            self.incorrect_answers[question_key] = question
        
        # Add to seen vocabulary
        self.seen_vocabulary.add(vocab)
        
        # Update difficulty factor
        self._update_difficulty_factor(vocab, is_correct)
        
        # Update BKT model
        difficulty = self.difficulty_map.get(vocab, 1.0)
        self.bkt_predictor.observe_with_scale(vocab, is_correct, 1.0, difficulty)
        
        # Update session predictions
        self._update_session_prediction(vocab, is_correct)
        
        return True
    
    def _extract_vocab_from_question(self, question):
        """Extract vocabulary from a question object"""
        vocab = None
        
        # Try different ways of getting vocabulary
        if hasattr(question, 'vocabulary'):
            vocab = question.vocabulary
        elif isinstance(question, dict) and 'vocabulary' in question:
            vocab = question['vocabulary']
        elif hasattr(question, 'question'):
            vocab = question.question
        elif isinstance(question, dict) and 'question' in question:
            vocab = question['question']
        
        # Normalize vocabulary
        if vocab:
            vocab = normalize_vocabulary(vocab)
        
        return vocab
    
    def _update_difficulty_factor(self, vocab, is_correct):
        """Update difficulty factor for a vocabulary item"""
        # Get current difficulty or default to 1.0
        current_difficulty = self.difficulty_map.get(vocab, 1.0)
        
        # Adjust difficulty based on correctness
        if is_correct:
            # Correct answer makes it easier next time
            new_difficulty = current_difficulty * 0.9
        else:
            # Incorrect answer makes it harder next time
            new_difficulty = current_difficulty * 1.1
        
        # Clamp difficulty between 0.5 and 2.0
        new_difficulty = max(0.5, min(2.0, new_difficulty))
        
        # Update difficulty map
        self.difficulty_map[vocab] = new_difficulty
    
    def _update_session_prediction(self, vocab, is_correct):
        """Update session prediction for a vocabulary item"""
        # Get parameters for this vocabulary
        params = self.bkt_predictor.vocab_parameters.get(vocab, {})
        mastery = params.get('prior', 0.5)
        guess = params.get('guess', 0.25)
        slip = params.get('slip', 0.1)
        
        # Calculate confidence
        confidence = calculate_bkt_confidence(mastery, guess, slip, vocab=vocab, params=params)
        
        # Store in session predictions
        self.session_predictions[vocab.lower()] = {
            'p_mastery': mastery,
            'guess': guess,
            'slip': slip,
            'confidence': confidence,
            'correct': 1 if is_correct else 0,
            'timestamp': int(time.time())
        }
    
    def merge_with_database(self):
        """Merge session predictions with database predictions"""
        self.merged_predictions = {}
        
        # First add database predictions
        for vocab, pred in self.db_predictions.items():
            self.merged_predictions[vocab] = pred
        
        # Then overwrite with session predictions
        for vocab, pred in self.session_predictions.items():
            self.merged_predictions[vocab] = pred
        
        return self.merged_predictions
    
    def get_session_data(self):
        """Get all session data"""
        return {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'session_start': self.session_start,
            'correct_answers': self.correct_answers,
            'incorrect_answers': self.incorrect_answers,
            'seen_vocabulary': list(self.seen_vocabulary),
            'difficulty_map': self.difficulty_map,
            'session_predictions': self.session_predictions
        }
    
    def get_bkt_sequence(self):
        """Get BKT sequence for LSTM model"""
        # Make sure we have merged the predictions
        if not self.merged_predictions:
            self.merge_with_database()
        
        # Get vocabulary in order
        ordered_vocab = self.bkt_predictor.get_vocabulary_in_order()
        
        # Generate sequence
        sequence = [float(self.merged_predictions.get(vocab, {}).get('p_mastery', 0.5)) for vocab in ordered_vocab]
        
        return sequence
    
    def get_next_vocabulary(self, vocab_list, num=1):
        """Get next vocabulary items to focus on"""
        if not vocab_list:
            return []
        
        # Filter to only include vocabulary in the provided list
        available_vocab = [v for v in vocab_list if v]
        
        # Score each vocabulary
        scored_vocab = []
        for vocab in available_vocab:
            # Get mastery from merged predictions or default
            mastery = self.merged_predictions.get(vocab, {}).get('p_mastery', 0.5)
            
            # Get difficulty factor
            difficulty = self.difficulty_map.get(vocab, 1.0)
            
            # Calculate priority score - lower mastery and higher difficulty gets priority
            priority_score = (1.0 - mastery) * difficulty
            
            scored_vocab.append((vocab, priority_score))
        
        # Sort by priority score (highest to lowest)
        scored_vocab.sort(key=lambda x: x[1], reverse=True)
        
        # Return the top N vocabularies
        return [v[0] for v in scored_vocab[:num]]
