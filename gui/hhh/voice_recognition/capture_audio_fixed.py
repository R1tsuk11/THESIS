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
    mobile_platform = False
    if 'FLET_VIEW' in os.environ and 'ANDROID_' in os.environ.get('ANDROID_DATA', ''):
        mobile_platform = True
        logger.info("Detected Android mobile platform")
    
    # Create temp paths with proper directory handling for mobile
    if mobile_platform:
        # On Android, ensure we use a writable directory
        temp_dir = os.environ.get('TMPDIR', '/data/data/com.example.arami/cache/')
        if not os.path.exists(temp_dir):
            temp_dir = os.path.dirname(os.path.abspath(__file__))
        temp_path = os.path.join(temp_dir, f"recording_{int(time.time())}.wav")
        enhanced_file = os.path.join(temp_dir, f"enhanced_{int(time.time())}.wav")
    else:
        # On desktop, use tempfile module
        temp_path = tempfile.mktemp(suffix=".wav")
        enhanced_file = "enhanced_recording.wav"
    
    # First try our AudioRecorderManager - best approach
    if recorder_manager:
        try:
            logger.info("Using AudioRecorderManager for recording")
            if not recorder_manager._initialized:
                recorder_manager.initialize()
            
            temp_file = recorder_manager.record(duration_seconds=duration)
            if temp_file and os.path.exists(temp_file):
                logger.info(f"Recording successful with AudioRecorderManager: {temp_file}")
                
                # Enhance audio
                logger.info("Enhancing audio...")
                audio_segment = AudioSegment.from_wav(temp_file)
                enhanced_audio = enhance_audio_for_waray(audio_segment)
                enhanced_audio.export(enhanced_file, format="wav")
                
                # Clean up temporary file
                try:
                    os.remove(temp_file)
                except Exception as e:
                    logger.warning(f"Could not remove temp file: {str(e)}")
                
                return enhanced_file
        except Exception as e:
            logger.error(f"Error using AudioRecorderManager: {e}")
            # Continue to fallback options
    
    # Fallback to direct flet_audio usage
    try:
        import flet_audio
        logger.info("Using flet_audio directly for microphone access")
        
        # Check what attributes and methods are available in flet_audio
        logger.info(f"flet_audio available attributes: {dir(flet_audio)}")
        
        # Different approaches based on flet_audio version
        if hasattr(flet_audio, 'record_audio'):
            # New API style
            logger.info("Using flet_audio.record_audio API")
            print("Recording... speak now")
            
            # Record directly to file
            flet_audio.record_audio(
                temp_path,  # Save directly to temp file
                duration_ms=duration * 1000  # Convert seconds to milliseconds
            )
            logger.info(f"Recording completed and saved to {temp_path}")
            
        elif hasattr(flet_audio, 'Audio'):
            # Alternative API style
            logger.info("Using flet_audio.Audio API")
            recorder = flet_audio.Audio()
            recorder.record_audio(duration_seconds=duration)
            print("Recording... speak now")
            
            # Wait for recording to complete
            time.sleep(duration + 0.5)  # Add a small buffer
            
            # Save the recorded audio
            audio_data = recorder.get_audio_data()
            logger.info(f"Saving audio to {temp_path}")
            with open(temp_path, "wb") as f:
                f.write(audio_data)
                
        elif hasattr(flet_audio, 'AudioRecorder'):
            # Newer API style
            logger.info("Using flet_audio.AudioRecorder API")
            recorder = flet_audio.AudioRecorder()
            recorder.start()
            print("Recording... speak now")
            time.sleep(duration)
            recorder.stop()
            audio_data = recorder.get_bytes()
            
            logger.info(f"Saving audio to {temp_path}")
            with open(temp_path, "wb") as f:
                f.write(audio_data)
                
        else:
            # Old API style - try last resort approach
            logger.info("Attempting legacy flet_audio API")
            # Create instance directly from the module
            recorder = flet_audio
            if hasattr(recorder, 'record'):
                recorder.record()
                print("Recording... speak now")
                time.sleep(duration)
                audio_data = recorder.stop_recording()
                
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
