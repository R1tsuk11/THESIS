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

def average_proficiency(p_masteries):
    if not p_masteries:
        return 0.0
    return sum(p_masteries) / len(p_masteries)

def track_proficiency_history(proficiency, user_id=None):
    """Store proficiency values in user-specific history"""
    history_file = get_lstm_history_path(user_id)
    print(f"[LSTM] Writing proficiency {proficiency:.4f} to history file {history_file}")
    
    try:
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                history = json.load(f)
        else:
            history = []
        
        # Handle different history formats
        if isinstance(history, list):
            # Convert dictionary format to simple values if needed
            if history and isinstance(history[0], dict) and 'proficiency' in history[0]:
                print(f"[LSTM] Converting history format from dictionaries to values")
                history = [item['proficiency'] for item in history]
            history.append(proficiency)
        else:
            print(f"[LSTM] Unexpected history format, reinitializing")
            history = [proficiency]
        
        # Create directory if needed
        os.makedirs(os.path.dirname(history_file) or '.', exist_ok=True)
        
        print(f"[LSTM] History now has {len(history)} entries: {history[-5:]}")
        with open(history_file, "w") as f:
            json.dump(history, f)
            
    except Exception as e:
        print(f"[LSTM] Error tracking history: {str(e)}")
        # Still try to save this point even if there was an error
        try:
            with open(history_file, "w") as f:
                json.dump([proficiency], f)
        except Exception:
            pass

def should_use_lstm(user_id=None):
    history_file = get_lstm_history_path(user_id)
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

def train_lstm_model(sequences, labels, model_path=MODEL_PATH, epochs=10):
    maxlen = max(len(seq) for seq in sequences)
    X = pad_sequences(sequences, maxlen=maxlen, dtype='float32')
    y = np.array(labels)
    model = build_lstm_model((X.shape[1], 1))
    X = np.expand_dims(X, -1)
    history = model.fit(X, y, epochs=epochs, verbose=0)
    model.save(model_path)
    print(f"[LSTM] Model saved to {model_path}")
    print(f"[LSTM] Training loss history: {history.history['loss']}")
    print(f"[LSTM] Training MAE history: {history.history['mae']}")
    return model

def force_train_if_needed(user_id=None):
    """Train or retrain the LSTM model if needed"""
    model_path = get_lstm_model_path(user_id)
    history_file = get_lstm_history_path(user_id)
    counter_file = get_lstm_counter_path(user_id)
    
    retrain = False
    
    # If user model doesn't exist but global model does, copy it
    if not os.path.exists(model_path) and user_id and os.path.exists(get_lstm_model_path()):
        print(f"[LSTM] Creating initial model for user {user_id} from global model")
        try:
            import shutil
            shutil.copy(get_lstm_model_path(), model_path)
            print(f"[LSTM] Copied global model to {model_path}")
            # No need to retrain yet, just copied the model
        except Exception as e:
            print(f"[LSTM] Error copying global model: {e}")
            retrain = True  # Force training if copy fails
    elif not os.path.exists(model_path):
        retrain = True
        print(f"[LSTM] Model file not found for user {user_id}! Forcing training from history.")
    
    # Check if we need to retrain based on new data
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)
        
        last_count = 0
        if os.path.exists(counter_file):
            try:
                with open(counter_file, "r") as f:
                    last_count = int(f.read().strip())
            except (ValueError, FileNotFoundError):
                last_count = 0
        
        # Train if we have enough new data points or need to retrain
        if len(history) - last_count >= LSTM_REFIT_THRESHOLD or retrain:
            if len(history) >= MIN_SEQUENCE_LENGTH:
                # Prepare sequences and labels
                labels = history
                sequences = [history[i:i+MIN_SEQUENCE_LENGTH] 
                            for i in range(len(history)-MIN_SEQUENCE_LENGTH+1)]
                
                if sequences:
                    print(f"[LSTM] Training model for user {user_id} on {len(sequences)} sequences")
                    # Use user-specific paths in training
                    train_lstm_model(sequences, labels[-len(sequences):], model_path)
                    # Update counter
                    with open(counter_file, "w") as f:
                        f.write(str(len(history)))
                else:
                    print(f"[LSTM] Not enough data to generate sequences for user {user_id}")
            else:
                print(f"[LSTM] Not enough history to train LSTM for user {user_id}")
    else:
        print(f"[LSTM] No history file found for user {user_id}")

# At the end of overall_proficiency function
def overall_proficiency(bkt_sequence, completion_percentage, user_id=None):
    try:
        if len(bkt_sequence) < MIN_SEQUENCE_LENGTH:
            print("[LSTM] Not enough data to predict proficiency. Using average.")
            avg = average_proficiency(bkt_sequence)
            confidence = 0.5  # Lower confidence for average-based prediction
            result = {
                "prediction": avg * completion_percentage,
                "confidence": confidence
            }
            track_proficiency_history(result["prediction"], user_id)
            
            # Use ASCII version instead
            print("\n=== LSTM PROFICIENCY ===")
            try:
                display_lstm_proficiency_ascii(user_id)
            except Exception as display_err:
                print(f"[LSTM] Display error: {display_err}")
                print(f"[LSTM] Proficiency: {result:.2f}")
            print("=======================\n")
            
            return result
        
        print("[LSTM] Using LSTM model for prediction.")
        result = predict_proficiency(bkt_sequence, user_id)  # Now returns dict with confidence
        
        if isinstance(result, dict):
            prediction = result["prediction"]
            confidence = result["confidence"]
        else:
            # Handle backward compatibility
            prediction = result
            confidence = 0.8
            
        adjusted_prediction = prediction * completion_percentage
        track_proficiency_history(adjusted_prediction, user_id)
        
        # Use ASCII version instead
        print("\n=== LSTM PROFICIENCY ===")
        try:
            display_lstm_proficiency_ascii(user_id)
        except Exception as display_err:
            print(f"[LSTM] Display error: {display_err}")
            print(f"[LSTM] Proficiency: {adjusted_prediction:.2f}")
        print("=======================\n")
        
        return {
            "prediction": adjusted_prediction,
            "confidence": confidence
        }
        
    except Exception as e:
        print(f"[LSTM] Error in overall_proficiency: {str(e)}", file=sys.stderr)
        return {
            "error": str(e),
            "method": "sys",
            "prediction": 0.0,
            "confidence": 0.0
        }
    
def debug_log(message, stderr=True):
    """Helper for consistent debug logging"""
    prefix = "[LSTM DEBUG]"
    full_message = f"{prefix} {message}"
    if stderr:
        print(full_message, file=sys.stderr)
    else:
        print(full_message)

def get_lstm_model_path(user_id=None):
    """Get path for user-specific LSTM model"""
    # Create a models directory to store all models
    if not os.path.exists("lstm_models"):
        os.makedirs("lstm_models", exist_ok=True)
    
    if user_id and str(user_id).lower() != "none":
        return os.path.join("lstm_models", f"lstm_proficiency_model_{user_id}.keras")
    return os.path.join("lstm_models", "lstm_proficiency_model.keras")

def get_lstm_history_path(user_id=None):
    """Get path for user-specific proficiency history"""
    # Create a history directory to store all history files
    if not os.path.exists("lstm_history"):
        os.makedirs("lstm_history", exist_ok=True)
    
    if user_id and str(user_id).lower() != "none":
        return os.path.join("lstm_history", f"temp_prof_history_{user_id}.json")
    return os.path.join("lstm_history", "temp_prof_history.json")

def get_lstm_counter_path(user_id=None):
    """Get path for user-specific LSTM counter"""
    # Create a counters directory to store all counter files
    if not os.path.exists("lstm_counters"):
        os.makedirs("lstm_counters", exist_ok=True)
    
    if user_id and str(user_id).lower() != "none":
        return os.path.join("lstm_counters", f"lstm_counter_{user_id}.json")
    return os.path.join("lstm_counters", "lstm_counter.json")

def calculate_history_confidence(history):
    """Calculate confidence based on historical stability"""
    if not isinstance(history, list) or len(history) < 3:
        return 0.7  # Default value for limited history
        
    # Get recent history points
    recent = history[-5:] if len(history) > 5 else history
    
    # Calculate stability (standard deviation)
    std_dev = np.std(recent)
    stability_confidence = max(0.3, min(0.95, np.exp(-7 * std_dev)))
    
    # Analyze trend consistency (if predictions follow a consistent pattern)
    if len(recent) > 3:
        # Calculate consecutive differences
        diffs = [abs(recent[i] - recent[i-1]) for i in range(1, len(recent))]
        # Standard deviation of differences (lower means more consistent changes)
        diff_std = np.std(diffs) if len(diffs) > 1 else 0
        trend_confidence = max(0.3, min(0.95, np.exp(-10 * diff_std)))
        
        # Combine both aspects of historical analysis
        return 0.6 * stability_confidence + 0.4 * trend_confidence
    
    return stability_confidence

def fallback_confidence(history):
    """Provide fallback confidence when other methods fail"""
    if isinstance(history, list):
        # Base on data amount
        return min(0.8, 0.4 + len(history) * 0.04)
    return 0.5  # Default moderate confidence

def calculate_confidence(model, X, history):
    """Calculate LSTM confidence using input perturbation technique"""
    try:
        # Generate multiple predictions by adding small noise to inputs
        n_iterations = 8
        predictions = []
        
        # Create variations of the input
        for i in range(n_iterations):
            # First prediction uses original input
            if i == 0:
                pred = model.predict(X, verbose=0)[0][0]
            else:
                # Add gaussian noise with increasing magnitude
                noise_level = 0.02 * (i / 3)
                X_noisy = X + np.random.normal(0, noise_level, X.shape)
                pred = model.predict(X_noisy, verbose=0)[0][0]
            predictions.append(pred)
        
        # Calculate variance to measure model uncertainty
        std_dev = np.std(predictions)
        model_confidence = max(0.3, min(0.95, np.exp(-8 * std_dev)))
        
        print(f"[LSTM] Input perturbation variance: {std_dev:.4f}, confidence: {model_confidence:.2f}")
        
        # Historical stability component
        history_confidence = calculate_history_confidence(history)
        
        # Data sufficiency component 
        data_confidence = min(0.9, 0.5 + (len(history) if isinstance(history, list) else 0) * 0.05)
        
        # Combine components with appropriate weights
        final_confidence = (0.4 * model_confidence + 
                           0.4 * history_confidence + 
                           0.2 * data_confidence)
        
        # Ensure reasonable bounds
        final_confidence = max(0.3, min(0.95, final_confidence))
        
        print(f"[LSTM] Final confidence: {final_confidence:.2f}")
        return final_confidence
        
    except Exception as e:
        print(f"[LSTM] Error in confidence calculation: {str(e)}")
        return fallback_confidence(history)
    
    except Exception as e:
        print(f"[LSTM] Error in confidence calculation: {str(e)}")
        # Fall back to simple confidence estimation
        if isinstance(history, list) and len(history) >= 2:
            # Use history stability as confidence
            recent = history[-5:] if len(history) > 5 else history
            stability = np.std(recent)
            confidence = max(0.5, min(0.9, np.exp(-3 * stability)))
            print(f"[LSTM] Fallback confidence from history stability: {confidence:.2f}")
            return confidence
        else:
            # No history, use moderate confidence
            print("[LSTM] Using default moderate confidence: 0.7")
            return 0.7

def ensure_global_history_exists():
    """Ensure the global temp_prof_history.json file exists"""
    # FIXED: Use the proper directory structure
    global_history_path = get_lstm_history_path()  # This will give us lstm_history/temp_prof_history.json
    
    print(f"[LSTM] Checking global history at: {global_history_path}")
    
    if not os.path.exists(global_history_path):
        print("[LSTM] Creating global history file")
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(global_history_path), exist_ok=True)
            
            # Create with some initial data if possible
            initial_history = [0.3, 0.35, 0.4, 0.45, 0.5]  # Basic progression
            with open(global_history_path, "w") as f:
                json.dump(initial_history, f)
            print(f"[LSTM] Created global history file at {global_history_path}")
        except Exception as e:
            print(f"[LSTM] Error creating global history file: {e}")
    else:
        # Verify the file is valid
        try:
            with open(global_history_path, "r") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    raise ValueError("History is not a list")
                print(f"[LSTM] Global history file valid with {len(history)} entries at {global_history_path}")
        except Exception as e:
            print(f"[LSTM] Global history file corrupted, recreating: {e}")
            try:
                initial_history = [0.3, 0.35, 0.4, 0.45, 0.5]
                with open(global_history_path, "w") as f:
                    json.dump(initial_history, f)
                print(f"[LSTM] Recreated global history file at {global_history_path}")
            except Exception as e2:
                print(f"[LSTM] Failed to recreate global history file: {e2}")

def predict_proficiency(bkt_sequence, user_id=None):
    """Predict proficiency using appropriate model for the user"""
    print(f"[LSTM] Predicting proficiency for user {user_id}, sequence: {bkt_sequence}")
    
    try:
        # IMPORTANT: Ensure global history file exists first
        ensure_global_history_exists()
        
        # Determine which model to use
        model_path = get_lstm_model_path(user_id)
        history_file = get_lstm_history_path(user_id)
        counter_file = get_lstm_counter_path(user_id)
        
        # If user doesn't have enough history, check if we should use the global model
        user_has_enough_data = False
        history = []
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                history = json.load(f)
                user_has_enough_data = len(history) >= MIN_SEQUENCE_LENGTH
        
        # If user doesn't have enough data, use global model with blend
        global_contribution = 1.0
        if not user_has_enough_data:
            print(f"[LSTM] User {user_id} has insufficient data, using global model")
            # FIXED: Check if global model exists and has enough data using proper path
            global_history_path = get_lstm_history_path()  # Global path (no user_id)
            if os.path.exists(get_lstm_model_path()) and os.path.exists(global_history_path):
                with open(global_history_path, "r") as f:
                    global_history = json.load(f)
                    if len(global_history) >= MIN_SEQUENCE_LENGTH:
                        # Use global model for prediction
                        model_path = get_lstm_model_path()
                        print(f"[LSTM] Using global model for prediction")
                    else:
                        # Not enough global data either
                        print(f"[LSTM] Not enough global data, using average")
                        avg = average_proficiency(bkt_sequence)
                        return {"prediction": avg, "confidence": 0.5}
            else:
                # No global model
                print(f"[LSTM] No global model available, using average")
                avg = average_proficiency(bkt_sequence)
                return {"prediction": avg, "confidence": 0.5}
        else:
            # As user gets more data, reduce global model influence
            data_points = len(history)
            if data_points >= MIN_SEQUENCE_LENGTH:
                global_contribution = max(0.0, min(1.0, 1.0 - (data_points - MIN_SEQUENCE_LENGTH) / 20))
                print(f"[LSTM] User has {data_points} data points, global contribution: {global_contribution:.2f}")
        
        # Check if we need to train or update user model
        force_train_if_needed(user_id)
        
        # If still no model, revert to average
        if not os.path.exists(model_path):
            print("[LSTM] Model still not found after force training. Returning average.")
            avg = average_proficiency(bkt_sequence)
            return {"prediction": avg, "confidence": 0.5}
        
        # Track the current history length
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                history = json.load(f)
        else:
            history = []
            
        with open(counter_file, "w") as f:
            f.write(str(len(history)))
            
        # Make prediction with user-specific or global model
        model = load_model(model_path)
        X = pad_sequences([bkt_sequence], maxlen=model.input_shape[1], dtype='float32')
        X = np.expand_dims(X, -1)
        pred = model.predict(X, verbose=0)
        raw_prediction = float(pred[0][0])

        # ENHANCED: Apply BKT-aware scaling
        if bkt_sequence:
            avg_bkt_mastery = sum(bkt_sequence) / len(bkt_sequence)
            
            # If BKT shows high mastery (>0.9), boost LSTM prediction significantly
            if avg_bkt_mastery > 0.9:
                boost_factor = min(1.4, 1.0 + (avg_bkt_mastery - 0.9) * 3)
                adjusted_prediction = min(0.95, raw_prediction * boost_factor)
                print(f"[LSTM] High BKT mastery detected ({avg_bkt_mastery:.3f}), "
                      f"boosting prediction: {raw_prediction:.3f} → {adjusted_prediction:.3f}")
                final_prediction = adjusted_prediction
            elif avg_bkt_mastery > 0.8:
                # Moderate boost for good mastery
                boost_factor = 1.0 + (avg_bkt_mastery - 0.8) * 1.5
                adjusted_prediction = min(0.9, raw_prediction * boost_factor)
                print(f"[LSTM] Good BKT mastery detected ({avg_bkt_mastery:.3f}), "
                      f"moderate boost: {raw_prediction:.3f} → {adjusted_prediction:.3f}")
                final_prediction = adjusted_prediction
            elif avg_bkt_mastery > 0.7:
                # Small boost for decent mastery
                boost_factor = 1.0 + (avg_bkt_mastery - 0.7) * 0.8
                adjusted_prediction = min(0.85, raw_prediction * boost_factor)
                print(f"[LSTM] Decent BKT mastery detected ({avg_bkt_mastery:.3f}), "
                      f"small boost: {raw_prediction:.3f} → {adjusted_prediction:.3f}")
                final_prediction = adjusted_prediction
            else:
                # Keep original prediction for lower mastery
                final_prediction = raw_prediction
                print(f"[LSTM] BKT mastery ({avg_bkt_mastery:.3f}) below threshold, keeping original: {raw_prediction:.3f}")
        else:
            final_prediction = raw_prediction

        # Calculate confidence
        user_confidence = calculate_confidence(model, X, history)
        
        # If we're using a blend, compute global prediction too
        if user_has_enough_data and global_contribution > 0:
            # Get global model prediction
            global_model_path = get_lstm_model_path()
            if os.path.exists(global_model_path):
                global_model = load_model(global_model_path)
                X_global = pad_sequences([bkt_sequence], maxlen=global_model.input_shape[1], dtype='float32')
                X_global = np.expand_dims(X_global, -1)
                global_pred = global_model.predict(X_global, verbose=0)
                global_prediction = float(global_pred[0][0])
                
                # Blend predictions
                final_prediction = (global_contribution * global_prediction + 
                                   (1.0 - global_contribution) * raw_prediction)
                print(f"[LSTM] Blended prediction: {global_prediction:.3f} (global) * {global_contribution:.2f} + "
                      f"{raw_prediction:.3f} (user) * {(1-global_contribution):.2f} = {final_prediction:.3f}")
                
                # FIXED: Get global confidence using proper path
                global_history_path = get_lstm_history_path()  # Global path
                print(f"[LSTM] Looking for global history at: {global_history_path}")
                if os.path.exists(global_history_path):
                    with open(global_history_path, "r") as f:
                        global_history = json.load(f)
                    global_confidence = calculate_confidence(global_model, X_global, global_history)
                    print(f"[LSTM] Found global history with {len(global_history)} entries")
                else:
                    print(f"[LSTM] Warning: Global history file missing at {global_history_path}, using default confidence")
                    global_confidence = 0.7
                    
                final_confidence = (global_contribution * global_confidence + 
                                   (1.0 - global_contribution) * user_confidence)
                
                return {"prediction": final_prediction, "confidence": final_confidence}
            
        # Always return dict with both values    
        return {"prediction": final_prediction, "confidence": user_confidence, "raw_prediction": raw_prediction, "bkt_adjustment": final_prediction != raw_prediction}
        
    except Exception as e:
        # Proper error handling
        import traceback
        print(f"[LSTM] Error in predict_proficiency: {str(e)}")
        traceback.print_exc()
        return {
            "prediction": 0.0, 
            "confidence": 0.3,
            "error": str(e)
        }

# Add this to lstm_engine.py
def display_lstm_proficiency(user_id=None):
    """
    Formats and prints LSTM proficiency prediction in a readable format
    
    Args:
        user_id: Optional user ID to include in the display
    """
    # Get history data
    history_file = get_lstm_history_path(user_id)  # Use user-specific path
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)
    else:
        history = []
    
    # Get prediction if we have enough data
    if len(history) >= MIN_SEQUENCE_LENGTH:
        # Get the last sequence for prediction
        sequence = history[-MIN_SEQUENCE_LENGTH:]
        prediction = predict_proficiency(sequence, user_id)  # Pass user_id
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

def display_lstm_proficiency_ascii(user_id=None):
    """ASCII-only version of the display function that works on all terminals"""
    # Get history data
    history_file = get_lstm_history_path(user_id)  # Use user-specific path
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)
    else:
        history = []
    
    # Get prediction if we have enough data
    if len(history) >= MIN_SEQUENCE_LENGTH:
        sequence = history[-MIN_SEQUENCE_LENGTH:]
        prediction = predict_proficiency(sequence, user_id)  # Pass user_id
        model_status = "Active"
    else:
        sequence = history if history else []
        prediction = average_proficiency(sequence) if sequence else 0.0
        model_status = f"Inactive (Need {MIN_SEQUENCE_LENGTH-len(history)} more data points)"
    
    # Print header
    print("\n+-----------------------------------------------------------------------+")
    print("|                          LSTM PROFICIENCY                              |")
    print("+-----------------------------------------------------------------------+")
    
    # User info
    if user_id:
        print(f"| User ID:                 {user_id:<45} |")
    
    # Model status
    print(f"| Model Status:            {model_status:<45} |")
    print(f"| History Data Points:     {len(history):<45} |")
    
    # Current prediction
    proficiency_percent = prediction * 100
    print(f"| Current Proficiency:     {proficiency_percent:.1f}% {get_proficiency_level(prediction):<37} |")
    
    # Learning curve
    if len(history) >= 2:
        trend = history[-1] - history[-2]
        trend_display = f"{trend*100:+.1f}% " + ("UP" if trend > 0 else "DOWN" if trend < 0 else "SAME")
        print(f"| Recent Trend:           {trend_display:<45} |")
    
    print("+-----------------------------------------------------------------------+")
    
    # Show recent history points
    print("| Recent Proficiency History:                                           |")
    recent = history[-5:] if len(history) > 5 else history
    for i, h in enumerate(recent):
        idx = len(history) - len(recent) + i
        print(f"|   Point {idx+1:<2}: {h*100:>6.1f}%                                                |")
    
    print("+-----------------------------------------------------------------------+")

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
    
def display_lstm_predictions_table(bkt_sequence, user_id=None):
    """Display LSTM predictions in a formatted table with RAW values"""
    try:
        # Get the prediction result
        result = predict_proficiency(bkt_sequence, user_id)
        
        # Always use raw values for display
        if isinstance(result, dict):
            overall_prediction = result.get("raw_prediction", result.get("prediction", 0))
            overall_confidence = result.get("confidence", 0)
        else:
            overall_prediction = result
            overall_confidence = 0.8
        
        # Print header
        print("┌" + "─" * 79 + "┐")
        print("│" + " " * 32 + "LSTM PREDICTIONS" + " " * 31 + "│")
        print("├" + "─" * 20 + "┬" + "─" * 13 + "┬" + "─" * 10 + "┬" + "─" * 10 + "┬" + "─" * 10 + "┤")
        print("│ Vocabulary           │ Proficiency   │ Conf     │ Method   │")
        print("├" + "─" * 20 + "┼" + "─" * 13 + "┼" + "─" * 10 + "┼" + "─" * 10 + "┼" + "─" * 10 + "┤")
        print("│ Overall Proficiency  │    {:.6f}   │  {:.4f}  │ {:^8} │".format(
            overall_prediction, overall_confidence, "LSTM"
        ))
        print("└" + "─" * 20 + "┴" + "─" * 13 + "┴" + "─" * 10 + "┴" + "─" * 10 + "┴" + "─" * 10 + "┘")
        print("* Proficiency levels above 0.70 indicate strong learning progress")
        
        # ENHANCED: Print detailed raw values
        print(f"\nRAW LSTM PROFICIENCY VALUES:")
        print(f"  - Raw Prediction: {overall_prediction:.8f}")
        print(f"  - Raw Confidence: {overall_confidence:.8f}")
        if bkt_sequence:
            print(f"  - BKT Sequence Used: {[f'{x:.6f}' for x in bkt_sequence]}")
            print(f"  - Average BKT Mastery: {sum(bkt_sequence)/len(bkt_sequence):.8f}")
        
        return {"confidence": overall_confidence, "prediction": overall_prediction}
        
    except Exception as e:
        print(f"[LSTM] Error displaying predictions table: {e}")
        return {"confidence": 0.5, "prediction": 0.0}