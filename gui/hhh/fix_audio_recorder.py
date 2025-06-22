"""
Script to fix audio_recorder.py and other files with indentation issues.
This script focuses on the specific indentation issues in our project.
"""

import re
import os

def fix_audio_recorder_py():
    """Fix specific indentation issues in audio_recorder.py."""
    file_path = "voice_recognition/audio_recorder.py"
    
    # Create a backup
    backup_path = file_path + ".bak"
    with open(file_path, "r") as f:
        content = f.read()
    
    with open(backup_path, "w") as f:
        f.write(content)
    
    print(f"Created backup at {backup_path}")
    
    # Fix specific issues
    
    # 1. Fix 'elif self._api_version == 'recorder':' line
    content = content.replace(
        "            elif self._api_version == 'recorder':                logger.info",
        "            elif self._api_version == 'recorder':\n                logger.info"
    )
    
    # 2. Fix 'elif self._api_version == 'flet_audio_recorder':' indentation if needed
    if "            elif self._api_version == 'flet_audio_recorder':" not in content:
        content = content.replace(
            "elif self._api_version == 'flet_audio_recorder':",
            "            elif self._api_version == 'flet_audio_recorder':"
        )
    
    # Write the fixed content
    with open(file_path, "w") as f:
        f.write(content)
    
    print(f"Fixed indentation issues in {file_path}")
    
    # Verify the file runs without syntax errors
    import subprocess
    result = subprocess.run(["python", "-m", "py_compile", file_path], 
                           capture_output=True, text=True)
    
    if result.returncode == 0:
        print("No syntax errors detected after fixing.")
        return True
    else:
        print(f"Syntax errors still present: {result.stderr}")
        return False

if __name__ == "__main__":
    print("Fixing indentation issues in audio files...")
    success = fix_audio_recorder_py()
    
    if success:
        print("All issues fixed successfully!")
    else:
        print("Some issues could not be fixed automatically.")
