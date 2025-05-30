import pandas as pd
from pyBKT.models import Model
import json
import os
import pickle
import sys

INPUT_CSV = "bkt_input.csv"
OUTPUT_JSON = "bkt_predictions.json"
MODEL_FILE = "bkt_model.pkl"

# Modify in bkt_engine_runner.py
def run_bkt_model(mode="predict"):
    """Run the BKT model with the given mode (fit or predict)"""
    print(f"[bkt_model_runner] Loaded input data: {len(df)} rows")

    if os.path.exists('bkt_model.pkl'):
        with open('bkt_model.pkl', 'rb') as f:
            model = pickle.load(f)
            print("[bkt_model_runner] Loaded model from disk.")
    else:
        model = Model()
        print("[bkt_model_runner] Created new model.")
        mode = "fit"  # Force fit for new model
        
    if mode == "fit":
        try:
            model.fit(data=df)
            with open('bkt_model.pkl', 'wb') as f:
                pickle.dump(model, f)
            print("[bkt_model_runner] Model fitted and saved to disk.")
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
                    
            # Save predictions to file
            with open('bkt_predictions.json', 'w') as f:
                json.dump(predictions, f, indent=2)
            print("[bkt_model_runner] Predictions saved to 'bkt_predictions.json'.")
        else:
            print("[bkt_model_runner] No data to make predictions.")
    except Exception as e:
        print(f"[bkt_model_runner] Error during prediction: {e}")
        
    # Clean up input file
    if os.path.exists("bkt_input.csv"):
        os.remove("bkt_input.csv")
        print("[bkt_model_runner] Deleted existing 'bkt_input.csv'.")

if __name__ == "__main__":
    fit = True
    if len(sys.argv) > 1 and sys.argv[1] == "predict":
        fit = False
    run_bkt_model(fit)
