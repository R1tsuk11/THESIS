import flet as ft
import os
import sys
import time
import tempfile
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our custom audio recorder - handle different import paths
try:
    from gui.hhh.voice_recognition.audio_recorder import recorder_manager
    logger.info("Using custom audio recorder manager from gui.hhh.voice_recognition")
    has_recorder_manager = True
except ImportError as e:
    logger.warning(f"Import from gui.hhh failed: {e}")
    try:
        from voice_recognition.audio_recorder import recorder_manager
        logger.info("Using custom audio recorder manager from voice_recognition")
        has_recorder_manager = True
    except ImportError as e:
        logger.warning(f"Import from voice_recognition failed: {e}")
        # Add the voice_recognition directory to the path and try again
        voice_recog_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_recognition")
        if os.path.exists(voice_recog_path):
            sys.path.append(voice_recog_path)
            try:
                from audio_recorder import recorder_manager
                logger.info("Using custom audio recorder manager from direct path")
                has_recorder_manager = True
            except ImportError as e:
                logger.warning(f"Custom audio recorder not available, falling back to default: {e}")
                has_recorder_manager = False
        else:
            logger.warning(f"Voice recognition path not found: {voice_recog_path}")
            has_recorder_manager = False

def lesson_pronounce_page(page: ft.Page):
    """Pronunciation exercise page for language learning"""
    page.title = "Arami - Pronunciation Exercise"
    page.padding = 0
    
    # Initialize Audio component for recording
    if has_recorder_manager:
        # Initialize the recorder manager
        initialized = recorder_manager.initialize()
        logger.info(f"Recorder manager initialized: {initialized}")
    
    def go_back(e):
        """Navigate back to the lesson-translate-sentence page"""
        page.go("/lesson-translate-sentence")
    
    def next_exercise(e):
        """Handle progression to the next exercise"""
        # This would typically navigate to another exercise
        print("Moving to next exercise")
        # Future routing could be added here
    
    # Define text variables
    instruction_text = "Pronounce the word:"
    word_text = "Aga"
    translation_text = "Morning"
    tap_record_text = "Tap to record"
    next_button_text = "NEXT"
    
    # Create top header with close button
    header = ft.Container(
        content=ft.Row(
            [
                ft.Container(width=50),  # Spacer
                ft.Container(
                    width=50, 
                    content=ft.IconButton(
                        icon=ft.Icons.CLOSE, 
                        icon_color="black",
                        on_click=go_back
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.END
        ),
        padding=ft.padding.only(top=10, right=10)
    )
      # Create microphone button
    mic_button = ft.ElevatedButton(
        content=ft.Icon(name=ft.Icons.MIC, color="black", size=40),
        bgcolor="#FFC107",  # Yellow
        style=ft.ButtonStyle(
            shape=ft.CircleBorder(),
            padding=20,
        ),
        height=80,
        width=80,
    )
    
    # Status text to show recording status
    status_text = ft.Text(
        value="Tap microphone to record",
        color="black",
        size=14,
        text_align=ft.TextAlign.CENTER
    )
    
    # Function to handle microphone button press
    def on_mic_press(e):
        """Handle microphone recording button press"""
        logger.info("Recording started")
        # Change button color to indicate recording
        mic_button.bgcolor = "#FF6F00"  # Darker orange during recording
        status_text.value = "Recording... speak now"
        page.update()
        
        # Start recording
        temp_path = None
        
        # Update UI to show processing
        def show_processing():
            mic_button.bgcolor = "#4CAF50"  # Green to indicate processing
            mic_button.content = ft.ProgressRing(width=40, height=40, stroke_width=3)
            status_text.value = "Processing audio..."
            page.update()
        
        # After recording completes, process it
        def stop_and_process():
            try:
                if has_recorder_manager:
                    # Use our custom recorder manager
                    logger.info("Using recorder manager to record")
                    temp_path = recorder_manager.record(duration_seconds=3)
                    if not temp_path:
                        logger.error("Failed to record audio with recorder manager")
                        status_text.value = "Recording failed. Please try again."
                        mic_button.bgcolor = "#FFC107"  # Back to yellow
                        mic_button.content = ft.Icon(name=ft.Icons.MIC, color="black", size=40)
                        page.update()
                        return
                    
                    logger.info(f"Recording saved to: {temp_path}")
                    show_processing()
                else:                    # Fallback: Use direct audio capture from our utils
                    try:
                        from gui.hhh.voice_recognition.speech_recognition_utils import capture_audio
                    except ImportError:
                        try:
                            from voice_recognition.speech_recognition_utils import capture_audio
                        except ImportError:
                            # Add the voice_recognition directory to the path and try again
                            voice_recog_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_recognition")
                            if os.path.exists(voice_recog_path):
                                sys.path.append(voice_recog_path)
                                from speech_recognition_utils import capture_audio
                    logger.info("Using speech_recognition_utils.capture_audio")
                    temp_path = capture_audio(duration=3)
                    if not temp_path:
                        logger.error("Failed to record audio with capture_audio")
                        status_text.value = "Recording failed. Please try again."
                        mic_button.bgcolor = "#FFC107"  # Back to yellow
                        mic_button.content = ft.Icon(name=ft.Icons.MIC, color="black", size=40)
                        page.update()
                        return
                    
                    show_processing()
            except Exception as e:
                logger.error(f"Recording error: {e}")
                # Reset button on error
                status_text.value = f"Error recording: {str(e)}"
                mic_button.bgcolor = "#FFC107"  # Back to yellow
                mic_button.content = ft.Icon(name=ft.Icons.MIC, color="black", size=40)
                page.update()
                return
              # Process the audio
            # Import here to avoid circular imports
            try:
                from gui.hhh.voice_recognition.speech_recognition_utils import SpeechProcessor
                from gui.hhh.voice_recognition.audio_processing import enhance_audio_for_waray
            except ImportError:
                try:
                    from voice_recognition.speech_recognition_utils import SpeechProcessor
                    from voice_recognition.audio_processing import enhance_audio_for_waray
                except ImportError:
                    # Add the voice_recognition directory to the path and try again
                    voice_recog_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_recognition")
                    if os.path.exists(voice_recog_path):
                        sys.path.append(voice_recog_path)
                        from speech_recognition_utils import SpeechProcessor
                        from audio_processing import enhance_audio_for_waray
            from pydub import AudioSegment
            
            try:
                # Enhance audio
                logger.info(f"Enhancing audio from {temp_path}")
                audio_segment = AudioSegment.from_wav(temp_path)
                enhanced_audio = enhance_audio_for_waray(audio_segment)
                enhanced_file = "enhanced_recording.wav"
                enhanced_audio.export(enhanced_file, format="wav")
                
                # Process with speech processor
                logger.info("Processing speech")
                processor = SpeechProcessor()
                predicted_word, confidence, phoneme_confidence = processor.predict_speech(
                    enhanced_file, word_text
                )
                
                # Update UI with results
                if predicted_word and predicted_word.lower() == word_text.lower():
                    # Correct pronunciation
                    mic_button.bgcolor = "#4CAF50"  # Keep green for correct
                    mic_button.content = ft.Icon(name=ft.Icons.CHECK_CIRCLE, color="white", size=40)
                    status_text.value = "Correct pronunciation! Well done."
                else:
                    # Incorrect pronunciation
                    mic_button.bgcolor = "#F44336"  # Red for incorrect
                    mic_button.content = ft.Icon(name=ft.Icons.ERROR, color="white", size=40)
                    status_text.value = f"Try again. You said: {predicted_word or 'unknown'}"
                
                page.update()
                
                # Clean up files
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    if os.path.exists(enhanced_file):
                        os.remove(enhanced_file)
                except Exception as e:
                    logger.warning(f"Error cleaning up files: {e}")
                
                # Reset button after a delay
                time.sleep(2)
                mic_button.bgcolor = "#FFC107"  # Back to yellow
                mic_button.content = ft.Icon(name=ft.Icons.MIC, color="black", size=40)
                status_text.value = "Tap microphone to record"
                page.update()
                
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                # Reset button on error
                mic_button.bgcolor = "#FFC107"  # Back to yellow
                mic_button.content = ft.Icon(name=ft.Icons.MIC, color="black", size=40)
                status_text.value = f"Error processing audio: {str(e)}"
                page.update()
        
        # Run in a separate thread to not block the UI
        threading.Thread(target=stop_and_process).start()
    
    # Attach click handler to mic button
    mic_button.on_click = on_mic_press
    
    # Card content
    card_content = ft.Container(
        content=ft.Column(
            [
                # Instruction text
                ft.Container(
                    content=ft.Text(
                        instruction_text,
                        color="#0078D7",  # Blue color
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    margin=ft.margin.only(bottom=15)
                ),
                
                # Word to pronounce
                ft.Container(
                    content=ft.Row(
                        [
                            # Sound icon
                            ft.Icon(
                                name=ft.Icons.VOLUME_UP_ROUNDED,
                                color="black",
                                size=20
                            ),
                            
                            # Word text
                            ft.Text(
                                word_text,
                                color="black",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10
                    ),
                    margin=ft.margin.only(bottom=10)
                ),
                
                # Translation text
                ft.Container(
                    content=ft.Text(
                        translation_text,
                        color="grey",
                        size=16,
                        italic=True,
                        text_align=ft.TextAlign.CENTER
                    ),
                    margin=ft.margin.only(bottom=30)
                ),
                
                # Microphone button
                ft.Container(
                    content=mic_button,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=15)
                ),
                
                # Status text
                ft.Container(
                    content=status_text,
                    margin=ft.margin.only(bottom=30)
                ),
                
                # Next button
                ft.Container(
                    content=ft.ElevatedButton(
                        text=next_button_text,
                        on_click=next_exercise,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                            color="white",
                            bgcolor="#4CAF50",  # Green
                        ),
                        width=200,
                        height=50,
                    ),
                    alignment=ft.alignment.center,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=page.width,
        padding=ft.padding.all(20),
        margin=ft.margin.only(top=20)
    )
    
    # Main page content
    page.add(
        ft.Column(
            [
                header,
                card_content
            ],
            spacing=0
        )
    )
    
    # Card content
    card_content = ft.Container(
        content=ft.Column(
            [
                # Instruction text
                ft.Container(
                    content=ft.Text(
                        instruction_text,
                        color="#0078D7",  # Blue color
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    margin=ft.margin.only(bottom=15)
                ),
                
                # Word to pronounce
                ft.Container(
                    content=ft.Row(
                        [
                            # Sound icon
                            ft.Icon(
                                name=ft.Icons.VOLUME_UP_ROUNDED,
                                color="black",
                                size=20
                            ),
                            
                            # Word text
                            ft.Text(
                                word_text,
                                color="black",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10
                    ),
                    width=320,
                    bgcolor="#FFF9C4",  # Light yellow background
                    padding=ft.padding.symmetric(vertical=15, horizontal=10),
                    border_radius=10,
                    margin=ft.margin.only(bottom=15)
                ),
                
                # Translation text
                ft.Container(
                    content=ft.Text(
                        translation_text,
                        color="black",
                        size=16,
                        text_align=ft.TextAlign.CENTER
                    ),
                    margin=ft.margin.only(bottom=30)
                ),
                
                # Microphone button
                ft.Container(
                    content=ft.Column(
                        [
                            # Circular yellow button with microphone
                            ft.Container(
                                content=ft.Icon(
                                    name=ft.Icons.MIC,
                                    color="black",
                                    size=40
                                ),
                                width=120,
                                height=120,
                                bgcolor="#FFC107",  # Yellow color
                                border_radius=60,  # Half of width/height for circle
                                alignment=ft.alignment.center,
                                on_click=on_mic_press,
                                margin=ft.margin.only(bottom=20),
                                # Add glow effect with box shadow
                                shadow=ft.BoxShadow(
                                    spread_radius=1,
                                    blur_radius=15,
                                    color=ft.colors.YELLOW_100,
                                    offset=ft.Offset(0, 0)
                                ),
                                # Assign to variable for reference in on_mic_press function
                                ref=lambda ref: setattr(ref.page, "mic_button", ref)
                            ),
                            
                            # "Tap to record" text
                            ft.Text(
                                tap_record_text,
                                color="black",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    margin=ft.margin.only(bottom=30)
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        ),
        padding=ft.padding.only(top=20)
    )
    
    # Progress indicator
    progress = ft.Container(
        content=ft.ProgressBar(value=0.33, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20)
    )
    
    # Bottom navigation
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color="grey",
                        on_click=go_back
                    ),
                    width=100,
                    bgcolor="#F5F5F5",
                    border_radius=ft.border_radius.all(30),
                    padding=5
                ),
                ft.Container(width=10),  # Spacer
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Text(
                            next_button_text,
                            color="white",
                            weight=ft.FontWeight.BOLD,
                            size=16
                        ),
                        style=ft.ButtonStyle(
                            bgcolor={"": "#0078D7"},
                            shape=ft.RoundedRectangleBorder(radius=30),
                        ),
                        width=200,
                        height=50,
                        on_click=next_exercise
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        padding=ft.padding.only(bottom=20)
    )
    
    # Main content column
    main_content = ft.Column(
        [
            header,
            ft.Container(
                content=card_content,
                alignment=ft.alignment.center
            ),
            progress,
            bottom_nav
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
        expand=True
    )
    
    # Add a blue bar at the top
    blue_bar = ft.Container(
        height=10,
        bgcolor="#0078D7",
        width=page.width
    )
    
    # Wrap everything in a stack
    stack = ft.Stack(
        [
            # White background
            ft.Container(bgcolor="white", expand=True),
            # Stack the blue bar and main content
            ft.Column([blue_bar, main_content], spacing=0, expand=True)
        ],
        expand=True
    )
    
    # Add the view to the page
    page.views.append(
        ft.View(
            "/lesson-pronounce",
            [stack],
            padding=0
        )
    )
    
    page.update()