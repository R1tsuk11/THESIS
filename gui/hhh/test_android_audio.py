"""
Test script for verifying audio recording on Android.
This specifically tests flet_audio_recorder integration.
"""

import os
import sys
import time
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Simulate Android environment if requested
if '--android' in sys.argv:
    os.environ['SIMULATE_ANDROID'] = 'true'
    logger.info("Running in Android simulation mode")

def test_recorder_manager():
    """Test the AudioRecorderManager's handling of flet_audio_recorder."""
    try:
        # Add the parent directory to sys.path to find the voice_recognition package
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Import the recorder manager
        from voice_recognition.audio_recorder import recorder_manager
        
        logger.info("Testing AudioRecorderManager...")
        
        # Initialize the recorder
        initialized = recorder_manager.initialize()
        logger.info(f"Recorder initialized: {initialized}")
        
        if not initialized:
            logger.error("Failed to initialize recorder_manager")
            return False
        
        # Check which API was selected
        logger.info(f"API version selected: {recorder_manager._api_version}")
        logger.info(f"Is mobile platform: {recorder_manager._is_mobile}")
        
        # Record audio
        logger.info("Recording audio for 3 seconds...")
        print("Speak now...")
        
        audio_path = recorder_manager.record(duration_seconds=3)
        
        if audio_path:
            logger.info(f"Successfully recorded audio to: {audio_path}")
            logger.info(f"File size: {os.path.getsize(audio_path)} bytes")
            
            # Play the audio if possible
            try:
                import subprocess
                logger.info("Attempting to play recorded audio...")
                if sys.platform == 'win32':
                    subprocess.Popen(f'start {audio_path}', shell=True)
                elif sys.platform == 'darwin':
                    subprocess.Popen(f'open {audio_path}', shell=True)
                else:
                    subprocess.Popen(f'xdg-open {audio_path}', shell=True)
            except Exception as e:
                logger.warning(f"Could not play audio: {e}")
            
            return True
        else:
            logger.error("Failed to record audio")
            return False
    except Exception as e:
        logger.error(f"Error in test_recorder_manager: {e}")
        logger.error(traceback.format_exc())
        return False

def test_capture_audio():
    """Test the capture_audio function from speech_recognition_utils."""
    try:
        # Add the parent directory to sys.path
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Import the capture_audio function
        from voice_recognition.speech_recognition_utils import capture_audio
        
        logger.info("Testing capture_audio function...")
        print("Speak now...")
        
        # Record audio
        audio_path = capture_audio(duration=3)
        
        if audio_path:
            logger.info(f"Successfully captured audio to: {audio_path}")
            logger.info(f"File size: {os.path.getsize(audio_path)} bytes")
            
            # Play the audio if possible
            try:
                import subprocess
                logger.info("Attempting to play recorded audio...")
                if sys.platform == 'win32':
                    subprocess.Popen(f'start {audio_path}', shell=True)
                elif sys.platform == 'darwin':
                    subprocess.Popen(f'open {audio_path}', shell=True)
                else:
                    subprocess.Popen(f'xdg-open {audio_path}', shell=True)
            except Exception as e:
                logger.warning(f"Could not play audio: {e}")
            
            return True
        else:
            logger.error("Failed to capture audio")
            return False
    except Exception as e:
        logger.error(f"Error in test_capture_audio: {e}")
        logger.error(traceback.format_exc())
        return False

def test_direct_flet_audio_recorder():
    """Test flet_audio_recorder directly."""
    try:
        import flet_audio_recorder
        logger.info(f"Successfully imported flet_audio_recorder: {getattr(flet_audio_recorder, '__file__', 'unknown')}")
          # Record a short sample
        logger.info("Starting recording test (3 seconds)...")
        print("Speak now...")
        
        # Create recorder instance
        recorder = flet_audio_recorder.AudioRecorder()
        
        # Start recording
        recorder.start_recording()
        
        # Wait for a few seconds
        time.sleep(3)
        
        # Stop recording and get the audio data
        audio_data = recorder.stop_recording()
        
        if audio_data:
            logger.info(f"Recorded audio data size: {len(audio_data)} bytes")
            
            # Save to file
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                  f"flet_recorder_test_{int(time.time())}.wav")
            
            with open(output_path, "wb") as f:
                f.write(audio_data)
                
            logger.info(f"Audio saved to: {output_path}")
            
            # Check file size
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"File size: {file_size} bytes")
                
                if file_size > 1000:
                    logger.info("Recording test PASSED!")
                    return True
                else:
                    logger.warning("File too small, recording might not have worked properly")
            else:
                logger.error("Failed to save audio file")
        else:
            logger.error("No audio data recorded")
            
        return False
    except ImportError as e:
        logger.error(f"Could not import flet_audio_recorder: {e}")
        return False
    except Exception as e:
        logger.error(f"Error testing flet_audio_recorder: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("===== Android Audio Recording Test =====")
    print("This script tests audio recording on Android/mobile platforms")
    print("Use --android to simulate Android environment\n")
    
    # Test recorder_manager
    print("\n1. Testing AudioRecorderManager...")
    if test_recorder_manager():
        print("✓ AudioRecorderManager test PASSED!")
    else:
        print("✗ AudioRecorderManager test FAILED!")
    
    # Test capture_audio
    print("\n2. Testing capture_audio function...")
    if test_capture_audio():
        print("✓ capture_audio test PASSED!")
    else:
        print("✗ capture_audio test FAILED!")
    
    # Test flet_audio_recorder directly
    print("\n3. Testing flet_audio_recorder directly...")
    if test_direct_flet_audio_recorder():
        print("✓ flet_audio_recorder direct test PASSED!")
    else:
        print("✗ flet_audio_recorder direct test FAILED!")
