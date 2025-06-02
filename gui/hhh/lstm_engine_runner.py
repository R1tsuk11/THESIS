import sys
import json
import os
import traceback
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from lstm_engine import average_proficiency, overall_proficiency

if __name__ == "__main__":
    # Arguments: <input_json_path> <proficiency_history_path>
    try:
        input_json = sys.argv[1]
        prof_history_path = sys.argv[2]
        user_id = sys.argv[3] if len(sys.argv) > 3 else None

        with open(input_json, "r") as f:
            data = json.load(f)
            bkt_sequence = data["bkt_sequence"]
            historical_sequences = data.get("historical_sequences", [])
            completion = data["completion_percentage"]

            print(f"[LSTM subprocess] Current bkt_sequence: {bkt_sequence}", file=sys.stderr)
            print(f"[LSTM subprocess] Found {len(historical_sequences)} historical sequences", file=sys.stderr)
            print(f"[LSTM subprocess] completion: {completion}", file=sys.stderr)

            # Merge historical_sequences before bkt_sequence
            if historical_sequences:
                merged_sequence = []
                for seq in historical_sequences:
                    merged_sequence.extend(seq)
                merged_sequence.extend(bkt_sequence)
                bkt_sequence = merged_sequence
                print(f"[LSTM subprocess] Merged sequence (historical first): {bkt_sequence}", file=sys.stderr)

        with open(prof_history_path, "r") as f:
            proficiency_history = json.load(f)
        print(f"[LSTM subprocess] proficiency_history: {proficiency_history}", file=sys.stderr)
        
        # Pass this to the overall_proficiency function
        output = overall_proficiency(
            merged_sequence, completion, user_id
        )
        
        # Validate JSON before returning it
        try:
            # Check if output is already a string
            if isinstance(output, (int, float, dict)):
                # Convert to proper JSON structure and then to string
                output_json = json.dumps({
                    "proficiency": float(output) if isinstance(output, (int, float)) else output.get("proficiency", 0.0),
                    "method": "lstm" if not isinstance(output, dict) else output.get("method", "fallback"),
                    "error": None if not isinstance(output, dict) else output.get("error", None),
                    "confidence": 0.8 if not isinstance(output, dict) else output.get("confidence", 0.0)
                })
            else:
                output_json = output
                
            # Validate it's proper JSON
            json.loads(output_json)
            print(output_json)  # Output the JSON result
        except (json.JSONDecodeError, TypeError) as json_err:
            print(f"[LSTM subprocess] Generated invalid JSON: {json_err}", file=sys.stderr)
            # Return a fallback valid JSON
            fallback = json.dumps({
                "error": "Invalid JSON generated",
                "method": "fallback",
                "proficiency": average_proficiency(bkt_sequence) * completion,
                "confidence": 50.0
            })
            print(fallback)
            
    except Exception as e:
        print(f"[LSTM subprocess] Exception: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        # Return valid JSON even in case of error
        error_json = json.dumps({
            "error": str(e),
            "method": "error",
            "proficiency": 0.0,
            "confidence": 0.0
        })
        print(error_json)
        sys.exit(1)