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

executor = ThreadPoolExecutor(max_workers=2)
TEMP_FILE = "temp_bkt_data.json"
bkt_model = Model()
bkt_data = []
bkt_thread = None
bkt_thread_lock = threading.Lock()

# Add to bkt_engine.py
def get_vocab_mastery(vocab, default_for_new=0.4, user_performance=None):
    """Get current mastery level with better handling for new vocabulary items
    
    Args:
        vocab: The vocabulary word to get mastery for
        default_for_new: Default mastery for new words (0.4 is slightly lower than neutral 0.5)
        user_performance: Optional dict of user performance data to adapt default for new words
    """
    state = load_temp_state()
    predictions = state.get("predictions", {})
    
    # If the vocab exists in predictions, return its mastery
    if vocab.lower() in predictions:
        return float(predictions[vocab.lower()].get("p_mastery", 0.5))
    
    # For new vocabulary words, adjust default based on recent performance
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

def select_adaptive_questions(all_questions, batch_size=10, min_questions_per_vocab=2, user_performance=None):
    """Select questions adaptively based on current BKT mastery levels and user performance"""
    print("[BKT] Selecting adaptive question batch...")
    
    # Group questions by vocabulary
    vocab_groups = {}
    for q in all_questions:
        vocab = getattr(q, "vocabulary", "").lower()
        if vocab and vocab not in vocab_groups:
            vocab_groups[vocab] = []
        if vocab:
            vocab_groups[vocab].append(q)
    
    # Get current mastery levels for each vocabulary, passing user performance data
    vocab_masteries = {vocab: get_vocab_mastery(vocab, user_performance=user_performance) 
                      for vocab in vocab_groups.keys()}
    
    # Sort vocabularies by mastery level (focus on lower mastery first)
    sorted_vocabs = sorted(vocab_masteries.items(), key=lambda x: x[1])
    
    # Create adaptive batch
    batch = []
    for vocab, mastery in sorted_vocabs:
        if len(batch) >= batch_size:
            break
            
        # Choose appropriate difficulty based on mastery
        if mastery < 0.3:
            difficulty_range = (1, 2)  # Easy to medium
            print(f"[BKT] Vocab '{vocab}' has low mastery ({mastery:.2f}): selecting easy-medium questions")
        elif mastery < 0.7:
            difficulty_range = (2, 3)  # Medium to hard
            print(f"[BKT] Vocab '{vocab}' has medium mastery ({mastery:.2f}): selecting medium-hard questions")
        else:
            difficulty_range = (3, 4)  # Hard
            print(f"[BKT] Vocab '{vocab}' has high mastery ({mastery:.2f}): selecting hard questions")
        # First select lesson questions (always include)
        lesson_qs = [q for q in vocab_groups[vocab] 
                   if getattr(q, "type", "") == "Lesson" and not getattr(q, "used", False)]
        
        if lesson_qs:
            lesson_qs[0].predicted_mastery = mastery  # Store the mastery prediction
            batch.append(lesson_qs[0])
            lesson_qs[0].used = True
            print(f"[BKT] Added lesson question for '{vocab}'")
        
        # Then select practice questions with appropriate difficulty
        # Fix: Safely handle None values in difficulty comparison
        matching_qs = []
        for q in vocab_groups[vocab]:
            q_difficulty = getattr(q, "difficulty", 2)  # Default to 2 if not specified
            # Convert to numeric type if it's not None, otherwise use default
            if q_difficulty is None:
                q_difficulty = 2  # Default difficulty
            
            # Make sure it's a number
            try:
                q_difficulty = float(q_difficulty)
            except (ValueError, TypeError):
                q_difficulty = 2  # Default if conversion fails
                
            # Now do the comparison safely
            if (difficulty_range[0] <= q_difficulty <= difficulty_range[1] and 
                not getattr(q, "used", False) and
                getattr(q, "type", "") != "Lesson"):
                matching_qs.append(q)
        
        # Sort by difficulty
        matching_qs.sort(key=lambda q: getattr(q, "difficulty", 2) or 2)  # Safe sorting
        
        # Add questions up to the minimum per vocabulary
        questions_to_add = min(min_questions_per_vocab, len(matching_qs))
        for i in range(questions_to_add):
            if len(batch) >= batch_size:
                break
            if i < len(matching_qs):
                matching_qs[i].predicted_mastery = mastery  # Store the mastery prediction
                batch.append(matching_qs[i])
                matching_qs[i].used = True
                print(f"[BKT] Added {getattr(matching_qs[i], 'type', 'unknown')} question for '{vocab}' (difficulty: {getattr(matching_qs[i], 'difficulty', '?')})")
    
    # Fill remaining slots with diverse questions if needed
    if len(batch) < batch_size:
        remaining = [q for q in all_questions if not getattr(q, "used", False)]
        # Safe sorting with default value
        remaining.sort(key=lambda q: getattr(q, "difficulty", 2) or 2)
        
        for q in remaining:
            if len(batch) >= batch_size:
                break
            vocab = getattr(q, "vocabulary", "").lower()
            mastery = vocab_masteries.get(vocab, 0.5)
            q.predicted_mastery = mastery
            batch.append(q)
            q.used = True
            print(f"[BKT] Added extra question for '{vocab}' to fill batch")
    
    # Tag this as a BKT-generated batch
    for q in batch:
        q.batch_id = time.time()
        
    print(f"[BKT] Selected {len(batch)} questions adaptively")
    return batch[:batch_size]

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

def load_temp_state():
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

def get_all_p_masteries():
    """
    Returns a list of p_mastery values (floats) for each vocabulary/skill
    from the latest BKT predictions.
    """
    state = load_temp_state()
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

    global bkt_model, bkt_data
    MAX_HISTORY = 10
    bkt_data = []  # clear previous data
    filtered_data = []

    # Load existing session state
    print("[update_bkt] Loading temp state...")
    state = load_temp_state()

    fitted = state.get('fitted', False)
    refit_counter = state.get('refit_counter', 0)
    base_prior = state.get('p_mastery', 0.5)
    base_guess = state.get('guess', 0.2)
    base_slip = state.get('slip', 0.1)

    print("[update_bkt] Getting user library...")
    library = get_user_library()
    if library is None:
        print("[update_bkt] No user library found.")
        return

    print(f"[update_bkt] Library loaded: {library}")
    grouped = {vocab: {'corrects': [], 'incorrects': []} for vocab in library}

    print("[update_bkt] Grouping correct answers...")
    for entry in correct_answers.values():
        vocab = entry.get('vocabulary')
        if vocab in grouped:
            grouped[vocab]['corrects'].append(entry.copy())
        else:
            print(f"[update_bkt] Skipping unrecognized vocab in correct answers: {vocab}")

    print("[update_bkt] Grouping incorrect answers...")
    for entry in incorrect_answers.values():
        vocab = entry.get('vocabulary')
        if vocab in grouped:
            grouped[vocab]['incorrects'].append(entry.copy())
        else:
            print(f"[update_bkt] Skipping unrecognized vocab in correct answers: {vocab}")

    print("[update_bkt] Preparing BKT data...")
    for vocab_entry in library:
        vocab = vocab_entry
        history = grouped.get(vocab, {'corrects': [], 'incorrects': []})
        print(f"[update_bkt] Processing vocab: {vocab}")

        total_attempts = len(history['corrects']) + len(history['incorrects'])
        if total_attempts == 0:
            print(f"[update_bkt] Skipping vocab '{vocab}' — no attempts recorded.")
            continue

        for correctness, entries in [('correct', history['corrects']), ('incorrect', history['incorrects'])]:
            print(f"[update_bkt]   Handling {correctness} entries: {len(entries)}")
            for entry in entries:
                print(f"[update_bkt]     Entry: {entry}")
                rt = entry.get('response_time', 0)
                df = entry.get('difficulty', 1)

                adjusted_guess = min(0.4, max(0.1, base_guess + 0.1 * df))
                adjusted_slip = min(0.3, max(0.05,
                    base_slip +
                    (0.05 if rt > 5.0 else 0)
                ))

                bkt_data.append({
                    "user_id": user_id,
                    "skill_name": vocab,
                    "correct": 1 if correctness == 'correct' else 0,
                    "guess": adjusted_guess,
                    "slip": adjusted_slip,
                    "prior": base_prior
                })

    if not bkt_data:
        print("[update_bkt] No BKT data to process.")
        return

    print(f"[update_bkt] Fitting BKT model. Refit count: {refit_counter}")
    df = pd.DataFrame(bkt_data)
    refit_threshold = 5
    refit_counter += 1

    print(f"[update_bkt] DataFrame shape: {df.shape}")
    print(df.head())
    print(df['skill_name'].value_counts())

    print("[DEBUG] Input to model.fit():")
    print(df.to_string(index=False))
    print("[DEBUG] Unique skills:", df['skill_name'].unique())
    print("[DEBUG] Data types:\n", df.dtypes)

    for skill in df['skill_name'].unique():
        skill_data = df[df['skill_name'] == skill]
        filtered_data.append(skill_data.tail(MAX_HISTORY))

    df = pd.concat(filtered_data)

    df.to_csv("bkt_input.csv", index=False)
    print("[update_bkt] BKT input data saved to 'bkt_input.csv'.")

    fit_flag = "fit" if (not fitted or refit_counter >= refit_threshold) else "predict"
            
    try:
        print("[update_bkt] Launching external BKT model runner...")
        result = subprocess.run(["python", "bkt_engine_runner.py", fit_flag], capture_output=True, text=True)
        print("[update_bkt] Model runner output:\n", result.stdout)
        if result.stderr:
            print("[update_bkt] Model runner errors:\n", result.stderr)
        # After fitting, reset refit_counter and set fitted=True
        if fit_flag == "fit":
            fitted = True
            refit_counter = 0
    except Exception as e:
        print(f"[update_bkt] Failed to run external model: {e}")
    except subprocess.TimeoutExpired:
        print("[update_bkt] ERROR: Model runner timed out.")
    except Exception as e:
        print(f"[update_bkt] ERROR: Failed to run BKT model runner: {e}")

    PREDICTION_FILE = "bkt_predictions.json"

    if os.path.exists(PREDICTION_FILE):
        with open(PREDICTION_FILE, "r") as f:
            new_predictions = json.load(f)
            print("[update_bkt] Predictions loaded from external model.")
            state['predictions'].update(new_predictions)
    else:
        print("[update_bkt] Prediction file not found after model run.")

    # Always save the updated state
    state['fitted'] = fitted
    state['refit_counter'] = refit_counter
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

