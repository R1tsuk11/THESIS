import os
import re

def fix_speech_recognition_utils():
    """Replace the problematic capture_audio function with the fixed version."""
    
    # Paths
    original_file = "voice_recognition/speech_recognition_utils.py"
    fixed_function_file = "voice_recognition/fixed_capture_audio.py"
    
    # Read the fixed function
    with open(fixed_function_file, 'r') as f:
        fixed_content = f.read()
    
    # Extract just the function definition
    pattern = r"def capture_audio.*?(?=\n\n|\Z)"
    match = re.search(pattern, fixed_content, re.DOTALL)
    if not match:
        print("Could not find the capture_audio function in the fixed file.")
        return False
    
    fixed_function = match.group(0)
    print(f"Fixed function length: {len(fixed_function)} characters")
    
    # Read the original file
    with open(original_file, 'r') as f:
        original_content = f.read()
    
    # Try to find the existing function
    pattern = r"def capture_audio.*?(?=def \w+|\Z)"
    match = re.search(pattern, original_content, re.DOTALL)
    
    if not match:
        print("Could not locate the capture_audio function in the original file.")
        # Try a more basic pattern
        pattern = r"def capture_audio\([^)]*\):.*?(?=def|\Z)"
        match = re.search(pattern, original_content, re.DOTALL)
        
        if not match:
            print("Still couldn't find the capture_audio function with the alternative pattern.")
            # Find line numbers for manual inspection
            lines = original_content.split('\n')
            for i, line in enumerate(lines):
                if "def capture_audio" in line:
                    print(f"Found 'def capture_audio' at line {i+1}")
            return False
    
    original_function = match.group(0)
    print(f"Original function length: {len(original_function)} characters")
    
    # Find start position of the original function
    start_pos = match.start()
    end_pos = match.end()
    
    # Create the new content by replacing just the matched function
    new_content = original_content[:start_pos] + fixed_function + original_content[end_pos:]
    
    # Write the result
    with open(original_file, 'w') as f:
        f.write(new_content)
    
    print("Successfully replaced the capture_audio function!")
    return True

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    fix_speech_recognition_utils()
