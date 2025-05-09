import pandas as pd
from pyBKT.models import Model
import json
import os
import pickle
import sys

INPUT_CSV = "bkt_input.csv"
OUTPUT_JSON = "bkt_predictions.json"
MODEL_FILE = "bkt_model.pkl"

def run_bkt_model(fit=True):
    if not os.path.exists(INPUT_CSV):
        print(f"[bkt_model_runner] Input file '{INPUT_CSV}' not found.")
        return

    # Load data
    df = pd.read_csv(INPUT_CSV)
    print(f"[bkt_model_runner] Loaded input data: {df.shape[0]} rows")

    # Fit model
    model = Model()

    if not fit:
        if not os.path.exists(MODEL_FILE):
            print("[bkt_model_runner] No fitted model found. Forcing fit.")
            fit = True
            
    if fit:
        try:
            model.fit(data=df)
            print("[bkt_model_runner] Model fitted successfully.")
            with open(MODEL_FILE, "wb") as mf:
                pickle.dump(model, mf)
        except Exception as e:
            print(f"[bkt_model_runner] Error fitting model: {e}")
            return
        
    else:
        if os.path.exists(MODEL_FILE):
            with open(MODEL_FILE, "rb") as mf:
                model = pickle.load(mf)
            print("[bkt_model_runner] Loaded model from disk.")
        else:
            print("[bkt_model_runner] No fitted model found. Cannot predict.")
            return
 
    # Predict
    try:
        pred_df = model.predict(data=df)
        pred_df['confidence'] = 1 - pred_df['guess'] - pred_df['slip']

        result = {}
        for vocab in pred_df['skill_name'].unique():
            last_row = pred_df[pred_df['skill_name'] == vocab].iloc[-1]
            result[vocab] = {
                'user_id': int(last_row['user_id']),
                'vocabulary': vocab,
                'correct': int(last_row['correct']),
                'p_mastery': float(last_row['state_predictions']),
                'guess': float(last_row['guess']),
                'slip': float(last_row['slip']),
                'confidence': float(last_row['confidence'])
            }

        with open(OUTPUT_JSON, "w") as f:
            json.dump(result, f, indent=4)

        # Delete the prediction DataFrame CSV file if it exists
        if os.path.exists(INPUT_CSV):
            os.remove(INPUT_CSV)
            print(f"[bkt_model_runner] Deleted existing '{INPUT_CSV}'.")

        print(f"[bkt_model_runner] Predictions saved to '{OUTPUT_JSON}'.")
    except Exception as e:
        print(f"[bkt_model_runner] Error during prediction: {e}")

if __name__ == "__main__":
    fit = True
    if len(sys.argv) > 1 and sys.argv[1] == "predict":
        fit = False
    run_bkt_model(fit)
