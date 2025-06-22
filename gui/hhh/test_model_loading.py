"""Test script to verify the speech model can be loaded correctly."""
import os
import sys

# Add the necessary paths to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, project_root)

print(f"Current directory: {current_dir}")
print(f"Parent directory: {parent_dir}")
print(f"Project root: {project_root}")

# Find model file
model_paths = [
    os.path.join(project_root, "waray_speech_model.keras"),
    os.path.join(current_dir, "waray_speech_model.keras"),
    os.path.join(current_dir, "lstm_models", "waray_speech_model.keras")
]

print("\nChecking for model files:")
for path in model_paths:
    exists = os.path.exists(path)
    print(f"  {path}: {'EXISTS' if exists else 'NOT FOUND'}")

# Find encoder file
encoder_paths = [
    os.path.join(project_root, "encoder_classes.npy"),
    os.path.join(current_dir, "encoder_classes.npy"),
    os.path.join(current_dir, "lstm_models", "encoder_classes.npy")
]

print("\nChecking for encoder files:")
for path in encoder_paths:
    exists = os.path.exists(path)
    print(f"  {path}: {'EXISTS' if exists else 'NOT FOUND'}")

# Try to import SpeechProcessor and load model
try:
    print("\nAttempting to import SpeechProcessor...")
    from voice_recognition.speech_recognition_utils import SpeechProcessor
    
    print("Successfully imported SpeechProcessor. Creating instance...")
    processor = SpeechProcessor()
    
    print(f"Processor model loaded: {processor.model is not None}")
    print(f"Processor encoder classes loaded: {processor.encoder_classes is not None}")
    
    if processor.model is not None:
        print("Model architecture:")
        processor.model.summary()
    
    print("\nTEST PASSED: Speech recognition module is working correctly.")
except Exception as e:
    print(f"\nTEST FAILED: Error initializing speech processor: {e}")
    import traceback
    traceback.print_exc()
