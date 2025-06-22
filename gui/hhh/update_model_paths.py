# Helper script to update model paths in speech_recognition_utils.py
import os
import re

def update_model_paths():
    # Read the speech_recognition_utils.py file
    file_path = 'voice_recognition/speech_recognition_utils.py'
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the model paths section
    model_paths_pattern = r"possible_model_paths = \[\s*\"waray_speech_model\.keras\".*?]"
    match = re.search(model_paths_pattern, content, re.DOTALL)
    
    if match:
        old_paths = match.group(0)
        
        # Create the new paths array with proper indentation
        new_paths = """possible_model_paths = [
                "waray_speech_model.keras",                  # Current directory
                "d:/lstm_prof/waray_speech_model.keras",     # Original path
                os.path.join(
                    os.path.dirname(__file__),
                    "waray_speech_model.keras"),  # Same folder as this script
                os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                    "waray_speech_model.keras")  # Project root
            ]"""
        
        # Replace the old paths with the new paths
        updated_content = content.replace(old_paths, new_paths)
        
        # Similarly for encoder paths
        encoder_paths_pattern = r"possible_encoder_paths = \[\s*\"encoder_classes\.npy\".*?]"
        match = re.search(encoder_paths_pattern, updated_content, re.DOTALL)
        
        if match:
            old_encoder_paths = match.group(0)
            
            # Create new encoder paths array
            new_encoder_paths = """possible_encoder_paths = [
                "encoder_classes.npy",                 # Current directory
                os.path.join(
                    os.path.dirname(__file__),
                    "encoder_classes.npy"),
                # Same folder as this script
                "d:/lstm_prof/encoder_classes.npy",     # Try absolute path
                os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                    "encoder_classes.npy")  # Project root
            ]"""
            
            # Replace encoder paths
            updated_content = updated_content.replace(old_encoder_paths, new_encoder_paths)
        
        # Write the updated content back to the file
        with open(file_path, 'w') as f:
            f.write(updated_content)
        
        print("Successfully updated model and encoder paths in speech_recognition_utils.py")
        return True
    else:
        print("Could not find model paths section in speech_recognition_utils.py")
        return False

if __name__ == "__main__":
    update_model_paths()
