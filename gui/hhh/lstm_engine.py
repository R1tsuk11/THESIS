import os
import json
import numpy as np
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.preprocessing.sequence import pad_sequences

MODEL_PATH = "lstm_proficiency_model.h5"
MIN_SEQUENCE_LENGTH = 10

def average_proficiency(p_masteries):
    if not p_masteries:
        return 0.0
    return sum(p_masteries) / len(p_masteries)

def track_proficiency_history(user_id, p_masteries, proficiency):
    history_file = f"user_{user_id}_proficiency_history.json"
    entry = {"p_masteries": p_masteries, "proficiency": proficiency}
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)
    else:
        history = []
    history.append(entry)
    with open(history_file, "w") as f:
        json.dump(history, f)

def should_use_lstm(user_id):
    history_file = f"user_{user_id}_proficiency_history.json"
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

def force_train_if_needed(user_id):
    if not os.path.exists(MODEL_PATH):
        print("[LSTM] Model file not found! Forcing training from history.")
        history_file = f"user_{user_id}_proficiency_history.json"
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                history = json.load(f)
            if len(history) >= MIN_SEQUENCE_LENGTH:
                sequences = [entry["p_masteries"] for entry in history]
                labels = [entry["proficiency"] for entry in history]
                train_lstm_model(sequences, labels)
            else:
                print("[LSTM] Not enough history to train LSTM.")
        else:
            print("[LSTM] No history file found for user.")

def predict_proficiency(bkt_sequence, user_id):
    print(f"[LSTM] Predicting proficiency for sequence: {bkt_sequence}")
    force_train_if_needed(user_id)
    if not os.path.exists(MODEL_PATH):
        print("[LSTM] Model still not found after force training. Returning average.")
        return average_proficiency(bkt_sequence)
    model = load_model(MODEL_PATH)
    X = pad_sequences([bkt_sequence], maxlen=model.input_shape[1], dtype='float32')
    X = np.expand_dims(X, -1)
    pred = model.predict(X)
    print(f"[LSTM] Prediction result: {pred}")
    return float(pred[0][0])

def overall_proficiency(bkt_sequence, completion_percentage, user_id):
    print(f"[LSTM] Calculating overall proficiency. Sequence length: {len(bkt_sequence)}, Completion: {completion_percentage}")
    if len(bkt_sequence) < MIN_SEQUENCE_LENGTH:
        print("[LSTM] Not enough data to predict proficiency. Using average.")
        return average_proficiency(bkt_sequence) * completion_percentage
    proficiency = predict_proficiency(bkt_sequence, user_id)
    adjusted_proficiency = proficiency * completion_percentage
    print(f"[LSTM] Raw proficiency: {proficiency}, Adjusted: {adjusted_proficiency}")
    return adjusted_proficiency