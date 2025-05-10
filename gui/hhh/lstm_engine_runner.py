import sys
import json
from lstm_engine import overall_proficiency

if __name__ == "__main__":
    # Arguments: <bkt_json_path> <completion>
    bkt_json = sys.argv[1]
    completion = float(sys.argv[2])
    with open(bkt_json, "r") as f:
        bkt_state = json.load(f)
    p_masteries = bkt_state.get("p_masteries", [])
    proficiency = overall_proficiency(p_masteries, completion)
    print(json.dumps({"proficiency": proficiency}))