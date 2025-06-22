# This is a temporary version of the capture_audio function with corrected indentation
# This can be integrated into the full speech_recognition_utils.py file

def capture_audio(duration=3, sample_rate=16000):
    """Capture audio from microphone with enhanced preprocessing.
    
    This function prioritizes our AudioRecorderManager for all platforms,
    then falls back to direct flet_audio for mobile platforms (Android/iOS),
    and finally speech_recognition for desktop platforms.
    
    Parameters:
        duration (int): Recording duration in seconds
        sample_rate (int): Audio sample rate
        
    Returns:
        str: Path to the enhanced audio file or None if recording failed
    """
    import platform
    import tempfile
    import time
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Try different ways to import audio_recorder
    recorder_manager = None
    try:
        try:
            from gui.hhh.voice_recognition.audio_recorder import recorder_manager
            logger.info("Using recorder_manager from gui.hhh.voice_recognition")
        except ImportError:
            try:
                from voice_recognition.audio_recorder import recorder_manager
                logger.info("Using recorder_manager from voice_recognition")
            except ImportError:
                try:
                    from .audio_recorder import recorder_manager
                    logger.info("Using recorder_manager from relative import")
                except (ImportError, ValueError):
                    try:
                        # Last resort, try direct import when running as main script
                        from audio_recorder import recorder_manager
                        logger.info("Using recorder_manager from direct import")
                    except ImportError:
                        logger.warning("Could not import recorder_manager")
                        recorder_manager = None
    except Exception as e:
        logger.error(f"Error importing recorder_manager: {e}")
        recorder_manager = None
    
    # Determine if we're likely on a mobile platform
    mobile_platform = ('ANDROID_DATA' in os.environ or
                     platform.system() == 'Darwin' and not platform.machine().startswith('i'))
    
    # Create temp paths
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, "audio_capture_temp.wav")
    enhanced_file = os.path.join(temp_dir, "enhanced_audio.wav")
    
    # First, try using the recorder_manager which should work on all platforms
    if recorder_manager:
        logger.info("Using AudioRecorderManager")
        audio_path = recorder_manager.record_audio(duration=duration)
        if audio_path:
            logger.info(f"Successfully recorded audio to {audio_path}")
            
            # Enhance audio
            try:
                from pydub import AudioSegment
                from audio_processing import enhance_audio_for_waray
                audio_segment = AudioSegment.from_file(audio_path)
                enhanced_audio = enhance_audio_for_waray(audio_segment)
                enhanced_audio.export(enhanced_file, format="wav")
                return enhanced_file
            except Exception as e:
                logger.error(f"Error enhancing audio: {e}")
                # Return the original recording if enhancement fails
                return audio_path
    
    # Next, try using flet_audio directly
    try:
        logger.info("Trying to use flet_audio directly")
        import flet_audio
        from pydub import AudioSegment
        from audio_processing import enhance_audio_for_waray
        
        # Check if we have the newest API
        has_new_api = hasattr(flet_audio, 'AudioRecorder')
        
        if has_new_api:
            logger.info("Using new flet_audio API")
            recorder = flet_audio.AudioRecorder()
            recorder.start_recording(path=temp_path)
            
            print("Recording... speak now")
            time.sleep(duration)
            recorder.stop_recording()
        elif hasattr(flet_audio, 'record_audio'):
            # Alternative API version
            logger.info("Using flet_audio.record_audio API")
            flet_audio.record_audio(temp_path, sample_rate)
            
            print("Recording... speak now")
            time.sleep(duration)
            flet_audio.stop_recording()
        elif hasattr(flet_audio, 'start_recording'):
            # Yet another API version
            logger.info("Using flet_audio.start_recording API")
            flet_audio.start_recording(temp_path)
            
            print("Recording... speak now")
            time.sleep(duration)
            audio_data = flet_audio.stop_recording()
            
            logger.info(f"Saving audio to {temp_path}")
            with open(temp_path, "wb") as f:
                f.write(audio_data)
        else:
            raise AttributeError("Could not find compatible recording method in flet_audio")
        
        # Verify the file was created successfully
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            logger.warning(f"Failed to save audio data to {temp_path}")
            return None
        
        # Enhance audio
        logger.info("Enhancing audio...")
        audio_segment = AudioSegment.from_wav(temp_path)
        enhanced_audio = enhance_audio_for_waray(audio_segment)
        enhanced_audio.export(enhanced_file, format="wav")
        
        # Clean up the temporary file
        try:
            os.remove(temp_path)
        except Exception as e:
            logger.warning(f"Could not remove temp file: {str(e)}")
        
        return enhanced_file
        
    except (ImportError, Exception) as e:
        logger.info(f"flet_audio not available or failed: {str(e)}")
        if mobile_platform:
            logger.error("Failed to use flet_audio on mobile platform. Audio capture may not work properly.")
            return None
            
        # Fall back to speech_recognition on desktop
        logger.info("Falling back to speech_recognition")
        
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone(sample_rate=sample_rate) as source:
                logger.info("Adjusting for ambient noise...")
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
                
                logger.info("Speak now...")
                print("Recording... speak now")
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=duration)
                    
                    # Save temporary WAV file
                    temp_file = temp_path
                    with open(temp_file, "wb") as f:
                        f.write(audio.get_wav_data())
                    
                    # Enhance audio
                    from pydub import AudioSegment
                    from audio_processing import enhance_audio_for_waray
                    audio_segment = AudioSegment.from_wav(temp_file)
                    enhanced_audio = enhance_audio_for_waray(audio_segment)
                    enhanced_audio.export(enhanced_file, format="wav")
                    
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                    
                    return enhanced_file
                    
                except sr.WaitTimeoutError:
                    logger.warning("No speech detected")
                    return None
                except Exception as e:
                    logger.error(f"Error capturing audio: {str(e)}")
                    return None
        
        except Exception as e:
            logger.error(f"Error in speech recognition fallback: {str(e)}")
            return None
