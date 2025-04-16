import flet as ft
import re
import os

correct_answers = {}
incorrect_answers = {}

def get_questions(page):
    """Retrieves questions for the current lesson."""
    level_data = page.session.get("level_data")
    if not level_data:
        print("Level data not found in session.")
        return None

    questions = level_data.questions_answers
    if not questions:
        print("No questions found in level data.")
        return None

    return questions

def build_lesson_question(question_data, progress_value, on_next, on_back):
    """Builds the layout for a 'Lesson' type question."""
    header = "Lesson"
    waray_phrase = None
    english_translation = None
    full_definition = question_data.question
    question = full_definition

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

def build_imgpicker_question(question_data, progress_value, on_next, on_back):
    selected_option = {"value": None}  # Use a dict to allow nonlocal mutation in nested functions
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_PATH = os.path.join(BASE_DIR, "assets")
    img1 = os.path.join(ASSETS_PATH, os.path.basename(question_data.choices[0]))
    img2 = os.path.join(ASSETS_PATH, os.path.basename(question_data.choices[1]))
    question = question_data.question
    correct_answer = question_data.correct_answer

    print("Image 1 src:", img1)
    print("Image 2 src:", img2)
    print(os.path.exists(img1))

    def on_option_click(e, option_index):
        selected_option["value"] = option_index

        for i, option in enumerate([image_option1, image_option2]):
            if i == selected_option["value"]:
                option.border = ft.border.all(3, "#0078D7")  # Blue border for selected
            else:
                option.border = ft.border.all(1, "#E0E0E0")  # Light gray border
        e.page.update()

    def handle_next(e):
        if selected_option["value"] == 0:
            print("User selected Choice 1")
        elif selected_option["value"] == 1:
            print("User selected Choice 2")
        else:
            print("User did not select any image")
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
                    [image_option1, image_option2],
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

def build_wordselect_question(question_data, progress_value, on_next, on_back):
    options = question_data.choices
    word_to_translate = question_data.question
    selected_option = {"value": None}

    def on_option_click(e, option_index, option_containers):
        selected_option["value"] = option_index
        for i, option in enumerate(option_containers):
            option.border = ft.border.all(1, "black") if i == option_index else None
        e.page.update()

    def handle_next(e):
        if selected_option["value"] == 0:
            print("User selected Choice 1")
        elif selected_option["value"] == 1:
            print("User selected Choice 2")
        elif selected_option["value"] == 2:
            print("User selected Choice 3")
        else:
            print("User did not select any image")
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

def build_tf_question(question_data, progress_value, on_next, on_back):
    selected_option = {"value": None}

    def on_option_click(e, option_index):
        selected_option["value"] = option_index
        for i, option in enumerate([option1, option2]):
            option.border = ft.border.all(1, "black") if i == selected_option["value"] else None
        e.page.update()

    def handle_next(e):
        if selected_option["value"] is None:
            print("No option was selected")
        elif selected_option["value"] == 0:
            print("Selected option: True")
        elif selected_option["value"] == 1:
            print("Selected option: False")
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

def build_pronounce_question(question_data, progress_value, on_next, on_back):
    """Builds the layout for a pronunciation type question."""

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


def render_question_layout(question_data, progress_value, on_next, on_back):
    question_type = question_data.type
    
    if question_type == "Lesson":
        return build_lesson_question(question_data, progress_value, on_next, on_back)
    elif question_type == "Image Picker":
        return build_imgpicker_question(question_data, progress_value, on_next, on_back)
    elif question_type == "Word Select / Translate":
        return build_wordselect_question(question_data, progress_value, on_next, on_back)
    elif question_type == "True or False":
        return build_tf_question(question_data, progress_value, on_next, on_back)
    elif question_type == "Cultural Trivia":
        return build_trivia_question(question_data, progress_value, on_next, on_back)
    elif question_type == "Pronounce":
        print("Pronounce question type not implemented yet. Using Word Select Layout")
        return build_wordselect_question(question_data, progress_value, on_next, on_back)
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
    total_questions = len(questions) if questions else 0
    current_question_index = {"value": 0}
    progress_value = (current_question_index["value"] + 1) / total_questions
    if not questions:
        page.views.append(ft.View("/lesson", [ft.Text("No questions available.")]))
        return

    def render_current_question(progress_value):
        page.views.clear()  # Optional: clear previous view

        question = questions[current_question_index["value"]]
        content = render_question_layout(
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
            page.go("/levels")  # or show results, etc.

    render_current_question(progress_value)
