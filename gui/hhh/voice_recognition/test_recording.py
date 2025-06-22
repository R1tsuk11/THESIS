"""
Test script to verify the recording functionality.
This will test the AudioRecorderManager directly without the UI.
"""

import os
import sys
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory and parent directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
parent_parent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, parent_parent_dir)

def test_recording():
    """Test basic recording functionality"""
    logger.info("Testing audio recording...")
    
    # Try to import the AudioRecorderManager
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
        
        # Initialize the recorder
        initialized = recorder_manager.initialize()
        logger.info(f"AudioRecorderManager initialized: {initialized}")
        logger.info(f"API version detected: {recorder_manager._api_version}")
        
        if not initialized:
            logger.error("Failed to initialize recorder")
            return False
        
        # Record audio
        logger.info("Recording audio for 3 seconds...")
        print("Recording... speak now")
        audio_path = recorder_manager.record(duration_seconds=3)
        
        if not audio_path:
            logger.error("Failed to record audio")
            return False
        
        logger.info(f"Successfully recorded audio to: {audio_path}")
        logger.info(f"File size: {os.path.getsize(audio_path)} bytes")
        
        # Try processing the audio with the SpeechProcessor
        try:
            # Import speech processing components
            try:
                from speech_recognition_utils import SpeechProcessor
                from audio_processing import enhance_audio_for_waray
            except ImportError:
                try:
                    from voice_recognition.speech_recognition_utils import SpeechProcessor
                    from voice_recognition.audio_processing import enhance_audio_for_waray
                except ImportError:
                    from gui.hhh.voice_recognition.speech_recognition_utils import SpeechProcessor
                    from gui.hhh.voice_recognition.audio_processing import enhance_audio_for_waray
            
            # Process audio
            logger.info("Processing audio with SpeechProcessor...")
            processor = SpeechProcessor()
            
            # Enhance audio first
            from pydub import AudioSegment
            audio_segment = AudioSegment.from_file(audio_path)
            enhanced_audio = enhance_audio_for_waray(audio_segment)
            enhanced_file = os.path.join(os.path.dirname(audio_path), "enhanced_test.wav")
            enhanced_audio.export(enhanced_file, format="wav")
            
            # Predict speech
            result = processor.predict_speech(enhanced_file)
            if result:
                predicted_word, confidence, _ = result
                logger.info(f"Predicted word: {predicted_word}")
                logger.info(f"Confidence: {confidence:.2f}")
            else:
                logger.warning("Failed to process audio")
                
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing recording: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting recording test")
    
    # Print important environment information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Script location: {os.path.abspath(__file__)}")
    
    # Run the test
    result = test_recording()
    logger.info(f"Test completed with {'success' if result else 'failure'}")
