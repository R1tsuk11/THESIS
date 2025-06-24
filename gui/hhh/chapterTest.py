import flet as ft
import os
import time
import json
import sys
import asyncio
import pymongo
from lessonScore import lesson_score
import matplotlib.pyplot as plt  # Import for visualization
import base64  # Import for encoding visualization images
from voice_recognition.audio_processing import is_valid_audio, extract_features
from voice_recognition.speech_recognition_utils import SpeechProcessor, capture_audio  # Import the more complete module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

correct_answers = {}
incorrect_answers = {}
grade_percentage = 0.0
total_response_time = 0.0
formatted_time = ""
id = 0
user_library = []  # Add this line
uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

correctDlg = ft.AlertDialog(
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

class Question:
    def __init__(self, data):
        self.id = data.get("id")
        self.type = data.get("type")
        self.question = data.get("question")
        self.choices = data.get("choices")
        self.correct_answer = data.get("correct_answer")
        self.vocabulary = data.get("vocabulary")
        self.difficulty = data.get("difficulty")
        self.response_time = data.get("response_time")
        # ADD THIS LINE:
        self.word_to_translate = data.get("word_to_translate")  # Handle word_to_translate attribute
        # Also add other potential attributes that might be missing:
        self.audio_file = data.get("audio_file")
        self.accuracy_threshold = data.get("accuracy_threshold", 0.6)
        self.accuracy = data.get("accuracy", 0.0)

def get_test_data(page):
    ct_data = page.session.get("ct_data")
    if not ct_data:
        print("Chapter Test data not found.")
        return None

    global id
    id = ct_data.module_id
    questions_raw = ct_data.questions_answers
    if not questions_raw:
        print("Chapter Test has no questions stored.")
        return None

    # Convert each dict to a Question object
    question_objects = [Question(qdata) for qtext, qdata in questions_raw.items()]
    return question_objects

def sanitize_keys(d):
    import re
    if isinstance(d, dict):
        return {re.sub(r"[^\w\-]", "_", k): sanitize_keys(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [sanitize_keys(i) for i in d]
    else:
        return d

def build_imgpicker_question(page, question_data, progress_value, on_next, on_back, current_question_index):
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

        page.open(correctDlg)
        await asyncio.sleep(1.5)
        page.close(correctDlg)

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

def build_wordselect_question(page, question_data, progress_value, on_next, on_back, current_question_index):
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

        page.open(correctDlg)
        await asyncio.sleep(1.5)
        page.close(correctDlg)

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

def build_tf_question(page, question_data, progress_value, on_next, on_back, current_question_index):
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

        page.open(correctDlg)
        await asyncio.sleep(1.5)
        page.close(correctDlg)

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

def build_translate_sentence_question(page, question_data, progress_value, on_next, on_back, current_question_index):
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

        page.open(correctDlg)
        await asyncio.sleep(1.5)
        page.close(correctDlg)

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

def build_pronounce_question(page, question_data, progress_value, on_next, on_back):
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
    accuracy_threshold = getattr(question_data, 'accuracy_threshold', 0.75)
    
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
                    txt_transcription.value = f"You said: {predicted_word}. Try saying '{vocabulary}'"
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
            
        # CRITICAL FIX: Use the same composite key format as other questions
        unique_key = f"{question_data.question}__{question_data.type}__{current_index['value']}"
        
        if question_data.accuracy >= accuracy_threshold:
            print(f"Pronunciation accepted with accuracy: {question_data.accuracy:.2f}")
            correct_answers[unique_key] = question_data  # ✅ Now uses composite key
        else:
            print(f"Pronunciation below threshold: {question_data.accuracy:.2f}")
            incorrect_answers[unique_key] = question_data  # ✅ Now uses composite key
            
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
                                vocabulary.title(),
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

def chapter_test_page(page, image_urls: list):
    page.title = "Arami - Chapter Test"
    page.padding = 0

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
                          on_click=lambda e: page.go("/levels")),
            ft.TextButton("No", 
                          style=ft.ButtonStyle(color=ft.Colors.BLUE), 
                          on_click=lambda e: page.close(dlg_modal)),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
        bgcolor=ft.Colors.WHITE
    )
    
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

    questions = get_test_data(page)
    if not questions:
        page.views.append(ft.View("/lesson", [ft.Text("No questions available.")]))
        return
    total_questions = len(questions)
    current_question_index = {"value": 0}
    progress_value = (current_question_index["value"] + 1) / total_questions

    def render_question_layout(page, question_data, progress_value, on_next, on_back, current_index=0):
        question_type = question_data.type
        
        if question_type == "Image Picker":
            return build_imgpicker_question(page, question_data, progress_value, on_next, on_back, current_index)
        elif question_type == "Word Select":
            return build_wordselect_question(page, question_data, progress_value, on_next, on_back, current_index)
        elif question_type == "True or False":
            return build_tf_question(page, question_data, progress_value, on_next, on_back, current_index)
        elif question_type == "Pronunciation":
            return build_pronounce_question(page, question_data, progress_value, on_next, on_back, current_index)
        elif question_type == "Translate Sentence":
            return build_translate_sentence_question(page, question_data, progress_value, on_next, on_back, current_index)
        else:
            return ft.Text("Unknown question type.")

    def render_current_question(progress_value):
            page.views.clear()  # Optional: clear previous view
            question = questions[current_question_index["value"]]
            content = render_question_layout(
                page = page,
                question_data=question,
                progress_value=progress_value,
                on_next=next_question,
                on_back=go_back,
                current_index = current_question_index,
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
        # Get the current question
        current_question = questions[current_question_index["value"]]
        
        # Track vocabulary for library
        if hasattr(current_question, "vocabulary") and current_question.vocabulary:
            vocab = current_question.vocabulary
            global user_library
            if vocab not in user_library:
                user_library.append(vocab)
                # Update the session library
                page.session.set("user_library", user_library)
        
        current_question_index["value"] += 1
        progress_value = (current_question_index["value"] + 1) / total_questions

        if current_question_index["value"] < len(questions):
            render_current_question(progress_value)
        else:
            # Chapter test completed
            user_id = page.session.get("user_id")
            module_id = page.session.get("module_id")
            
            # Update user library file
            update_user_library()
            
            grade_percentage = (len(correct_answers) / total_questions) * 100
            formatted_time = f"{int(total_response_time // 60)}:{int(total_response_time % 60):02d}"
            
            # Check if chapter test passed
            ct_data = page.session.get("ct_data")
            passed = grade_percentage >= (ct_data.pass_threshold if ct_data else 70)
            
            print(f"[CHAPTER TEST] Completed with {grade_percentage:.1f}% (Pass threshold: {ct_data.pass_threshold if ct_data else 70}%)")
            
            # CRITICAL: Save chapter test completion to database
            if passed and user_id and module_id:
                try:
                    arami = pymongo.MongoClient(uri)["arami"]
                    users_col = arami["users"]
                    
                    # Update chapter test completion in database
                    update_result = users_col.update_one(
                        {
                            "user_id": int(user_id),
                            "modules.id": int(module_id)
                        },
                        {
                            "$set": {
                                "modules.$[module].chapter_test.completed": True,
                                "modules.$[module].chapter_test.grade_percentage": grade_percentage,
                                "modules.$[module].chapter_test.completion_time": total_response_time
                            }
                        },
                        array_filters=[
                            {"module.id": int(module_id)}
                        ]
                    )
                    
                    print(f"[CHAPTER TEST] Database update result: {update_result.modified_count} document(s) modified")
                    
                    # Check if module is now complete (all levels + chapter test done)
                    user_doc = users_col.find_one({"user_id": int(user_id)})
                    if user_doc:
                        for module in user_doc.get("modules", []):
                            if module.get("id") == int(module_id):
                                # Check if all levels are completed
                                all_levels_complete = all(
                                    level.get("completed", False) 
                                    for level in module.get("levels", [])
                                )
                                
                                chapter_test_complete = module.get("chapter_test", {}).get("completed", False)
                                
                                if all_levels_complete and chapter_test_complete:
                                    # Mark module as completed
                                    users_col.update_one(
                                        {
                                            "user_id": int(user_id),
                                            "modules.id": int(module_id)
                                        },
                                        {
                                            "$set": {
                                                "modules.$[module].completed": True
                                            }
                                        },
                                        array_filters=[
                                            {"module.id": int(module_id)}
                                        ]
                                    )
                                    
                                    print(f"[MODULE] Module {module_id} marked as completed!")
                                    
                                    # Unlock next module if exists
                                    next_module_id = int(module_id) + 1
                                    next_module_update = users_col.update_one(
                                        {
                                            "user_id": int(user_id),
                                            "modules.id": next_module_id
                                        },
                                        {
                                            "$set": {
                                                "modules.$[module].unlocked": True
                                            }
                                        },
                                        array_filters=[
                                            {"module.id": next_module_id}
                                        ]
                                    )
                                    
                                    if next_module_update.modified_count > 0:
                                        print(f"[MODULE] Next module {next_module_id} unlocked!")
                                    else:
                                        print(f"[MODULE] No next module to unlock or already unlocked")
                                
                                break
                    
                    # Update session data to reflect completion
                    modules = page.session.get("modules")
                    if modules is None:
                        modules = []
                        
                    for module in modules:
                        if hasattr(module, 'id') and str(module.id) == str(module_id):
                            if hasattr(module, 'chapter_test'):
                                module.chapter_test.completed = True
                                module.chapter_test.grade_percentage = grade_percentage
                                
                            # Check if module should be marked as completed
                            all_levels_complete = all(
                                getattr(level, 'completed', False) 
                                for level in getattr(module, 'levels', [])
                            )
                            
                            if all_levels_complete and module.chapter_test.completed:
                                module.completed = True
                                print(f"[SESSION] Module {module_id} marked as completed in session")
                            
                            break
                    
                    page.session.set("modules", modules)
                    
                    # Check for achievements
                    from achievements_manager import check_and_unlock_achievements
                    check_and_unlock_achievements(user_id, page)
                    
                except Exception as e:
                    print(f"[CHAPTER TEST] Error saving completion: {e}")
                    import traceback
                    traceback.print_exc()

            cache_chaptertest_data_to_temp(
                module_id=id,
                grade_percentage=grade_percentage,
                total_time_spent=total_response_time,
                correct_answers=correct_answers,
                incorrect_answers=incorrect_answers,
                completion_time=total_response_time,
                completed=True
            )

            lesson_score(page, grade_percentage, correct_answers, incorrect_answers, formatted_time)
            reset_var()

    def cache_chaptertest_data_to_temp(module_id, grade_percentage, total_time_spent, correct_answers, incorrect_answers, completion_time=None, completed=None):
        questions_correct_sanitized = sanitize_keys({
            k: v.__dict__ if hasattr(v, "__dict__") else v
            for k, v in correct_answers.items()
        })
        
        questions_incorrect_sanitized = sanitize_keys({
            k: v.__dict__ if hasattr(v, "__dict__") else v
            for k, v in incorrect_answers.items()
        })

        chapter_test_data = {
            "module_id": module_id,
            "grade_percentage": grade_percentage,
            "total_time_spent": total_time_spent,
            "questions_correct": questions_correct_sanitized,
            "questions_incorrect": questions_incorrect_sanitized,
        }
        
        # Add the new parameters to the saved data if provided
        if completion_time is not None:
            chapter_test_data["completion_time"] = completion_time
            
        if completed is not None:
            chapter_test_data["completed"] = completed

        with open("temp_chaptertest_data.json", "w", encoding="utf-8") as f:
            json.dump(chapter_test_data, f, indent=4)

    def reset_var():
        current_question_index["value"] = 0
        global correct_answers, incorrect_answers, total_response_time, formatted_time, grade_percentage
        total_response_time = 0
        formatted_time = "0:00"
        grade_percentage = 0 
        correct_answers.clear()
        incorrect_answers.clear()

    # Load user library
    global user_library
    user_library = get_user_library() or []
    
    # Get user library from session if available
    session_library = page.session.get("user_library")
    if session_library:
        user_library = session_library
        print(f"Loaded user library from session with {len(user_library)} items")

    render_current_question(progress_value)

def get_user_library():
    try:
        with open("temp_library.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Temp library cache not found.")
        return []
    
def update_user_library():
    global user_library
    try:
        with open("temp_library.json", "w") as f:
            json.dump(user_library, f)
    except Exception as e:
        print(f"Error updating library: {e}")