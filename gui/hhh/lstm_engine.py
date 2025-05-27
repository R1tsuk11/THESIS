import os
import json
import numpy as np
import sys
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.preprocessing.sequence import pad_sequences

MODEL_PATH = "lstm_proficiency_model.keras"
MIN_SEQUENCE_LENGTH = 3
LSTM_REFIT_THRESHOLD = 5
COUNTER_FILE = "lstm_counter.json"
history_file = "temp_prof_history.json"

def average_proficiency(p_masteries):
    if not p_masteries:
        return 0.0
    return sum(p_masteries) / len(p_masteries)

def track_proficiency_history(proficiency):
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
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
    return model

def train_lstm_model(sequences, labels, epochs=10):
    maxlen = max(len(seq) for seq in sequences)
    X = pad_sequences(sequences, maxlen=maxlen, dtype='float32')
    y = np.array(labels)
    model = build_lstm_model((X.shape[1], 1))
    X = np.expand_dims(X, -1)
    history = model.fit(X, y, epochs=epochs, verbose=0)
    model.save(MODEL_PATH)
    print(f"[LSTM] Model saved to {MODEL_PATH}")
    print(f"[LSTM] Training loss history: {history.history['loss']}")
    print(f"[LSTM] Training MAE history: {history.history['mae']}")
    # Evaluate on training data
    loss, mae = model.evaluate(X, y, verbose=0)
    print(f"[LSTM] Final training loss (MSE): {loss}, MAE: {mae}")
    return model

def force_train_if_needed():
    retrain = False
    if not os.path.exists(MODEL_PATH):
        retrain = True
        print("[LSTM] Model file not found! Forcing training from history.")
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)
        last_count = 0
        if os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, "r") as f:
                last_count = int(f.read().strip())
        if len(history) - last_count >= LSTM_REFIT_THRESHOLD or retrain:
            if len(history) >= MIN_SEQUENCE_LENGTH:
                labels = history
                sequences = [history[i:i+MIN_SEQUENCE_LENGTH] 
                             for i in range(len(history)-MIN_SEQUENCE_LENGTH+1)]
                if sequences:
                    print(f"[LSTM] Training model on {len(sequences)} sequences.")
                    train_lstm_model(sequences, labels[-len(sequences):])
                else:
                    print("[LSTM] Not enough data to generate sequences for training.")
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
    
    with open(history_file, "r") as f:
            history = json.load(f)
    with open(COUNTER_FILE, "w") as f:
        f.write(str(len(history)))
        
    model = load_model(MODEL_PATH)
    X = pad_sequences([bkt_sequence], maxlen=model.input_shape[1], dtype='float32')
    X = np.expand_dims(X, -1)
    pred = model.predict(X)
    print(f"[LSTM] Prediction result: {pred}")
    return float(pred[0][0])

# At the end of overall_proficiency function
def overall_proficiency(bkt_sequence, completion_percentage, proficiency_history, user_id=None):
    # Your existing code
    
    try:
        if len(bkt_sequence) < MIN_SEQUENCE_LENGTH:
            print("[LSTM] Not enough data to predict proficiency. Using average.")
            avg = average_proficiency(bkt_sequence)
            result = avg * completion_percentage
            print(f"Result: {result}")
            track_proficiency_history(result)
            
            # Display the LSTM proficiency
            print("\n=== LSTM PROFICIENCY ===")
            display_lstm_proficiency(user_id)
            print("=======================\n")
            
            return result
        
        print("[LSTM] Using LSTM model for prediction.")
        proficiency = predict_proficiency(bkt_sequence)
        adjusted_proficiency = proficiency * completion_percentage
        track_proficiency_history(adjusted_proficiency)
        
        # Display the LSTM proficiency
        print("\n=== LSTM PROFICIENCY ===")
        display_lstm_proficiency(user_id)
        print("=======================\n")
        
        return adjusted_proficiency
        
    except Exception as e:
        print(f"[LSTM] Error in overall_proficiency: {str(e)}", file=sys.stderr)
        return {"error": str(e),  "method": "sys"}
    
# Add this to lstm_engine.py
def display_lstm_proficiency(user_id=None):
    """
    Formats and prints LSTM proficiency prediction in a readable format
    
    Args:
        user_id: Optional user ID to include in the display
    """
    # Get history data
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)
    else:
        history = []
    
    # Get prediction if we have enough data
    if len(history) >= MIN_SEQUENCE_LENGTH:
        # Get the last sequence for prediction
        sequence = history[-MIN_SEQUENCE_LENGTH:]
        prediction = predict_proficiency(sequence)
        model_status = "Active"
    else:
        sequence = history if history else []
        prediction = average_proficiency(sequence) if sequence else 0.0
        model_status = f"Inactive (Need {MIN_SEQUENCE_LENGTH-len(history)} more data points)"
    
    # Print header
    print("\n┌───────────────────────────────────────────────────────────────────┐")
    print("│                          LSTM PROFICIENCY                          │")
    print("├───────────────────────────────────────────────────────────────────┤")
    
    # User info
    if user_id:
        print(f"│ User ID:                 {user_id:<41} │")
    
    # Model status
    print(f"│ Model Status:            {model_status:<41} │")
    print(f"│ History Data Points:     {len(history):<41} │")
    
    # Current prediction
    proficiency_percent = prediction * 100
    print(f"│ Current Proficiency:     {proficiency_percent:.1f}% {get_proficiency_level(prediction):<33} │")
    
    # Learning curve
    if len(history) >= 2:
        trend = history[-1] - history[-2]
        trend_display = f"{trend*100:+.1f}% " + ("↑" if trend > 0 else "↓" if trend < 0 else "→")
        print(f"│ Recent Trend:           {trend_display:<41} │")
    
    print("├───────────────────────────────────────────────────────────────────┤")
    
    # Show recent history points
    print("│ Recent Proficiency History:                                       │")
    recent = history[-5:] if len(history) > 5 else history
    for i, h in enumerate(recent):
        idx = len(history) - len(recent) + i
        print(f"│   Point {idx+1:<2}: {h*100:>6.1f}%                                            │")
    
    print("└───────────────────────────────────────────────────────────────────┘")

def get_proficiency_level(proficiency):
    """Returns a text description of proficiency level"""
    if proficiency < 0.2:
        return "(Beginner)"
    elif proficiency < 0.4:
        return "(Elementary)"
    elif proficiency < 0.6:
        return "(Intermediate)"
    elif proficiency < 0.8:
        return "(Advanced)"
    else:
        return "(Proficient)"