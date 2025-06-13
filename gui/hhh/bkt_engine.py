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
    
    def __init__(self, vocab_parameters):
        """Initialize with vocabulary parameters"""
        self.vocab_parameters = vocab_parameters
    
    def predict(self, vocab, correct_history=None):
        """
        Predict knowledge state using BKT algorithm
        
        Parameters:
        - vocab: The vocabulary item to predict mastery for
        - correct_history: List of 1s and 0s representing correct/incorrect responses
                          (if None, returns prior probability)
        
        Returns:
        - Mastery probability (0-1)
        """
        if vocab not in self.vocab_parameters:
            return 0.5  # Default for unknown vocab
        
        params = self.vocab_parameters[vocab]
        learn = params.get('learn', 0.15)    # Learning probability
        guess = params.get('guess', 0.25)    # Guess probability
        slip = params.get('slip', 0.1)       # Slip probability
        prior = params.get('prior', 0.5)     # Prior probability of mastery
        
        # If no history provided, return prior
        if correct_history is None or len(correct_history) == 0:
            return prior
            
        # Start with prior probability
        mastery = prior
        
        # Update for each observation in history
        for is_correct in correct_history:
            # Step 1: Update based on observation
            if is_correct:
                # P(mastered | correct)
                mastery = (mastery * (1 - slip)) / (mastery * (1 - slip) + (1 - mastery) * guess)
            else:
                # P(mastered | incorrect)
                mastery = (mastery * slip) / (mastery * slip + (1 - mastery) * (1 - guess))
                
            # Step 2: Account for learning
            mastery = mastery + (1 - mastery) * learn
            
        return mastery
    
    def predict_from_df(self, df):
        """
        Make predictions from a pandas DataFrame (similar to PyBKT interface)
        
        Parameters:
        - df: DataFrame with 'skill_name' and 'correct' columns
        
        Returns:
        - DataFrame with predictions added
        """
        result_df = df.copy()
        result_df['state_predictions'] = 0.0
        
        # Group by skill and user
        groups = df.groupby(['skill_name', 'user_id'])
        
        for (vocab, user), group in groups:
            # Get history of correct/incorrect for this user and skill
            history = group['correct'].astype(int).tolist()
            
            # Calculate probability for increasing prefixes of history
            for i in range(len(history)):
                prefix = history[:i+1]
                prob = self.predict(vocab, prefix)
                result_df.loc[group.index[i], 'state_predictions'] = prob
                
        return result_df
    
    def get_vocabulary_in_order(self):
        """Return vocabulary items in their original qbank order"""
        vocab_items = list(self.vocab_parameters.items())
        # Sort by the 'order' parameter
        vocab_items.sort(key=lambda x: x[1].get('order', 999999))
        return [vocab for vocab, _ in vocab_items]

def get_custom_bkt_path(user_id=None):
    """Get path for user-specific custom BKT predictor"""
    if user_id and str(user_id).lower() != "none":
        return f"custom_bkt_predictor_{user_id}.pkl"
    return "custom_bkt_predictor.pkl"

def load_custom_bkt(user_id=None):
    """Load the custom BKT predictor for a specific user"""
    model_path = get_custom_bkt_path(user_id)
    try:
        if os.path.exists(model_path):
            print(f"[BKT] Loading custom predictor for user {user_id}")
            
            with open(model_path, "rb") as f:
                try:
                    # Try normal loading first
                    predictor = pickle.load(f)
                    
                    # Check if the loaded predictor has the required method
                    if not hasattr(predictor, 'get_vocabulary_in_order'):
                        print(f"[BKT] Adding missing get_vocabulary_in_order method to predictor")
                        # Add the method dynamically
                        def get_vocabulary_in_order(self):
                            """Return vocabulary items in their original qbank order"""
                            vocab_items = list(self.vocab_parameters.items())
                            # Sort by the 'order' parameter
                            vocab_items.sort(key=lambda x: x[1].get('order', 999999))
                            return [vocab for vocab, _ in vocab_items]
                        
                        # Bind the method to the instance
                        import types
                        predictor.get_vocabulary_in_order = types.MethodType(get_vocabulary_in_order, predictor)
                    
                    return predictor
                    
                except (AttributeError, pickle.UnpicklingError):
                    # If that fails, reload and recreate object
                    f.seek(0)  # Go back to start of file
                    raw_data = pickle.load(f)
                    
                    # Extract parameters if possible
                    if hasattr(raw_data, 'vocab_parameters'):
                        vocab_params = raw_data.vocab_parameters
                        # Create a new CustomBKTPredictor with those parameters
                        return CustomBKTPredictor(vocab_params)
                    else:
                        print("[BKT] Could not extract parameters from predictor")
                        return None
        else:
            print(f"[BKT] No custom predictor found for user {user_id}, creating new one")
            
            # CHANGE: Explicitly create a user-specific predictor first
            user_predictor = create_user_bkt_predictor(user_id)
            if user_predictor:
                print(f"[BKT] Successfully created custom BKT predictor for user {user_id}")
                return user_predictor
                
            # Fall back to default if creation failed
            print(f"[BKT] Failed to create custom predictor, checking default")
            if os.path.exists("custom_bkt_predictor.pkl"):
                with open("custom_bkt_predictor.pkl", "rb") as f:
                    predictor = pickle.load(f)
                    # Save as user-specific model
                    save_custom_bkt(predictor, user_id)
                    return predictor
    except Exception as e:
        print(f"[BKT] Error loading custom BKT predictor: {e}")
    
    return None

def save_custom_bkt(predictor, user_id=None):
    """Save the custom BKT predictor for a specific user"""
    model_path = get_custom_bkt_path(user_id)
    try:
        with open(model_path, "wb") as f:
            pickle.dump(predictor, f)
        print(f"[BKT] Saved custom predictor for user {user_id}")
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
    custom_bkt = load_custom_bkt(user_id)
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

def select_adaptive_questions(questions_pool, user_performance=None, user_id=None):
    """
    Select questions adaptively while preserving lesson structure.
    Each vocabulary gets 1 lesson + 3 practice questions.
    Pronunciation questions are always included.
    Questions already seen won't be reused.
    """
    global current_vocab, questions_seen
    
    if not questions_pool:
        return []
        
    global uid
    if not user_id:
        user_id = uid
        
    # Load BKT predictor for proper vocab order
    custom_bkt = load_custom_bkt(user_id)
    ordered_vocab = custom_bkt.get_vocabulary_in_order() if custom_bkt else []
    
    # Filter out questions already seen
    fresh_questions = [q for q in questions_pool if getattr(q, "id", None) not in questions_seen]
    if not fresh_questions:
        print("[BKT] Warning: No fresh questions available!")
        return []
    
    # Group questions by vocabulary maintaining original order
    vocab_questions = {}
    
    for q in fresh_questions:
        vocab = getattr(q, "vocabulary", "").lower()
        if vocab not in vocab_questions:
            vocab_questions[vocab] = {"lesson": [], "pronunciation": [], "practice": []}
            
        if q.type == "Lesson":
            vocab_questions[vocab]["lesson"].append(q)
        elif q.type == "Pronunciation":
            vocab_questions[vocab]["pronunciation"].append(q)
        else:
            vocab_questions[vocab]["practice"].append(q)
    
    # Build the new batch preserving structure
    selected_questions = []
    
    # Determine which vocabularies to process based on current progress
    if current_vocab in ordered_vocab:
        current_index = ordered_vocab.index(current_vocab)
        vocabs_to_process = ordered_vocab[current_index:current_index+3]  # Current + next 2 vocabs
    else:
        vocabs_to_process = ordered_vocab[:3]  # First 3 vocabs
    
    # Mastery from previous vocab (for transfer learning)
    previous_mastery = 0.5  # Default medium mastery
    
    for vocab in vocabs_to_process:
        if vocab not in vocab_questions:
            continue
            
        # Get mastery for this vocabulary
        mastery = 0.4  # Default medium mastery
        if user_performance and vocab in user_performance:
            actual_performance = user_performance[vocab]
            # Use predicted mastery or calculate from answers if available
            if "predicted_mastery" in actual_performance:
                mastery = actual_performance["predicted_mastery"]
            elif actual_performance["answers"]:
                mastery = sum(actual_performance["answers"]) / len(actual_performance["answers"])
        
        # Apply mastery transfer from previous vocabulary
        if vocab != vocabs_to_process[0]:  # Not the first vocab in this batch
            # Blend current vocab mastery with previous performance
            mastery = (mastery * 0.7) + (previous_mastery * 0.3)
        
        print(f"[BKT] Vocab '{vocab}' has mastery {mastery:.2f}")
        
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
        
        # 3. Select practice questions based on difficulty and mastery
        remaining_slots = 3 - (1 if q_sets["pronunciation"] else 0)  # After lesson & pronunciation
        practice_questions = select_by_difficulty(q_sets["practice"], mastery, remaining_slots)
        
        for q in practice_questions:
            selected_questions.append(q)
            questions_seen.add(getattr(q, "id", None))
            print(f"[BKT] Added {q.type} question for '{vocab}' (difficulty: {getattr(q, 'difficulty', 'N/A')})")
        
        # Update previous mastery for next vocabulary
        previous_mastery = mastery
        
        # Update current vocabulary tracking
        if not current_vocab:
            current_vocab = vocab
    
    print(f"[BKT] Selected {len(selected_questions)} questions adaptively while preserving structure")
    return selected_questions

def update_current_vocab(completed_vocab, ordered_vocab_list):
    """
    Update the current vocabulary tracking based on completion
    
    Args:
        completed_vocab: The vocabulary item just completed
        ordered_vocab_list: Ordered list of vocabulary items
        
    Returns:
        The next vocabulary item
    """
    global current_vocab
    
    try:
        current_index = ordered_vocab_list.index(completed_vocab)
        if current_index < len(ordered_vocab_list) - 1:
            next_vocab = ordered_vocab_list[current_index + 1]
            current_vocab = next_vocab
            print(f"[BKT] Advancing to next vocabulary: {current_vocab}")
            return next_vocab
        else:
            current_vocab = None
            print("[BKT] All vocabularies completed")
            return None
    except ValueError:
        print(f"[BKT] Warning: Vocabulary '{completed_vocab}' not found in ordered list")
        return None

def check_vocab_completion(performance_data, vocab):
    """Check if a vocabulary item has been completed (all questions answered)"""
    if not vocab or vocab not in performance_data:
        return False
        
    # Typically 4 questions per vocabulary (1 lesson + 3 practice)
    data = performance_data.get(vocab, {})
    answers = data.get("answers", [])
    return len(answers) >= 4  # Consider vocab complete after 4 answers

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
    custom_bkt = load_custom_bkt(user_id)
    ordered_vocab = custom_bkt.get_vocabulary_in_order() if custom_bkt else []
    
    # Check if this vocabulary is complete
    is_vocab_complete = check_vocab_completion(performance_data, vocab)
    
    if is_vocab_complete:
        print(f"[BKT] Vocabulary '{vocab}' completed!")
        # Vocabulary complete, move to next vocabulary
        next_vocab = update_current_vocab(vocab, ordered_vocab)
        
        # Check if we need to rebatch for next vocabulary
        need_rebatch, rebatch_vocab = should_rebatch(performance_data, vocab, ordered_vocab)
        
        if need_rebatch:
            print(f"[BKT] Rebatching needed for next vocabulary '{rebatch_vocab}'")
            return True  # Signal that rebatching is needed
    
    return False  # No rebatching needed

def select_by_difficulty(questions, mastery, count):
    """Select questions with appropriate difficulty based on mastery level."""
    if not questions or count <= 0:
        return []
    
    # Sort questions by difficulty
    questions_by_difficulty = {}
    for q in questions:
        difficulty = getattr(q, "difficulty", 1)
        if difficulty not in questions_by_difficulty:
            questions_by_difficulty[difficulty] = []
        questions_by_difficulty[difficulty].append(q)
    
    # Define target difficulties based on mastery
    if mastery < 0.3:
        # Low mastery: select easier questions
        target_difficulties = [1, 1, 2]
    elif mastery > 0.7:
        # High mastery: select harder questions
        target_difficulties = [2, 3, 3]
    else:
        # Medium mastery: select mixed questions
        target_difficulties = [1, 2, 3]
    
    # Select questions with desired difficulties
    selected = []
    for difficulty in target_difficulties[:count]:
        candidates = questions_by_difficulty.get(difficulty, [])
        if not candidates:  # Fall back to any difficulty if necessary
            all_questions = [q for difficulty_group in questions_by_difficulty.values() for q in difficulty_group]
            candidates = all_questions if all_questions else questions
        
        if candidates:
            # Try not to repeat question types
            question_types = [q.type for q in selected]
            unique_type_questions = [q for q in candidates if q.type not in question_types]
            
            if unique_type_questions:
                selected.append(unique_type_questions[0])
            else:
                selected.append(candidates[0])
    
    return selected[:count]

def should_rebatch(performance_data, current_vocab, vocab_list, threshold=0.3):
    """
    Determine if we need to rebatch questions based on current vocabulary completion
    
    Args:
        performance_data: Dictionary mapping vocabulary to lists of correct/incorrect answers
        current_vocab: The vocabulary item the user is currently working on
        vocab_list: Ordered list of vocabulary items in the lesson
        threshold: Threshold for rebatching (difference between expected and actual accuracy)
    
    Returns:
        Boolean indicating if rebatching is needed and the vocabulary that triggered it
    """
    # Don't rebatch if we don't have a current vocabulary
    if not current_vocab:
        return False, None
        
    # Check if we have performance data for the current vocabulary
    if current_vocab not in performance_data:
        return False, None
        
    # Check if we have enough answers for the current vocabulary (typical vocab has 4 questions)
    data = performance_data[current_vocab]
    if len(data.get("answers", [])) < 4:  # Not enough answers yet
        return False, None
        
    # Get the index of the current vocab in the list
    try:
        current_index = vocab_list.index(current_vocab)
    except ValueError:
        return False, None
        
    # If this was the last vocabulary, no need to rebatch
    if current_index >= len(vocab_list) - 1:
        return False, None
        
    # Calculate actual accuracy for the current vocabulary
    actual_accuracy = sum(data["answers"]) / len(data["answers"])
    
    # Get predicted mastery and expected accuracy  
    mastery = get_vocab_mastery(current_vocab)
    state = load_temp_state()
    predictions = state.get("predictions", {})
    vocab_pred = predictions.get(current_vocab.lower(), {})
    guess = float(vocab_pred.get("guess", 0.2))
    slip = float(vocab_pred.get("slip", 0.1))
    expected_accuracy = mastery * (1 - slip) + (1 - mastery) * guess
    
    # Compare actual vs expected
    if abs(actual_accuracy - expected_accuracy) > threshold:
        print(f"[BKT] Performance for '{current_vocab}' differs significantly from prediction")
        print(f"[BKT] Expected: {expected_accuracy:.2f}, Actual: {actual_accuracy:.2f}")
        
        # Return the NEXT vocabulary to rebatch (not the current one)
        next_vocab = vocab_list[current_index + 1]
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
        bkt_thread = threading.Thread(target=update_bkt, args=(user_id, correct_answers, incorrect_answers))
        bkt_thread.start()

def get_user_library():
    try:
        with open("temp_library.json", "r") as f:
            user_library = json.load(f)
            return user_library
    except FileNotFoundError:
        print("Temp library cache not found.")
        return None

# Update at the top of bkt_engine.py
def get_user_temp_file(user_id=None):
    """Get user-specific temp file path"""
    if user_id and str(user_id).lower() != "none":
        return f"temp_bkt_data_{user_id}.json"
    return "temp_bkt_data.json"

# Update load_temp_state function
def load_temp_state(user_id=None):
    TEMP_FILE = get_user_temp_file(user_id)
    if os.path.exists(TEMP_FILE):
        with open(TEMP_FILE, "r") as f:
            return json.load(f)
    return {
        "predictions": {},
        "fitted": False,
        "refit_counter": 0,
        "p_mastery": 0.5,
        "guess": 0.2,
        "slip": 0.1
    }

# Update save_temp_state function
def save_temp_state(state, user_id=None):
    TEMP_FILE = get_user_temp_file(user_id)
    with open(TEMP_FILE, "w") as f:
        json.dump(state, f, indent=4)

def get_all_p_masteries(user_id=None):
    """
    Returns a list of p_mastery values (floats) for each vocabulary/skill
    from the latest BKT predictions.
    """
    state = load_temp_state(user_id)
    predictions = state.get("predictions", {})
    p_masteries = []
    for vocab, pred in predictions.items():
        p = pred.get("p_mastery")
        if p is not None:
            p_masteries.append(float(p))
    return p_masteries

def save_temp_state(state):
    with open(TEMP_FILE, "w") as f:
        json.dump(state, f, indent=4)

def update_bkt(user_id, correct_answers, incorrect_answers):
    global uid
    print(f"[update_bkt] Starting BKT update for user {user_id}...")
    uid = user_id
    
    # Load or create custom BKT predictor
    custom_bkt = load_custom_bkt(user_id)
    if custom_bkt is None:
        print(f"[update_bkt] No custom BKT predictor found. Creating for user {user_id}")
        custom_bkt = create_user_bkt_predictor(user_id)
        if custom_bkt is None:
            print("[update_bkt] Failed to create custom BKT predictor")
            return

    # FIRST CHANGE: Load user's complete answer history from database
    usercol = connect_to_mongoDB()
    user_data = usercol.find_one({"user_id": user_id})
    if not user_data:
        print(f"[update_bkt] User {user_id} not found in database")
        return
        
    # Get user's complete history from database
    all_correct_answers = user_data.get("questions_correct", {})
    all_incorrect_answers = user_data.get("questions_incorrect", {})
    
    # Merge with new answers (if any)
    if correct_answers:
        all_correct_answers.update(correct_answers)
    if incorrect_answers:
        all_incorrect_answers.update(incorrect_answers)

    print("[update_bkt] Getting user library...")
    library = get_user_library()
    if library is None:
        print("[update_bkt] No user library found.")
        return

    # Group answers by vocabulary using COMPLETE history
    grouped = {vocab: {'corrects': [], 'incorrects': []} for vocab in library}

    print("[update_bkt] Grouping correct answers from complete history...")
    for entry in all_correct_answers.values():
        vocab = entry.get('vocabulary')
        if vocab in grouped:
            grouped[vocab]['corrects'].append(entry.copy())
        else:
            print(f"[update_bkt] Skipping unrecognized vocab in correct answers: {vocab}")

    print("[update_bkt] Grouping incorrect answers from complete history...")
    for entry in all_incorrect_answers.values():
        vocab = entry.get('vocabulary')
        if vocab in grouped:
            grouped[vocab]['incorrects'].append(entry.copy())
        else:
            print(f"[update_bkt] Skipping unrecognized vocab in incorrect answers: {vocab}")
    
    # Load existing state (for backward compatibility)
    state = load_temp_state(user_id)
    predictions = state.get("predictions", {})
    
    # Update predictions using custom BKT
    for vocab in library:
        history = grouped.get(vocab, {'corrects': [], 'incorrects': []})
        total_attempts = len(history['corrects']) + len(history['incorrects'])
        
        if total_attempts == 0:
            print(f"[update_bkt] Skipping vocab '{vocab}' — no attempts recorded.")
            continue
        
        # Convert to sequence of correct/incorrect
        sequence = []
        all_attempts = []

        # Combine corrects and incorrects with timestamps
        for entry in history['corrects']:
            all_attempts.append((entry.get('timestamp', 0), 1))  # 1 for correct
        for entry in history['incorrects']:
            all_attempts.append((entry.get('timestamp', 0), 0))  # 0 for incorrect

        # Sort by timestamp
        all_attempts.sort(key=lambda x: x[0])

        # Extract just the correctness values in chronological order
        sequence = [attempt[1] for attempt in all_attempts]
        
        # Get parameters for this vocabulary
        params = custom_bkt.vocab_parameters.get(vocab.lower(), {})
        if not params:
            print(f"[update_bkt] No parameters found for '{vocab}'. Using defaults.")
            params = {
                'learn': 0.15,
                'guess': 0.25,
                'slip': 0.1,
                'prior': 0.5
            }
            custom_bkt.vocab_parameters[vocab.lower()] = params
        
        # Calculate mastery with custom BKT
        mastery = custom_bkt.predict(vocab.lower(), sequence)
        
        # Update predictions dictionary (for backward compatibility)
        predictions[vocab.lower()] = {
            'p_mastery': float(mastery),
            'guess': float(params.get('guess', 0.25)),
            'slip': float(params.get('slip', 0.1)),
            'confidence': 1.0 - float(params.get('guess', 0.25)) - float(params.get('slip', 0.1)),
            'correct': 1 if sequence and sequence[-1] == 1 else 0
        }
    
    # Save updated custom BKT
    save_custom_bkt(custom_bkt, user_id)
    
    # Save updated state (for backward compatibility)
    state['predictions'] = predictions
    state['fitted'] = True
    save_temp_state(state)
    
    print("\nDisplaying BKT predictions after update:")
    display_bkt_predictions(user_id)

    save_predictions_file()

    # Add this to bkt_engine.py
def display_bkt_predictions(user_id, filter_vocab=None):
    """
    Formats and prints BKT predictions in a readable table format
    
    Args:
        user_id: User ID to check predictions for
        filter_vocab: Optional vocab name to filter for a specific word
    """
    state = load_temp_state()
    predictions = state.get("predictions", {})
    
    if not predictions:
        print("\n┌───────────────────────────────────────┐")
        print("│           BKT MODEL PREDICTIONS        │")
        print("├───────────────────────────────────────┤")
        print("│ No predictions available               │")
        print("└───────────────────────────────────────┘")
        return
    
    # Filter if needed
    if filter_vocab:
        filtered_preds = {k: v for k, v in predictions.items() if k == filter_vocab}
        if not filtered_preds:
            print(f"No BKT prediction found for '{filter_vocab}'")
            return
        predictions = filtered_preds
    
    # Print header
    print("\n┌─────────────────────────────────────────────────────────────────────────────────┐")
    print("│                                 BKT MODEL PREDICTIONS                            │")
    print("├──────────────────────┬─────────────┬──────────┬──────────┬──────────┬───────────┤")
    print("│ Vocabulary           │ Mastery     │ Guess    │ Slip     │ Conf     │ Last      │")
    print("├──────────────────────┼─────────────┼──────────┼──────────┼──────────┼───────────┤")
    
    # Sort by mastery descending
    sorted_items = sorted(predictions.items(), 
                         key=lambda x: float(x[1].get('p_mastery', 0)), 
                         reverse=True)
    
    # Print each vocabulary item
    for vocab, pred in sorted_items:
        p_mastery = float(pred.get('p_mastery', 0))
        guess = float(pred.get('guess', 0))
        slip = float(pred.get('slip', 0))
        conf = float(pred.get('confidence', 0))
        correct = pred.get('correct', "-")
        
        # Format vocab name (truncate if too long)
        vocab_display = vocab[:18] + '..' if len(vocab) > 20 else vocab.ljust(20)
        
        # Format values with color indicators using ASCII
        mastery_str = f"{p_mastery:.2f}" + ('*' if p_mastery > 0.85 else ' ')
        
        # Print the row
        print(f"│ {vocab_display:<20} │ {mastery_str:^11} │ {guess:^8.2f} │ {slip:^8.2f} │ {conf:^8.2f} │ {correct:^9} │")
    
    print("└──────────────────────┴─────────────┴──────────┴──────────┴──────────┴───────────┘")
    print("* Mastery levels above 0.85 are considered 'mastered'")

#########################################################################################

    """if not fitted or refit_counter >= refit_threshold:
        if len(df) < 5:
            print("[update_bkt] Not enough data to fit BKT model. Skipping fit.")
        else:
            print("[update_bkt] Fitting BKT model...")
            try:
                start = time.time()
                bkt_model.fit(data=df)
                end = time.time()
                print(f"[update_bkt] Model fitted in {end - start:.2f} seconds.")
                fitted = True
                refit_counter = 0
            except Exception as e:
                print(f"[update_bkt] ERROR during fit: {e}")
    else:
        print("[update_bkt] Using existing fitted model.")

    if fitted:
        print("[update_bkt] Running predictions...")
        try:
            prediction_df = bkt_model.predict(data=df)
            prediction_df['confidence'] = 1 - prediction_df['guess'] - prediction_df['slip']

            for vocab in prediction_df['skill_name'].unique():
                last_row = prediction_df[prediction_df['skill_name'] == vocab].iloc[-1]
                previous_predictions[vocab] = {
                    'user_id': last_row['user_id'],
                    'vocabulary': last_row['skill_name'],
                    'correct': last_row['correct'],
                    'p_mastery': last_row['state_predictions'],
                    'guess': last_row['guess'],
                    'slip': last_row['slip'],
                    'confidence': last_row['confidence'],
                }

            updated_state = {
                "predictions": previous_predictions,
                "fitted": fitted,
                "refit_counter": refit_counter,
                "p_mastery": base_prior,
                "guess": base_guess,
                "slip": base_slip
            }

            print("[update_bkt] Saving updated state to temp file...")
            save_temp_state(updated_state)
            print("[update_bkt] BKT update complete and saved.")
            
        except Exception as e:
            print(f"[update_bkt] ERROR during prediction: {e}")
    else:
        print("[update_bkt] Skipping prediction since model is not fitted.")"""

