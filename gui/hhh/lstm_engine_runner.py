import sys
import json
import os
import traceback
import time
import numpy as np

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings

def get_path(base_dir, filename, user_id=None):
    """Get path for a file, creating directory if needed"""
    os.makedirs(base_dir, exist_ok=True)
    if user_id and str(user_id).lower() != "none":
        return os.path.join(base_dir, f"{filename}_{user_id}.json")
    return os.path.join(base_dir, f"{filename}.json")

def get_history_path(user_id=None):
    """Get path for user's history file"""
    return get_path("lstm_history", "temp_prof_history", user_id)

def get_counter_path(user_id=None):
    """Get path for user's counter file"""
    return get_path("lstm_counters", "lstm_counter", user_id)

def get_model_path(user_id=None):
    """Get path for user's model file"""
    os.makedirs("lstm_models", exist_ok=True)
    if user_id and str(user_id).lower() != "none":
        return os.path.join("lstm_models", f"lstm_proficiency_model_{user_id}.keras")
    return os.path.join("lstm_models", "lstm_proficiency_model.keras")
    
def simple_proficiency_calculation(bkt_sequence, completion, user_id):
    """Simple and reliable proficiency calculation that won't hang"""
    log(f"Starting proficiency calculation for user {user_id}")
    
    # Get appropriate paths
    history_path = get_history_path(user_id)
    model_path = get_model_path(user_id)
    
    # Create user model if needed
    setup_user_model(user_id)
    
    # Calculate basic average as fallback
    avg = sum(bkt_sequence) / len(bkt_sequence) if bkt_sequence else 0
    result = avg * completion / 100.0  # Assuming completion is in percent
    
    # Attempt LSTM prediction if model exists
    prediction = result
    confidence = 0.5
    method = "average"
    error = None
    
    try:
        # Only try to use the model if it exists
        if os.path.exists(model_path):
            from tensorflow.keras.models import load_model
            from tensorflow.keras.preprocessing.sequence import pad_sequences
            
            log(f"Loading model from {model_path}")
            model = load_model(model_path)
            
            # Prepare input
            X = pad_sequences([bkt_sequence], maxlen=model.input_shape[1], dtype='float32')
            X = np.expand_dims(X, -1)  # Add feature dimension
            
            # Make prediction
            log("Making prediction with model")
            pred = model.predict(X, verbose=0)
            prediction = float(pred[0][0])
            
            # Calculate loss/confidence
            y_true = np.array([prediction])  # Use prediction as target
            loss = float(model.evaluate(X, y_true, verbose=0)[0])
            confidence = max(0.3, min(0.95, np.exp(-loss)))
            
            log(f"Model prediction: {prediction}, loss: {loss}, confidence: {confidence}")
            method = "lstm"
            
            # Apply completion percentage
            prediction = prediction * completion / 100.0
    except Exception as e:
        log(f"Error using LSTM model: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        error = str(e)
        # Fall back to average method
    
    # Update history with this prediction
    try:
        update_history(history_path, prediction)
    except Exception as e:
        log(f"Error updating history: {str(e)}")
    
    # Return result
    return {
        "proficiency": prediction,
        "confidence": confidence,
        "method": method,
        "error": error
    }

def setup_user_model(user_id):
    """Set up a user model if it doesn't exist"""
    if not user_id:
        return
        
    user_model_path = get_model_path(user_id)
    base_model_path = get_model_path()
    
    # Copy base model to user model if it doesn't exist
    if not os.path.exists(user_model_path) and os.path.exists(base_model_path):
        log(f"Creating user model for {user_id}")
        try:
            import shutil
            shutil.copy(base_model_path, user_model_path)
            log(f"Copied base model to {user_model_path}")
        except Exception as e:
            log(f"Error copying model: {str(e)}")

def update_history(history_path, prediction):
    """Update the history file with new prediction"""
    log(f"Updating history at {history_path}")
    
    try:
        # Read existing history or create new
        if os.path.exists(history_path):
            with open(history_path, "r") as f:
                history = json.load(f)
                # Handle different formats
                if isinstance(history, dict) and "values" in history:
                    history = history["values"]
                elif isinstance(history, list) and history and isinstance(history[0], dict):
                    history = [item["proficiency"] for item in history if "proficiency" in item]
        else:
            history = []
            
        # Add new prediction
        history.append(prediction)
        log(f"History now has {len(history)} entries")
        
        # Save updated history
        os.makedirs(os.path.dirname(history_path) or '.', exist_ok=True)
        with open(history_path, "w") as f:
            json.dump(history, f)
            
    except Exception as e:
        log(f"Error processing history: {str(e)}")

def log(message):
    """Helper to print debug logs"""
    print(f"[LSTM Runner] {message}", file=sys.stderr)

if __name__ == "__main__":
    start_time = time.time()
    log("LSTM Runner starting")
    
    try:
        # Parse command line arguments
        if len(sys.argv) < 3:
            log("Error: Missing arguments")
            print(json.dumps({
                "error": "Missing arguments",
                "method": "error",
                "proficiency": 0.0,
                "confidence": 0.0
            }))
            sys.exit(1)
            
        input_json_path = sys.argv[1]
        user_id = sys.argv[2] if len(sys.argv) > 2 else None
        
        # Load input data
        log(f"Reading input from {input_json_path}")
        with open(input_json_path, "r") as f:
            input_data = json.load(f)
            
        bkt_sequence = input_data.get("bkt_sequence", [])
        completion_percentage = input_data.get("completion_percentage", 100)
        
        log(f"Processing for user {user_id}, sequence length: {len(bkt_sequence)}, completion: {completion_percentage}%")
        
        # Calculate proficiency
        result = simple_proficiency_calculation(bkt_sequence, completion_percentage, user_id)
        
        # Output result as JSON
        output = {
            "proficiency": result["proficiency"],
            "method": result["method"],
            "confidence": result["confidence"],
            "error": result["error"],
            "runtime_ms": int((time.time() - start_time) * 1000)
        }
        
        log(f"Calculation complete. Result: {result['proficiency']:.4f}, confidence: {result['confidence']:.2f}")
        print(json.dumps(output))
        
    except Exception as e:
        log(f"Global error: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({
            "error": str(e),
            "method": "error",
            "proficiency": 0.0,
            "confidence": 0.0,
            "runtime_ms": int((time.time() - start_time) * 1000)
        }))