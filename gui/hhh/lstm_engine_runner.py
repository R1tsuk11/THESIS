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
    try:
        # Set up paths
        model_path = get_model_path(user_id)
        history_path = get_history_path(user_id)
        
        # Ensure user model exists
        setup_user_model(user_id)
        
        # Check if model exists
        if not os.path.exists(model_path):
            log(f"Model not found at {model_path}")
            return {
                "proficiency": 0.5,
                "method": "fallback",
                "confidence": 0.5,
                "error": "Model not found"
            }
        
        # Load model
        log(f"Loading model from {model_path}")
        from tensorflow.keras.models import load_model
        from tensorflow.keras.preprocessing.sequence import pad_sequences
        model = load_model(model_path)
        
        # Prepare input data
        X = np.array([bkt_sequence])
        if len(X[0]) != model.input_shape[1]:
            # Pad sequence if necessary
            X = pad_sequences(X, maxlen=model.input_shape[1], dtype='float32')
        
        # Add channel dimension if needed
        if len(model.input_shape) > 2:  # Model expects 3D input
            X = np.expand_dims(X, -1)
        
        # Make prediction
        log("Making prediction with model")
        pred = model.predict(X, verbose=0)
        prediction = float(pred[0][0])
        
        # Calculate confidence using multiple approaches
        try:
            # Generate multiple predictions by adding small noise to inputs
            n_iterations = 5  # Fewer iterations for speed in subprocess
            predictions = []
            
            # Create variations of the input
            for i in range(n_iterations):
                if i == 0:
                    pred = prediction  # First prediction already made
                else:
                    # Add gaussian noise
                    noise_level = 0.02 * i
                    X_noisy = X + np.random.normal(0, noise_level, X.shape)
                    pred = model.predict(X_noisy, verbose=0)[0][0]
                predictions.append(pred)
            
            # Calculate variance to measure model uncertainty
            std_dev = np.std(predictions)
            model_confidence = max(0.3, min(0.95, np.exp(-8 * std_dev)))
            log(f"Input perturbation variance: {std_dev:.4f}, confidence: {model_confidence:.2f}")
            
            # Calculate historical component if history exists
            history_confidence = 0.7  # Default
            history = []  # Initialize empty history
            if os.path.exists(history_path):
                try:
                    with open(history_path, "r") as f:
                        history = json.load(f)
                        if isinstance(history, list) and len(history) >= 3:
                            recent = history[-5:] if len(history) > 5 else history
                            std_dev = np.std(recent)
                            history_confidence = max(0.3, min(0.95, np.exp(-7 * std_dev)))
                except Exception as e:
                    log(f"Error reading history: {str(e)}")
            
            # Data sufficiency component
            data_points = len(history) if history else 0
            data_confidence = min(0.9, 0.5 + (data_points * 0.05))
            
            # Combine components
            confidence = (0.4 * model_confidence + 
                         0.4 * history_confidence + 
                         0.2 * data_confidence)
                         
            # Ensure reasonable bounds
            confidence = max(0.3, min(0.95, confidence))
            
        except Exception as e:
            log(f"Error calculating confidence: {str(e)}")
            confidence = 0.7  # Default moderate confidence
        
        # Update history with new prediction
        update_history(history_path, prediction)
        
        # Return calculation result
        return {
            "proficiency": prediction,
            "method": "lstm",
            "confidence": confidence,
            "error": None
        }
        
    except Exception as e:
        log(f"Error in proficiency calculation: {str(e)}")
        return {
            "proficiency": 0.0,
            "method": "error",
            "confidence": 0.0,
            "error": str(e)
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