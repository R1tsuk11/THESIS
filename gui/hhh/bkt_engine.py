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

