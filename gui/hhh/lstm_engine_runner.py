import sys
import json
import os
from lstm_engine import overall_proficiency, train_lstm_model, MIN_SEQUENCE_LENGTH

if __name__ == "__main__":
    # Arguments: <bkt_json_path> <completion> <history_file>
    bkt_json = sys.argv[1]
    completion = float(sys.argv[2])
    history_file = sys.argv[3] if len(sys.argv) > 3 else None

    # Train if needed
    if history_file and os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)
        if len(history) >= MIN_SEQUENCE_LENGTH:
            sequences = [entry["p_masteries"] for entry in history]
            labels = [entry["proficiency"] for entry in history]
            train_lstm_model(sequences, labels)

    # Predict
    with open(bkt_json, "r") as f:
        bkt_state = json.load(f)
    p_masteries = bkt_state.get("p_masteries", [])
    proficiency = overall_proficiency(p_masteries, completion)
    print(json.dumps({"proficiency": proficiency}))