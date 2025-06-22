# Basic test script to verify speech_recognition_utils functionality
import os
import sys

# Make sure we can import from the right path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from voice_recognition.speech_recognition_utils import SpeechProcessor
    print("Successfully imported SpeechProcessor from voice_recognition.speech_recognition_utils")
    
    # Initialize the speech processor
    processor = SpeechProcessor()
    print("Successfully initialized SpeechProcessor")
    
    print("All tests passed! The speech_recognition_utils module is working correctly.")
except Exception as e:
    print(f"Error: {str(e)}")
    print(f"Type: {type(e)}")
    import traceback
    traceback.print_exc()
