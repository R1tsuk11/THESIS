import pandas as pd
from pyBKT.models import Model
import json
import os
import pickle
import sys

INPUT_CSV = "bkt_input.csv"
OUTPUT_JSON = "bkt_predictions.json"
MODEL_FILE = "bkt_model.pkl"  # Default model path

# Add function to get user-specific model path
def get_user_bkt_model_path(user_id=None):
    """Get user-specific BKT model path"""
    if user_id and str(user_id).lower() != "none":
        return f"bkt_model_{user_id}.pkl"
    return "bkt_model.pkl"

# Modify run_bkt_model to accept user_id
def run_bkt_model(mode="predict", user_id=None):
    """Run the BKT model with the given mode (fit or predict) for specific user"""
    # Set user-specific model and prediction paths
    global MODEL_FILE
    MODEL_FILE = get_user_bkt_model_path(user_id)
    
    print(f"[bkt_model_runner] Running for user_id: {user_id} with model path: {MODEL_FILE}")
    
    # Load input data
    if os.path.exists(INPUT_CSV):
        df = pd.read_csv(INPUT_CSV)
    else:
        df = pd.DataFrame()
    print(f"[bkt_model_runner] Loaded input data: {len(df)} rows")

    if os.path.exists(MODEL_FILE):
        with open(MODEL_FILE, 'rb') as f:
            model = pickle.load(f)
            print(f"[bkt_model_runner] Loaded model from {MODEL_FILE}")
    else:
        model = Model()
        print(f"[bkt_model_runner] Created new model for user {user_id}")
        mode = "fit"  # Force fit for new model
        
    if mode == "fit":
        try:
            model.fit(data=df)
            with open(MODEL_FILE, 'wb') as f:
                pickle.dump(model, f)
            print(f"[bkt_model_runner] Model fitted and saved to {MODEL_FILE}")
        except Exception as e:
            print(f"[bkt_model_runner] Error during fit: {e}")
            
    # Make predictions
    try:
        if len(df) > 0:
            prediction_df = model.predict(data=df)
            
            # Build predictions dictionary
            predictions = {}
            for skill in df['skill_name'].unique():
                skill_data = df[df['skill_name'] == skill]
                if len(skill_data) > 0:
                    # Get the last row for this skill
                    last_row = skill_data.iloc[-1]
                    
                    # Calculate mastery increase for first-time learning
                    # Make mastery more responsive in early learning
                    mastery = last_row.get('state_predictions', 0.5)
                    
                    # If mastery is still at default but answers are correct, boost it
                    if abs(mastery - 0.5) < 0.01 and all(skill_data['correct'] == 1):
                        correct_count = len(skill_data)
                        # More aggressive update for consistent correct answers
                        mastery = min(0.85, 0.5 + (0.1 * correct_count))
                        print(f"[bkt_model_runner] Boosted mastery for '{skill}' to {mastery:.2f} based on {correct_count} correct answers")
                    
                    predictions[skill.lower()] = {
                        'p_mastery': float(mastery),
                        'guess': float(last_row.get('guess', 0.2)),
                        'slip': float(last_row.get('slip', 0.1)),
                        'confidence': 1.0 - float(last_row.get('guess', 0.2)) - float(last_row.get('slip', 0.1)),
                        'correct': int(last_row.get('correct', 0))
                    }
                    
            # Save predictions to user-specific file
            with open(OUTPUT_JSON, 'w') as f:
                json.dump(predictions, f, indent=2)
            print(f"[bkt_model_runner] Predictions saved to '{OUTPUT_JSON}'")
        else:
            print(f"[bkt_model_runner] No data to make predictions for user {user_id}")
    except Exception as e:
        print(f"[bkt_model_runner] Error during prediction: {e}")
        
    # Clean up input file
    if os.path.exists(INPUT_CSV):
        os.remove(INPUT_CSV)
        print(f"[bkt_model_runner] Deleted existing '{INPUT_CSV}'")

if __name__ == "__main__":
    # Parse command line arguments
    mode = "predict"
    user_id = None
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    
    if len(sys.argv) > 2:
        user_id = sys.argv[2]
        
    print(f"[bkt_model_runner] Running in {mode} mode for user {user_id}")
    run_bkt_model(mode == "fit", user_id)