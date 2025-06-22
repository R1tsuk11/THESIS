import flet as ft
import re
import os
import sys
import time
import json
from lessonScore import lesson_score
from flet_audio import Audio # CHECHANGE
import asyncio
import matplotlib.pyplot as plt  # Import for visualization
import base64  # Import for encoding visualization images
from voice_recognition.audio_processing import is_valid_audio, extract_features
from voice_recognition.speech_recognition_utils import SpeechProcessor, capture_audio  # Import the more complete module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from bkt_engine import should_rebatch, select_adaptive_questions, get_vocab_mastery
import threading

correct_answers = {}
incorrect_answers = {}
grade_percentage = 0.0
total_response_time = 0.0
formatted_time = ""
user_library = []

def create_correct_dialog():
    """Create a fresh correct/incorrect dialog for each lesson session"""
    return ft.AlertDialog(
        content=ft.Column(
            [
                ft.Container(content=ft.Icon(size=60), padding=ft.padding.only(top=15)),  # Placeholder for icon
                ft.Container(content=ft.Text(""))        # Placeholder for text
            ],
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        ),
        alignment=ft.alignment.center,
        bgcolor="#F5F5F5"
    )

def get_questions(page):
    """Retrieves questions for the current lesson."""
    level_data = page.session.get("level_data")
    if not level_data:
        print("Level data not found in session.")
        return None

    questions = level_data.questions_answers

    if not questions:
        print("No questions found.")
        return None

    # ENHANCED: Ensure all questions have proper IDs
    for i, q in enumerate(questions):
        q.lesson_id = level_data.lesson_id
        q.module_name = level_data.module_name
        
        # Set ID if missing
        if not hasattr(q, 'id') or q.id is None:
            q.id = f"L{level_data.lesson_id}Q{i+1}"
            print(f"[QUESTION] Assigned ID {q.id} to {getattr(q, 'type', 'Unknown')} question")

    # Pre-load lesson images
    lesson_images = []
    for q in questions:
        if getattr(q, "type", None) == "Lesson" and getattr(q, "image", None):
            lesson_images.append(q.image)
    
    # Add invisible images to the page to trigger preloading
    for img_url in lesson_images:
        page.controls.append(
            ft.Image(src=img_url, visible=False, width=1, height=1)
        )
    page.update()

    print(f"[QUESTIONS] Loaded {len(questions)} questions with proper IDs")
    return questions

def get_user_library():
    try:
        with open("temp_library.json", "r") as f:
            user_library = json.load(f)
            return user_library
    except FileNotFoundError:
        print("Temp library cache not found.")
        return None
    
def update_user_library():
    global user_library
    try:
        with open("temp_library.json", "w") as f:
            json.dump(user_library, f)
    except Exception as e:
        print(f"Error updating library: {e}")

def build_lesson_question(page, question_data, progress_value, on_next, on_back, current_index, user_id=None):
    """Builds the layout for a 'Lesson' type question."""
    # Dynamic image selection based on vocabulary
    vocabulary = question_data.vocabulary.lower() if hasattr(question_data, 'vocabulary') else ""
    lessonImg = question_data.image if hasattr(question_data, 'image') else None
    audioFile = question_data.audio_file if hasattr(question_data, 'audio_file') else None #CHECHANGE
    
    # Print lesson ID for debugging
    print(f"Lesson ID: {getattr(question_data, 'lesson_id')}")
    print(f"Vocabulary: {vocabulary}")

    # START OF CHECHANGE
    m1_audio_urls = [
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572609/maupay_nga_aga_urhv6g.mp3", # Maupay nga aga - 0
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572617/aga_yrse5r.mp3", # Aga - 1
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572604/gihapon_qd9eky.mp3", # Gihapon - 2
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572607/kamusta_ka_tjidng.mp3", # Kamusta ka - 3
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572605/ikaw_h70yiy.mp3", # Ikaw - 4
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572614/okay_la_ako_r9uavj.mp3", # Okay la ako - 5
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572611/maupay_nga_kulop_vdaxud.mp3", # Maupay nga kulop - 6
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572612/maupay_eix9qv.mp3", # Maupay - 7
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572626/diri_brlstl.mp3", # Diri - 8
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572605/it_drrhnr.mp3", # It - 9
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572610/maupay_nga_gabi_nhfibv.mp3", # Maupay nga gabi - 10
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572627/gab-i_e17xsu.mp3", # Gab-i - 11
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572622/ano_it_imo_ngaran_jf1rih.mp3", # Ano it imo ngaran - 12
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572613/ngaran_zuesqm.mp3", # Ngaran - 13
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572618/ako_hi_ovqdlr.mp3", # Ako hi - 14
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572621/damo_nga_salamat_hgathz.mp3", # Damo nga salamat - 15
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749573317/waray_sapayan_qixfxl.mp3", # Waray sapayan - 16
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572616/pasylo-a_ako_l0cvux.mp3", # Pasylo-a ako - 17
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572608/maaram_ka_mag_english_iuws71.mp3", # Maaram ka mag English - 18
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572623/diri_ako_makarit_ha_waray_xoofdv.mp3", # Diri ako makarita ha waray - 19
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572620/ambot_ws7epc.mp3" # Ambot - 20
        ]

    # Create hidden audio instances to force browser preloading
    preloaded_audios = []
    for url in m1_audio_urls:
        preloaded = Audio(src=url)
        preloaded_audios.append(preloaded)
    
    # Autoplay audio for initial load
    autoplay_audio = Audio(src="https://res.cloudinary.com/djm2qhi9f/video/upload/v1749580135/silent_pwwtrp.mp3", autoplay=True)
    
    # Main audio player
    # current_audio_index = 0
    audio_player = Audio(src=audioFile)
    
    # Create overlay with audio components (hidden)
    page.overlay.extend([
        autoplay_audio,     # Add autoplay audio
        *preloaded_audios,  # Add preloaded audio instances
        audio_player,       # Add main audio player
    ])

    def play_audio(e):
        print(f"Playing audio for vocabulary: {vocabulary}")
        print(f"Audio file: {audioFile}")
        audio_player.play()

    # END OF CHECHANGE
    
    print(f"Selected image for '{vocabulary}': {lessonImg}")
    
    start_time = time.time()
    header_text = "Lesson"
    
    # More robust extraction of waray_phrase and english_translation
    waray_phrase = None
    english_translation = None
    full_definition = question_data.question

    # First attempt: extract phrases in single quotes
    matches = re.findall(r"'([^']+)'", full_definition)
    
    # Check if we have the expected pattern with Waray and English in quotes
    if len(matches) >= 2:
        waray_phrase = matches[0]
        english_translation = matches[1]
    else:
        # Second attempt: try to use vocabulary and other patterns
        waray_phrase = question_data.vocabulary
        
        # Different ways to extract English meaning
        # Pattern: "means 'X' in English"
        eng_match = re.search(r"means\s+'([^']+)'", full_definition)
        if eng_match:
            english_translation = eng_match.group(1)
        # Pattern: "means X in English" (without quotes)
        elif "means" in full_definition and "in English" in full_definition:
            parts = full_definition.split("means")[1].split("in English")[0].strip()
            if parts and not parts.startswith("'"):
                english_translation = parts
        # Pattern: check if there's a hyphen/dash with English after
        elif " - " in full_definition:
            english_translation = full_definition.split(" - ")[1].strip()
        # Pattern: check if there's "translation" in the text
        elif "translation" in full_definition.lower():
            parts = full_definition.lower().split("translation")[1].strip()
            if parts.startswith(":"):
                english_translation = parts[1:].strip()
            else:
                english_translation = parts
        else:
            # Last resort - check what's after vocabulary in the question
            vocab_pos = full_definition.find(question_data.vocabulary)
            if vocab_pos > -1:
                rest = full_definition[vocab_pos + len(question_data.vocabulary):].strip()
                if rest.startswith("="):
                    english_translation = rest[1:].strip()
                elif rest.startswith("means"):
                    english_translation = rest[5:].strip()
                else:
                    english_translation = "Translation not available"
            else:
                english_translation = "Translation not available"
    
    # Debug output
    print(f"Waray phrase: '{waray_phrase}'")
    print(f"English translation: '{english_translation}'")
    
    global user_library

    if question_data.vocabulary not in user_library:
        user_library.append(question_data.vocabulary)

    def add_time(e):
        global total_response_time
        response_time = time.time() - start_time
        question_data.response_time = response_time
        total_response_time += response_time

        if on_next:
            on_next(e)

    # Close button header
    header = ft.Container(
        content=ft.Row(
            [
                ft.Container(width=50),  # Spacer
                ft.Container(
                    width=50,
                    content=ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color="#000000",
                        on_click=on_back
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.END
        ),
        padding=ft.padding.only(top=10, right=10)
    )

    card_content = ft.Container(
        content=ft.Column(
            [
                # Header row with dividers and title
                ft.Row(
                    [
                        ft.Container(content=ft.Divider(color="grey", thickness=1), expand=True),
                        ft.Container(
                            content=ft.Text(
                                header_text,
                                color="grey",
                                size=14,
                                weight=ft.FontWeight.W_500
                            ),
                            padding=ft.padding.symmetric(horizontal=10)
                        ),
                        ft.Container(content=ft.Divider(color="grey", thickness=1), expand=True),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                # Waray phrase with volume icon - now wrapping enabled
                ft.Container(
                    content=ft.Row(
                        [
                            ft.IconButton( #CHECHANGE Button with function
                                icon=ft.Icons.VOLUME_UP,
                                icon_color="#0078D7",
                                icon_size=24,
                                on_click=play_audio
                            ),
                            ft.Text(
                                waray_phrase,
                                color="#0078D7",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                                max_lines=3,  # Allow up to 3 lines
                                overflow=ft.TextOverflow.VISIBLE,  # Show all text
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=5,
                        wrap=True  # Enable wrapping
                    ),
                    margin=ft.margin.only(bottom=10)
                ),
                # English translation - now with wrapping
                ft.Container(
                    content=ft.Text(
                        english_translation,
                        color="grey",
                        size=16,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=4,  # Allow up to 4 lines
                        overflow=ft.TextOverflow.VISIBLE
                    ),
                    margin=ft.margin.only(bottom=20)
                ),
                # Image
                ft.Container(
                    content=ft.Image(
                        src=lessonImg,
                        width=300,
                        #height=150,
                        fit=ft.ImageFit.CONTAIN,
                        border_radius=ft.border_radius.all(16)  
                    ),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=20)
                ),
                # Full definition - now with wrapping
                ft.Container(
                    content=ft.Text(
                        full_definition,
                        text_align=ft.TextAlign.CENTER,
                        size=16,
                        weight=ft.FontWeight.W_500,
                        color="#000000",
                        max_lines=8,  # Allow up to 8 lines
                        overflow=ft.TextOverflow.VISIBLE
                    ),
                    margin=ft.margin.only(bottom=20),
                    padding=ft.padding.symmetric(horizontal=10)  # Add horizontal padding
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        ),
        width=312,
        bgcolor="white",
        border_radius=10,
        padding=20,
        margin=ft.margin.symmetric(vertical=20),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.Colors.GREY_400,
            offset=ft.Offset(2, 2)
        )
    )
    
    # Create a ListView for scrollable content
    scrollable_content = ft.ListView(
        controls=[card_content],
        expand=True,
        spacing=0,
        padding=0,
        auto_scroll=False
    )

    # Progress bar
    progress = ft.Container(
        content=ft.ProgressBar(value=progress_value, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20)
    )

    # Navigation controls
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Text("NEXT", color="white", weight=ft.FontWeight.BOLD, size=16),
                        style=ft.ButtonStyle(
                            bgcolor={"": "#0078D7"},
                            shape=ft.RoundedRectangleBorder(radius=25),
                        ),
                        width=280,
                        height=50,
                        on_click=add_time
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        padding=ft.padding.only(bottom=30)
    )

    return ft.Column(
        [
            header,  # Added header with close button  
            # Scrollable content area (takes available space)
            ft.Container(
                content=scrollable_content,
                expand=True,  # This makes it take up available space
                alignment=ft.alignment.center,
                width=312  # Keep the width constrained
            ),
            progress,
            bottom_nav,
    
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )

def build_imgpicker_question(page, question_data, progress_value, on_next, on_back, current_question_index, user_id=None, correctDlg=None):
    start_time = time.time()
    selected_option = {"value": None}  # Use a dict to allow nonlocal mutation in nested functions
    m_one_image = [

        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712836/M1V1_fzmf6o.png", # 0 - M1V1
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712836/M1V2_ebbvj7.png", # 1 - M1V2
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712835/M1V3_fca0i3.png", # 2 - M1V3
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712835/M1V4_czg2wz.png", # 3 - M1V4
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712836/M1V5_ifphew.png", # 4 - M1V5
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712836/M1V6_gpvjj3.png", # 5 - M1V6
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712836/M1V7_s7iuny.png", # 6 - M1V7
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712836/M1V8_obseud.png", # 7 - M1V8
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712837/M1V9_ohh2bf.png", # 8 - M1V9
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712835/M1V10_k3p0za.png", # 9 - M1V10
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712835/M1V11_yn14oe.png", # 10 - M1V11
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712835/M1V12_fvcmkb.png", # 11 - M1V12
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712835/M1V13_rgxhc3.png", # 12 - M1V13
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712836/M1V14_rhov3g.png", # 13 - M1V14
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712835/M1V15_nnsh6x.png", # 14 - M1V15
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747712837/M1V16_yuxzyw.png", # 15 - M1V16
    ]
    question = question_data.question
    correct_answer = question_data.correct_answer
    global user_library

   # Define image variables
    img1 = None
    img2 = None
    
    # Try to get image URLs based on the indices in choices
    try:
        # Check if choices contains numeric indices
        if all(str(choice).isdigit() for choice in question_data.choices):
            try:
                # Try cloudinary URLs first
                img1 = m_one_image[int(question_data.choices[0])]
                img2 = m_one_image[int(question_data.choices[1])]

                print("Using cloudinary URLs for images")
            except (ValueError, IndexError) as e:
                print(f"Cloudinary URL error: {e}")
                raise  # Re-raise to trigger the fallback
        else:
            # Fall back to direct URLs in choices
            img1 = question_data.choices[0]
            img2 = question_data.choices[1]
            
    except Exception as e:
        print(f"Error loading images: {e}")
        # Fallback to local files
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ASSETS_PATH = os.path.join(BASE_DIR, "assets")
        
        # For each choice, try different ways to find the image
        def find_image(choice):
            # Try direct filename
            path = os.path.join(ASSETS_PATH, os.path.basename(str(choice)))
            if os.path.exists(path):
                return path
                
            # Try with extension
            for ext in ['.jpg', '.png', '.jpeg']:
                path = os.path.join(ASSETS_PATH, f"{str(choice)}{ext}")
                if os.path.exists(path):
                    return path
                    
            # Try with underscores instead of spaces
            path = os.path.join(ASSETS_PATH, f"{str(choice).replace(' ', '_')}.png")
            if os.path.exists(path):
                return path
                
            # Last resort - return the choice as is (might be a URL or path)
            return str(choice)
            
        img1 = find_image(question_data.choices[0])
        img2 = find_image(question_data.choices[1])
        
    print("Image 1 src:", img1)
    print("Image 2 src:", img2)

    def on_option_click(e, option_index):
        selected_option["value"] = option_index

        for i, option in enumerate([image_option1, image_option2]):
            if i == selected_option["value"]:
                option.border = ft.border.all(3, "#0078D7")  # Blue border for selected
            else:
                option.border = ft.border.all(1, "#E0E0E0")  # Light gray border
        e.page.update()

    async def handle_next(e):
        response_time = time.time() - start_time
        question_data.response_time = response_time
        global total_response_time
        total_response_time += response_time
        if selected_option["value"] == 0:
            print("User selected Choice 1")
        elif selected_option["value"] == 1:
            print("User selected Choice 2")
        else:
            print("User did not select any image")
            page.open(ft.SnackBar(ft.Text("Please select an answer option."), bgcolor="#FF0000"))
            page.update()
            return

        question_data.answer = question_data.choices[selected_option["value"]]

        if question_data.choices[selected_option["value"]] == correct_answer:
            print("Correct answer!")
            correctDlg.content.controls[0].content = ft.Icon(
                name=ft.icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                color="green",
                size=60
            )
            correctDlg.content.controls[1].content = ft.Text(
                "Correct",
                color="black",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            )
            unique_key = f"{question_data.question}__{question_data.type}__{current_question_index['value']}"
            correct_answers[unique_key] = question_data
            if question_data.vocabulary not in user_library:
                user_library.append(question_data.vocabulary)
        else:
            print("Incorrect answer.")
            correctDlg.content.controls[0].content = ft.Icon(
                name=ft.icons.CLOSE,
                color="red",
                size=60
            )
            correctDlg.content.controls[1].content = ft.Text(
                "Incorrect",
                color="black",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            )
            unique_key = f"{question_data.question}__{question_data.type}__{current_question_index['value']}"
            incorrect_answers[unique_key] = question_data
            if question_data.vocabulary not in user_library:
                user_library.append(question_data.vocabulary)

        try:
            page.open(correctDlg)
            page.update()  # Force UI update
            await asyncio.sleep(1.5)
            page.close(correctDlg)
            page.update()  # Force UI update again
        except Exception as dialog_error:
            print(f"[DIALOG] Error handling dialog: {dialog_error}")
            # Continue without dialog if there's an error
            
        if on_next:
            on_next(e)

    image_option1 = ft.Container(
        content=ft.Image(
            src=img1,
            width=320,
            height=180,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(10),
        ),
        width=320,
        height=180,
        border=ft.border.all(1, "#E0E0E0"),
        border_radius=ft.border_radius.all(10),
        margin=ft.margin.only(bottom=15),
        on_click=lambda e: on_option_click(e, 0)
    )

    image_option2 = ft.Container(
        content=ft.Image(
            src=img2,
            width=320,
            height=180,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(10),
        ),
        width=320,
        height=180,
        border=ft.border.all(1, "#E0E0E0"),
        border_radius=ft.border_radius.all(10),
        margin=ft.margin.only(bottom=15),
        on_click=lambda e: on_option_click(e, 1)
    )

    # Create content for scrollable area
    scrollable_content = ft.Column(
        [
            # Header
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(width=50),
                        ft.Container(
                            width=50,
                            content=ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color="#000000",
                                on_click=on_back
                            )
                        )
                    ],
                    alignment=ft.MainAxisAlignment.END
                ),
                padding=ft.padding.only(top=10, right=10)
            ),

            ft.Container(
                content=ft.Text(
                    "Which image best represents the word?",
                    color="#0078D7",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                margin=ft.margin.only(top=20, bottom=15)
            ),

            # Instruction text
            ft.Container(
                content=ft.Text(
                    question,
                    color="#0078D7",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                margin=ft.margin.only(top=20, bottom=15)
            ),

            # Image choices
            ft.Container(
                content=ft.Column(
                    [image_option1, image_option2],
                    spacing=0
                )
            ),
            
            # Extra space at the bottom to ensure content isn't cut off when scrolling
            ft.Container(height=20)
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.START,
    )
    
    # Make the content scrollable with ListView
    scrollable_area = ft.ListView(
        controls=[scrollable_content],
        expand=True,
        spacing=0,
        padding=0,
        auto_scroll=False
    )

    # Progress bar (fixed position)
    progress_bar = ft.Container(
        content=ft.ProgressBar(value=progress_value, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20, top=10)
    )

    # Navigation buttons (fixed position)
    nav_buttons = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Text(
                            "NEXT",
                            color="white",
                            weight=ft.FontWeight.BOLD,
                            size=16
                        ),
                        style=ft.ButtonStyle(
                            bgcolor={"": "#0078D7"},
                            shape=ft.RoundedRectangleBorder(radius=30),
                        ),
                        width=280, 
                        height=50,
                        on_click=handle_next
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        padding=ft.padding.only(bottom=30)
    )

    return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=scrollable_area,
                        expand=True,
                        width=320,
                        alignment=ft.alignment.center
                    ),
                    progress_bar,
                    nav_buttons
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                expand=True
            ),
            bgcolor="#FFFFFF",  # Set background color to white
            expand=True
        )

def build_wordselect_question(page, question_data, progress_value, on_next, on_back, current_question_index, user_id, correctDlg=None):
    start_time = time.time()
    options = question_data.choices
    word_to_translate = question_data.word_to_translate
    instruction = question_data.question
    selected_option = {"value": None}
    correct_answer = question_data.correct_answer
    global user_library

    def on_option_click(e, option_index, option_containers):
        selected_option["value"] = option_index
        for i, option in enumerate(option_containers):
            option.border = ft.border.all(1, "#000000") if i == option_index else None
        e.page.update()

    async def handle_next(e):
        response_time = time.time() - start_time
        question_data.response_time = response_time
        global total_response_time
        total_response_time += response_time
        if selected_option["value"] == 0:
            print("User selected Choice 1")
        elif selected_option["value"] == 1:
            print("User selected Choice 2")
        elif selected_option["value"] == 2:
            print("User selected Choice 3")
        else:
            print("User did not select any image")
            page.open(ft.SnackBar(ft.Text("Please select an answer option."), bgcolor="#FF0000"))
            page.update()
            return

        question_data.answer = question_data.choices[selected_option["value"]]

        if question_data.choices[selected_option["value"]] == correct_answer:
            print("Correct answer!")
            correctDlg.content.controls[0].content = ft.Icon(
                name=ft.icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                color="green",
                size=60
            )
            correctDlg.content.controls[1].content = ft.Text(
                "Correct",
                color="black",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            )
            unique_key = f"{question_data.question}__{question_data.type}__{current_question_index['value']}"
            correct_answers[unique_key] = question_data
            if question_data.vocabulary not in user_library:
                user_library.append(question_data.vocabulary)
        else:
            print("Incorrect answer.")
            correctDlg.content.controls[0].content = ft.Icon(
                name=ft.icons.CLOSE,
                color="red",
                size=60
            )
            correctDlg.content.controls[1].content = ft.Text(
                "Incorrect",
                color="black",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            )
            unique_key = f"{question_data.question}__{question_data.type}__{current_question_index['value']}"
            incorrect_answers[unique_key] = question_data
            if question_data.vocabulary not in user_library:
                user_library.append(question_data.vocabulary)

        try:
            page.open(correctDlg)
            page.update()  # Force UI update
            await asyncio.sleep(1.5)
            page.close(correctDlg)
            page.update()  # Force UI update again
        except Exception as dialog_error:
            print(f"[DIALOG] Error handling dialog: {dialog_error}")
            # Continue without dialog if there's an error

        page.update()

        if on_next:
            on_next(e)

    # Option containers (created dynamically from the options list)
    option_containers = []
    for i, opt_text in enumerate(options):
        container = ft.Container(
            content=ft.Text(
                opt_text,
                color="#000000",  
                size=18,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
                max_lines=3,  # Allow up to 3 lines
                overflow=ft.TextOverflow.VISIBLE
            ),
            width=320,
            bgcolor="#F5F5F5",
            padding=ft.padding.symmetric(vertical=15),
            border_radius=10,
            margin=ft.margin.only(bottom=10 if i < len(options)-1 else 20),
        )
        container.on_click = lambda e, idx=i: on_option_click(e, idx, option_containers)
        option_containers.append(container)

    scrollable_content = ft.Column(
        [
            # Header with close/back button
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(width=50),
                        ft.Container(
                            width=50,
                            content=ft.IconButton(icon=ft.Icons.CLOSE, icon_color="#000000", on_click=on_back),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
                padding=ft.padding.only(top=10, right=10),
            ),

            # Instruction
            ft.Container(
                content=ft.Text(f"{instruction}:", color="#0078D7", size=17, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                margin=ft.margin.only(top=10)
            ),

            ft.Container(
                content=ft.Text(
                    word_to_translate,
                    color="#000000",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=4,  # Allow multiple lines
                    overflow=ft.TextOverflow.VISIBLE
                ),
                width=320,
                bgcolor="#FFF9C4",
                padding=ft.padding.symmetric(vertical=15, horizontal=10),
                border_radius=10,
                margin=ft.margin.only(bottom=30)
            ),

            # Option buttons
            ft.Column(option_containers),
            
            # Add some extra space at the bottom to prevent cut-off
            ft.Container(height=20)
        ],
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
    
    # Make content scrollable with ListView
    scrollable_area = ft.ListView(
        controls=[scrollable_content],
        expand=True,
        spacing=0,
        padding=0,
        auto_scroll=False
    )

    # Progress bar (fixed position)
    progress_bar = ft.Container(
        content=ft.ProgressBar(value=progress_value, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20)
    )

    # Navigation buttons (fixed position)
    nav_buttons = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Text(
                            "NEXT",
                            color="white",
                            weight=ft.FontWeight.BOLD,
                            size=16
                        ),
                        style=ft.ButtonStyle(
                            bgcolor={"": "#0078D7"},
                            shape=ft.RoundedRectangleBorder(radius=30),
                        ),
                        width=280,  
                        height=50,
                        on_click=handle_next
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        padding=ft.padding.only(bottom=30)
    )

    return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=scrollable_area,
                        expand=True,
                        width=320,
                        alignment=ft.alignment.center
                    ),
                    progress_bar,
                    nav_buttons
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                expand=True
            ),
            bgcolor="#FFFFFF",  # Set background color to white
            expand=True
        )

def build_tf_question(page, question_data, progress_value, on_next, on_back, current_question_index, user_id, correctDlg=None):
    start_time = time.time()
    selected_option = {"value": None}
    correct_answer = question_data.correct_answer
    global user_library

    def on_option_click(e, option_index):
        selected_option["value"] = option_index
        for i, option in enumerate([option1, option2]):
            option.border = ft.border.all(1, "#000000") if i == selected_option["value"] else None
        e.page.update()

    async def handle_next(e):
        response_time = time.time() - start_time
        question_data.response_time = response_time
        global total_response_time
        total_response_time += response_time
        if selected_option["value"] == 0:
            print("Selected option: True")
        elif selected_option["value"] == 1:
            print("Selected option: False")
        else:
            print("No option selected")
            page.open(ft.SnackBar(ft.Text("Please select an answer option."), bgcolor="#FF0000"))
            page.update()
            return

        question_data.answer = question_data.choices[selected_option["value"]]

        if question_data.choices[selected_option["value"]] == correct_answer:
            print("Correct answer!")
            correctDlg.content.controls[0].content = ft.Icon(
                name=ft.icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                color="green",
                size=60
            )
            correctDlg.content.controls[1].content = ft.Text(
                "Correct",
                color="black",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            )
            unique_key = f"{question_data.question}__{question_data.type}__{current_question_index['value']}"
            correct_answers[unique_key] = question_data
            if question_data.vocabulary not in user_library:
                user_library.append(question_data.vocabulary)
        else:
            print("Incorrect answer.")
            correctDlg.content.controls[0].content = ft.Icon(
                name=ft.icons.CLOSE,
                color="red",
                size=60
            )
            correctDlg.content.controls[1].content = ft.Text(
                "Incorrect",
                color="black",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            )
            unique_key = f"{question_data.question}__{question_data.type}__{current_question_index['value']}"
            incorrect_answers[unique_key] = question_data
            if question_data.vocabulary not in user_library:
                user_library.append(question_data.vocabulary)

        try:
            page.open(correctDlg)
            page.update()  # Force UI update
            await asyncio.sleep(1.5)
            page.close(correctDlg)
            page.update()  # Force UI update again
        except Exception as dialog_error:
            print(f"[DIALOG] Error handling dialog: {dialog_error}")
            # Continue without dialog if there's an error

        page.update()

        if on_next:
            on_next(e)

    # UI Elements
    question_text = question_data.question
    option1_text = question_data.choices[0]
    option2_text = question_data.choices[1]

    option1 = ft.Container(
        content=ft.Text(option1_text, color="#000000", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        width=320,
        bgcolor="#F5F5F5",
        padding=ft.padding.symmetric(vertical=15),
        border_radius=10,
        margin=ft.margin.only(bottom=10),
        on_click=lambda e: on_option_click(e, 0)
    )

    option2 = ft.Container(
        content=ft.Text(option2_text, color="#000000", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        width=320,
        bgcolor="#F5F5F5",
        padding=ft.padding.symmetric(vertical=15),
        border_radius=10,
        margin=ft.margin.only(bottom=20),
        on_click=lambda e: on_option_click(e, 1)
    )

    # Header with close/back button
    header = ft.Container(
        content=ft.Row(
            [
                ft.Container(width=50),
                ft.Container(
                    width=50,
                    content=ft.IconButton(icon=ft.Icons.CLOSE, icon_color="#000000", on_click=on_back),
                ),
            ],
            alignment=ft.MainAxisAlignment.END,
        ),
        padding=ft.padding.only(top=10, right=10),
    )

    # Content with question and options
    card_content = ft.Container(
        content=ft.Column(
            [
                ft.Text("TRUE OR FALSE", color="#0078D7", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Container(
                    content=ft.Text(
                        question_text,
                        color="#000000",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=6,  # Allow up to 6 lines
                        overflow=ft.TextOverflow.VISIBLE
                    ),
                    width=320,
                    bgcolor="#FFF9C4",
                    padding=ft.padding.symmetric(vertical=15, horizontal=10),
                    border_radius=10,
                    margin=ft.margin.only(bottom=30)
                ),
                option1,
                option2
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        padding=ft.padding.only(top=20)
    )

    # Progress bar
    progress_bar = ft.Container(
        content=ft.ProgressBar(value=progress_value, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20)
    )

    # Bottom navigation
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Text("NEXT", color="white", weight=ft.FontWeight.BOLD, size=16),
                        style=ft.ButtonStyle(
                            bgcolor={"": "#0078D7"},
                            shape=ft.RoundedRectangleBorder(radius=30),
                        ),
                        width=280,  
                        height=50,
                        on_click=handle_next
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=ft.padding.only(bottom=30),
    )

    # Main layout with stack for white background
    return ft.Stack(
        [
            ft.Container(bgcolor="white", expand=True),
            ft.Column([
                # Blue bar on top (fixed)
                # ft.Container(height=10, bgcolor="#0078D7", width=50),

                # Main content with three sections
                ft.Column(
                    [
                        # Header with close button
                        header,
                        
                        # Scrollable content area
                        ft.Container(
                            content=card_content,
                            expand=True,
                            width=320,  # Fixed width
                            alignment=ft.alignment.center
                        ),
                        
                        # Fixed progress bar
                        progress_bar,
                        
                        # Fixed bottom navigation
                        bottom_nav
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True
                )
            ], spacing=0, expand=True)
        ],
        expand=True
    )

def build_trivia_question(question_data, progress_value, on_next, on_back):
    # Extract data
    trivia_text = question_data.question
    start_time = time.time()

    def add_time(e):
        response_time = time.time() - start_time
        question_data.response_time = response_time
        global total_response_time
        total_response_time += response_time

        if on_next:
            on_next(e)

    # Close button header
    header = ft.Container(
        content=ft.Row(
            [
                ft.Container(width=50),  # Spacer
                ft.Container(
                    width=50,
                    content=ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color="#000000",
                        on_click=on_back
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.END
        ),
        padding=ft.padding.only(top=10, right=10)
    )

    # Card content
    card_content = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(content=ft.Divider(color="grey", thickness=1), width=60),
                        ft.Container(
                            content=ft.Text(question_data.type, color="grey", size=14, weight=ft.FontWeight.W_500),
                            padding=ft.padding.symmetric(horizontal=10)
                        ),
                        ft.Container(content=ft.Divider(color="grey", thickness=1), width=60),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Container(
                    content=ft.Text(
                        trivia_text,
                        text_align=ft.TextAlign.CENTER,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color="#0078D7",
                        max_lines=10,  # Allow up to 10 lines
                        overflow=ft.TextOverflow.VISIBLE
                    ),
                    margin=ft.margin.only(top=20, bottom=20),
                    padding=ft.padding.symmetric(horizontal=20)
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        ),
        width=312,
        bgcolor="white",
        border_radius=10,
        padding=20,
        margin=ft.margin.only(top=20, bottom=20)
    )

    # Create a ListView for scrollable content
    scrollable_content = ft.ListView(
        controls=[card_content],
        expand=True,
        spacing=0,
        padding=0,
        auto_scroll=False
    )

    # Progress bar
    progress = ft.Container(
        content=ft.ProgressBar(value=progress_value, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20)
    )

    # Navigation controls - removed back button and adjusted next button width
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Text("NEXT", color="white", weight=ft.FontWeight.BOLD, size=16),
                        style=ft.ButtonStyle(
                            bgcolor={"": "#0078D7"},
                            shape=ft.RoundedRectangleBorder(radius=25),
                        ),
                        width=280,
                        height=50,
                        on_click=add_time
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        padding=ft.padding.only(bottom=30)
    )

    return ft.Column(
        [
            header,
            # Scrollable content area (takes available space)
            ft.Container(
                content=scrollable_content,
                expand=True,
                alignment=ft.alignment.center,
                width=312  # Keep the width constrained
            ),
            progress,
            bottom_nav
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )

def build_translate_sentence_question(page, question_data, progress_value, on_next, on_back, current_question_index, user_id, correctDlg=None):
    start_time = time.time()
    options = question_data.choices
    word_to_translate = question_data.question
    selected_option = {"value": None}
    correct_answer = question_data.correct_answer
    global user_library

    def on_option_click(e, option_index, option_containers):
        selected_option["value"] = option_index
        for i, option in enumerate(option_containers):
            option.border = ft.border.all(1, "#000000") if i == option_index else None
        e.page.update()

    async def handle_next(e):
        response_time = time.time() - start_time
        question_data.response_time = response_time
        global total_response_time
        total_response_time += response_time
        if selected_option["value"] == 0:
            print("User selected Choice 1")
        elif selected_option["value"] == 1:
            print("User selected Choice 2")
        elif selected_option["value"] == 2:
            print("User selected Choice 3")
        else:
            print("User did not select any image")
            page.open(ft.SnackBar(ft.Text("Please select an answer option."), bgcolor="#FF0000"))
            page.update()
            return

        question_data.answer = question_data.choices[selected_option["value"]]

        if question_data.choices[selected_option["value"]] == correct_answer:
            print("Correct answer!")
            correctDlg.content.controls[0].content = ft.Icon(
                name=ft.icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                color="green",
                size=60
            )
            correctDlg.content.controls[1].content = ft.Text(
                "Correct",
                color="black",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            )
            unique_key = f"{question_data.question}__{question_data.type}__{current_question_index['value']}"
            correct_answers[unique_key] = question_data
            if question_data.vocabulary not in user_library:
                user_library.append(question_data.vocabulary)
        else:
            print("Incorrect answer.")
            correctDlg.content.controls[0].content = ft.Icon(
                name=ft.icons.CLOSE,
                color="red",
                size=60
            )
            correctDlg.content.controls[1].content = ft.Text(
                "Incorrect",
                color="black",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            )
            unique_key = f"{question_data.question}__{question_data.type}__{current_question_index['value']}"
            incorrect_answers[unique_key] = question_data
            if question_data.vocabulary not in user_library:
                user_library.append(question_data.vocabulary)

        try:
            page.open(correctDlg)
            page.update()  # Force UI update
            await asyncio.sleep(1.5)
            page.close(correctDlg)
            page.update()  # Force UI update again
        except Exception as dialog_error:
            print(f"[DIALOG] Error handling dialog: {dialog_error}")
            # Continue without dialog if there's an error
        
        page.update()

        if on_next:
            on_next(e)

    # Option containers (created dynamically from the options list)
    option_containers = []
    for i, opt_text in enumerate(options):
        container = ft.Container(
            content=ft.Text(
                opt_text,
                color="#000000",  
                size=18,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
                max_lines=3,  # Allow up to 3 lines
                overflow=ft.TextOverflow.VISIBLE
            ),
            width=320,
            bgcolor="#F5F5F5",
            padding=ft.padding.symmetric(vertical=15),
            border_radius=10,
            margin=ft.margin.only(bottom=10 if i < len(options)-1 else 20),
        )
        container.on_click = lambda e, idx=i: on_option_click(e, idx, option_containers)
        option_containers.append(container)

    scrollable_content = ft.Column(
        [
            # Header with close/back button
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(width=50),
                        ft.Container(
                            width=50,
                            content=ft.IconButton(icon=ft.Icons.CLOSE, icon_color="#000000", on_click=on_back),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
                padding=ft.padding.only(top=10, right=10),
            ),

            # Instruction
            ft.Container(
                content=ft.Text("Translate to Waray:", color="#0078D7", size=17, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                margin=ft.margin.only(top=10)
            ),

            ft.Container(
                content=ft.Text(
                    word_to_translate,
                    color="#000000",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=4,  # Allow multiple lines
                    overflow=ft.TextOverflow.VISIBLE
                ),
                width=320,
                bgcolor="#FFF9C4",
                padding=ft.padding.symmetric(vertical=15, horizontal=10),
                border_radius=10,
                margin=ft.margin.only(bottom=30)
            ),

            # Option buttons
            ft.Column(option_containers),
            
            # Add some extra space at the bottom to prevent cut-off
            ft.Container(height=20)
        ],
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
    
    # Make content scrollable with ListView
    scrollable_area = ft.ListView(
        controls=[scrollable_content],
        expand=True,
        spacing=0,
        padding=0,
        auto_scroll=False
    )

    # Progress bar (fixed position)
    progress_bar = ft.Container(
        content=ft.ProgressBar(value=progress_value, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20)
    )

    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Text("NEXT", color="white", weight=ft.FontWeight.BOLD, size=16),
                        style=ft.ButtonStyle(
                            bgcolor={"": "#0078D7"},
                            shape=ft.RoundedRectangleBorder(radius=30),
                        ),
                        width=280,  
                        height=50,
                        on_click=handle_next
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=ft.padding.only(bottom=30),
    )
    
    # Main layout with fixed top bar, scrollable content, and fixed bottom elements
    return ft.Stack(
        [
            ft.Container(bgcolor="white", expand=True),
            ft.Column([
                # Blue bar on top (fixed)
                # ft.Container(height=10, bgcolor="#0078D7", width=50),

                # Main content with three sections
                ft.Column(
                    [
                        # 1. Scrollable content area
                        ft.Container(
                            content=scrollable_area,
                            expand=True,
                            width=320,  # Fixed width
                            alignment=ft.alignment.center
                        ),
                        
                        # 2. Fixed progress bar
                        progress_bar,
                        
                        # 3. Fixed bottom navigation
                        bottom_nav
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True
                )
            ], spacing=0, expand=True)
        ],
        expand=True
    )

def build_pronounce_question(page, question_data, progress_value, on_next, on_back, current_index, user_id):
    start_time = time.time()
    question_text = question_data.question
    vocabulary = question_data.vocabulary.lower() if hasattr(question_data, 'vocabulary') else ""
    audioFile = question_data.audio_file if hasattr(question_data, 'audio_file') else None #CHECHANGE

    
    # Check if the question is specifically asking for a subword (like "aga" from "Maupay nga aga")
    # This is often in the question text: "How do you pronounce 'aga'?"
    target_word = vocabulary
    question_text = question_data.question.lower()
    
    # Try to extract the specific word to pronounce from the question
    if "pronounce" in question_text and "'" in question_text:
        # Extract word between single quotes
        quoted_parts = re.findall(r"'([^']+)'", question_text)
        if quoted_parts:
            target_word = quoted_parts[0].lower()
            print(f"Pronunciation target extracted from question: '{target_word}'")
    
    # Set the actual word to recognize
    recognition_target = target_word
    print(f"Will recognize pronunciation for: '{recognition_target}'")
    accuracy_threshold = getattr(question_data, 'accuracy_threshold', 0.6)
    
    # Remove the incorrect Page._current reference
    # Instead, we'll use the page reference from the update function context
    
    # Create speech processor with error handling
    try:
        # Use explicit paths to ensure files are found
        script_dir = os.path.dirname(os.path.abspath(__file__))
        proj_dir = os.path.abspath(os.path.join(script_dir, '../../'))
        model_path = os.path.join(proj_dir, 'waray_speech_model.keras')
        encoder_path = os.path.join(proj_dir, 'encoder_classes.npy')
        
        speech_processor = SpeechProcessor(model_path=model_path, encoder_path=encoder_path)
        model_available = speech_processor.model is not None
    except Exception as e:
        print(f"Error loading speech processor: {str(e)}")
        model_available = False
        speech_processor = None

    recording = {"is_recording": False, "audio_data": None, "file_path": None}
    transcription = {"text": "", "accuracy": 0.0}

    # New UI 
    txt_transcription = ft.Text("Tap to record", color="black", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    txt_accuracy = ft.Text("", size=16, text_align=ft.TextAlign.CENTER)
    pronunciation_tips = ft.Text("", size=14, color="orange", visible=False, text_align=ft.TextAlign.CENTER)
    pronunciation_chart = ft.Image(visible=False)

    # Define mic_icon as a mutable container
    mic_icon = ft.Container(
        content=ft.Icon(
            name=ft.Icons.MIC,
            color="black",
            size=40
        ),
        alignment=ft.alignment.center,
    )
    # Yellow Microphone Button
    button_mic = ft.Container(
        content=mic_icon,
        width=120,
        height=120,
        bgcolor="#FFC107", 
        border_radius=60,  
        alignment=ft.alignment.center,
        on_click=lambda e: start_recording(e),
        # Glow effect 
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.YELLOW_100,
            offset=ft.Offset(0, 0)
        )
    )
    # START OF CHECHANGE
    m1_audio_urls = [
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572609/maupay_nga_aga_urhv6g.mp3", # Maupay nga aga - 0
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572617/aga_yrse5r.mp3", # Aga - 1
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572604/gihapon_qd9eky.mp3", # Gihapon - 2
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572607/kamusta_ka_tjidng.mp3", # Kamusta ka - 3
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572605/ikaw_h70yiy.mp3", # Ikaw - 4
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572614/okay_la_ako_r9uavj.mp3", # Okay la ako - 5
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572611/maupay_nga_kulop_vdaxud.mp3", # Maupay nga kulop - 6
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572612/maupay_eix9qv.mp3", # Maupay - 7
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572626/diri_brlstl.mp3", # Diri - 8
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572605/it_drrhnr.mp3", # It - 9
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572610/maupay_nga_gabi_nhfibv.mp3", # Maupay nga gabi - 10
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572627/gab-i_e17xsu.mp3", # Gab-i - 11
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572622/ano_it_imo_ngaran_jf1rih.mp3", # Ano it imo ngaran - 12
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572613/ngaran_zuesqm.mp3", # Ngaran - 13
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572618/ako_hi_ovqdlr.mp3", # Ako hi - 14
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572621/damo_nga_salamat_hgathz.mp3", # Damo nga salamat - 15
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749573317/waray_sapayan_qixfxl.mp3", # Waray sapayan - 16
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572616/pasylo-a_ako_l0cvux.mp3", # Pasylo-a ako - 17
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572608/maaram_ka_mag_english_iuws71.mp3", # Maaram ka mag English - 18
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572623/diri_ako_makarit_ha_waray_xoofdv.mp3", # Diri ako makarita ha waray - 19
            "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572620/ambot_ws7epc.mp3" # Ambot - 20
        ]

    # START OF CHECHANGE
    # Create hidden audio instances to force browser preloading
    preloaded_audios = []
    for url in m1_audio_urls:
        preloaded = Audio(src=url)
        preloaded_audios.append(preloaded)
    
    # Autoplay audio for initial load
    autoplay_audio = Audio(src="https://res.cloudinary.com/djm2qhi9f/video/upload/v1749580135/silent_pwwtrp.mp3", autoplay=True)
    
    # Main audio player
    # current_audio_index = 0
    audio_player = Audio(src=audioFile)
    
    # Create overlay with audio components (hidden)
    page.overlay.extend([
        autoplay_audio,     # Add autoplay audio
        *preloaded_audios,  # Add preloaded audio instances
        audio_player,       # Add main audio player
    ])
    

    def on_sound_click(e): 
        print("Sound clicked") #Placeholder for sound playback functionality
        audio_player.play()

    # END OF CHECHANGE
    
    # Import threading here to avoid issues
    import threading

    def start_recording(e):
        button_mic.disabled = True
        button_mic.bgcolor = "#FF9800"  # Darker yellow when recording
        mic_icon.content = ft.ProgressRing(width=40, height=40, color="black")  # Show loading spinner
        txt_transcription.value = "Loading..."
        txt_accuracy.value = ""
        pronunciation_tips.visible = False
        pronunciation_chart.visible = False
        e.page.update()
        
        recording["is_recording"] = True
        threading.Thread(target=lambda: record_audio(e.page)).start()

    def record_audio(page):

        time.sleep(2.5)
        # Update UI to show listening state
        mic_icon.content = ft.Icon(
            name=ft.Icons.MIC,
            color="black",
            size=40
        )  # Restore mic icon
        txt_transcription.value = "Listening..."
        page.update()


        if not model_available:
            # Simulate audio processing when model isn't available
            time.sleep(2)
            txt_transcription.value = vocabulary  # Assume correct for demo
            txt_accuracy.value = "Model not available - simulating correct pronunciation"
            txt_accuracy.color = "orange"
            button_mic.disabled = False
            button_mic.bgcolor = "#FFC107"
            button_mic.icon_color = "white"
            page.update()
            return
            
        try:
            recording["file_path"] = capture_audio(duration=3)
            
            if recording["file_path"] and os.path.exists(recording["file_path"]):
                process_recording(page)
            else:
                txt_transcription.value = "No audio detected. Please try again."
                txt_accuracy.value = ""
                button_mic.bgcolor = "#FFC107"  # Reset button color
                button_mic.disabled = False
                page.update()
        except Exception as e:
            txt_transcription.value = f"Error recording audio: {str(e)}"
            button_mic.bgcolor = "#FFC107"  # Reset button color
            button_mic.disabled = False
            page.update()
        finally:
            recording["is_recording"] = False
            
    def process_recording(page):
        if not model_available:
            return
            
        try:
            # Pass the target_word instead of vocabulary
            predicted_word, confidence, phoneme_confidence = speech_processor.predict_speech(
                recording["file_path"], recognition_target
            )

            button_mic.bgcolor = "#FFC107"  # Reset button color
            
            # Compare with the specific target word not the full vocabulary
            if predicted_word:
                txt_transcription.value = f"You said: {predicted_word}"
                
                # Get any pronunciation errors from the NLTK analysis that was performed
                nltk_errors = getattr(speech_processor, 'pronunciation_errors', [])
                
                if predicted_word.lower() == recognition_target.lower():
                    accuracy = confidence if confidence else 0.75
                    txt_accuracy.value = f"Accuracy: {accuracy:.0%}"
                    
                    if accuracy >= accuracy_threshold:
                        txt_accuracy.color = "green"
                        question_data.accuracy = accuracy
                        
                        # Show detailed phoneme feedback
                        if phoneme_confidence:
                            # Identify problematic phonemes
                            problem_phonemes = [(p, s) for p, s in phoneme_confidence.items() if s < 0.7]
                            if problem_phonemes:
                                feedback_text = "Work on: "
                                feedback_text += ", ".join([f"{p} ({s:.0%})" for p, s in problem_phonemes])
                                
                                # Add NLTK analysis if available
                                if nltk_errors:
                                    feedback_text += "\n\nGoogle analysis: " + "\n• ".join([""] + nltk_errors)
                                    
                                pronunciation_tips.value = feedback_text
                                pronunciation_tips.visible = True
                            else:
                                pronunciation_tips.visible = False
                                
                            # Generate and display visualization
                            viz_buffer = visualize_pronunciation_feedback(vocabulary, phoneme_confidence)
                            if viz_buffer:
                                pronunciation_chart.src_base64 = base64.b64encode(viz_buffer.read()).decode('utf-8')
                                pronunciation_chart.visible = True
                    else:
                        txt_accuracy.color = "orange"
                        question_data.accuracy = accuracy
                        
                        # Show pronunciation tips for specific syllables
                        if phoneme_confidence:
                            problem_syllables = speech_processor._identify_problem_syllables(
                                [(p, s) for p, s in phoneme_confidence.items() if s < 0.7],
                                speech_processor._map_phonemes_to_syllables(vocabulary.lower())
                            )
                            
                            feedback_text = ""
                            if problem_syllables:
                                feedback_text = f"Focus on syllables: {', '.join(problem_syllables)}"
                            
                            # Add NLTK analysis if available
                            if nltk_errors:
                                if feedback_text:
                                    feedback_text += "\n\nGoogle analysis: " + "\n• ".join([""] + nltk_errors)
                                else:
                                    feedback_text = "Google analysis: " + "\n• ".join([""] + nltk_errors)
                            
                            pronunciation_tips.value = feedback_text
                            pronunciation_tips.visible = bool(feedback_text)
                else:
                    txt_transcription.value = f"You said: {predicted_word}. Try saying '{target_word}'"
                    txt_accuracy.value = f"Incorrect word detected"
                    txt_accuracy.color = "red"
                    question_data.accuracy = 0.0
                    
                    # Show general pronunciation tips with NLTK analysis
                    feedback_text = "Try again, focusing on clear pronunciation"
                    
                    if nltk_errors:
                        feedback_text += "\n\nPronunciation analysis: " + "\n• ".join([""] + nltk_errors)
                    
                    pronunciation_tips.value = feedback_text
                    pronunciation_tips.visible = True
                    pronunciation_chart.visible = False
            else:
                txt_transcription.value = "Speech not recognized clearly. Please try again."
                txt_accuracy.value = ""
                question_data.accuracy = 0.0
                pronunciation_tips.visible = False
                pronunciation_chart.visible = False
                
        except Exception as e:
            txt_transcription.value = f"Error processing speech: {str(e)}"
            txt_accuracy.value = ""
            button_mic.bgcolor = "#FFC107"  # Reset button color
            pronunciation_tips.visible = False
            pronunciation_chart.visible = False
            
        finally:
            button_mic.disabled = False
            button_mic.bgcolor = "#FFC107"  # Reset button color
            page.update()
            
            # Clean up temp file
            try:
                if recording["file_path"] and os.path.exists(recording["file_path"]):
                    os.remove(recording["file_path"])
            except Exception:
                pass

    def handle_next(e):
        response_time = time.time() - start_time
        question_data.response_time = response_time
        global total_response_time
        total_response_time += response_time
        
        if not question_data.accuracy:
            question_data.accuracy = 0.0
            
        if question_data.accuracy >= accuracy_threshold:
            print(f"Pronunciation accepted with accuracy: {question_data.accuracy:.2f}")
            correct_answers[question_data.question] = question_data
        else:
            print(f"Pronunciation below threshold: {question_data.accuracy:.2f}")
            incorrect_answers[question_data.question] = question_data
            
        if on_next:
            on_next(e)

    
    # Main UI Layout
    # Close Button Func
    header = ft.Container(
        content=ft.Row(
            [
                ft.Container(width=50),  
                ft.Container(
                    width=50, 
                    content=ft.IconButton(
                        icon=ft.Icons.CLOSE, 
                        icon_color="black",
                        on_click=on_back
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.END
        ),
        padding=ft.padding.only(top=10, right=10)
    )
    
    card_content = ft.Container(
        content=ft.Column(
            [
                # Instruction text
                ft.Container(
                    content=ft.Text(
                        "Pronounce the word:",
                        color="#0078D7",  
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    margin=ft.margin.only(bottom=15)
                ),
                
                # Word to pronounce with sound icon
                ft.Container(
                    content=ft.Row(
                        [
                            # Sound icon (BUTTON)
                            ft.IconButton(
                                icon=ft.Icons.VOLUME_UP_ROUNDED,
                                icon_color="black",
                                icon_size=20,
                                on_click=on_sound_click
                            ),
                            
                            # Word text
                            ft.Text(
                                target_word.title(),
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
                
                # Translation or question text
                ft.Container(
                    content=ft.Text(
                        question_text,
                        color="black",
                        size=16,
                        text_align=ft.TextAlign.CENTER
                    ),
                    margin=ft.margin.only(bottom=30)
                ),
                
                # Microphone button section
                ft.Container(
                    content=ft.Column(
                        [
                            button_mic,
                            ft.Container(height=20),  # Spacer
                            txt_transcription
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Accuracy display
                ft.Container(
                    txt_accuracy,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=10)
                ),
                
                # Pronunciation tips
                ft.Container(
                    pronunciation_tips,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=10)
                ),
                
                # Pronunciation chart
                ft.Container(
                    pronunciation_chart,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=20)
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        ),
        padding=ft.padding.only(top=20)
    )

    progress = ft.Container(
        ft.ProgressBar(value=progress_value, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20)
    )

    # Bottom navigation
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Text("NEXT", color="white", weight=ft.FontWeight.BOLD, size=16),
                        style=ft.ButtonStyle(
                            bgcolor={"": "#0078D7"},
                            shape=ft.RoundedRectangleBorder(radius=30),
                        ),
                        width=280,  
                        height=50,
                        on_click=handle_next
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=ft.padding.only(bottom=30),
    )

    return ft.Container(
        bgcolor="white",
        content=ft.Column(
            [
                header,
                ft.Container(
                    content=ft.ListView(  # Use ListView instead of Column with scroll
                        controls=[
                            ft.Container(
                                content=card_content,
                                alignment=ft.alignment.center
                            ),
                            progress,
                            bottom_nav
                        ],
                        spacing=20,
                        padding=ft.padding.all(20)
                    ),
                    expand=True,
                    height=None  # Let it take available space
                )
            ],
            expand=True
        ),
        expand=True
    )

def visualize_pronunciation_feedback(word, phoneme_confidence):
    """Generate a visual representation of pronunciation accuracy for each phoneme."""
    if not phoneme_confidence:
        return None
        
    # Create figure
    fig, ax = plt.figure(figsize=(10, 3)), plt.gca()
    
    # Colors for different confidence levels
    colors = ['#ff6b6b', '#ffa06b', '#ffd46b', '#d4ff6b', '#6bff6b']
    
    # Create bars for each phoneme
    phonemes = list(phoneme_confidence.keys())
    scores = list(phoneme_confidence.values())
    
    # Create bars with color gradients based on score
    bars = ax.bar(phonemes, scores, color=[colors[min(int(s*5), 4)] for s in scores])
    
    # Add labels
    ax.set_ylim(0, 1.1)
    ax.set_title(f"Pronunciation Analysis for '{word}'")
    ax.set_ylabel("Confidence Score")
    ax.set_xlabel("Phonemes")
    
    # Add threshold line
    ax.axhline(y=0.7, linestyle='--', color='gray', alpha=0.7)
    ax.text(len(phonemes)/2, 0.72, "Acceptable Threshold", ha='center', va='bottom', color='gray')
    
    # Add problem indicators
    for i, score in enumerate(scores):
        if score < 0.7:
            ax.text(i, score + 0.05, "!", ha='center', va='bottom', color='red', fontweight='bold')
    
    # Save to buffer
    from io import BytesIO
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    
    return buf  # Return buffer for display in GUI

def cleanup_lesson_session(page):
    """Clean up lesson session resources"""
    try:
        # Clear any open dialogs
        if hasattr(page, 'overlay') and page.overlay:
            page.overlay.clear()
        
        # Cancel any active threads (though most should be daemon threads)
        import threading
        active_threads = threading.active_count()
        print(f"[CLEANUP] Active threads before cleanup: {active_threads}")
        
        # Clear session data
        global correct_answers, incorrect_answers, user_library
        correct_answers.clear()
        incorrect_answers.clear()
        user_library.clear()
        
        # Force page update
        page.update()
        
        print("[CLEANUP] Lesson session cleaned up successfully")
        
    except Exception as e:
        print(f"[CLEANUP] Error during cleanup: {e}")

def lesson_page(page: ft.Page, image_urls: list):
    page.title = "Arami - Lesson"
    page.padding = 0
    performance_tracker = {}  # Track performance during lesson
    rebatching_needed = False

    correctDlg = create_correct_dialog()
    
    # Clear any existing overlays to prevent conflicts
    if hasattr(page, 'overlay'):
        # Remove any existing dialogs
        page.overlay.clear()

    def render_question_layout(page, question_data, progress_value, on_next, on_back, current_index, user_id=None):
        question_type = question_data.type
        
        if question_type == "Lesson":
            return build_lesson_question(page, question_data, progress_value, on_next, on_back, current_index, user_id)
        elif question_type == "Image Picker":
            return build_imgpicker_question(page, question_data, progress_value, on_next, on_back, current_index, user_id, correctDlg)
        elif question_type == "Word Select":
            return build_wordselect_question(page, question_data, progress_value, on_next, on_back, current_index, user_id, correctDlg)
        elif question_type == "True or False":
            return build_tf_question(page, question_data, progress_value, on_next, on_back, current_index, user_id, correctDlg)
        elif question_type == "Cultural Trivia":
            return build_trivia_question(question_data, progress_value, on_next, on_back)
        elif question_type == "Pronunciation":
            return build_pronounce_question(page, question_data, progress_value, on_next, on_back, current_index, user_id)
        elif question_type == "Translate Sentence":
            return build_translate_sentence_question(page, question_data, progress_value, on_next, on_back, current_index, user_id, correctDlg)
        else:
            return ft.Text("Unknown question type.")

    # Initialize BKT engine
    import bkt_engine
    user_id = page.session.get("user_id")
    if user_id is not None:
        bkt_engine.uid = user_id
        print(f"[USER] Set global BKT user ID to: {user_id}")
        
        # IMPORTANT: Initialize the lesson BKT session
        try:
            from lesson_bkt_engine import get_session_bkt
            session = get_session_bkt(user_id)
            if session:
                print(f"[LessonBKT] Initialized session for user {user_id}")
            else:
                print(f"[LessonBKT] Warning: Could not initialize session for user {user_id}")
        except Exception as e:
            print(f"[LessonBKT] Error initializing session: {e}")

    from bkt_engine import update_current_vocab
    bkt_engine.current_vocab = None  # Reset current vocabulary tracking
    bkt_engine.questions_seen = set()  # Reset questions seen tracking

    # EXIT ALERT
    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text(
            "Are you sure you want to leave?",
            size=20,
            color="black",
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        content=ft.Text(
            "Your progress will be lost.",
            size=14,
            color="black",
            text_align=ft.TextAlign.CENTER,
        ),
        actions=[
            ft.TextButton("Yes", 
                          style=ft.ButtonStyle(color=ft.Colors.BLUE),
                          on_click=lambda e: [cleanup_lesson_session(page), page.go("/levels")]),
            ft.TextButton("No", 
                          style=ft.ButtonStyle(color=ft.Colors.BLUE), 
                          on_click=lambda e: page.close(dlg_modal)),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )
    
    def get_user_overall_proficiency(user_id):
        """Get user's overall proficiency from database"""
        try:
            import pymongo
            arami = pymongo.MongoClient("mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/")["arami"]
            users_col = arami["users"]
            
            user_doc = users_col.find_one({"user_id": int(user_id)})
            if user_doc:
                proficiency = user_doc.get("proficiency", 0.5)
                if isinstance(proficiency, dict):
                    proficiency = proficiency.get("proficiency", 0.5)
                
                # Convert to 0-1 scale if needed
                if proficiency > 1.0:
                    proficiency = proficiency / 100.0
                
                # Ensure valid range
                proficiency = max(0.01, min(1.0, proficiency))
                return proficiency
                
        except Exception as e:
            print(f"[Proficiency] Error getting proficiency: {e}")
        
        return 0.5  # Default

    def apply_initial_difficulty_adjustment(questions, overall_proficiency):
        """Apply initial difficulty based on overall proficiency to ALL questions"""
        print(f"[LESSON] Applying initial difficulty adjustment based on proficiency: {overall_proficiency:.3f}")
        
        # Determine base difficulty range based on overall proficiency
        if overall_proficiency < 0.2:          # Very low (0-20%)
            base_range = [1, 2]  # Easy questions only
            adjustment_message = "Very low proficiency - starting with easy questions"
        elif overall_proficiency < 0.4:       # Low (20-40%)
            base_range = [1, 2, 3]  # Easy to medium
            adjustment_message = "Low proficiency - starting with easy-medium questions"
        elif overall_proficiency < 0.6:       # Medium (40-60%)
            base_range = [2, 3, 4]  # Medium questions
            adjustment_message = "Medium proficiency - starting with medium questions"
        elif overall_proficiency < 0.8:       # High (60-80%)
            base_range = [3, 4, 5]  # Medium to hard
            adjustment_message = "High proficiency - starting with medium-hard questions"
        else:                                  # Very high (80-100%)
            base_range = [4, 5]  # Hard questions only
            adjustment_message = "Very high proficiency - starting with hard questions"
        
        print(f"[LESSON] {adjustment_message}")
        print(f"[LESSON] Initial difficulty range: {base_range}")
        
        # Apply to all practice questions (skip lesson and cultural trivia)
        questions_adjusted = 0
        for question in questions:
            q_type = getattr(question, 'type', '')
            if q_type not in ['Lesson', 'Cultural Trivia']:
                # Assign difficulty from base range (cycling through if needed)
                difficulty = base_range[questions_adjusted % len(base_range)]
                question.difficulty = difficulty
                questions_adjusted += 1
                
                vocab = getattr(question, 'vocabulary', 'Unknown')
                print(f"[LESSON] Set initial difficulty {difficulty} for {q_type} - {vocab}")
        
        print(f"[LESSON] Applied initial difficulty to {questions_adjusted} questions")

    def go_back(e):
    # Show exit dialog instead of immediately navigating back
        page.open(dlg_modal)
        page.update()
        # page.go("/levels")

    # Background with landscape image
    background = ft.Container(
        content=ft.Image(
            src=image_urls[8],
            width=page.width,
            height=page.height,
            fit=ft.ImageFit.COVER
        ),
        expand=True
    )
    
    def handle_question_progression(current_index, questions, current_question):
        """Handle progression to next question with proper vocabulary grouping"""
        
        current_vocab = getattr(current_question, 'vocabulary', '')
        current_type = getattr(current_question, 'type', '')
        
        print(f"[PROGRESSION] Current: {current_type} - {current_vocab}")
        
        # If this is a lesson question, go to first practice of same vocab
        if current_type == 'Lesson':
            next_index = find_first_practice_question(current_index, questions, current_vocab)
            if next_index is not None:
                print(f"[PROGRESSION] Moving from lesson to practice: index {next_index}")
                return next_index
        
        # If this is a practice question, check if more practice needed for this vocab
        elif current_type in ['Word Select', 'Translate Sentence', 'True or False', 'Image Picker', 'Pronunciation']:
            # Check if this vocabulary section is complete
            if is_vocabulary_section_complete(current_index, questions, current_vocab):
                next_index = find_next_lesson_question(current_index, questions)
                if next_index is not None:
                    print(f"[PROGRESSION] Vocabulary complete, moving to next lesson: index {next_index}")
                    return next_index
        
        # Default: just go to next question
        return current_index + 1

    def find_first_practice_question(lesson_index, questions, vocabulary):
        """Find the first practice question for a given vocabulary after lesson"""
        for i in range(lesson_index + 1, len(questions)):
            q = questions[i]
            q_vocab = getattr(q, 'vocabulary', '')
            q_type = getattr(q, 'type', '')
            
            if q_vocab == vocabulary and q_type != 'Lesson':
                return i
        return None

    def find_next_lesson_question(current_index, questions):
        """Find the next lesson question after current position"""
        for i in range(current_index + 1, len(questions)):
            q = questions[i]
            q_type = getattr(q, 'type', '')
            
            if q_type == 'Lesson':
                return i
        return None

    def is_vocabulary_section_complete(current_index, questions, vocabulary):
        """Check if all practice questions for a vocabulary are complete"""
        # Count remaining questions for this vocabulary
        remaining_same_vocab = 0
        for i in range(current_index + 1, len(questions)):
            q = questions[i]
            q_vocab = getattr(q, 'vocabulary', '')
            q_type = getattr(q, 'type', '')
            
            if q_vocab == vocabulary and q_type != 'Lesson':
                remaining_same_vocab += 1
            elif q_type == 'Lesson':  # Hit next lesson
                break
        
        # For now, consider complete after each question (you can adjust this logic)
        # You might want to check performance_tracker here instead
        return remaining_same_vocab == 0

    def debug_question_sequence(questions):
        """Debug function to show question sequence"""
        print("\n[DEBUG] Question Sequence:")
        current_vocab = None
        
        for i, q in enumerate(questions):
            vocab = getattr(q, 'vocabulary', 'Unknown')
            q_type = getattr(q, 'type', 'Unknown')
            difficulty = getattr(q, 'difficulty', 'None')
            
            # IMPROVED: Better ID handling
            q_id = getattr(q, 'id', None)
            if q_id is None:
                # Try to get ID from question data or assign based on position
                q_id = f"Q{i+1}"
            
            # Show vocabulary breaks
            if vocab != current_vocab:
                if current_vocab is not None:
                    print("  " + "-" * 50)
                current_vocab = vocab
                print(f"  VOCABULARY: {vocab}")
            
            print(f"    {i+1:2d}. ID:{str(q_id):6s} {q_type:15s} (diff: {difficulty})")
        
        print("  " + "-" * 50)
        print()

    def create_proper_lesson_sequence(lesson_questions):
        """Create a proper sequence that follows vocabulary sections"""
        vocabulary_groups = group_questions_by_vocabulary(lesson_questions)
        
        # Create sequence: Lesson -> Practice questions for that vocab -> Next Lesson -> etc.
        proper_sequence = []
        
        for vocab, questions in vocabulary_groups.items():
            # Find the lesson question (difficulty = None or type = "Lesson")
            lesson_q = None
            practice_qs = []
            
            for q in questions:
                if getattr(q, 'type', '') == 'Lesson' or getattr(q, 'difficulty', None) is None:
                    lesson_q = q
                else:
                    practice_qs.append(q)
            
            # Add lesson first, then practice questions
            if lesson_q:
                proper_sequence.append(lesson_q)
            proper_sequence.extend(practice_qs)
        
        return proper_sequence

    def get_next_question_in_sequence(current_index, questions):
        """Get the next question following the proper vocabulary sequence"""
        
        if current_index >= len(questions) - 1:
            return None
        
        current_question = questions[current_index]
        current_vocab = getattr(current_question, 'vocabulary', '')
        current_type = getattr(current_question, 'type', '')
        
        # If current is a lesson, next should be first practice question of same vocab
        if current_type == 'Lesson':
            for i in range(current_index + 1, len(questions)):
                next_q = questions[i]
                next_vocab = getattr(next_q, 'vocabulary', '')
                next_type = getattr(next_q, 'type', '')
                
                # Find first practice question of same vocabulary
                if next_vocab == current_vocab and next_type != 'Lesson':
                    return i
        
        # Otherwise, just return next question
        return current_index + 1

    def initialize_question_sequence():
        """Initialize and debug the question sequence"""
        print(f"[LESSON] Loaded {len(questions)} questions")
        
        # Debug the sequence
        debug_question_sequence(questions)
        
        # Verify vocabulary groupings
        vocab_counts = {}
        for q in questions:
            vocab = getattr(q, 'vocabulary', 'Unknown')
            q_type = getattr(q, 'type', 'Unknown')
            
            if vocab not in vocab_counts:
                vocab_counts[vocab] = {}
            
            vocab_counts[vocab][q_type] = vocab_counts[vocab].get(q_type, 0) + 1
        
        print("\n[LESSON] Vocabulary distribution:")
        for vocab, types in vocab_counts.items():
            print(f"  {vocab}: {dict(types)}")
        print()

    def group_questions_by_vocabulary(questions):
        """Group questions by vocabulary to ensure proper progression"""
        vocabulary_groups = {}
        
        for question in questions:
            vocab = getattr(question, 'vocabulary', 'Unknown')
            if vocab not in vocabulary_groups:
                vocabulary_groups[vocab] = []
            vocabulary_groups[vocab].append(question)
        
        # Sort each group by difficulty
        for vocab in vocabulary_groups:
            vocabulary_groups[vocab].sort(key=lambda x: getattr(x, 'difficulty', 0) or 0)
        
        return vocabulary_groups

    def get_full_question_pool_for_rebatching(page):
        """Get the full question pool for the current lesson from qbank using your existing structure"""
        try:
            # Get current lesson info from session (same way get_questions does it)
            level_data = page.session.get("level_data")
            if not level_data:
                print("[REBATCH] No level_data found in session")
                return []
            
            # ENHANCED: Get the ORIGINAL full pool before any filtering
            # This should give us access to ALL difficulties for each vocabulary
            all_questions = level_data.questions_answers
            
            if not all_questions:
                print("[REBATCH] No questions found in level_data")
                return []
            
            print(f"[REBATCH] Found {len(all_questions)} questions in full pool")
            
            # IMPROVED: Try to get access to the original qbank data
            try:
                # Import and access the original qbank module
                import sys
                import os
                qbank_path = os.path.join(os.path.dirname(__file__), 'qbank.py')
                
                if os.path.exists(qbank_path):
                    # Get the current lesson/module info
                    lesson_id = getattr(level_data, 'lesson_id', None)
                    module_name = getattr(level_data, 'module_name', None)
                    
                    print(f"[REBATCH] Looking for additional questions: lesson_id={lesson_id}, module={module_name}")
                    
                    # Try to import qbank and get more questions
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("qbank", qbank_path)
                    qbank_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(qbank_module)
                    
                    # Get the module data (e.g., module_1)
                    if hasattr(qbank_module, 'module_1'):
                        module_data = qbank_module.module_1
                        
                        # Find the lesson key (e.g., "Lesson 3")
                        lesson_key = f"Lesson {lesson_id}"
                        if lesson_key in module_data:
                            qbank_questions = module_data[lesson_key]
                            print(f"[REBATCH] Found {len(qbank_questions)} questions in qbank for {lesson_key}")
                            
                            # Convert qbank questions to objects if needed
                            from types import SimpleNamespace
                            additional_questions = []
                            
                            for q_data in qbank_questions:
                                if isinstance(q_data, dict):
                                    q_obj = SimpleNamespace(**q_data)
                                    # Set lesson metadata
                                    q_obj.lesson_id = lesson_id
                                    q_obj.module_name = module_name
                                    additional_questions.append(q_obj)
                            
                            # Merge with existing questions (avoid duplicates)
                            existing_ids = {getattr(q, 'id', None) for q in all_questions}
                            for q in additional_questions:
                                if getattr(q, 'id', None) not in existing_ids:
                                    all_questions.append(q)
                            
                            print(f"[REBATCH] Total questions after qbank merge: {len(all_questions)}")
                            
            except Exception as qbank_error:
                print(f"[REBATCH] Could not access qbank: {qbank_error}")
            
            # Group questions by vocabulary and difficulty to see what's available
            vocab_difficulties = {}
            for q in all_questions:
                vocab = getattr(q, 'vocabulary', 'Unknown')
                difficulty = getattr(q, 'difficulty', None)
                q_type = getattr(q, 'type', 'Unknown')
                
                if vocab not in vocab_difficulties:
                    vocab_difficulties[vocab] = {}
                
                if q_type not in vocab_difficulties[vocab]:
                    vocab_difficulties[vocab][q_type] = []
                
                if difficulty is not None:
                    vocab_difficulties[vocab][q_type].append(difficulty)
            
            # Log available difficulties for debugging
            print(f"[REBATCH] Available question pool breakdown:")
            for vocab, types in vocab_difficulties.items():
                for q_type, difficulties in types.items():
                    if difficulties:  # Only show if there are actual difficulties
                        unique_diffs = sorted(set(difficulties))
                        print(f"  {vocab} - {q_type}: difficulties {unique_diffs}")
            
            return all_questions
            
        except Exception as e:
            print(f"[REBATCH] Error getting question pool: {e}")
            import traceback
            traceback.print_exc()
            return []
        
    def select_question_by_difficulty(vocab, question_type, target_difficulty, all_questions):
        """Select a question of specific difficulty for a vocabulary and type"""
        
        # Find all questions matching vocab and type
        matching_questions = []
        for q in all_questions:
            q_vocab = getattr(q, 'vocabulary', '').lower()
            q_type = getattr(q, 'type', '')
            q_difficulty = getattr(q, 'difficulty', None)
            
            if (q_vocab == vocab.lower() and 
                q_type == question_type and 
                q_difficulty is not None):
                matching_questions.append((q, q_difficulty))
        
        if not matching_questions:
            print(f"[QUESTION_SELECT] No {question_type} questions found for '{vocab}' in question pool")
            return None
        
        # IMPROVED: First try to find exact difficulty match
        exact_matches = [(q, diff) for q, diff in matching_questions if diff == target_difficulty]
        
        if exact_matches:
            # Found exact match - return the first one
            selected_question = exact_matches[0][0]
            actual_difficulty = exact_matches[0][1]
            print(f"[QUESTION_SELECT] Found EXACT match for {question_type} '{vocab}': target {target_difficulty}, got {actual_difficulty}")
            return selected_question
        
        # No exact match - find closest difficulty
        matching_questions.sort(key=lambda x: abs(x[1] - target_difficulty))
        best_match = matching_questions[0]
        selected_question = best_match[0]
        actual_difficulty = best_match[1]
        
        print(f"[QUESTION_SELECT] Found CLOSEST match for {question_type} '{vocab}': target {target_difficulty}, got {actual_difficulty}")
        
        return selected_question

    def apply_rebatched_difficulties_to_remaining_questions(current_index, questions, difficulty_change, page):
        """Apply rebatched difficulties and actually select appropriate questions from the current lesson pool"""
        
        try:
            # Get the full question pool using your existing structure
            full_question_pool = get_full_question_pool_for_rebatching(page)
            
            if not full_question_pool:
                print("[REBATCH] Cannot rebatch - no question pool available")
                return
            
            print(f"[REBATCH] Full question pool: {len(full_question_pool)} questions")
            
            # Apply rebatching to remaining questions
            remaining_questions = questions[current_index + 1:]
            rebatched_count = 0
            actually_replaced_count = 0
            
            for i, question in enumerate(remaining_questions):
                q_type = getattr(question, 'type', '')
                if q_type in ['Lesson', 'Cultural Trivia']:
                    continue  # Skip non-practice questions
                
                vocab = getattr(question, 'vocabulary', '')
                current_difficulty = getattr(question, 'difficulty', 2)
                target_difficulty = max(1, min(5, current_difficulty + difficulty_change))
                
                print(f"[REBATCH] Processing {q_type} - {vocab}: current diff {current_difficulty} → target {target_difficulty}")
                
                # Try to find a better question with the target difficulty
                better_question = select_question_by_difficulty(vocab, q_type, target_difficulty, full_question_pool)
                
                if better_question and getattr(better_question, 'difficulty', None) != current_difficulty:
                    # Replace the question with the better one ONLY if it's actually different
                    actual_index = current_index + 1 + i
                    
                    # Preserve the lesson_id and module_name from the original question
                    original_lesson_id = getattr(questions[actual_index], 'lesson_id', None)
                    original_module_name = getattr(questions[actual_index], 'module_name', None)
                    
                    questions[actual_index] = better_question
                    new_difficulty = getattr(better_question, 'difficulty', target_difficulty)
                    
                    # Restore the lesson metadata
                    if original_lesson_id:
                        questions[actual_index].lesson_id = original_lesson_id
                    if original_module_name:
                        questions[actual_index].module_name = original_module_name
                    
                    actually_replaced_count += 1
                    print(f"[REBATCH] ✓ REPLACED {q_type} - {vocab}: difficulty {current_difficulty} → {new_difficulty}")
                else:
                    # Just update the difficulty if no better question found or same question
                    question.difficulty = target_difficulty
                    print(f"[REBATCH] ✓ UPDATED {q_type} - {vocab}: difficulty {current_difficulty} → {target_difficulty} (same question)")
                
                rebatched_count += 1
            
            print(f"[REBATCH] Successfully rebatched {rebatched_count} questions ({actually_replaced_count} actually replaced)")
            
        except Exception as e:
            print(f"[REBATCH] Error in rebatching: {e}")
            import traceback
            traceback.print_exc()

    def check_vocabulary_completion_and_rebatch(vocab, current_index, questions, performance_tracker, overall_proficiency, page):
        """Check if vocabulary is completed and trigger rebatching if needed"""
        
        if vocab not in performance_tracker:
            return False
        
        answers = performance_tracker[vocab]["answers"]
        
        # Check if we have enough answers to consider this vocabulary "completed"
        if len(answers) < 3:
            return False
        
        print(f"[REBATCH] Vocabulary '{vocab}' completed with {len(answers)} answers")
        
        # Calculate performance metrics
        accuracy = sum(answers) / len(answers)
        performance_level = "excellent" if accuracy >= 0.9 else "good" if accuracy >= 0.75 else "moderate" if accuracy >= 0.5 else "poor"
        
        print(f"[REBATCH] Performance for '{vocab}': {accuracy:.1%} ({performance_level})")
        
        # Get remaining questions (those not yet seen)
        remaining_questions = questions[current_index + 1:]
        if not remaining_questions:
            print("[REBATCH] No remaining questions to rebatch")
            return False
        
        # CRITICAL: Determine new difficulty adjustment based on performance
        if accuracy >= 0.9:  # Excellent performance (90%+)
            difficulty_change = +2  # Much harder
            change_message = "Excellent performance - increasing difficulty significantly"
        elif accuracy >= 0.75:  # Good performance (75%+)
            difficulty_change = +1  # Harder
            change_message = "Good performance - increasing difficulty"
        elif accuracy >= 0.5:  # Moderate performance (50%+)
            difficulty_change = 0   # Same
            change_message = "Moderate performance - maintaining difficulty"
        else:  # Poor performance (<50%)
            difficulty_change = -1  # Easier
            change_message = "Poor performance - decreasing difficulty"
        
        print(f"[REBATCH] {change_message} (change: {difficulty_change:+d})")
        
        # ENHANCED: Apply rebatching with actual question replacement, passing page object
        apply_rebatched_difficulties_to_remaining_questions(current_index, questions, difficulty_change, page)
        
        return True

    def assign_question_difficulty(question, user_id):
        """Assign difficulty to a question - now uses pre-set difficulty from rebatching"""
        try:
            # CRITICAL: Never assign difficulty to lesson questions
            q_type = getattr(question, 'type', 'Unknown')
            if q_type == "Lesson":
                question.difficulty = None
                print(f"[QUESTION] Lesson question - no difficulty assigned")
                return
            
            # Check if difficulty is already set (from initial setup or rebatching)
            if hasattr(question, 'difficulty') and question.difficulty is not None:
                vocab = getattr(question, 'vocabulary', 'Unknown')
                print(f"[QUESTION] Using pre-set difficulty {question.difficulty} for {q_type} - {vocab}")
                return
            
            # Fallback: set default difficulty if somehow not set
            question.difficulty = 2  # Default to medium
            print(f"[QUESTION] Applied fallback difficulty 2 for {getattr(question, 'vocabulary', 'Unknown')}")
            
        except Exception as e:
            print(f"[QUESTION] Error in assign_question_difficulty: {e}")
            question.difficulty = 2  # Default to medium

    # Load questions
    questions = get_questions(page)
    initialize_question_sequence()
    global user_library
    user_library = get_user_library()

    user_id = page.session.get("user_id")
    overall_proficiency = get_user_overall_proficiency(user_id)
    
    print(f"[LESSON] User {user_id} overall proficiency: {overall_proficiency:.3f}")
    
    # ENHANCED: Apply initial difficulty adjustment to ALL questions based on overall proficiency
    apply_initial_difficulty_adjustment(questions, overall_proficiency)

    total_questions = len(questions)
    weighted_questions = [q for q in questions if getattr(q, 'correct_answer', None) is not None]
    current_question_index = {"value": 0}
    progress_value = (current_question_index["value"] + 1) / total_questions

    if not questions:
        page.views.append(ft.View("/lesson", [ft.Text("No questions available.")]))
        return

    def render_current_question(progress_value):
        page.views.clear()  # Optional: clear previous view
        question = questions[current_question_index["value"]]
        
        # IMPORTANT: Get user_id from the page session
        user_id = page.session.get("user_id")
        
        # CRITICAL FIX: Only assign difficulty if it's a lesson question OR if difficulty is not set
        q_type = getattr(question, 'type', 'Unknown')
        
        if q_type == "Lesson":
            # Lesson questions should NOT have difficulty
            question.difficulty = None
            print(f"[QUESTION] Lesson question - no difficulty assigned for {getattr(question, 'vocabulary', 'Unknown')}")
        elif not hasattr(question, 'difficulty') or question.difficulty is None:
            # Only assign if not already set by rebatching
            assign_question_difficulty(question, user_id)
        else:
            # Use pre-set difficulty from rebatching
            vocab = getattr(question, 'vocabulary', 'Unknown')
            print(f"[QUESTION] Using rebatched difficulty {question.difficulty} for {q_type} - {vocab}")
        
        # Initialize performance tracking for this vocabulary
        vocab = getattr(question, "vocabulary", "").lower()
        if vocab and vocab not in performance_tracker:
            performance_tracker[vocab] = {"answers": [], "predicted_mastery": getattr(question, "predicted_mastery", 0.5)}
            
        content = render_question_layout(
            page = page,
            question_data=question,
            progress_value=progress_value,
            on_next=next_question,
            on_back=go_back,
            current_index = current_question_index,
            user_id=user_id
        )

        page.views.append(
            ft.View(
                "/lesson",
                [ft.Stack([background, content], expand=True)],
                padding=0
            )
        )
        page.update()
    
    def next_question(e=None):
        """Handle moving to next question with BKT integration and proper vocabulary progression"""
        
        # Get the current question
        current_question = questions[current_question_index["value"]]

        # Calculate response time for this question
        response_time = getattr(current_question, 'response_time', None)
        
        # Log difficulty and vocabulary information
        difficulty = getattr(current_question, "difficulty", "N/A")
        vocab = getattr(current_question, "vocabulary", "Unknown").lower()
        q_type = getattr(current_question, "type", "Unknown")
        
        # Get user ID
        user_id = page.session.get("user_id")
        
        print(f"[DEBUG] Processing question {current_question_index['value']+1}: {q_type} - {vocab} " +
            f"(Difficulty: {difficulty}, Response Time: {response_time:.2f}s)" if response_time else 
            f"(Difficulty: {difficulty})")
        
        # ENHANCED: Handle vocabulary progression logic
        current_vocab = getattr(current_question, 'vocabulary', '')
        current_type = getattr(current_question, 'type', '')
        
        print(f"[PROGRESSION] Current question: {current_type} - {current_vocab}")
            
        # Track performance for this vocabulary using the new lesson BKT engine
        if vocab and q_type != "Lesson" and q_type != "Cultural Trivia":
            try:
                # Check if the question was answered correctly
                unique_key = f"{current_question.question}__{current_question.type}__{current_question_index['value']}"
                is_correct = unique_key in correct_answers
                
                # Initialize vocabulary tracking if needed
                if vocab not in performance_tracker:
                    performance_tracker[vocab] = {"answers": [], "predicted_mastery": 0.5}
                
                # Add answer to performance tracker
                performance_tracker[vocab]["answers"].append(1 if is_correct else 0)
                
                # Process with the lesson BKT engine - NOW WITH RESPONSE TIME
                from lesson_bkt_engine import process_lesson_question
                
                # Process the question answer with response time
                mastery = process_lesson_question(user_id, unique_key, current_question, is_correct, response_time)
                
                if isinstance(mastery, float):
                    time_info = f" (response: {response_time:.2f}s)" if response_time else ""
                    print(f"[LessonBKT] Updated mastery for '{vocab}': {mastery:.3f}{time_info}")
                else:
                    print(f"[LessonBKT] Warning: Unexpected return type: {type(mastery)}")
                    mastery = 0.5
                
                # Continue with rebatching logic...
                if len(performance_tracker[vocab]["answers"]) >= 3:
                    print(f"[BKT] Vocabulary '{vocab}' completed with {len(performance_tracker[vocab]['answers'])} answers!")
                    
                    # Get performance summary
                    answers = performance_tracker[vocab]["answers"]
                    accuracy = sum(answers) / len(answers) if answers else 0
                    performance_level = "excellent" if accuracy >= 0.9 else "good" if accuracy >= 0.75 else "moderate" if accuracy >= 0.5 else "poor"
                    
                    print(f"[LessonBKT] Performance summary for '{vocab}': {accuracy:.1%} ({performance_level})")
                    
                    # UPDATED: Trigger rebatching with page object
                    overall_proficiency = get_user_overall_proficiency(user_id)
                    rebatch_triggered = check_vocabulary_completion_and_rebatch(
                        vocab, 
                        current_question_index["value"], 
                        questions, 
                        performance_tracker, 
                        overall_proficiency,
                        page  # ADDED: Pass page object
                    )
                    
                    if rebatch_triggered:
                        print(f"[REBATCH] Successfully rebatched remaining questions based on '{vocab}' performance")
                    
            except ImportError as e:
                print(f"[BKT] Import error: {e}")
            except Exception as e:
                print(f"[BKT] Error processing question: {e}")

        # ENHANCED: Smart progression logic
        next_index = handle_question_progression(current_question_index["value"], questions, current_question)
        
        if next_index is None:
            # End of lesson
            complete_lesson_and_calculate_grade(user_id)
            return
        
        # Move to the determined next question
        current_question_index["value"] = next_index
        progress_value = (current_question_index["value"] + 1) / total_questions
        
        if current_question_index["value"] < len(questions):
            render_current_question(progress_value)
        else:
            complete_lesson_and_calculate_grade(user_id)

    def complete_lesson_and_calculate_grade(user_id):
        """Handle lesson completion with BKT session saving - SAVE ONCE ONLY"""
        try:
            # IMPORTANT: Save the lesson BKT session ONCE at the very end
            from lesson_bkt_engine import save_session_to_database, reset_session
            
            # Calculate grade first
            print("\n--- LESSON COMPLETION DIAGNOSTIC ---")
            print(f"Total questions: {total_questions}")
            
            # Track question types to ensure proper counting
            question_types = {}
            for q in questions:
                q_type = getattr(q, "type", "Unknown")
                question_types[q_type] = question_types.get(q_type, 0) + 1
            print(f"Questions by type: {question_types}")
            
            # Calculate how many questions were actually graded
            actually_presented = current_question_index["value"]
            actually_weighted_count = len([q for q in questions[:actually_presented] if (
                getattr(q, 'type', "") not in ["Lesson", "Cultural Trivia"] and 
                (getattr(q, 'correct_answer', None) is not None or getattr(q, 'type', "") == "Pronunciation")
            )])

            print(f"Actually weighted questions presented: {actually_weighted_count}")
            print(f"Correct answers: {len(correct_answers)}")
            print(f"Incorrect answers: {len(incorrect_answers)}")

            # Calculate grade based on how many questions were correctly answered
            if actually_weighted_count > 0:
                grade_percentage = round((len(correct_answers) / actually_weighted_count) * 100, 2)
                grade_percentage = min(grade_percentage, 100)
            else:
                grade_percentage = 0
                
            print(f"Final grade percentage: {grade_percentage}%")
                    
            formatted_time = f"{int(total_response_time // 60)}:{int(total_response_time % 60):02d}"
            correct_answers_serialized = {k: v.__dict__ if hasattr(v, "__dict__") else v for k, v in correct_answers.items()}
            incorrect_answers_serialized = {k: v.__dict__ if hasattr(v, "__dict__") else v for k, v in incorrect_answers.items()}
            page.session.set("updated_data", [grade_percentage, formatted_time, total_response_time, correct_answers_serialized, incorrect_answers_serialized, questions])
            update_user_library()

            # Register vocabulary with SuperMemo
            if user_id:
                print("[SuperMemo] Collecting vocabulary for batch registration")
                
                # Collect all unique vocabulary words
                vocab_to_register = set()
                for q_id, q_data in correct_answers.items():
                    vocab = q_data.vocabulary if hasattr(q_data, 'vocabulary') else q_data.get('vocabulary')
                    if vocab:
                        vocab_to_register.add(vocab)
                        
                # Register them in a separate thread
                def register_vocab_batch(user_id, vocab_list):
                    try:
                        from supermemo_engine import register_new_vocabulary_batch
                        register_new_vocabulary_batch(user_id, list(vocab_list))
                    except Exception as e:
                        print(f"[SuperMemo] Error registering vocabulary: {e}")
                        
                # Start the registration thread
                import threading
                registration_thread = threading.Thread(
                    target=register_vocab_batch, 
                    args=(user_id, vocab_to_register),
                    daemon=True
                )
                registration_thread.start()
            
            # Show lesson score
            lesson_score(page, grade_percentage, correct_answers, incorrect_answers, formatted_time)
            reset_var()
            
        except Exception as e:
            print(f"[LESSON] Error in lesson completion: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to original completion logic
            lesson_score(page, 0, correct_answers, incorrect_answers, "0:00")
            reset_var()

    def check_rebatch_need(vocab, current_index):
        nonlocal rebatching_needed
        
        # Skip if we already decided to rebatch
        if rebatching_needed:
            return
            
        # Check if rebatching is needed
        should_rebatch_result, trigger_vocab = should_rebatch({
            vocab: performance_tracker[vocab]
        })
        
        if should_rebatch_result:
            print(f"[BKT] Rebatching needed due to performance for '{trigger_vocab}'")
            rebatching_needed = True
            
            # Get remaining questions (those not yet seen)
            remaining_questions = questions[current_index+1:]
            if not remaining_questions:
                print("[BKT] No remaining questions to rebatch")
                return
                
            # Group questions by vocabulary to preserve structure
            vocab_groups = {}
            for q in remaining_questions:
                q_vocab = getattr(q, "vocabulary", "").lower()
                if q_vocab not in vocab_groups:
                    vocab_groups[q_vocab] = []
                vocab_groups[q_vocab].append(q)
                
            # Re-select questions for each vocabulary group
            new_batch = []
            for vocab_name, vocab_questions in vocab_groups.items():
                # Pass relevant performance data for this vocab
                vocab_performance = {
                    vocab_name: performance_tracker.get(vocab_name, {"answers": [], "predicted_mastery": 0.4})
                }
                
                # Select adaptive questions for this vocabulary group
                rebatched_group = select_adaptive_questions(vocab_questions, vocab_performance)
                new_batch.extend(rebatched_group)
                
            # Replace remaining questions with new batch
            questions[current_index+1:] = new_batch
            print(f"[BKT] Rebatched {len(new_batch)} questions while preserving lesson structure")

    def get_vocabulary_from_question(question):
        """Extract vocabulary from question object consistently"""
        if not question:
            return None
        
        # Try different attributes that might contain the vocabulary
        if hasattr(question, 'vocabulary'):
            return question.vocabulary
        elif hasattr(question, 'word_to_translate'):
            return question.word_to_translate
        elif isinstance(question, dict):
            return question.get('vocabulary') or question.get('word_to_translate')
        
        return None

    def reset_var():
        current_question_index["value"] = 0
        global correct_answers, incorrect_answers, total_response_time, formatted_time, grade_percentage
        total_response_time = 0
        formatted_time = "0:00"
        grade_percentage = 0 
        correct_answers.clear()
        incorrect_answers.clear()

    render_current_question(progress_value)


