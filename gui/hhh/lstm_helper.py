import os
import json
import subprocess
import tempfile
import sys
import time

def get_lstm_proficiency(bkt_sequence, completion_percentage, user_id=None):
    """
    Get LSTM proficiency prediction using subprocess to avoid Flet UI freezing
    
    Args:
        bkt_sequence: List of BKT mastery values
        completion_percentage: Percentage of lesson completed (0-100)
        user_id: Optional user ID for user-specific model
        
    Returns:
        Dictionary with proficiency, confidence and other details
    """
    if not bkt_sequence:
        return {
            "proficiency": 0.0,
            "confidence": 0.0,
            "method": "none",
            "error": "No BKT sequence provided"
        }
        
    # Create temp input file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        input_file = f.name
        json.dump({
            "bkt_sequence": bkt_sequence,
            "completion_percentage": completion_percentage
        }, f)
    
    try:
        with open(input_file, 'r') as f:
            input_data = json.load(f)
            if not input_data.get("bkt_sequence"):
                # Try to recover from database directly as last resort
                from bkt_engine import ensure_bkt_data_loaded
                bkt_sequence = ensure_bkt_data_loaded(user_id, force_db_refresh=True)
                if bkt_sequence:
                    print(f"[LSTM] Recovered sequence with {len(bkt_sequence)} values from database")
                    input_data["bkt_sequence"] = bkt_sequence
                    # Re-save the file with recovered data
                    with open(input_file, 'w') as f_fix:
                        json.dump(input_data, f_fix)
    except Exception as e:
        print(f"[LSTM] Error validating input file: {e}")

    try:
        # Run subprocess with timeout
        cmd = [
            sys.executable, 
            "lstm_engine_runner.py", 
            input_file,
            str(user_id) if user_id else "None"
        ]
        
        print(f"[LSTM] Running subprocess: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait with timeout (10 seconds max)
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            print("[LSTM] Process timed out after 10 seconds")
            return {
                "proficiency": average_proficiency(bkt_sequence) * completion_percentage / 100.0,
                "confidence": 0.3,
                "method": "timeout",
                "error": "Process timed out"
            }
            
        # Process output
        if stderr:
            print(f"[LSTM] Process stderr: {stderr}")
            
        if stdout:
            try:
                result = json.loads(stdout)
                return result
            except json.JSONDecodeError:
                print(f"[LSTM] Failed to parse JSON output: {stdout}")
        
        try:
            # Get the proficiency value
            proficiency_value = result["proficiency"] if isinstance(result, dict) and "proficiency" in result else 0
            
            # Save to main history file that the app expects
            history_path = "temp_prof_history.json"
            
            if os.path.exists(history_path):
                with open(history_path, "r") as f:
                    history = json.load(f)
                    
                    # Make sure history is a list
                    if not isinstance(history, list):
                        if isinstance(history, dict) and "values" in history:
                            history = history["values"]
                        else:
                            history = []
            else:
                history = []
                
            # Add the new prediction and save
            history.append(proficiency_value)
            with open(history_path, "w") as f:
                json.dump(history, f)
            
            print(f"[LSTM] Saved proficiency {proficiency_value:.4f} to main history file")
        except Exception as e:
            print(f"[LSTM] Error saving to main history: {str(e)}")
            
        if result:
            return result
        else:
            # Fallback to average if no usable output
            return {
                "proficiency": average_proficiency(bkt_sequence) * completion_percentage / 100.0,
                "confidence": 0.3,
                "method": "fallback",
                "error": "Failed to parse output"
            }
    
    except Exception as e:
        print(f"[LSTM] Error running subprocess: {str(e)}")
        return {
            "proficiency": average_proficiency(bkt_sequence) * completion_percentage / 100.0,
            "confidence": 0.3,
            "method": "error",
            "error": str(e)
        }
    finally:
        # Clean up temp file
        try:
            os.unlink(input_file)
        except:
            pass

def average_proficiency(masteries):
    """Calculate simple average proficiency"""
    if not masteries:
        return 0.0
    return sum(masteries) / len(masteries)