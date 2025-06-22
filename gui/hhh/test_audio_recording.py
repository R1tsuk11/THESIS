"""
Test script for audio recording in Arami application.
This script specifically tests the audio recording functionality in both desktop and Android modes.
"""

import os
import sys
import logging
import time
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_paths():
    """Set up paths for imports."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # Add to path
    sys.path.insert(0, current_dir)
    sys.path.insert(0, parent_dir)
    
    # For voice_recognition module
    voice_recog_path = os.path.join(current_dir, "voice_recognition")
    if os.path.exists(voice_recog_path):
        sys.path.insert(0, voice_recog_path)
        
    # Print paths for debugging
    logger.info(f"Current dir: {current_dir}")
    logger.info(f"Parent dir: {parent_dir}")
    logger.info(f"Voice recognition path: {voice_recog_path}")
    logger.info(f"System path: {sys.path}")

def test_recording_methods():
    """Test all available recording methods."""
    logger.info("===== Testing Recording Methods =====")
    
    # Try direct import of audio_recorder first
    try:
        setup_paths()
        try:
            from voice_recognition.audio_recorder import AudioRecorderManager
            logger.info("Successfully imported AudioRecorderManager")
            
            # Create an instance
            recorder = AudioRecorderManager()
            
            # Initialize
            initialized = recorder.initialize()
            logger.info(f"AudioRecorderManager initialized: {initialized}")
            
            if initialized:
                # Record audio
                logger.info("Testing audio recording (3 seconds)...")
                print("Speak now...")
                
                audio_file = recorder.record(duration_seconds=3)
                
                if audio_file:
                    logger.info(f"Audio recorded to: {audio_file}")
                    
                    # Check file size
                    if os.path.exists(audio_file):
                        file_size = os.path.getsize(audio_file)
                        logger.info(f"File size: {file_size} bytes")
                        
                        if file_size > 1000:
                            logger.info("Direct recording test PASSED!")
                            return True
                        else:
                            logger.warning("File too small, recording might not have worked properly")
                    else:
                        logger.error(f"Audio file does not exist: {audio_file}")
                else:
                    logger.error("Failed to record audio")
            else:
                logger.error("Failed to initialize AudioRecorderManager")
        except ImportError as e:
            logger.error(f"Could not import AudioRecorderManager: {e}")
            logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"Error in direct recording test: {e}")
            logger.error(traceback.format_exc())
        
        # Now try via capture_audio
        try:
            from voice_recognition.speech_recognition_utils import capture_audio
            logger.info("Successfully imported capture_audio")
            
            # Test recording
            logger.info("Testing audio recording with capture_audio (3 seconds)...")
            print("Speak now...")
            
            # Record audio
            audio_file = capture_audio(duration=3)
            
            if audio_file:
                logger.info(f"Audio captured to: {audio_file}")
                
                # Check file size
                if os.path.exists(audio_file):
                    file_size = os.path.getsize(audio_file)
                    logger.info(f"File size: {file_size} bytes")
                    
                    if file_size > 1000:
                        logger.info("capture_audio test PASSED!")
                        return True
                    else:
                        logger.warning("File too small, recording might not have worked properly")
                else:
                    logger.error(f"Audio file does not exist: {audio_file}")
            else:
                logger.error("Failed to capture audio")
        except ImportError as e:
            logger.error(f"Could not import capture_audio: {e}")
            logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"Error in capture_audio test: {e}")
            logger.error(traceback.format_exc())
        
        # If we get here, both methods failed
        logger.error("All recording methods failed")
        return False
    except Exception as e:
        logger.error(f"Error in recording test: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("===== Audio Recording Test =====")
    
    # Check for Android simulation flag
    if '--android' in sys.argv:
        os.environ['SIMULATE_ANDROID'] = 'true'
        logger.info("Running in Android simulation mode")
    
    # Run tests
    recording_result = test_recording_methods()
    
    # Print summary
    logger.info("===== Test Results =====")
    logger.info(f"Audio recording test: {'PASSED' if recording_result else 'FAILED'}")
    
    if recording_result:
        logger.info("Test PASSED! Audio recording is working properly.")
    else:
        logger.info("Test FAILED. Check the logs for details.")
