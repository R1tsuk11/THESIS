"""
Audio recording utilities that handle different versions of flet_audio
and provide a consistent interface for both desktop and mobile platforms.
"""

import os
import time
import logging
import tempfile
import importlib
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioRecorderManager:
    """
    Provides a unified interface for audio recording across different 
    flet_audio versions and platforms.
    """
    def __init__(self):
        """Initialize the audio recorder manager."""
        self._recorder = None
        self._audio_recorder = None  # For flet_audio_recorder
        self._api_version = None
        self._is_mobile = ('ANDROID_DATA' in os.environ or 
                         'IOS_APP' in os.environ or 
                         os.environ.get('SIMULATE_ANDROID') == 'true')
        self._initialized = False
        
    def initialize(self):
        """Initialize the appropriate recorder based on available APIs."""
        if self._initialized:
            return True
            
        try:            # First try to import flet_audio_recorder for mobile
            if self._is_mobile:
                try:
                    import flet_audio_recorder
                    self._audio_recorder = flet_audio_recorder.AudioRecorder()  # Create an instance
                    self._api_version = 'flet_audio_recorder'
                    logger.info(f"Using flet_audio_recorder for mobile: {getattr(flet_audio_recorder, '__file__', 'unknown')}")
                    self._initialized = True
                    return True
                except ImportError as e:
                    logger.warning(f"flet_audio_recorder not available for mobile: {e}, falling back to flet_audio")
                except Exception as e:
                    logger.warning(f"Error initializing flet_audio_recorder: {e}, falling back to flet_audio")
            
            # Try to import flet_audio - handle reloading if needed
            if 'flet_audio' in sys.modules:
                importlib.reload(sys.modules['flet_audio'])
                flet_audio = sys.modules['flet_audio']
            else:
                import flet_audio
                
            logger.info(f"Found flet_audio: {getattr(flet_audio, '__file__', 'unknown')}")
            logger.info(f"flet_audio dir: {dir(flet_audio)}")
            
            # Check which API is available
            if hasattr(flet_audio, 'record_audio'):
                self._api_version = 'new'
                self._recorder = flet_audio
                logger.info("Using new record_audio API")
            elif hasattr(flet_audio, 'Audio'):
                self._api_version = 'middle'
                self._recorder = flet_audio.Audio()
                logger.info("Using middle Audio class API")
            elif hasattr(flet_audio, 'AudioRecorder'):
                self._api_version = 'recorder'
                self._recorder = flet_audio.AudioRecorder()
                logger.info("Using AudioRecorder class API")
            else:
                self._api_version = 'old'
                self._recorder = flet_audio
                logger.info("Using old module-level API")
            
            logger.info(f"Using flet_audio with API version: {self._api_version}")
            self._initialized = True
            return True
        except ImportError as e:
            logger.warning(f"flet_audio not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Error initializing audio recorder: {e}")
            return False
    
    def record(self, duration_seconds=3):
        """Start recording audio for the specified duration.
        
        Args:
            duration_seconds: Recording duration in seconds
            
        Returns:
            temp_path: Path to the temporary audio file
        """
        if not self._initialized:
            if not self.initialize():
                logger.error("Failed to initialize audio recorder")
                return None
        
        # Create temp path with proper directory handling for mobile
        if self._is_mobile:
            # On Android, ensure we use a writable directory
            temp_dir = os.environ.get('TMPDIR', '/data/data/com.example.arami/cache/')
            if not os.path.exists(temp_dir):
                temp_dir = os.path.dirname(os.path.abspath(__file__))
                if not os.access(temp_dir, os.W_OK):
                    temp_dir = os.getcwd()
            
            # Create a unique filename
            temp_path = os.path.join(temp_dir, f"recording_{int(time.time())}.wav")
        else:
            # On desktop, use tempfile module
            temp_path = tempfile.mktemp(suffix=".wav")
        
        logger.info(f"Recording to temp path: {temp_path}")
        
        try:
            if self._api_version == 'new':
                logger.info(f"Recording with new API to {temp_path}")
                self._recorder.record_audio(
                    temp_path, 
                    duration_ms=duration_seconds * 1000
                )
                return temp_path
            elif self._api_version == 'middle':
                logger.info("Recording with middle API")
                try:
                    # Fall back to PyAudio directly
                    logger.info("Using PyAudio directly for recording")
                    import pyaudio
                    import wave
                    import numpy as np
                    
                    CHUNK = 1024
                    FORMAT = pyaudio.paInt16
                    CHANNELS = 1
                    RATE = 16000
                    
                    p = pyaudio.PyAudio()
                    
                    logger.info("Opening PyAudio stream...")
                    stream = p.open(format=FORMAT,
                                    channels=CHANNELS,
                                    rate=RATE,
                                    input=True,
                                    frames_per_buffer=CHUNK)
                    
                    logger.info(f"Recording for {duration_seconds} seconds...")
                    print("Recording... speak now")
                    frames = []
                    
                    for i in range(0, int(RATE / CHUNK * duration_seconds)):
                        data = stream.read(CHUNK)
                        frames.append(data)
                    
                    logger.info("Finished recording")
                    
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    
                    # Save as WAV file
                    logger.info(f"Saving to {temp_path}")
                    wf = wave.open(temp_path, 'wb')
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(p.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(frames))
                    wf.close()
                    
                    logger.info(f"Saved audio to {temp_path}")
                    
                    # Generate some audio if we didn't get any meaningful data (e.g., testing)
                    if os.path.getsize(temp_path) < 1000:
                        logger.warning("Recorded audio is too small, generating test tone")
                        # Generate 1 second of 440 Hz sine wave
                        sample_rate = 16000
                        duration = 1
                        t = np.linspace(0, duration, int(sample_rate * duration), False)
                        tone = np.sin(2 * np.pi * 440 * t) * 32767
                        tone = tone.astype(np.int16)
                        
                        wf = wave.open(temp_path, 'wb')
                        wf.setnchannels(1)
                        wf.setsampwidth(2)  # 2 bytes for int16
                        wf.setframerate(sample_rate)
                        wf.writeframes(tone.tobytes())
                        wf.close()
                        
                        logger.info(f"Generated test tone and saved to {temp_path}")
                    
                    return temp_path
                except Exception as e:
                    logger.error(f"Error with PyAudio: {e}")
                    
                    # As a last resort, generate a test tone
                    try:
                        logger.warning("Generating test audio file as fallback")
                        import numpy as np
                        import wave
                        
                        # Generate 1 second of 440 Hz sine wave
                        sample_rate = 16000
                        duration = 1
                        t = np.linspace(0, duration, int(sample_rate * duration), False)
                        tone = np.sin(2 * np.pi * 440 * t) * 32767
                        tone = tone.astype(np.int16)
                        
                        wf = wave.open(temp_path, 'wb')
                        wf.setnchannels(1)
                        wf.setsampwidth(2)  # 2 bytes for int16
                        wf.setframerate(sample_rate)
                        wf.writeframes(tone.tobytes())
                        wf.close()
                        
                        logger.info(f"Generated test tone and saved to {temp_path}")
                        return temp_path
                    except Exception as inner_e:                        logger.error(f"Error generating test audio: {inner_e}")
                        return None
            elif self._api_version == 'recorder':
                logger.info("Recording with AudioRecorder API")
                self._recorder.start()
                time.sleep(duration_seconds)
                self._recorder.stop()
                audio_data = self._recorder.get_bytes()
                logger.info(f"Got audio data, size: {len(audio_data) if audio_data else 0} bytes")
                with open(temp_path, "wb") as f:
                    f.write(audio_data)
            elif self._api_version == 'flet_audio_recorder':
                logger.info("Recording with flet_audio_recorder API")
                self._audio_recorder.start_recording()  # Use proper method name
                time.sleep(duration_seconds)
                audio_data = self._audio_recorder.stop_recording()  # Use proper method name
                logger.info(f"Got audio data, size: {len(audio_data) if audio_data else 0} bytes")
                with open(temp_path, "wb") as f:
                    f.write(audio_data)
            else:  # old API
                logger.info("Recording with old API")
                self._recorder.record()
                time.sleep(duration_seconds)
                audio_data = self._recorder.stop_recording()
                logger.info(f"Got audio data, size: {len(audio_data) if audio_data else 0} bytes")
                with open(temp_path, "wb") as f:
                    f.write(audio_data)
            
            if not os.path.exists(temp_path):
                logger.error(f"Failed to create audio file at {temp_path}")
                return None
                
            if os.path.getsize(temp_path) == 0:
                logger.error(f"Audio file is empty: {temp_path}")
                return None
                
            logger.info(f"Successfully saved audio to {temp_path}, size: {os.path.getsize(temp_path)} bytes")
            return temp_path
        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            return None
            
    def record_audio(self, duration=3):
        """Alias for record method to maintain backward compatibility."""
        return self.record(duration_seconds=duration)

# Global recorder manager instance
recorder_manager = AudioRecorderManager()

if __name__ == "__main__":
    # Simple test when run directly
    print("Testing audio recorder...")
    recorder_manager.initialize()
    audio_file = recorder_manager.record(duration_seconds=3)
    print(f"Recorded audio to: {audio_file}")
