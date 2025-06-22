"""
Test script to diagnose flet_audio issues
Run this script to check the installed version of flet_audio and available APIs
"""

import sys
import os
import logging

# Add the current directory and parent directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
parent_parent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, parent_parent_dir)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_flet_audio():
    """Test flet_audio package to check installed version and API"""
    logger.info("Testing flet_audio package...")
    
    # Check Python path
    logger.info(f"Python path: {sys.path}")
    
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
            # First try direct import
            try:
                from audio_recorder import recorder_manager
                logger.info("Imported recorder_manager directly")
            except ImportError:
                # Then try relative import
                try:
                    from .audio_recorder import recorder_manager
                    logger.info("Imported recorder_manager via relative import")
                except (ImportError, ValueError):
                    # Try with full path
                    try:
                        from voice_recognition.audio_recorder import recorder_manager
                        logger.info("Imported recorder_manager from voice_recognition")
                    except ImportError:
                        # Try with gui.hhh prefix
                        from gui.hhh.voice_recognition.audio_recorder import recorder_manager
                        logger.info("Imported recorder_manager from gui.hhh.voice_recognition")
            
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
    
    # Print important environment information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Script location: {os.path.abspath(__file__)}")
    
    # Check for important modules
    for module in ['flet', 'flet_audio', 'numpy', 'tensorflow', 'pydub']:
        try:
            __import__(module)
            logger.info(f"Module {module} is available")
        except ImportError:
            logger.warning(f"Module {module} is NOT available")
    
    # Run the test
    result = test_flet_audio()
    logger.info(f"Test completed with {'success' if result else 'failure'}")
