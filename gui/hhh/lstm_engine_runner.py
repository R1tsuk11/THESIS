import sys
import json
import os
import traceback
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from lstm_engine import overall_proficiency

if __name__ == "__main__":
    # Arguments: <input_json_path> <proficiency_history_path>
    try:
        input_json = sys.argv[1]
        prof_history_path = sys.argv[2]

        with open(input_json, "r") as f:
            data = json.load(f)
        bkt_sequence = data["bkt_sequence"]
        completion = data["completion_percentage"]

        with open(prof_history_path, "r") as f:
            proficiency_history = json.load(f)

        print(f"[LSTM subprocess] bkt_sequence: {bkt_sequence}", file=sys.stderr)
        print(f"[LSTM subprocess] completion: {completion}", file=sys.stderr)
        print(f"[LSTM subprocess] proficiency_history: {proficiency_history}", file=sys.stderr)

        proficiency, updated_history = overall_proficiency(
        bkt_sequence, completion, proficiency_history
    )
    
        # Store the updated history
        with open(prof_history_path, "w") as f:
            json.dump(updated_history, f)
        
        # Ensure we print valid JSON to stdout
        if proficiency is not None:
            print(json.dumps({"proficiency": proficiency}))
        else:
            print(json.dumps({"proficiency": 0.0}))
            
    except Exception as e:
        print(f"[LSTM subprocess] Exception: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)