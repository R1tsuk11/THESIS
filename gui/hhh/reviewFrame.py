import flet as ft
import re
import os
import time
import json
import sys
from reviewScore import lesson_score
import asyncio
from supermemo_engine import update_supermemo_state, connect_to_mongoDB
import threading
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

def batch_update_supermemo(user_id, correct_answers, incorrect_answers):
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    if not user or "supermemo" not in user:
        print(f"[DEBUG] No supermemo data for user {user_id}")
        return

    supermemo = user["supermemo"]
    # Update correct answers
    for q in correct_answers.values():
        vocab = q.vocabulary
        for group in ["needs_practice", "mastered"]:
            if vocab in supermemo.get(group, {}):
                state = supermemo[group][vocab]
                new_state = update_supermemo_state(state, 5)  # 5 = correct
                supermemo[group][vocab] = new_state
                usercol.update_one({"user_id": user_id}, {"$set": {f"supermemo.{group}.{vocab}": new_state}})
                print(f"[DEBUG] Batch updated SuperMemo for {vocab} (correct) in {group}: {new_state}")
                break
    # Update incorrect answers
    for q in incorrect_answers.values():
        vocab = q.vocabulary
        for group in ["needs_practice", "mastered"]:
            if vocab in supermemo.get(group, {}):
                state = supermemo[group][vocab]
                new_state = update_supermemo_state(state, 2)  # 2 = incorrect
                supermemo[group][vocab] = new_state
                usercol.update_one({"user_id": user_id}, {"$set": {f"supermemo.{group}.{vocab}": new_state}})
                print(f"[DEBUG] Batch updated SuperMemo for {vocab} (incorrect) in {group}: {new_state}")
                break

class AttrDict(dict):
    """Allows attribute access to dict keys."""
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(item)
    def __setattr__(self, key, value):
        self[key] = value

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

def get_review_questions(page):
    review_questions = page.session.get("daily_review_questions")
    if not review_questions:
        print("No review questions found in session.")
        return []
    return [AttrDict(q) for q in review_questions]

def build_imgpicker_question(page, question_data, progress_value, on_next, on_back):
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

    # Try to get image URLs based on the indices in choices
    try:
        # Check if choices contains numeric indices
        if all(str(choice).isdigit() for choice in question_data.choices):
            img1 = m_one_image[int(question_data.choices[0])]
            img2 = m_one_image[int(question_data.choices[1])]
            if len(question_data.choices) > 2:
                img3 = m_one_image[int(question_data.choices[2])]
            else:
                img3 = None
        else:
            # Fall back to direct URLs in choices
            img1 = question_data.choices[0]
            img2 = question_data.choices[1]
            img3 = question_data.choices[2] if len(question_data.choices) > 2 else None
    except (ValueError, IndexError) as e:
        print(f"Error loading images: {e}")
        # Fallback to local files as last resort
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ASSETS_PATH = os.path.join(BASE_DIR, "assets")
        img1 = os.path.join(ASSETS_PATH, os.path.basename(str(question_data.choices[0])))
        img2 = os.path.join(ASSETS_PATH, os.path.basename(str(question_data.choices[1])))
        img3 = os.path.join(ASSETS_PATH, os.path.basename(str(question_data.choices[2]))) if len(question_data.choices) > 2 else None
        
    print("Image 1 src:", img1)
    print("Image 2 src:", img2)
    if img3:
        print("Image 3 src:", img3)

    def on_option_click(e, option_index):
        selected_option["value"] = option_index

        for i, option in enumerate([image_option1, image_option2, image_option3]):
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
            correct_answers[question_data.question] = question_data

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
            incorrect_answers[question_data.question] = question_data
            
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

    image_option3 = ft.Container(
        content=ft.Image(
            src=img3,
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
        on_click=lambda e: on_option_click(e, 2)
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
                    [image_option1, image_option2, image_option3],
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

def build_wordselect_question(page, question_data, progress_value, on_next, on_back):
    start_time = time.time()
    options = question_data.choices
    word_to_translate = question_data.question
    selected_option = {"value": None}
    correct_answer = question_data.correct_answer

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
            correct_answers[question_data.question] = question_data
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
            incorrect_answers[question_data.question] = question_data

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

    # Create content to be scrollable
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
        margin=ft.margin.only(bottom=20),
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
                ft.Container(height=10, bgcolor="#0078D7", width=50),

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

def build_tf_question(page, question_data, progress_value, on_next, on_back):
    start_time = time.time()
    selected_option = {"value": None}
    correct_answer = question_data.correct_answer

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
            correct_answers[question_data.question] = question_data
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
            incorrect_answers[question_data.question] = question_data    

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

    card_content = ft.Container(
        content=ft.Column(
            [
                ft.Text("TRUE OR FALSE", color="#0078D7", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Container(
                    content=ft.Text(question_text, color="black", size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
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
        margin=ft.margin.only(bottom=20),
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
                ft.Container(height=10, bgcolor="#0078D7", width=50),

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

def build_translate_sentence_question(page, question_data, progress_value, on_next, on_back):
    start_time = time.time()
    options = question_data.choices
    word_to_translate = question_data.question
    selected_option = {"value": None}
    correct_answer = question_data.correct_answer

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
            correct_answers[question_data.question] = question_data

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
            incorrect_answers[question_data.question] = question_data

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
        margin=ft.margin.only(bottom=20),
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
                ft.Container(height=10, bgcolor="#0078D7", width=50),

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

def build_pronounce_question(question_data, progress_value, on_next, on_back):
    start_time = time.time()
    question_text = question_data.question
    vocabulary = question_data.vocabulary
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

    # Create UI components
    txt_transcription = ft.Text("Tap the microphone to start recording", color="grey", size=16)
    txt_accuracy = ft.Text("", size=16)
    pronunciation_tips = ft.Text("", size=14, color="orange", visible=False)
    pronunciation_chart = ft.Image(visible=False)
    button_mic = ft.IconButton(
        icon=ft.icons.MIC,
        icon_color="white",
        bgcolor="#0078D7",
        icon_size=36,
        on_click=lambda e: start_recording(e)
    )
    
    # Import threading here to avoid issues
    import threading

    def start_recording(e):
        button_mic.disabled = True
        txt_transcription.value = "Listening..."
        txt_accuracy.value = ""
        pronunciation_tips.visible = False
        pronunciation_chart.visible = False
        e.page.update()
        
        recording["is_recording"] = True
        threading.Thread(target=lambda: record_audio(e.page)).start()

    def record_audio(page):
        if not model_available:
            # Simulate audio processing when model isn't available
            time.sleep(2)
            txt_transcription.value = vocabulary  # Assume correct for demo
            txt_accuracy.value = "Model not available - simulating correct pronunciation"
            txt_accuracy.color = "orange"
            button_mic.disabled = False
            button_mic.bgcolor = "#0078D7"
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
                button_mic.disabled = False
                page.update()
        except Exception as e:
            txt_transcription.value = f"Error recording audio: {str(e)}"
            button_mic.disabled = False
            page.update()
        finally:
            recording["is_recording"] = False
            
    def process_recording(page):
        if not model_available:
            return
            
        try:
            predicted_word, confidence, phoneme_confidence = speech_processor.predict_speech(
                recording["file_path"], vocabulary
            )
            
            if predicted_word:
                txt_transcription.value = f"You said: {predicted_word}"
                
                # Get any pronunciation errors from the NLTK analysis that was performed
                nltk_errors = getattr(speech_processor, 'pronunciation_errors', [])
                
                if predicted_word.lower() == vocabulary.lower():
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
            pronunciation_tips.visible = False
            pronunciation_chart.visible = False
            
        finally:
            button_mic.disabled = False
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
    
    # Create the main UI layout
    card_content = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(ft.Divider(color="grey", thickness=1), width=60),
                        ft.Container(
                            ft.Text("Pronounce", color="grey", size=14, weight=ft.FontWeight.W_500),
                            padding=ft.padding.symmetric(horizontal=10)
                        ),
                        ft.Container(ft.Divider(color="grey", thickness=1), width=60),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Container(
                    ft.Text(
                        question_text,
                        text_align=ft.TextAlign.CENTER,
                        size=16,
                        weight=ft.FontWeight.W_500
                    ),
                    margin=ft.margin.only(bottom=10, top=10)
                ),
                ft.Container(
                    ft.Text(
                        vocabulary,
                        color="#0078D7",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    margin=ft.margin.only(bottom=20)
                ),
                ft.Container(
                    button_mic,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=20, top=10)
                ),
                ft.Container(
                    txt_transcription,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=10)
                ),
                ft.Container(
                    txt_accuracy,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=10)
                ),
                ft.Container(
                    pronunciation_tips,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=10)
                ),
                ft.Container(
                    pronunciation_chart,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=20)
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5
        ),
        width=312,
        bgcolor="white",
        border_radius=10,
        padding=20,
        margin=ft.margin.only(top=20, bottom=20)
    )

    progress = ft.Container(
        ft.ProgressBar(value=progress_value, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20)
    )

    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        icon_color="grey",
                        on_click=on_back
                    ),
                    width=100,
                    bgcolor="white",
                    border_radius=ft.border_radius.all(30),
                    padding=5
                ),
                ft.Container(width=10),
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Text("NEXT", color="white", weight=ft.FontWeight.BOLD, size=16),
                        style=ft.ButtonStyle(
                            bgcolor={"": "#0078D7"},
                            shape=ft.RoundedRectangleBorder(radius=30),
                        ),
                        width=200,
                        height=50,
                        on_click=handle_next
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        padding=ft.padding.only(bottom=20)
    )

    return ft.Column(
        [
            card_content,
            progress,
            bottom_nav
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
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

def render_question_layout(page, question_data, progress_value, on_next, on_back):
    question_type = question_data.type
    
    if question_type == "Image Picker":
        return build_imgpicker_question(page, question_data, progress_value, on_next, on_back)
    elif question_type == "Word Select / Translate":
        return build_wordselect_question(page, question_data, progress_value, on_next, on_back)
    elif question_type == "True or False":
        return build_tf_question(page, question_data, progress_value, on_next, on_back)
    elif question_type == "Pronunciation":
        return build_pronounce_question(question_data, progress_value, on_next, on_back)
    elif question_type == "Translate Sentence":
        return build_translate_sentence_question(page, question_data, progress_value, on_next, on_back)
    else:
        return ft.Text("Unknown question type.")

def review_session(page, image_urls: list):
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
                          on_click=lambda e: page.go("/main-menu")),
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
            src="assets/landscape_background.png",
            width=page.width,
            height=page.height,
            fit=ft.ImageFit.COVER
        ),
        expand=True
    )

    # Load review questions
    questions = get_review_questions(page)
    total_questions = len(questions)
    current_question_index = {"value": 0}
    progress_value = (current_question_index["value"] + 1) / total_questions
    if not questions:
        page.views.append(ft.View("/daily-review", [ft.Text("No questions available.")]))
        return

    def render_current_question(progress_value):
            page.views.clear()  # Optional: clear previous view
            question = questions[current_question_index["value"]]
            content = render_question_layout(
                page = page,
                question_data=question,
                progress_value=progress_value,
                on_next=next_question,
                on_back=go_back
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
        current_question_index["value"] += 1
        progress_value = (current_question_index["value"] + 1) / total_questions
        if current_question_index["value"] < len(questions):
            render_current_question(progress_value)
        else:
            print("DEBUG correct_answers:", correct_answers)
            print("DEBUG incorrect_answers:", incorrect_answers)
            print("DEBUG correct_answers keys:", list(correct_answers.keys()))
            print("DEBUG incorrect_answers keys:", list(incorrect_answers.keys()))
            print("DEBUG correct_answers values:", list(correct_answers.values()))
            print("DEBUG incorrect_answers values:", list(incorrect_answers.values()))
            print(len(correct_answers))
            grade_percentage = round((len(correct_answers) / len(questions)) * 100, 2)
            formatted_time = f"{int(total_response_time // 60)}:{int(total_response_time % 60):02d}"
            user_id = page.session.get("user_id")
            threading.Thread(
                target=batch_update_supermemo,
                args=(user_id, correct_answers.copy(), incorrect_answers.copy()),
                daemon=True
            ).start()
            lesson_score(page, grade_percentage, correct_answers, incorrect_answers, formatted_time)
            reset_var()

    def reset_var():
        current_question_index["value"] = 0
        global correct_answers, incorrect_answers, total_response_time, formatted_time, grade_percentage
        total_response_time = 0
        formatted_time = "0:00"
        grade_percentage = 0 
        correct_answers.clear()
        incorrect_answers.clear()

    render_current_question(progress_value)