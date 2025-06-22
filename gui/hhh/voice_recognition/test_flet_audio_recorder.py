"""
Test script for the flet_audio_recorder implementation.
This checks that recording works properly on mobile devices.
"""

import os
import sys
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Simulate Android mode if needed
if '--android' in sys.argv:
    os.environ['SIMULATE_ANDROID'] = 'true'
    logger.info("Running in Android simulation mode")

def test_flet_audio_recorder():
    """Test flet_audio_recorder for mobile devices."""
    try:
        import flet_audio_recorder
        logger.info(f"Successfully imported flet_audio_recorder: {getattr(flet_audio_recorder, '__file__', 'unknown')}")
        logger.info(f"Available methods: {dir(flet_audio_recorder)}")
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
        logger.info("Trying to install the package...")
        
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "flet_audio_recorder"])
            logger.info("Installation completed, please run the test again")
        except Exception as e:
            logger.error(f"Failed to install flet_audio_recorder: {e}")
        
        return False
    except Exception as e:
        logger.error(f"Error testing flet_audio_recorder: {e}")
        return False

def test_audio_recorder_manager():
    """Test the AudioRecorderManager with flet_audio_recorder."""
    try:
        # Import the AudioRecorderManager
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from voice_recognition.audio_recorder import AudioRecorderManager
        
        logger.info("Creating AudioRecorderManager instance...")
        recorder = AudioRecorderManager()
        
        # Initialize
        initialized = recorder.initialize()
        logger.info(f"AudioRecorderManager initialized: {initialized}")
        if not initialized:
            logger.error("Failed to initialize AudioRecorderManager")
            return False
        
        # Record
        logger.info("Starting recording (3 seconds)...")
        print("Speak now...")
        
        audio_path = recorder.record(duration_seconds=3)
        
        if audio_path:
            logger.info(f"Audio recorded to: {audio_path}")
            
            # Check file size
            if os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                logger.info(f"File size: {file_size} bytes")
                
                if file_size > 1000:
                    logger.info("AudioRecorderManager test PASSED!")
                    return True
                else:
                    logger.warning("File too small, recording might not have worked properly")
            else:
                logger.error("Failed to save audio file")
        else:
            logger.error("No audio path returned")
            
        return False
    except Exception as e:
        logger.error(f"Error testing AudioRecorderManager: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("===== flet_audio_recorder Test =====")
    
    # Test direct flet_audio_recorder
    logger.info("----- Testing direct flet_audio_recorder -----")
    direct_result = test_flet_audio_recorder()
    
    # Test AudioRecorderManager
    logger.info("----- Testing AudioRecorderManager with flet_audio_recorder -----")
    manager_result = test_audio_recorder_manager()
    
    # Print summary
    logger.info("===== Test Results =====")
    logger.info(f"Direct flet_audio_recorder test: {'PASSED' if direct_result else 'FAILED'}")
    logger.info(f"AudioRecorderManager test: {'PASSED' if manager_result else 'FAILED'}")
    
    if direct_result and manager_result:
        logger.info("All tests PASSED! Recording with flet_audio_recorder is working properly.")
    else:
        logger.info("Some tests FAILED. Check the logs for details.")
