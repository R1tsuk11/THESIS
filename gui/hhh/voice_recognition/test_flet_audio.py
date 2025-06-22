"""
Test script to diagnose flet_audio issues
Run this script to check the installed version of flet_audio and available APIs
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_flet_audio():
    """Test flet_audio package to check installed version and API"""
    logger.info("Testing flet_audio package...")
    
    # Check if running on Android
    is_android = 'ANDROID_DATA' in os.environ
    logger.info(f"Running on Android: {is_android}")
    
    try:
        import flet_audio
        logger.info(f"Successfully imported flet_audio")
        logger.info(f"flet_audio file location: {getattr(flet_audio, '__file__', 'unknown')}")
        logger.info(f"flet_audio version: {getattr(flet_audio, '__version__', 'unknown')}")
        
        # Check available attributes and methods
        attrs = dir(flet_audio)
        logger.info(f"Available attributes and methods: {attrs}")
        
        # Check specific APIs
        has_record_audio = hasattr(flet_audio, 'record_audio')
        has_audio_class = hasattr(flet_audio, 'Audio')
        has_recorder_class = hasattr(flet_audio, 'AudioRecorder')
        
        logger.info(f"Has record_audio function: {has_record_audio}")
        logger.info(f"Has Audio class: {has_audio_class}")
        logger.info(f"Has AudioRecorder class: {has_recorder_class}")
        
        # Test each API if available
        if has_audio_class:
            logger.info("Testing Audio class...")
            try:
                audio = flet_audio.Audio()
                logger.info(f"Audio instance methods: {dir(audio)}")
                logger.info("Audio class initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Audio class: {e}")
        
        if has_recorder_class:
            logger.info("Testing AudioRecorder class...")
            try:
                recorder = flet_audio.AudioRecorder()
                logger.info(f"AudioRecorder instance methods: {dir(recorder)}")
                logger.info("AudioRecorder class initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing AudioRecorder class: {e}")
          # Test our custom AudioRecorderManager
        logger.info("Testing AudioRecorderManager...")
        try:
            # First try relative import
            try:
                from .audio_recorder import recorder_manager
            except (ImportError, ValueError):
                # Then try direct import (when running the script directly)
                try:
                    from audio_recorder import recorder_manager
                except ImportError:
                    # Last resort: try to add the parent directory to the path
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                    from audio_recorder import recorder_manager
            
            initialized = recorder_manager.initialize()
            logger.info(f"AudioRecorderManager initialized: {initialized}")
            logger.info(f"API version detected: {recorder_manager._api_version}")
        except Exception as e:
            logger.error(f"Error with AudioRecorderManager: {e}")
        
        return True
    except ImportError as e:
        logger.error(f"Could not import flet_audio: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error testing flet_audio: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting flet_audio diagnostic test")
    result = test_flet_audio()
    logger.info(f"Test completed with {'success' if result else 'failure'}")
