import flet as ft
import re
import os
import time
import json
from lessonScore import lesson_score
import asyncio

correct_answers = {}
incorrect_answers = {}
grade_percentage = 0.0
total_response_time = 0.0
formatted_time = ""
user_library = []

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

    for q in questions:
        q.lesson_id = level_data.lesson_id
        q.module_name = level_data.module_name

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

def build_lesson_question(question_data, progress_value, on_next, on_back):
    """Builds the layout for a 'Lesson' type question."""
    start_time = time.time()
    header = "Lesson"
    waray_phrase = None
    english_translation = None
    full_definition = question_data.question
    question = full_definition
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

    # Find all substrings in single quotes
    matches = re.findall(r"'(.*?)'", question)

    if len(matches) >= 2:
        waray_phrase = matches[0]
        english_translation = matches[1]
    else:
        print("Not enough matches found in the question string.")

    card_content = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(ft.Divider(color="grey", thickness=1), width=60),
                        ft.Container(
                            ft.Text(header, color="grey", size=14, weight=ft.FontWeight.W_500),
                            padding=ft.padding.symmetric(horizontal=10)
                        ),
                        ft.Container(ft.Divider(color="grey", thickness=1), width=60),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.icons.VOLUME_UP,
                            icon_color="#0078D7",
                            icon_size=24,
                            # Optionally play audio here
                        ),
                        ft.Text(
                            waray_phrase,
                            color="#0078D7",
                            size=24,
                            weight=ft.FontWeight.BOLD
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5
                ),
                ft.Container(
                    ft.Text(english_translation, color="grey", size=16),
                    margin=ft.margin.only(bottom=20)
                ),
                ft.Container(
                    ft.Image(
                        src="assets/L1.png",
                        width=250,
                        height=150,
                        fit=ft.ImageFit.CONTAIN
                    ),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=20)
                ),
                ft.Container(
                    ft.Text(
                        full_definition,
                        text_align=ft.TextAlign.CENTER,
                        size=16,
                        weight=ft.FontWeight.W_500,
                        color="black"
                    ),
                    margin=ft.margin.only(bottom=20)
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
                        on_click=add_time
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

def build_imgpicker_question(page, question_data, progress_value, on_next, on_back):
    start_time = time.time()
    selected_option = {"value": None}  # Use a dict to allow nonlocal mutation in nested functions
    img1 = "assets/" + question_data.choices[0]
    img2 = "assets/" + question_data.choices[1]
    img3 = "assets/" + question_data.choices[2]
    question = question_data.question
    correct_answer = question_data.correct_answer
    global user_library

    print("Image 1 src:", img1)
    print("Image 2 src:", img2)
    print("Image 3 src:", img3)
    print(os.path.exists(img1))

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
            correct_answers[question_data.question] = question_data
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

    return ft.Column(
        [
            # Header
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(width=50),
                        ft.Container(
                            width=50,
                            content=ft.IconButton(
                                icon=ft.icons.CLOSE,
                                icon_color="black",
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

            # Progress bar
            ft.Container(
                content=ft.ProgressBar(value=progress_value, bgcolor="#e0e0e0", color="#0078D7", width=300),
                margin=ft.margin.only(bottom=20, top=10)
            ),

            # Navigation buttons
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.IconButton(
                                icon=ft.icons.ARROW_BACK,
                                icon_color="grey",
                                on_click=on_back
                            ),
                            width=70,
                            bgcolor="#F5F5F5",
                            border_radius=ft.border_radius.all(30),
                            padding=5
                        ),
                        ft.Container(width=10),
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
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        expand=True
    )

def build_wordselect_question(page, question_data, progress_value, on_next, on_back):
    start_time = time.time()
    options = question_data.choices
    word_to_translate = question_data.question
    selected_option = {"value": None}
    correct_answer = question_data.correct_answer
    global user_library

    def on_option_click(e, option_index, option_containers):
        selected_option["value"] = option_index
        for i, option in enumerate(option_containers):
            option.border = ft.border.all(1, "black") if i == option_index else None
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
            content=ft.Text(opt_text, size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            width=320,
            bgcolor="#F5F5F5",
            padding=ft.padding.symmetric(vertical=15),
            border_radius=10,
            margin=ft.margin.only(bottom=10 if i < len(options)-1 else 20),
        )
        container.on_click = lambda e, idx=i: on_option_click(e, idx, option_containers)
        option_containers.append(container)

    return ft.Stack(
        [
            ft.Container(bgcolor="white", expand=True),
            ft.Column([
                # Blue bar on top
                ft.Container(height=10, bgcolor="#0078D7", width=50),

                # Main content
                ft.Column(
                    [
                        # Header with close/back button
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Container(width=50),
                                    ft.Container(
                                        width=50,
                                        content=ft.IconButton(icon=ft.icons.CLOSE, icon_color="black", on_click=on_back),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.END,
                            ),
                            padding=ft.padding.only(top=10, right=10),
                        ),

                        # Card content
                        ft.Container(
                            content=ft.Column(
                                [
                                    # Instruction
                                    ft.Text(word_to_translate, color="#0078D7", size=18, weight=ft.FontWeight.BOLD),

                                    # Word to translate
                                    ft.Container(
                                        content=ft.Text(word_to_translate, size=20, weight=ft.FontWeight.BOLD),
                                        width=320,
                                        bgcolor="#FFF9C4",
                                        padding=ft.padding.symmetric(vertical=15),
                                        border_radius=10,
                                        margin=ft.margin.only(bottom=30)
                                    ),

                                    # Option buttons
                                    ft.Column(option_containers)
                                ],
                                alignment=ft.MainAxisAlignment.START,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            padding=ft.padding.only(top=20),
                        ),

                        # Progress bar
                        ft.Container(
                            content=ft.ProgressBar(value=progress_value, bgcolor="#e0e0e0", color="#0078D7", width=300),
                            margin=ft.margin.only(bottom=20),
                        ),

                        # Bottom nav
                        ft.Container(
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
                                        padding=5,
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
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            padding=ft.padding.only(bottom=20),
                        )
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
    global user_library

    def on_option_click(e, option_index):
        selected_option["value"] = option_index
        for i, option in enumerate([option1, option2]):
            option.border = ft.border.all(1, "black") if i == selected_option["value"] else None
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
        content=ft.Text(option1_text, color="black", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        width=320,
        bgcolor="#F5F5F5",
        padding=ft.padding.symmetric(vertical=15),
        border_radius=10,
        margin=ft.margin.only(bottom=10),
        on_click=lambda e: on_option_click(e, 0)
    )

    option2 = ft.Container(
        content=ft.Text(option2_text, color="black", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
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

    progress = ft.ProgressBar(value=progress_value, bgcolor="#e0e0e0", color="#0078D7", width=300)

    return ft.Column(
        [
            card_content,
            ft.Container(content=progress, margin=ft.margin.only(bottom=20)),
            ft.Row(
                [
                    ft.IconButton(icon=ft.icons.ARROW_BACK, icon_color="grey", on_click=on_back),
                    ft.Container(width=10),
                    ft.ElevatedButton(
                        content=ft.Text("NEXT", color="white", weight=ft.FontWeight.BOLD, size=16),
                        style=ft.ButtonStyle(
                            bgcolor={"": "#0078D7"},
                            shape=ft.RoundedRectangleBorder(radius=30),
                        ),
                        width=200,
                        height=50,
                        on_click=handle_next
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            )
        ],
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0
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
                        icon=ft.icons.CLOSE,
                        icon_color="black",
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
                        weight=ft.FontWeight.BOLD,  # Changed to BOLD
                        color="#0078D7"
                    ),
                    margin=ft.margin.only(top=20, bottom=20),
                    padding=ft.padding.symmetric(horizontal=10)
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        ),
        width=312,
        height=280,
        bgcolor="white",
        border_radius=10,
        padding=20,
        margin=ft.margin.only(top=20, bottom=20)
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
                        on_click=add_time
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        padding=ft.padding.only(bottom=20)
    )

    return ft.Column(
        [
            header,
            ft.Container(content=card_content, alignment=ft.alignment.center),
            progress,
            bottom_nav
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
        expand=True
    )

def build_translate_sentence_question(page, question_data, progress_value, on_next, on_back):
    start_time = time.time()
    options = question_data.choices
    word_to_translate = question_data.question
    selected_option = {"value": None}
    correct_answer = question_data.correct_answer
    global user_library

    def on_option_click(e, option_index, option_containers):
        selected_option["value"] = option_index
        for i, option in enumerate(option_containers):
            option.border = ft.border.all(1, "black") if i == option_index else None
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
            content=ft.Text(opt_text, size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            width=320,
            bgcolor="#F5F5F5",
            padding=ft.padding.symmetric(vertical=15),
            border_radius=10,
            margin=ft.margin.only(bottom=10 if i < len(options)-1 else 20),
        )
        container.on_click = lambda e, idx=i: on_option_click(e, idx, option_containers)
        option_containers.append(container)

    return ft.Stack(
        [
            ft.Container(bgcolor="white", expand=True),
            ft.Column([
                # Blue bar on top
                ft.Container(height=10, bgcolor="#0078D7", width=50),

                # Main content
                ft.Column(
                    [
                        # Header with close/back button
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Container(width=50),
                                    ft.Container(
                                        width=50,
                                        content=ft.IconButton(icon=ft.icons.CLOSE, icon_color="black", on_click=on_back),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.END,
                            ),
                            padding=ft.padding.only(top=10, right=10),
                        ),

                        # Card content
                        ft.Container(
                            content=ft.Column(
                                [
                                    # Instruction
                                    ft.Text(word_to_translate, color="#0078D7", size=18, weight=ft.FontWeight.BOLD),

                                    # Word to translate
                                    ft.Container(
                                        content=ft.Text(word_to_translate, size=20, weight=ft.FontWeight.BOLD),
                                        width=320,
                                        bgcolor="#FFF9C4",
                                        padding=ft.padding.symmetric(vertical=15),
                                        border_radius=10,
                                        margin=ft.margin.only(bottom=30)
                                    ),

                                    # Option buttons
                                    ft.Column(option_containers)
                                ],
                                alignment=ft.MainAxisAlignment.START,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            padding=ft.padding.only(top=20),
                        ),

                        # Progress bar
                        ft.Container(
                            content=ft.ProgressBar(value=progress_value, bgcolor="#e0e0e0", color="#0078D7", width=300),
                            margin=ft.margin.only(bottom=20),
                        ),

                        # Bottom nav
                        ft.Container(
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
                                        padding=5,
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
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            padding=ft.padding.only(bottom=20),
                        )
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
    """Builds the layout for a pronunciation type question."""

    start_time = time.time()
    instruction_text = question_data.question
    word_text = question_data.get("waray_text", "Aga")
    translation_text = question_data.get("english_text", "Morning")
    tap_record_text = question_data.get("record_instruction", "Tap to record")

    def on_mic_press(e):
        print("Recording started")
        # Recording logic goes here

    # Card content
    card_content = ft.Container(
        content=ft.Column(
            [
                ft.Text(instruction_text, color="#0078D7", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(name=ft.icons.VOLUME_UP_ROUNDED, color="black", size=20),
                            ft.Text(word_text, color="black", size=18, weight=ft.FontWeight.BOLD)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10
                    ),
                    width=320,
                    bgcolor="#FFF9C4",
                    padding=ft.padding.symmetric(vertical=15, horizontal=10),
                    border_radius=10,
                    margin=ft.margin.only(top=15, bottom=15)
                ),
                ft.Text(translation_text, color="black", size=16, text_align=ft.TextAlign.CENTER),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(
                                content=ft.Icon(name=ft.icons.MIC, color="black", size=40),
                                width=120,
                                height=120,
                                bgcolor="#FFC107",
                                border_radius=60,
                                alignment=ft.alignment.center,
                                on_click=on_mic_press,
                                margin=ft.margin.only(bottom=20),
                                shadow=ft.BoxShadow(
                                    spread_radius=1,
                                    blur_radius=15,
                                    color=ft.colors.YELLOW_100,
                                    offset=ft.Offset(0, 0)
                                )
                            ),
                            ft.Text(tap_record_text, color="black", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    margin=ft.margin.only(top=30, bottom=30)
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        padding=ft.padding.only(top=20)
    )

    progress = ft.Container(
        ft.ProgressBar(value=progress_value, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20)
    )

    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.IconButton(icon=ft.icons.ARROW_BACK, icon_color="grey", on_click=on_back),
                    width=100,
                    bgcolor="#F5F5F5",
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
                        on_click=on_next
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


def render_question_layout(page, question_data, progress_value, on_next, on_back):
    question_type = question_data.type
    
    if question_type == "Lesson":
        return build_lesson_question(question_data, progress_value, on_next, on_back)
    elif question_type == "Image Picker":
        return build_imgpicker_question(page, question_data, progress_value, on_next, on_back)
    elif question_type == "Word Select":
        return build_wordselect_question(page, question_data, progress_value, on_next, on_back)
    elif question_type == "True or False":
        return build_tf_question(page, question_data, progress_value, on_next, on_back)
    elif question_type == "Cultural Trivia":
        return build_trivia_question(question_data, progress_value, on_next, on_back)
    elif question_type == "Pronounce":
        print("Pronounce question type not implemented yet. Using Word Select Layout")
        return build_wordselect_question(page, question_data, progress_value, on_next, on_back)
    elif question_type == "Translate Sentence":
        return build_translate_sentence_question(page, question_data, progress_value, on_next, on_back)
    else:
        return ft.Text("Unknown question type.")

def lesson_page(page: ft.Page):
    page.title = "Arami - Lesson"
    page.padding = 0

    def go_back(e):
        page.go("/levels")

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
    
    # Load questions
    questions = get_questions(page)
    global user_library
    user_library = get_user_library()
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
            print(len(weighted_questions))
            print(len(correct_answers))
            grade_percentage = round((len(correct_answers) / len(weighted_questions)) * 100, 2)
            formatted_time = f"{int(total_response_time // 60)}:{int(total_response_time % 60):02d}"
            correct_answers_serialized = {k: v.__dict__ if hasattr(v, "__dict__") else v for k, v in correct_answers.items()}
            incorrect_answers_serialized = {k: v.__dict__ if hasattr(v, "__dict__") else v for k, v in incorrect_answers.items()}
            page.session.set("updated_data", [grade_percentage, formatted_time, total_response_time, correct_answers_serialized, incorrect_answers_serialized, questions])
            update_user_library()
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
