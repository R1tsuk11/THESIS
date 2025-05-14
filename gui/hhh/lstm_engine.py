import os
import json
import numpy as np
import sys
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.preprocessing.sequence import pad_sequences

MODEL_PATH = "lstm_proficiency_model.h5"
MIN_SEQUENCE_LENGTH = 3
history_file = "temp_prof_history.json"

def average_proficiency(p_masteries):
    if not p_masteries:
        return 0.0
    return sum(p_masteries) / len(p_masteries)

def track_proficiency_history(p_masteries, proficiency):
    """Store only the proficiency values in history"""
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)
    else:
        history = []
    
    if isinstance(history, list) and all(isinstance(x, (int, float)) for x in history):
        # History is already in new format
        history.append(proficiency)
    else:
        # Convert old format to new format
        history = [entry["proficiency"] if isinstance(entry, dict) else entry 
                  for entry in history]
        history.append(proficiency)
    
    print(f"[LSTM] Adding proficiency to history: {proficiency}")
    print(f"[LSTM] History now has {len(history)} entries")
    
    with open(history_file, "w") as f:
        json.dump(history, f)

def should_use_lstm():
    if not os.path.exists(history_file):
        return False
    with open(history_file, "r") as f:
        history = json.load(f)
    return len(history) >= MIN_SEQUENCE_LENGTH

def build_lstm_model(input_shape):
    model = Sequential()
    model.add(LSTM(64, input_shape=input_shape, return_sequences=False))
    model.add(Dense(1, activation='sigmoid'))  # Output: proficiency (0-1)
    model.compile(optimizer='adam', loss='mse')
    return model

def train_lstm_model(sequences, labels, epochs=10):
    maxlen = max(len(seq) for seq in sequences)
    X = pad_sequences(sequences, maxlen=maxlen, dtype='float32')
    y = np.array(labels)
    model = build_lstm_model((X.shape[1], 1))
    X = np.expand_dims(X, -1)
    model.fit(X, y, epochs=epochs)
    model.save(MODEL_PATH)
    return model

def force_train_if_needed():
    if not os.path.exists(MODEL_PATH):
        print("[LSTM] Model file not found! Forcing training from history.")
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                history = json.load(f)
            if len(history) >= MIN_SEQUENCE_LENGTH:
                # Use the proficiency values directly as labels
                labels = history
                # Generate sequences from consecutive proficiencies
                sequences = [history[i:i+MIN_SEQUENCE_LENGTH] 
                           for i in range(len(history)-MIN_SEQUENCE_LENGTH)]
                train_lstm_model(sequences, labels[-len(sequences):])
            else:
                print("[LSTM] Not enough history to train LSTM.")
        else:
            print("[LSTM] No history file found for user.")

def predict_proficiency(bkt_sequence):
    print(f"[LSTM] Predicting proficiency for sequence: {bkt_sequence}")
    if should_use_lstm():
        force_train_if_needed()
    if not os.path.exists(MODEL_PATH):
        print("[LSTM] Model still not found after force training. Returning average.")
        return average_proficiency(bkt_sequence)
    model = load_model(MODEL_PATH)
    X = pad_sequences([bkt_sequence], maxlen=model.input_shape[1], dtype='float32')
    X = np.expand_dims(X, -1)
    pred = model.predict(X)
    print(f"[LSTM] Prediction result: {pred}")
    return float(pred[0][0])

def overall_proficiency(bkt_sequence, completion_percentage, proficiency_history=None):
    print(f"[LSTM] DEBUG: Starting overall_proficiency", file=sys.stderr)
    print(f"[LSTM] DEBUG: MIN_SEQUENCE_LENGTH={MIN_SEQUENCE_LENGTH}", file=sys.stderr)
    print(f"[LSTM] Sequence length: {len(bkt_sequence)}", file=sys.stderr)
    
    if proficiency_history is None:
        print("[LSTM] proficiency_history is None, initializing to empty list.")
        proficiency_history = []
    
    # Check sequence length and use fallback
    if len(bkt_sequence) < MIN_SEQUENCE_LENGTH:
        print("[LSTM] Not enough data to predict proficiency. Using average.", file=sys.stderr)
        avg = average_proficiency(bkt_sequence)
        result = avg * completion_percentage
        track_proficiency_history(bkt_sequence, result)  # Track even fallback results
        print(json.dumps({"proficiency": result}))
        return result, proficiency_history
    
    print("[LSTM] Using LSTM model for prediction.")
    if history_file and os.path.exists(history_file):
        proficiency = predict_proficiency(bkt_sequence)
    adjusted_proficiency = proficiency * completion_percentage
    track_proficiency_history(bkt_sequence, adjusted_proficiency)
    print(json.dumps({"proficiency": adjusted_proficiency}))

    return adjusted_proficiency, proficiency_history