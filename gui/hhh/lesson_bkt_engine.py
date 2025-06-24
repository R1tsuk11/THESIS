"""
Lesson BKT Engine - A dedicated BKT engine for lesson/chapter test sessions
This engine addresses persistent issues with:
1. Database overwriting instead of merging
2. Difficulty transfer between items
3. Session management and database merging
"""

import json
import os
import time
import pymongo
import traceback
from collections import defaultdict
import threading
import random

# Import existing BKT engine functionality we'll reuse
from bkt_engine import (
    CustomBKTPredictor, 
    calculate_bkt_confidence,
    get_vocabulary_from_question,
    get_custom_bkt,
    save_custom_bkt,
    apply_time_decay,
    debug_question_object
)

# MongoDB connection string
uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

# Global lock for thread safety
session_lock = threading.RLock()

# Global session store
active_sessions = {}

_saving_sessions = set()

class LessonSession:
    """
    Represents a single lesson or chapter test session
    Tracks correct and incorrect answers within the session
    """
    def __init__(self, user_id, session_id=None):
        self.user_id = user_id
        self.session_id = session_id or f"lesson_{user_id}_{int(time.time())}"
        self.session_start_time = time.time()
        self.correct_answers = {}
        self.incorrect_answers = {}
        self.seen_vocabulary = set()
        self.difficulty_factors = {}
        self.bkt_predictor = None
        self.session_predictions = {}
        self.database_predictions = {}
        self.merged_predictions = {}
        
    def add_correct_answer(self, question_key, question):
        """Add a correct answer to the session"""
        self.correct_answers[question_key] = question
        vocab = get_vocabulary_from_question(question)
        if vocab:
            self.seen_vocabulary.add(vocab)
            # Update difficulty factor - correct answer makes it easier next time
            self.difficulty_factors[vocab] = self.difficulty_factors.get(vocab, 1.0) * 0.9
    
    def add_incorrect_answer(self, question_key, question):
        """Add an incorrect answer to the session"""
        self.incorrect_answers[question_key] = question
        vocab = get_vocabulary_from_question(question)
        if vocab:
            self.seen_vocabulary.add(vocab)
            # Update difficulty factor - incorrect answer makes it harder next time
            self.difficulty_factors[vocab] = self.difficulty_factors.get(vocab, 1.0) * 1.1
    
    def get_difficulty_factor(self, vocab):
        """Get the difficulty factor for a vocabulary item"""
        return self.difficulty_factors.get(vocab, 1.0)
    
    def get_all_answers(self):
        """Get all answers in the session"""
        return {
            "correct": self.correct_answers,
            "incorrect": self.incorrect_answers
        }
    
    def process_bkt_update(self, impact_scale=1.0):
        """Process a BKT update for the session"""
        try:
            # Get existing BKT predictor or create new one
            self.bkt_predictor = get_custom_bkt(self.user_id)
            if not self.bkt_predictor:
                print(f"[LessonBKT] Creating new BKT predictor for user {self.user_id}")
                self.bkt_predictor = CustomBKTPredictor()
            
            # Apply time decay before updates
            apply_time_decay(self.bkt_predictor)
            
            # Process all vocabulary items in this session
            for vocab in self.seen_vocabulary:
                # Skip empty vocab
                if not vocab:
                    continue
                
                # Debug the current parameters
                before_params = self.bkt_predictor.vocab_parameters.get(vocab, {})
                print(f"[LessonBKT] Before update '{vocab}': prior={before_params.get('prior', 0.5)}")
                
                # Find matching correct and incorrect answers for this vocab
                was_correct = False
                was_incorrect = False
                
                # Check correct answers
                normalized_vocab = vocab.lower().strip()
                for q in self.correct_answers.values():
                    q_vocab = get_vocabulary_from_question(q)
                    if q_vocab and q_vocab.lower().strip() == normalized_vocab:
                        was_correct = True
                        break
                
                # Check incorrect answers
                for q in self.incorrect_answers.values():
                    q_vocab = get_vocabulary_from_question(q)
                    if q_vocab and q_vocab.lower().strip() == normalized_vocab:
                        was_incorrect = True
                        break
                
                # Extract difficulty from session
                difficulty_factor = self.get_difficulty_factor(vocab)
                
                # Update BKT for this vocabulary
                if was_correct:
                    new_mastery = self.bkt_predictor.observe_with_scale(vocab, True, impact_scale, difficulty_factor)
                    print(f"[LessonBKT] Updated '{vocab}' with CORRECT observation: new mastery = {new_mastery:.2f}")
                elif was_incorrect:
                    new_mastery = self.bkt_predictor.observe_with_scale(vocab, False, impact_scale, difficulty_factor)
                    print(f"[LessonBKT] Updated '{vocab}' with INCORRECT observation: new mastery = {new_mastery:.2f}")
                
                # Debug the updated parameters
                after_params = self.bkt_predictor.vocab_parameters.get(vocab, {})
                print(f"[LessonBKT] After update '{vocab}': prior={after_params.get('prior', 0.5)}")
                
                # Store the updated prediction in the session
                latest_params = self.bkt_predictor.vocab_parameters.get(vocab, {})
                latest_guess = float(latest_params.get('guess', 0.25))
                latest_slip = float(latest_params.get('slip', 0.1))
                latest_mastery = float(latest_params.get('prior', 0.5))
                
                # Calculate confidence
                confidence = calculate_bkt_confidence(
                    latest_mastery,
                    latest_guess,
                    latest_slip,
                    vocab=vocab,
                    params=latest_params
                )
                
                # Store in session predictions
                self.session_predictions[vocab.lower()] = {
                    'p_mastery': latest_mastery,
                    'guess': latest_guess,
                    'slip': latest_slip,
                    'confidence': confidence,
                    'correct': 1 if was_correct else 0 if was_incorrect else -1,
                    'timestamp': int(time.time())
                }
            
            # Save the updated BKT predictor
            save_custom_bkt(self.user_id, self.bkt_predictor)
            
            # After all updates, load database predictions for merging
            self._load_database_predictions()
            
            # Merge session and database predictions
            self._merge_predictions()
            
            return True
        except Exception as e:
            print(f"[LessonBKT] Error processing BKT update: {str(e)}")
            traceback.print_exc()
            return False
    
    def _load_database_predictions(self):
        """Load predictions from database with temp file fallback"""
        try:
            # First try database
            arami = pymongo.MongoClient(uri)["arami"]
            users_col = arami["users"]
            
            user_doc = users_col.find_one({"user_id": int(self.user_id)})
            if user_doc and "bkt_data" in user_doc:
                bkt_data = user_doc["bkt_data"]
                
                # Load predictions from database
                if isinstance(bkt_data, dict) and "predictions" in bkt_data:
                    self.database_predictions = bkt_data["predictions"]
                    print(f"[LessonBKT] Loaded {len(self.database_predictions)} predictions from database")
                    return
                
                # Load from vocabulary parameters if predictions not found
                for vocab, params in bkt_data.items():
                    if vocab not in ["fitted", "refit_counter", "predictions"] and isinstance(params, dict):
                        if "prior" in params:
                            self.database_predictions[vocab] = {
                                "p_mastery": params.get("prior", 0.5),
                                "guess": params.get("guess", 0.25),
                                "slip": params.get("slip", 0.1),
                                "confidence": 0.7,
                                "timestamp": int(time.time())
                            }
                
                if self.database_predictions:
                    print(f"[LessonBKT] Loaded {len(self.database_predictions)} predictions from database vocabulary")
                    return
            
            # Fallback to temp files if database fails
            print(f"[LessonBKT] Database load failed, trying temp files for user {self.user_id}")
            bkt_data, predictions_data = load_lesson_bkt_from_temp_files(self.user_id)
            
            if predictions_data and "predictions" in predictions_data:
                self.database_predictions = predictions_data["predictions"]
                print(f"[LessonBKT] Loaded {len(self.database_predictions)} predictions from temp files")
            elif bkt_data:
                # Convert BKT data to predictions format
                for vocab, params in bkt_data.items():
                    if isinstance(params, dict) and "prior" in params:
                        self.database_predictions[vocab] = {
                            "p_mastery": params.get("prior", 0.5),
                            "guess": params.get("guess", 0.25),
                            "slip": params.get("slip", 0.1),
                            "confidence": 0.7,
                            "timestamp": int(time.time())
                        }
                print(f"[LessonBKT] Converted {len(self.database_predictions)} BKT parameters to predictions")
            
        except Exception as e:
            print(f"[LessonBKT] Error loading database predictions: {e}")
            self.database_predictions = {}
    
    def _merge_predictions(self):
        """Merge session and database predictions, prioritizing session values"""
        self.merged_predictions = {}
        
        # First add database predictions
        for vocab, pred in self.database_predictions.items():
            self.merged_predictions[vocab] = pred
        
        # Then overwrite with session predictions (these take precedence)
        for vocab, pred in self.session_predictions.items():
            self.merged_predictions[vocab] = pred
        
        print(f"[LessonBKT] Merged {len(self.session_predictions)} session predictions with {len(self.database_predictions)} database predictions")
        print(f"[LessonBKT] Final prediction count: {len(self.merged_predictions)}")
    
    def save_to_database(self):
        """Save the merged predictions to the database"""
        try:
            arami = pymongo.MongoClient(uri)["arami"]
            users_col = arami["users"]
            
            # Get user document
            user_doc = users_col.find_one({"user_id": int(self.user_id)})
            if user_doc:
                # Create bkt_data structure if it doesn't exist
                if "bkt_data" not in user_doc:
                    user_doc["bkt_data"] = {}
                
                # Set the predictions
                if isinstance(user_doc["bkt_data"], dict):
                    user_doc["bkt_data"]["predictions"] = self.merged_predictions
                    # Also store session history for tracking
                    if "session_history" not in user_doc["bkt_data"]:
                        user_doc["bkt_data"]["session_history"] = []
                    
                    # Add session summary to history
                    session_summary = {
                        "session_id": self.session_id,
                        "timestamp": int(time.time()),
                        "correct_count": len(self.correct_answers),
                        "incorrect_count": len(self.incorrect_answers),
                        "vocab_list": list(self.seen_vocabulary)
                    }
                    user_doc["bkt_data"]["session_history"].append(session_summary)
                else:
                    # If bkt_data is not a dict, reset it
                    user_doc["bkt_data"] = {
                        "predictions": self.merged_predictions,
                        "session_history": [{
                            "session_id": self.session_id,
                            "timestamp": int(time.time()),
                            "correct_count": len(self.correct_answers),
                            "incorrect_count": len(self.incorrect_answers),
                            "vocab_list": list(self.seen_vocabulary)
                        }]
                    }
                
                # Update the document in the database
                users_col.update_one(
                    {"user_id": int(self.user_id)},
                    {"$set": {"bkt_data": user_doc["bkt_data"]}}
                )
                
                # Also save predictions to bkt_predictions.json for backward compatibility
                with open('bkt_predictions.json', 'w') as f:
                    json.dump(self.merged_predictions, f)
                
                print(f"[LessonBKT] Successfully saved session data to database")
                return True
            else:
                print(f"[LessonBKT] User {self.user_id} not found in database")
                return False
        except Exception as e:
            print(f"[LessonBKT] Error saving to database: {str(e)}")
            traceback.print_exc()
            return False
    
    def get_bkt_sequence(self):
        """Get the BKT sequence for the LSTM model"""
        try:
            # Get vocabulary in order from the BKT predictor
            if self.bkt_predictor and hasattr(self.bkt_predictor, 'get_vocabulary_in_order'):
                try:
                    ordered_vocab = self.bkt_predictor.get_vocabulary_in_order()
                except Exception as e:
                    print(f"[LessonBKT] Error getting vocabulary order: {e}")
                    ordered_vocab = []
            else:
                ordered_vocab = []
            
            # If no ordered vocabulary, use merged predictions keys
            if not ordered_vocab:
                ordered_vocab = sorted(self.merged_predictions.keys())
            
            # If still no vocabulary, use session predictions
            if not ordered_vocab:
                ordered_vocab = sorted(self.session_predictions.keys())
            
            # Generate the BKT sequence using available predictions
            bkt_sequence = []
            for vocab in ordered_vocab:
                # Try session predictions first
                if vocab in self.session_predictions:
                    mastery = self.session_predictions[vocab].get('p_mastery', 0.5)
                # Then merged predictions
                elif vocab in self.merged_predictions:
                    mastery = self.merged_predictions[vocab].get('p_mastery', 0.5)
                # Then BKT predictor parameters
                elif (self.bkt_predictor and 
                    hasattr(self.bkt_predictor, 'vocab_parameters') and 
                    vocab in self.bkt_predictor.vocab_parameters):
                    mastery = self.bkt_predictor.vocab_parameters[vocab].get('prior', 0.5)
                else:
                    mastery = 0.5  # Default
                
                bkt_sequence.append(float(mastery))
            
            # Ensure we have at least some values in the sequence
            if not bkt_sequence:
                print(f"[LessonBKT] Warning: No vocabulary found, using default sequence")
                bkt_sequence = [0.5, 0.55, 0.6, 0.65, 0.7]
            
            print(f"[LessonBKT] Generated BKT sequence with {len(bkt_sequence)} values")
            print(f"[LessonBKT] Sequence has {sum(1 for x in bkt_sequence if x != 0.5)} non-default values")
            
            return bkt_sequence
            
        except Exception as e:
            print(f"[LessonBKT] Error generating BKT sequence: {e}")
            traceback.print_exc()
            # Return default sequence on error
            return [0.5, 0.55, 0.6, 0.65, 0.7]
    
    def get_next_vocabulary(self, vocab_list, num=1):
        """Get the next vocabulary to focus on based on mastery level and difficulty"""
        if not self.bkt_predictor or not vocab_list:
            return []
        
        # Filter to only include vocabulary in the provided list
        available_vocab = [v for v in vocab_list if v]
        
        # Sort by a combination of mastery level and difficulty
        scored_vocab = []
        for vocab in available_vocab:
            # Get mastery from session predictions or fallback to database or default
            mastery = 0.5
            if vocab in self.session_predictions:
                mastery = self.session_predictions[vocab].get('p_mastery', 0.5)
            elif vocab in self.database_predictions:
                mastery = self.database_predictions[vocab].get('p_mastery', 0.5)
            
            # Get difficulty factor - higher means harder
            difficulty = self.get_difficulty_factor(vocab)
            
            # Calculate priority score - lower mastery and higher difficulty gets priority
            priority_score = (1.0 - mastery) * difficulty
            
            scored_vocab.append((vocab, priority_score))
        
        # Sort by priority score (highest to lowest)
        scored_vocab.sort(key=lambda x: x[1], reverse=True)
        
        # Return the top N vocabularies
        return [v[0] for v in scored_vocab[:num]]


# Global session management functions

def create_or_get_session(user_id, session_id=None):
    """Create a new session or get an existing one"""
    with session_lock:
        # Create session key
        session_key = f"{user_id}_{session_id}" if session_id else f"{user_id}_default"
        
        # Create new session if it doesn't exist
        if session_key not in active_sessions:
            active_sessions[session_key] = LessonSession(user_id, session_id)
        
        return active_sessions[session_key]

def get_vocab_mastery_from_session(user_id, vocab, session_id=None):
    """Get the current mastery for a vocabulary from the session with difficulty transfer"""
    try:
        session = create_or_get_session(user_id, session_id)
        
        # Check session predictions first
        normalized_vocab = vocab.lower().strip()
        if normalized_vocab in session.session_predictions:
            mastery = session.session_predictions[normalized_vocab].get('p_mastery', 0.5)
            print(f"[LessonBKT] Found mastery for '{vocab}' in session: {mastery:.3f}")
            return mastery
        
        # Check merged predictions
        if normalized_vocab in session.merged_predictions:
            mastery = session.merged_predictions[normalized_vocab].get('p_mastery', 0.5)
            print(f"[LessonBKT] Found mastery for '{vocab}' in merged predictions: {mastery:.3f}")
            return mastery
        
        # Try using the BKT predictor directly with proper parameters
        if session.bkt_predictor:
            try:
                # Check if the vocabulary exists in the predictor's parameters
                if normalized_vocab in session.bkt_predictor.vocab_parameters:
                    # Get the current prior (mastery) directly from parameters
                    mastery = session.bkt_predictor.vocab_parameters[normalized_vocab].get('prior', 0.5)
                    print(f"[LessonBKT] Found mastery for '{vocab}' in BKT parameters: {mastery:.3f}")
                    return mastery
                else:
                    # FIXED: Use the correct difficulty transfer calculation
                    transferred_mastery = calculate_difficulty_transfer_for_mastery(session)
                    
                    # Initialize vocabulary with transferred mastery
                    print(f"[LessonBKT] Vocabulary '{vocab}' not in BKT, initializing with transferred mastery: {transferred_mastery:.3f}")
                    session.bkt_predictor.vocab_parameters[normalized_vocab] = {
                        'prior': transferred_mastery,
                        'guess': 0.25,
                        'slip': 0.1,
                        'learn': 0.1,
                        'observations': []
                    }
                    return transferred_mastery
            except Exception as e:
                print(f"[LessonBKT] Error accessing BKT parameters: {e}")
        
        # FIXED: Default fallback with base mastery instead of transfer
        base_mastery = get_base_mastery_for_new_vocab(user_id)
        print(f"[LessonBKT] Using base mastery for '{vocab}': {base_mastery:.3f}")
        return base_mastery
        
    except Exception as e:
        print(f"[LessonBKT] Error getting vocab mastery: {e}")
        return 0.5

def calculate_difficulty_transfer_for_mastery(session):
    """Calculate the starting mastery for new vocabulary based on previous performance (simplified version)"""
    try:
        if not session or not session.session_predictions:
            return 0.5  # Default if no session data
        
        # Get performance from completed vocabulary in this session
        completed_vocab_masteries = []
        completed_vocab_performance = []
        
        for vocab, prediction in session.session_predictions.items():
            mastery = prediction.get('p_mastery', 0.5)
            completed_vocab_masteries.append(mastery)
            
            # Also consider the performance (correct/incorrect)
            correct_flag = prediction.get('correct', -1)
            if correct_flag != -1:  # Only if we have performance data
                completed_vocab_performance.append(correct_flag)
        
        if not completed_vocab_masteries:
            return 0.5  # Default if no completed vocabulary
        
        # Calculate average mastery of completed vocabulary
        avg_mastery = sum(completed_vocab_masteries) / len(completed_vocab_masteries)
        
        # Calculate recent performance rate
        recent_performance = 1.0  # Default to good performance
        if completed_vocab_performance:
            recent_performance = sum(completed_vocab_performance) / len(completed_vocab_performance)
        
        # Apply transfer logic
        if avg_mastery >= 0.8 and recent_performance >= 0.8:
            # Excellent performance - start next vocab with higher difficulty
            transferred_mastery = min(0.75, avg_mastery * 0.9)  # Start at 90% of previous, max 0.75
            print(f"[LessonBKT] Excellent performance detected (avg: {avg_mastery:.3f}, rate: {recent_performance:.3f}) - transferring high difficulty")
        elif avg_mastery >= 0.7 and recent_performance >= 0.7:
            # Good performance - moderate transfer
            transferred_mastery = min(0.65, avg_mastery * 0.8)  # Start at 80% of previous, max 0.65
            print(f"[LessonBKT] Good performance detected (avg: {avg_mastery:.3f}, rate: {recent_performance:.3f}) - transferring moderate difficulty")
        elif avg_mastery >= 0.6:
            # Decent performance - small transfer
            transferred_mastery = min(0.55, avg_mastery * 0.7)  # Start at 70% of previous, max 0.55
            print(f"[LessonBKT] Decent performance detected (avg: {avg_mastery:.3f}, rate: {recent_performance:.3f}) - transferring small difficulty")
        else:
            # Poor performance - start easier
            transferred_mastery = max(0.4, avg_mastery * 0.9)  # Start at 90% of previous, min 0.4
            print(f"[LessonBKT] Poor performance detected (avg: {avg_mastery:.3f}, rate: {recent_performance:.3f}) - starting easier")
        
        return transferred_mastery
        
    except Exception as e:
        print(f"[LessonBKT] Error calculating mastery transfer: {e}")
        return 0.5  # Safe fallback

def process_lesson_question(user_id, question_id, question, is_correct, response_time=None):
    """Process a single lesson question with ENHANCED response time and difficulty conditioning"""
    session = create_or_get_session(user_id)
    if not session:
        return 0.5

    vocab = extract_vocabulary_from_question(question)
    if not vocab:
        return 0.5

    vocab = vocab.lower().strip()

    # CRITICAL FIX: For pronunciation questions, check accuracy attribute
    actual_is_correct = is_correct
    if hasattr(question, 'type') and question.type == 'Pronunciation':
        accuracy = getattr(question, 'accuracy', 0.0)
        accuracy_threshold = getattr(question, 'accuracy_threshold', 0.6)
        actual_is_correct = accuracy >= accuracy_threshold

        print(f"[LessonBKT] Pronunciation question processing:")
        print(f"  - Original is_correct: {is_correct}")
        print(f"  - Question accuracy: {accuracy:.2f}")
        print(f"  - Accuracy threshold: {accuracy_threshold:.2f}")
        print(f"  - Actual is_correct: {actual_is_correct}")

    # CRITICAL: Override is_correct with the computed value
    is_correct = actual_is_correct

    # Get or initialize vocabulary in session
    if vocab not in session.session_predictions:
        base_mastery = get_base_mastery_for_new_vocab(user_id)
        session.session_predictions[vocab] = {
            'p_mastery': base_mastery,
            'guess': 0.25,
            'slip': 0.10,
            'confidence': 0.5,
            'correct': 0,
            'reviewed': False,
            'timestamp': int(time.time()),
            'difficulty_level': 1,
            'transferred_difficulty': 0,
            'observations': [],
            'response_times': []
        }
        print(f"[LessonBKT] Initialized '{vocab}' with base mastery: {base_mastery:.3f}")

    # Get current prediction
    current_pred = session.session_predictions[vocab]
    old_mastery = current_pred['p_mastery']
    old_guess = current_pred.get('guess', 0.25)
    old_slip = current_pred.get('slip', 0.10)

    # ENHANCED: Much more sophisticated response time and difficulty analysis
    base_learn_rate = 0.12  # Slightly lower base rate
    difficulty = getattr(question, 'difficulty', 1)

    # Enhanced difficulty-based expected times (more realistic)
    expected_times = {
        1: 1.5,   # Very easy - should be quick
        2: 2.5,   # Easy - reasonable time
        3: 4.0,   # Medium - think time
        4: 6.0,   # Hard - significant thought
        5: 8.0    # Very hard - lots of thinking
    }

    time_factor = 1.0
    difficulty_factor = 1.0

    if response_time:
        current_pred['response_times'].append(response_time)
        expected_time = expected_times.get(difficulty, 3.0)
        time_ratio = response_time / expected_time

        print(f"[LessonBKT] Response analysis: {response_time:.1f}s (expected: {expected_time:.1f}s, ratio: {time_ratio:.2f})")

        if is_correct:
            if time_ratio < 0.4:  # Very fast correct
                if difficulty <= 2:
                    time_factor = 1.4
                    print(f"[LessonBKT] Excellent: Very fast correct on easy question")
                else:
                    time_factor = 0.9
                    print(f"[LessonBKT] Suspicious: Very fast correct on hard question")
            elif time_ratio < 0.8:  # Reasonably fast correct
                if difficulty >= 4:
                    time_factor = 1.3
                    print(f"[LessonBKT] Excellent: Fast correct on hard question")
                else:
                    time_factor = 1.2
                    print(f"[LessonBKT] Good: Fast correct on medium question")
            elif time_ratio < 1.3:  # Normal time correct
                time_factor = 1.0
                print(f"[LessonBKT] Normal: Reasonable time correct")
            elif time_ratio < 2.0:  # Slow correct
                if difficulty >= 4:
                    time_factor = 0.95
                    print(f"[LessonBKT] Acceptable: Slow but correct on hard question")
                else:
                    time_factor = 0.7
                    print(f"[LessonBKT] Concerning: Slow correct on easy question")
            else:  # Very slow correct
                if difficulty >= 4:
                    time_factor = 0.8
                    print(f"[LessonBKT] Slow but correct: Very slow on hard question")
                else:
                    time_factor = 0.6
                    print(f"[LessonBKT] Slow but correct: Very slow on easy question")
        else:
            if time_ratio < 0.5:
                time_factor = 0.2
                print(f"[LessonBKT] Very poor: Fast incorrect (careless/guessing)")
            elif time_ratio < 1.0:
                time_factor = 0.4
                print(f"[LessonBKT] Poor: Medium speed incorrect")
            else:
                time_factor = 0.3
                print(f"[LessonBKT] Very poor: Slow incorrect (struggled and failed)")

    # ENHANCED: More pronounced difficulty-based adjustments
    if difficulty <= 1:
        difficulty_factor = 0.6
        print(f"[LessonBKT] Very easy question - reduced learning factor")
    elif difficulty == 2:
        difficulty_factor = 0.8
        print(f"[LessonBKT] Easy question - reduced learning factor")
    elif difficulty == 3:
        difficulty_factor = 1.0
        print(f"[LessonBKT] Medium question - standard learning factor")
    elif difficulty == 4:
        difficulty_factor = 1.4
        print(f"[LessonBKT] Hard question - increased learning factor")
    else:
        difficulty_factor = 1.8
        print(f"[LessonBKT] Very hard question - greatly increased learning factor")

    learn_rate = base_learn_rate * time_factor * difficulty_factor
    learn_rate = max(0.02, min(0.4, learn_rate))

    print(f"[LessonBKT] Final learning rate: {learn_rate:.3f} "
          f"(base: {base_learn_rate:.3f} × time: {time_factor:.2f} × difficulty: {difficulty_factor:.2f})")

    observations = current_pred.get('observations', [])

    # Adaptive parameter adjustment based on performance history
    if response_time is not None:
        # Use time_ratio and difficulty for dynamic adjustment
        if is_correct:
            # Fast and correct on hard question: decrease guess/slip more
            if time_ratio < 0.8 and difficulty >= 4:
                new_guess = max(0.02, old_guess * 0.7)
                new_slip = max(0.02, old_slip * 0.8)
            # Fast and correct on easy/medium: moderate decrease
            elif time_ratio < 0.8:
                new_guess = max(0.03, old_guess * 0.8)
                new_slip = max(0.03, old_slip * 0.85)
            # Slow and correct on easy: less decrease, maybe slight increase in slip
            elif time_ratio > 1.5 and difficulty <= 2:
                new_guess = max(0.05, old_guess * 0.95)
                new_slip = min(0.4, old_slip * 1.05)
            else:
                # Default: gentle decrease
                new_guess = max(0.03, old_guess * 0.9)
                new_slip = max(0.03, old_slip * 0.9)
        else:
            # Incorrect and fast: likely guessing, increase guess
            if time_ratio < 0.8:
                new_guess = min(0.5, old_guess * 1.15)
                new_slip = min(0.4, old_slip * 1.05)
            # Incorrect and slow: likely confusion, increase slip more
            elif time_ratio > 1.5:
                new_guess = min(0.5, old_guess * 1.05)
                new_slip = min(0.4, old_slip * 1.15)
            else:
                # Default: gentle increase
                new_guess = min(0.5, old_guess * 1.05)
                new_slip = min(0.4, old_slip * 1.05)
    else:
        # Fallback if no response_time: use old logic or keep unchanged
        new_guess = old_guess
        new_slip = old_slip

    # Consistency bonus/penalty (optional, can keep from your original code)
    if len(observations) >= 2:
        recent_performance = [obs.get('correct', False) for obs in observations[-5:]]
        if len(recent_performance) >= 3:
            if all(recent_performance[-3:]):
                learn_rate *= 1.2
                print(f"[LessonBKT] Consistency bonus applied - 3 correct in a row")
            elif not any(recent_performance[-3:]):
                learn_rate *= 0.7
                print(f"[LessonBKT] Consistency penalty applied - 3 incorrect in a row")

    # Enhanced BKT update with dynamic parameters
    if is_correct:
        new_mastery = (old_mastery * (1 - new_slip)) / (old_mastery * (1 - new_slip) + (1 - old_mastery) * new_guess)
        new_mastery = new_mastery + (1 - new_mastery) * learn_rate
    else:
        new_mastery = (old_mastery * new_slip) / (old_mastery * new_slip + (1 - old_mastery) * (1 - new_guess))
        new_mastery = new_mastery + (1 - new_mastery) * (learn_rate * 0.4)

    new_mastery = max(0.01, min(0.99, new_mastery))
    new_guess = max(0.02, min(0.5, new_guess))
    new_slip = max(0.02, min(0.4, new_slip))

    confidence = calculate_bkt_confidence_enhanced(new_mastery, new_guess, new_slip, vocab, current_pred)

    current_pred['p_mastery'] = new_mastery
    current_pred['guess'] = new_guess
    current_pred['slip'] = new_slip
    current_pred['confidence'] = confidence
    current_pred['timestamp'] = int(time.time())
    current_pred['correct'] = 1 if is_correct else 0

    observation = {
        'correct': is_correct,
        'timestamp': int(time.time()),
        'question_id': question_id,
        'difficulty': difficulty,
        'response_time': response_time,
        'type': getattr(question, 'type', None),
        'time_ratio': time_ratio if response_time else None,
        'time_factor': time_factor,
        'difficulty_factor': difficulty_factor,
        'learn_rate': learn_rate
    }

    if 'observations' not in current_pred:
        current_pred['observations'] = []
    current_pred['observations'].append(observation)

    print(f"[LessonBKT] Updated '{vocab}': mastery {old_mastery:.3f}→{new_mastery:.3f}, " +
          f"guess {old_guess:.3f}→{new_guess:.3f}, slip {old_slip:.3f}→{new_slip:.3f}, " +
          f"conf: {confidence:.3f} (correct={is_correct})")

    save_session_to_file(user_id, session)

    return new_mastery

def calculate_bkt_confidence_enhanced(mastery, guess, slip, vocab=None, prediction_data=None):
    """Enhanced confidence calculation considering response patterns"""
    base_conf = 0.5
    
    # Mastery contribution (higher mastery = higher confidence)
    mastery_contrib = 0.25 * min(1.0, mastery)
    
    # Parameter quality (lower guess/slip = higher confidence)
    param_contrib = 0.15 * (1.0 - (guess + slip) / 2.0)
    
    # Consistency contribution from observations
    consistency_contrib = 0.0
    if prediction_data and 'observations' in prediction_data:
        observations = prediction_data['observations']
        if len(observations) >= 3:
            recent_results = [obs.get('correct', False) for obs in observations[-5:]]
            consistency = sum(recent_results) / len(recent_results)
            consistency_contrib = 0.10 * consistency
    
    # Response time contribution
    time_contrib = 0.0
    if prediction_data and 'observations' in prediction_data:
        # Only consider non-Lesson observations for response time
        times = [
            obs['response_time']
            for obs in prediction_data['observations']
            if obs.get('response_time') and getattr(obs, 'type', None) != 'Lesson' and obs.get('type', None) != 'Lesson'
        ]
        if times:
            avg_time = sum(times) / len(times)
            # Optimal time range is 2-4 seconds
            if 2.0 <= avg_time <= 4.0:
                time_contrib = 0.10
            elif avg_time < 2.0:
                time_contrib = 0.05  # Very fast might be guessing
            else:
                time_contrib = 0.02  # Very slow suggests uncertainty

    confidence = base_conf + mastery_contrib + param_contrib + consistency_contrib + time_contrib
    return min(0.95, max(0.25, confidence))

def get_base_mastery_for_new_vocab(user_id):
    """Get base mastery for new vocabulary based on overall proficiency only"""
    try:
        import pymongo
        arami = pymongo.MongoClient("mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/")["arami"]
        users_col = arami["users"]
        
        user_doc = users_col.find_one({"user_id": int(user_id)})
        if user_doc:
            # Get overall proficiency
            proficiency = user_doc.get("proficiency", 0.5)
            if isinstance(proficiency, dict):
                proficiency = proficiency.get("proficiency", 0.5)
            
            # Convert to 0-1 scale if needed
            if proficiency > 1.0:
                proficiency = proficiency / 100.0
            
            # Base mastery mapping from overall proficiency
            if proficiency < 0.2:
                base_mastery = 0.3  # Low proficiency → low starting mastery
            elif proficiency < 0.4:
                base_mastery = 0.4  # Medium-low proficiency
            elif proficiency < 0.6:
                base_mastery = 0.5  # Medium proficiency
            elif proficiency < 0.8:
                base_mastery = 0.6  # High proficiency
            else:
                base_mastery = 0.7  # Very high proficiency
            
            print(f"[LessonBKT] Base mastery for new vocab: {base_mastery:.3f} (from proficiency: {proficiency:.3f})")
            return base_mastery
            
    except Exception as e:
        print(f"[LessonBKT] Error getting base mastery: {e}")
    
    return 0.5  # Default

def get_vocab_performance_summary(prediction):
    """
    Calculate the percent correct for a vocabulary from its observations.
    Ensures all 'correct' values are treated as int (0/1).
    """
    observations = prediction.get('observations', [])
    if not observations:
        return 0.0

    correct_count = 0
    total_count = 0
    for obs in observations:
        if 'correct' in obs:
            val = obs['correct']
            # Convert bool to int if needed
            if isinstance(val, bool):
                val = int(val)
            correct_count += val
            total_count += 1

    if total_count == 0:
        return 0.0

    percent = (correct_count / total_count) * 100
    return percent

def get_difficulty_transfer_bonus(user_id, vocab):
    """Get difficulty transfer bonus for a vocabulary"""
    session = create_or_get_session(user_id)
    if not session:
        return 0
    
    # Check if there's a difficulty transfer for this vocab
    if hasattr(session, 'difficulty_transfers') and session.difficulty_transfers:
        transfer_info = session.difficulty_transfers.get(vocab.lower(), {})
        if transfer_info:
            bonus = transfer_info.get('bonus', 0)
            source = transfer_info.get('source_vocab', 'unknown')
            transfer_type = transfer_info.get('transfer_type', 'unknown')
            
            if bonus > 0:
                print(f"[DifficultyTransfer] Applying +{bonus} difficulty bonus to '{vocab}' (from '{source}' - {transfer_type} performance)")
            
            # Clear the transfer after using it once
            del session.difficulty_transfers[vocab.lower()]
            save_session_to_file(user_id, session)
            
            return bonus
    
    return 0

def get_vocab_difficulty_info(user_id, vocab):
    """Get comprehensive difficulty information for a vocabulary"""
    session = create_or_get_session(user_id)
    if not session or vocab.lower() not in session.session_predictions:
        return {
            'base_mastery': 0.5,
            'difficulty_bonus': 0,
            'final_difficulty': 2,  # Changed from 1 to 2 (middle difficulty)
            'source': 'default'
        }
    
    pred = session.session_predictions[vocab.lower()]
    mastery = pred.get('p_mastery', 0.5)
    
    # UPDATED: Calculate base difficulty from mastery (1-5 range)
    if mastery >= 0.85:
        base_difficulty = 5  # Hardest
    elif mastery >= 0.75:
        base_difficulty = 4  # Hard
    elif mastery >= 0.65:
        base_difficulty = 3  # Medium-hard
    elif mastery >= 0.45:
        base_difficulty = 2  # Medium
    else:
        base_difficulty = 1  # Easy
    
    # Get transfer bonus
    difficulty_bonus = get_difficulty_transfer_bonus(user_id, vocab)
    final_difficulty = min(5, max(1, base_difficulty + difficulty_bonus))  # Cap between 1-5
    
    return {
        'base_mastery': mastery,
        'base_difficulty': base_difficulty,
        'difficulty_bonus': difficulty_bonus,
        'final_difficulty': final_difficulty,
        'source': 'session_data'
    }

def extract_vocabulary_from_question(question):
    """Extract vocabulary from question object consistently"""
    try:
        # Try multiple attribute names for vocabulary
        vocab_attrs = ['vocabulary', 'word_to_translate', 'vocab']
        
        for attr in vocab_attrs:
            vocab = getattr(question, attr, None)
            if vocab and isinstance(vocab, str) and vocab.strip():
                return vocab.strip()
        
        # Fallback: try to get from question content
        question_text = getattr(question, 'question', '')
        if question_text:
            # This is a simplified extraction - you might want to make it more sophisticated
            return question_text.split()[0] if question_text.split() else None
        
        return None
        
    except Exception as e:
        print(f"[LessonBKT] Error extracting vocabulary: {e}")
        return None

def save_session_to_file(user_id, session):
    """Save session to file for persistence"""
    try:
        session_file = f"lesson_session_{user_id}.json" if user_id else "lesson_session.json"

        # Prepare session data for JSON serialization
        # CRITICAL FIX: Convert all 'correct' in observations to int
        session_predictions = session.session_predictions.copy()
        for vocab, pred in session_predictions.items():
            if 'observations' in pred:
                for obs in pred['observations']:
                    if 'correct' in obs:
                        obs['correct'] = int(obs['correct'])

        session_data = {
            'user_id': session.user_id,
            'session_id': session.session_id,
            'session_start_time': session.session_start_time,
            'seen_vocabulary': list(session.seen_vocabulary),
            'difficulty_factors': session.difficulty_factors,
            'session_predictions': session_predictions,
            'database_predictions': session.database_predictions,
            'merged_predictions': session.merged_predictions,
            'difficulty_transfers': getattr(session, 'difficulty_transfers', {}),
            'timestamp': int(time.time())
        }

        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        print(f"[LessonBKT] Saved session to {session_file}")
        return True

    except Exception as e:
        print(f"[LessonBKT] Error saving session to file: {e}")
        return False

def load_session_from_file(user_id, session_id=None):
    """Load session from file if it exists"""
    try:
        session_file = f"lesson_session_{user_id}.json" if user_id else "lesson_session.json"
        
        if not os.path.exists(session_file):
            return None
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Recreate session object
        session = LessonSession(user_id, session_id)
        session.session_start_time = session_data.get('session_start_time', time.time())
        session.seen_vocabulary = set(session_data.get('seen_vocabulary', []))
        session.difficulty_factors = session_data.get('difficulty_factors', {})
        session.session_predictions = session_data.get('session_predictions', {})
        session.database_predictions = session_data.get('database_predictions', {})
        session.merged_predictions = session_data.get('merged_predictions', {})
        session.difficulty_transfers = session_data.get('difficulty_transfers', {})
        
        print(f"[LessonBKT] Loaded session from {session_file}")
        return session
        
    except Exception as e:
        print(f"[LessonBKT] Error loading session from file: {e}")
        return None

def calculate_difficulty_transfer(user_id, completed_vocab, next_vocab_list):
    """Calculate difficulty transfer bonus based on previous vocabulary performance"""
    session = create_or_get_session(user_id)
    if not session or completed_vocab.lower() not in session.session_predictions:
        return {}
    
    completed_pred = session.session_predictions[completed_vocab.lower()]
    observations = completed_pred.get('observations', [])
    
    if len(observations) < 2:
        return {}
    
    # Calculate performance metrics
    correct_count = sum(1 for obs in observations if obs.get('correct', False))
    total_count = len(observations)
    accuracy = correct_count / total_count if total_count > 0 else 0
    
    # Calculate average difficulty of completed vocabulary
    difficulties = [obs.get('difficulty', 2) for obs in observations]
    avg_difficulty = sum(difficulties) / len(difficulties) if difficulties else 2
    
    # UPDATED: Determine difficulty transfer bonus with 1-5 range
    difficulty_transfer = {}
    
    if accuracy >= 0.9:  # Excellent performance (90%+)
        bonus = min(2, max(0, int(avg_difficulty) + 1 - 2))  # Increase by 1, but reasonable cap
        transfer_type = "excellent"
    elif accuracy >= 0.75:  # Good performance (75%+)
        bonus = max(0, min(1, int(avg_difficulty) - 2))  # Maintain or slight increase
        transfer_type = "good"
    elif accuracy >= 0.5:  # Moderate performance (50%+)
        bonus = max(-1, int(avg_difficulty) - 3)  # Slight decrease
        transfer_type = "moderate"
    else:  # Poor performance (<50%)
        bonus = -2  # Decrease difficulty significantly
        transfer_type = "poor"
    
    print(f"[LessonBKT] Difficulty transfer from '{completed_vocab}': accuracy={accuracy:.1%}, avg_diff={avg_difficulty:.1f} → bonus={bonus} ({transfer_type})")
    
    # Apply to next vocabularies
    for vocab in next_vocab_list:
        difficulty_transfer[vocab.lower()] = {
            'bonus': bonus,
            'source_vocab': completed_vocab,
            'source_accuracy': accuracy,
            'transfer_type': transfer_type
        }
    
    return difficulty_transfer

def get_next_vocabulary(user_id, remaining_vocab_list, num=1):
    """Get next vocabulary to focus on with difficulty transfer"""
    session = create_or_get_session(user_id)
    if not session or not remaining_vocab_list:
        return remaining_vocab_list[:num] if remaining_vocab_list else []
    
    # Check if we just completed a vocabulary (has 3+ observations)
    completed_vocab = None
    for vocab, pred in session.session_predictions.items():
        observations = pred.get('observations', [])
        if len(observations) >= 3:  # Just completed
            # Check if this was the most recently updated
            if pred.get('timestamp', 0) == max(p.get('timestamp', 0) for p in session.session_predictions.values()):
                completed_vocab = vocab
                break
    
    if completed_vocab:
        # Calculate and apply difficulty transfer
        difficulty_transfer = calculate_difficulty_transfer(user_id, completed_vocab, remaining_vocab_list)
        
        # Apply difficulty transfer to session
        for vocab, transfer_info in difficulty_transfer.items():
            if vocab in [v.lower() for v in remaining_vocab_list]:
                # Store difficulty transfer info in session for later use
                if 'difficulty_transfers' not in session.__dict__:
                    session.difficulty_transfers = {}
                session.difficulty_transfers[vocab] = transfer_info
                print(f"[LessonBKT] Prepared difficulty transfer for '{vocab}': +{transfer_info['bonus']} difficulty")
        
        # Save session with transfer info
        save_session_to_file(user_id, session)
    
    # Return next vocabulary in order (preserve qbank ordering)
    return remaining_vocab_list[:num]

def update_session_bkt(user_id, impact_scale=1.0, session_id=None):
    """Update BKT for the current session"""
    session = create_or_get_session(user_id, session_id)
    return session.process_bkt_update(impact_scale)

def save_session_to_database(user_id):
    """Save lesson BKT session data to database - FIXED to actually save data"""
    try:
        session = create_or_get_session(user_id)
        if not session:
            print(f"[LessonBKT] No session to save for user {user_id}")
            return False
        
        if not session.session_predictions:
            print(f"[LessonBKT] No session predictions to save for user {user_id}")
            return False
        
        print(f"[LessonBKT] Starting database save for user {user_id} with {len(session.session_predictions)} predictions")
        
        # Connect to database
        arami = pymongo.MongoClient(uri)["arami"]
        users_col = arami["users"]
        
        user_doc = users_col.find_one({"user_id": int(user_id)})
        if not user_doc:
            print(f"[LessonBKT] User {user_id} not found")
            return False
        
        # Get existing BKT data
        existing_bkt_data = user_doc.get("bkt_data", {})
        if not isinstance(existing_bkt_data, dict):
            existing_bkt_data = {}
        
        # CRITICAL FIX: Ensure predictions structure exists
        if "predictions" not in existing_bkt_data:
            existing_bkt_data["predictions"] = {}
        
        existing_predictions = existing_bkt_data["predictions"]
        
        # Add session predictions (these take precedence)
        new_vocab_count = 0
        updated_vocab_count = 0
        
        for vocab, pred in session.session_predictions.items():
            if vocab not in existing_predictions:
                new_vocab_count += 1
                print(f"[LessonBKT] Adding NEW vocab '{vocab}': mastery={pred.get('p_mastery', 0.5):.6f}")
            else:
                old_mastery = existing_predictions[vocab].get('p_mastery', 0.5)
                new_mastery = pred.get('p_mastery', 0.5)
                if abs(old_mastery - new_mastery) > 0.001:  # Only count as update if significant change
                    updated_vocab_count += 1
                    print(f"[LessonBKT] Updating vocab '{vocab}': {old_mastery:.6f} → {new_mastery:.6f}")
            
            existing_predictions[vocab] = pred
        
        # CRITICAL FIX: Also save to main BKT structure for compatibility
        for vocab, pred in session.session_predictions.items():
            existing_bkt_data[vocab] = {
                'prior': pred.get('p_mastery', 0.5),
                'guess': pred.get('guess', 0.25),
                'slip': pred.get('slip', 0.1),
                'learn': 0.15,
                'observations': pred.get('observations', []),
                'timestamp': int(time.time())
            }
        
        # Update BKT data structure
        updated_bkt_data = {
            **existing_bkt_data,
            "predictions": existing_predictions,
            "last_lesson_update": int(time.time()),
            "lesson_vocab_count": len(session.session_predictions)
        }
        
        # Save to database
        update_result = users_col.update_one(
            {"user_id": int(user_id)},
            {"$set": {"bkt_data": updated_bkt_data}}
        )
        
        print(f"[LessonBKT] Database update result: matched={update_result.matched_count}, modified={update_result.modified_count}")
        print(f"[LessonBKT] Summary: {new_vocab_count} new vocab, {updated_vocab_count} updated vocab")
        
        if update_result.modified_count > 0:
            # CRITICAL: Also save to temp files for immediate use
            try:
                # Save lesson predictions file for logout processing
                lesson_file = f"lesson_bkt_predictions_{user_id}.json"
                with open(lesson_file, 'w') as f:
                    json.dump({
                        "predictions": existing_predictions,
                        "timestamp": int(time.time()),
                        "vocab_count": len(session.session_predictions)
                    }, f, indent=2)
                print(f"[LessonBKT] Created lesson predictions file: {lesson_file}")
                
                # Update main bkt_predictions.json for compatibility
                with open('bkt_predictions.json', 'w') as f:
                    json.dump(existing_predictions, f, indent=2)
                print(f"[LessonBKT] Updated main bkt_predictions.json with {len(existing_predictions)} predictions")
                
            except Exception as e:
                print(f"[LessonBKT] Error creating temp files: {e}")
            
            print(f"[LessonBKT] Successfully saved {len(session.session_predictions)} vocabulary predictions")
            return True
        else:
            print(f"[LessonBKT] No changes were made to database")
            return False
            
    except Exception as e:
        print(f"[LessonBKT] Error saving to database: {e}")
        import traceback
        traceback.print_exc()
    return False
    
def save_lesson_bkt_to_temp_files(user_id, session):
    """Save lesson BKT data to temp files as backup (similar to bkt_engine.py)"""
    try:
        # 1. Save BKT data to temp file
        temp_bkt_file = f"temp_lesson_bkt_data_{user_id}.json" if user_id else "temp_lesson_bkt_data.json"
        
        bkt_data = {}
        if session.bkt_predictor and hasattr(session.bkt_predictor, 'vocab_parameters'):
            for vocab, params in session.bkt_predictor.vocab_parameters.items():
                if isinstance(params, dict) and vocab not in ["fitted", "refit_counter"]:
                    bkt_data[vocab] = {
                        'prior': float(params.get('prior', 0.5)),
                        'guess': float(params.get('guess', 0.25)),
                        'slip': float(params.get('slip', 0.1)),
                        'learn': float(params.get('learn', 0.15)),
                        'observations': params.get('observations', [])
                    }
        
        with open(temp_bkt_file, 'w') as f:
            json.dump(bkt_data, f, indent=2)
        print(f"[LessonBKT] Saved BKT data to {temp_bkt_file}")
        
        # 2. Save predictions to temp file (compatible with bkt_predictions.json format)
        temp_predictions_file = f"lesson_bkt_predictions_{user_id}.json" if user_id else "lesson_bkt_predictions.json"
        
        predictions_data = {
            "predictions": session.session_predictions,
            "merged_predictions": session.merged_predictions,
            "timestamp": int(time.time()),
            "user_id": user_id
        }
        
        with open(temp_predictions_file, 'w') as f:
            json.dump(predictions_data, f, indent=2)
        print(f"[LessonBKT] Saved predictions to {temp_predictions_file}")
        
        # 3. Also update the main bkt_predictions.json file for compatibility
        try:
            # Load existing predictions
            existing_predictions = {}
            if os.path.exists('bkt_predictions.json'):
                with open('bkt_predictions.json', 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        existing_predictions = data.get('predictions', data)
            
            # Merge with lesson predictions
            for vocab, pred in session.session_predictions.items():
                existing_predictions[vocab] = pred
            
            # Save back to main file
            with open('bkt_predictions.json', 'w') as f:
                json.dump(existing_predictions, f, indent=2)
            print(f"[LessonBKT] Updated main bkt_predictions.json with {len(session.session_predictions)} items")
            
        except Exception as e:
            print(f"[LessonBKT] Error updating main predictions file: {e}")
        
        return True
        
    except Exception as e:
        print(f"[LessonBKT] Error saving to temp files: {e}")
        return False

def load_lesson_bkt_from_temp_files(user_id):
    """Load lesson BKT data from temp files if database fails"""
    try:
        # 1. Try to load BKT data
        temp_bkt_file = f"temp_lesson_bkt_data_{user_id}.json" if user_id else "temp_lesson_bkt_data.json"
        bkt_data = {}
        
        if os.path.exists(temp_bkt_file):
            with open(temp_bkt_file, 'r') as f:
                bkt_data = json.load(f)
            print(f"[LessonBKT] Loaded BKT data from {temp_bkt_file}")
        
        # 2. Try to load predictions
        temp_predictions_file = f"lesson_bkt_predictions_{user_id}.json" if user_id else "lesson_bkt_predictions.json"
        predictions_data = {}
        
        if os.path.exists(temp_predictions_file):
            with open(temp_predictions_file, 'r') as f:
                predictions_data = json.load(f)
            print(f"[LessonBKT] Loaded predictions from {temp_predictions_file}")
        
        return bkt_data, predictions_data
        
    except Exception as e:
        print(f"[LessonBKT] Error loading from temp files: {e}")
        return {}, {}

def clear_lesson_bkt_temp_files(user_id=None):
    """Clear lesson BKT temp files"""
    files_to_clear = [
        f"temp_lesson_bkt_data_{user_id}.json" if user_id else "temp_lesson_bkt_data.json",
        f"lesson_bkt_predictions_{user_id}.json" if user_id else "lesson_bkt_predictions.json"
    ]
    
    for file_path in files_to_clear:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[LessonBKT] Removed temp file: {file_path}")
            except Exception as e:
                print(f"[LessonBKT] Error removing {file_path}: {e}")

def get_session_bkt_sequence(user_id, session_id=None):
    """Get BKT sequence from current session - FIXED to not add extra padding"""
    try:
        session = create_or_get_session(user_id, session_id)
        if not session or not session.session_predictions:
            print(f"[LessonBKT] No session data, returning default sequence")
            return [0.5, 0.55, 0.6, 0.65, 0.7]
        
        # Get actual mastery values from session (NO PADDING)
        masteries = []
        vocab_count = 0
        
        print(f"[LessonBKT] Generating sequence from {len(session.session_predictions)} session vocabularies:")
        for vocab, prediction in session.session_predictions.items():
            mastery = prediction.get('p_mastery', 0.5)
            masteries.append(mastery)
            vocab_count += 1
            print(f"  {vocab_count}. {vocab}: {mastery:.3f}")
        
        # CRITICAL FIX: Return actual sequence without any padding
        print(f"[LessonBKT] Generated sequence from {len(masteries)} vocabularies (no padding)")
        return masteries
        
    except Exception as e:
        print(f"[LessonBKT] Error generating sequence: {e}")
        return [0.5, 0.55, 0.6, 0.65, 0.7]

def get_lesson_bkt_summary(user_id):
    """Get summary of lesson BKT session"""
    session = create_or_get_session(user_id)
    if not session:
        return "No session data available"
    
    session_count = len([v for v in session.session_predictions.values() 
                        if v.get('timestamp', 0) > 0])
    
    # Count transferred vocabularies (those with default timestamps or low confidence)
    transferred_count = 0
    for vocab, pred in session.session_predictions.items():
        if pred.get('confidence', 0.5) == 0.5 and len(pred.get('observations', [])) == 0:
            transferred_count += 1
    
    avg_mastery = 0.0
    if session.session_predictions:
        masteries = [p.get('p_mastery', 0.5) for p in session.session_predictions.values()]
        avg_mastery = sum(masteries) / len(masteries)
    
    return f"{session_count} session, {transferred_count} transferred, avg mastery: {avg_mastery:.3f}"
        
def get_next_vocabulary(user_id, vocab_list, num=1, session_id=None):
    """Get the next vocabulary to focus on"""
    session = create_or_get_session(user_id, session_id)
    return session.get_next_vocabulary(vocab_list, num)

def clear_session(user_id, session_id=None):
    """Clear a session from memory"""
    with session_lock:
        session_key = f"{user_id}_{session_id}" if session_id else f"{user_id}_default"
        if session_key in active_sessions:
            del active_sessions[session_key]
            return True
        return False

# Utility function to use in run_bkt_and_lstm
def run_lesson_bkt_and_get_sequence(user_id, correct_answers, incorrect_answers, impact_scale=1.0):
    """
    Process a lesson session and return the BKT sequence
    This is the main integration point for run_bkt_and_lstm
    """
    # Create a new session
    session_id = f"lesson_{int(time.time())}"
    session = create_or_get_session(user_id, session_id)
    
    # Add all answers to the session
    for key, question in correct_answers.items():
        session.add_correct_answer(key, question)
    
    for key, question in incorrect_answers.items():
        session.add_incorrect_answer(key, question)
    
    # Process BKT update
    session.process_bkt_update(impact_scale)
    
    # Save to database
    session.save_to_database()
    
    # Get the BKT sequence
    bkt_sequence = session.get_bkt_sequence()
    
    # Clear the session
    clear_session(user_id, session_id)
    
    return bkt_sequence


def get_session_bkt(user_id, session_id=None):
    """Get the BKT session for a user, creating it if needed"""
    try:
        session = create_or_get_session(user_id, session_id)
        
        # Ensure the session has a BKT predictor
        if not session.bkt_predictor:
            session.bkt_predictor = get_custom_bkt(user_id)
            if not session.bkt_predictor:
                session.bkt_predictor = CustomBKTPredictor()
                print(f"[LessonBKT] Created new BKT predictor for user {user_id}")
            else:
                print(f"[LessonBKT] Loaded existing BKT predictor for user {user_id}")
        
        # Load database predictions if not already loaded
        if not session.database_predictions:
            session._load_database_predictions()
            session._merge_predictions()
        
        # Initialize vocabulary count tracking
        vocab_count = 0
        if session.bkt_predictor and hasattr(session.bkt_predictor, 'vocab_parameters'):
            vocab_count = len([k for k in session.bkt_predictor.vocab_parameters.keys() 
                             if k not in ['fitted', 'refit_counter']])
        
        print(f"[LessonBKT] Session initialized for user {user_id} with {vocab_count} vocabulary items")
        print(f"[LessonBKT] Session has {len(session.seen_vocabulary)} seen vocabulary in current session")
        return session
        
    except Exception as e:
        print(f"[LessonBKT] Error getting session BKT: {e}")
        traceback.print_exc()
        return None

def reset_session(user_id, session_id=None):
    """Reset/clear a session - alias for clear_session"""
    return clear_session(user_id, session_id)

def get_next_vocabulary_simple(user_id, current_vocab=None, session_id=None):
    """Simple version that returns the next vocabulary item to focus on"""
    try:
        session = create_or_get_session(user_id, session_id)
        
        # Get all vocabulary from the BKT predictor
        if session.bkt_predictor:
            all_vocab = list(session.bkt_predictor.vocab_parameters.keys())
            # Remove system keys
            all_vocab = [v for v in all_vocab if v not in ["fitted", "refit_counter"]]
        else:
            all_vocab = list(session.merged_predictions.keys())
        
        if not all_vocab:
            return None
            
        # If no current vocab specified, return the first one
        if not current_vocab:
            return all_vocab[0] if all_vocab else None
            
        # Find current vocab index
        try:
            current_idx = all_vocab.index(current_vocab.lower().strip())
            next_idx = current_idx + 1
            
            # Return next vocab if available
            if next_idx < len(all_vocab):
                return all_vocab[next_idx]
            else:
                return None  # No more vocabulary
                
        except ValueError:
            # Current vocab not found, return first available
            return all_vocab[0] if all_vocab else None
            
    except Exception as e:
        print(f"[LessonBKT] Error getting next vocabulary: {e}")
        return None
    
def display_lesson_bkt_predictions(user_id):
    """Display current BKT predictions for lesson session - RAW VALUES"""
    try:
        session = create_or_get_session(user_id)
        if not session:
            print("[LessonBKT] No active session found")
            return 0
        
        session_predictions = session.session_predictions
        
        # Get database predictions for comparison
        db_predictions = {}
        try:
            arami = pymongo.MongoClient(uri)["arami"]
            user_doc = arami["users"].find_one({"user_id": int(user_id)})
            if user_doc and "bkt_data" in user_doc:
                bkt_data = user_doc["bkt_data"]
                if "predictions" in bkt_data:
                    db_predictions = bkt_data["predictions"]
        except Exception as e:
            print(f"[LessonBKT] Error loading database predictions: {e}")
        
        # Combine predictions
        all_predictions = {}
        for vocab, pred in db_predictions.items():
            all_predictions[vocab] = {**pred, 'source': 'Database'}
        for vocab, pred in session_predictions.items():
            all_predictions[vocab] = {**pred, 'source': 'Session'}
        
        if not all_predictions:
            print("[LessonBKT] No predictions to display")
            return 0
        
        session_count = len(session_predictions)
        db_count = len([v for v in all_predictions.values() if v.get('source') == 'Database'])
        
        # ENHANCED: Display table with RAW values
        print("┌" + "─" * 95 + "┐")
        print(f"│ LESSON BKT PREDICTIONS ({session_count} session, {db_count} database) - RAW VALUES │".ljust(97) + "│")
        print("├" + "─" * 20 + "┬" + "─" * 15 + "┬" + "─" * 12 + "┬" + "─" * 12 + "┬" + "─" * 12 + "┬" + "─" * 10 + "┬" + "─" * 8 + "┤")
        print("│ Vocabulary           │ Mastery         │ Guess        │ Slip         │ Conf         │ Obs/RT   │ Source │")
        print("├" + "─" * 20 + "┼" + "─" * 15 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 12 + "┼" + "─" * 10 + "┼" + "─" * 8 + "┤")
        
        # Sort by mastery (descending)
        sorted_predictions = sorted(all_predictions.items(), 
                                  key=lambda x: (-x[1].get('p_mastery', 0), x[1]['source'] != 'Session'))
        
        for vocab, prediction in sorted_predictions:
            mastery = prediction.get('p_mastery', 0)
            guess = prediction.get('guess', 0)
            slip = prediction.get('slip', 0)
            confidence = prediction.get('confidence', 0)
            source = prediction['source']
            
            # Calculate observation display
            observations = prediction.get('observations', [])
            obs_count = len(observations) if isinstance(observations, list) else 0
            
            response_times = []
            if isinstance(observations, list):
                for obs in observations:
                    if isinstance(obs, dict) and 'response_time' in obs:
                        rt = obs['response_time']
                        if rt and rt > 0:
                            response_times.append(rt)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            if obs_count > 0:
                if avg_response_time > 0:
                    obs_display = f"{obs_count}obs/{avg_response_time:.1f}s"
                else:
                    obs_display = f"{obs_count} obs"
            else:
                obs_display = "No obs"
            
            if len(obs_display) > 10:
                obs_display = obs_display[:9] + "…"
            
            # CRITICAL FIX: Show RAW values with higher precision
            print("│ {:<20} │ {:>12.8f}{}│ {:>10.6f} │ {:>10.6f} │ {:>10.6f} │ {:<10} │ {:<6} │".format(
                vocab[:20], mastery, '*' if source == 'Session' else ' ', guess, slip, confidence, obs_display, source
            ))
        
        print("└" + "─" * 20 + "┴" + "─" * 15 + "┴" + "─" * 12 + "┴" + "─" * 12 + "┴" + "─" * 12 + "┴" + "─" * 10 + "┴" + "─" * 8 + "┘")
        
        # ENHANCED: Print raw summary values
        print(f"\nRAW BKT VALUES SUMMARY:")
        for vocab, prediction in sorted_predictions:
            print(f"  {vocab}: mastery={prediction.get('p_mastery', 0):.8f}, "
                  f"guess={prediction.get('guess', 0):.6f}, "
                  f"slip={prediction.get('slip', 0):.6f}, "
                  f"conf={prediction.get('confidence', 0):.6f}")
        
        print(f"[LessonBKT] Displayed {len(all_predictions)} vocabulary predictions from lesson session")
        
        return len(all_predictions)
        
    except Exception as e:
        print(f"[LessonBKT] Error displaying predictions: {e}")
        return 0
