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

from mainmenu import connect_to_mongoDB

executor = ThreadPoolExecutor(max_workers=2)
TEMP_FILE = "temp_bkt_data.json"
PREDICTION_FILE = "bkt_predictions.json"
bkt_model = Model()
bkt_data = []
bkt_thread = None
bkt_thread_lock = threading.Lock()

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
            
            # Fix the pickle issue by loading the parameters and creating a new object
            with open(model_path, "rb") as f:
                try:
                    # Try normal loading first
                    return pickle.load(f)
                except AttributeError:
                    # If that fails, load raw data and recreate object
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
            print(f"[BKT] No custom predictor found for user {user_id}, checking default")
            # Try to load the default model
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

def select_adaptive_questions(questions_pool, user_performance=None):
    """
    Select questions adaptively while preserving lesson structure.
    Each vocabulary gets 1 lesson + 3 practice questions.
    Pronunciation questions are always included.
    """
    if not questions_pool:
        return []
        
    # Group questions by vocabulary
    vocab_questions = {}
    for q in questions_pool:
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
    
    for vocab, q_sets in vocab_questions.items():
        # Get mastery for this vocabulary
        mastery = 0.4  # Default medium mastery
        if user_performance and vocab in user_performance:
            actual_performance = user_performance[vocab]
            # Use predicted mastery or calculate from answers if available
            if "predicted_mastery" in actual_performance:
                mastery = actual_performance["predicted_mastery"]
            elif actual_performance["answers"]:
                mastery = sum(actual_performance["answers"]) / len(actual_performance["answers"])
        
        print(f"[BKT] Vocab '{vocab}' has mastery {mastery:.2f}")
        
        # 1. Always add the lesson question
        if q_sets["lesson"]:
            selected_questions.append(q_sets["lesson"][0])
            print(f"[BKT] Added lesson question for '{vocab}'")
        
        # 2. Always add pronunciation question if available
        if q_sets["pronunciation"]:
            selected_questions.append(q_sets["pronunciation"][0])
            print(f"[BKT] Added pronunciation question for '{vocab}'")
        
        # 3. Select practice questions based on difficulty and mastery
        remaining_slots = 3 - (1 if q_sets["pronunciation"] else 0)  # After lesson & pronunciation
        practice_questions = select_by_difficulty(q_sets["practice"], mastery, remaining_slots)
        selected_questions.extend(practice_questions)
        
        for q in practice_questions:
            print(f"[BKT] Added {q.type} question for '{vocab}' (difficulty: {getattr(q, 'difficulty', 'N/A')})")
    
    print(f"[BKT] Selected {len(selected_questions)} questions adaptively while preserving structure")
    return selected_questions

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

def should_rebatch(performance_data, threshold=0.3):
    """
    Determine if we need to rebatch questions based on performance changes
    
    Args:
        performance_data: Dictionary mapping vocabulary to lists of correct/incorrect answers
        threshold: Threshold for rebatching (difference between expected and actual accuracy)
    
    Returns:
        Boolean indicating if rebatching is needed and the vocabulary that triggered it
    """
    state = load_temp_state()
    predictions = state.get("predictions", {})
    
    for vocab, data in performance_data.items():
        if not data["answers"]:
            continue  # Skip if no answers for this vocabulary
            
        # Calculate actual accuracy
        actual_accuracy = sum(data["answers"]) / len(data["answers"])
        
        # Get predicted mastery and expected accuracy
        mastery = get_vocab_mastery(vocab)
        # Expected accuracy from BKT (using mastery, guess and slip)
        vocab_pred = predictions.get(vocab.lower(), {})
        guess = float(vocab_pred.get("guess", 0.2))
        slip = float(vocab_pred.get("slip", 0.1))
        expected_accuracy = mastery * (1 - slip) + (1 - mastery) * guess
        
        # Compare actual vs expected
        if abs(actual_accuracy - expected_accuracy) > threshold:
            print(f"[BKT] Performance for '{vocab}' differs significantly from prediction")
            print(f"[BKT] Expected: {expected_accuracy:.2f}, Actual: {actual_accuracy:.2f}")
            return True, vocab
            
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
    print(f"[update_bkt] Starting BKT update for user {user_id}...")
    
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

