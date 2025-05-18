import flet as ft
import re
import os
import time
import json
from reviewScore import lesson_score
import asyncio
from supermemo_engine import update_supermemo_state, connect_to_mongoDB
import threading

correct_answers = {}
incorrect_answers = {}
grade_percentage = 0.0
total_response_time = 0.0
formatted_time = ""

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

def build_wordselect_question(page, question_data, progress_value, on_next, on_back):
    start_time = time.time()
    options = question_data.choices
    word_to_translate = question_data.question
    selected_option = {"value": None}
    correct_answer = question_data.correct_answer

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
    
    if question_type == "Image Picker":
        return build_imgpicker_question(page, question_data, progress_value, on_next, on_back)
    elif question_type == "Word Select / Translate":
        return build_wordselect_question(page, question_data, progress_value, on_next, on_back)
    elif question_type == "True or False":
        return build_tf_question(page, question_data, progress_value, on_next, on_back)
    elif question_type == "Pronounce":
        print("Pronounce question type not implemented yet. Using Word Select Layout")
        return build_wordselect_question(page, question_data, progress_value, on_next, on_back)
    else:
        return ft.Text("Unknown question type.")

def review_session(page):
    def go_back(e):
        page.go("/main-menu")

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

def daily_review_page(page):
    """Daily review page showing the review session screen with routing."""
    page.title = "Arami - Daily Review"
    page.padding = 0
    page.bgcolor = "#FFFFFF"

    # Main card content
    card_content = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Text(
                        "Time for your",
                        size=16,
                        weight=ft.FontWeight.W_500,
                        color="#424242",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    margin=ft.margin.only(top=20)
                ),
                ft.Container(
                    content=ft.Text(
                        "daily review",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color="#0078D7",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ),
                ft.Container(
                    content=ft.Text(
                        "session!",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color="#0078D7",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ),
                ft.Container(
                    content=ft.Image(
                        src="assets/reviewPic.png",
                        width=270,
                        fit=ft.ImageFit.CONTAIN
                    ),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=10,bottom=10)  # Reduced margin
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5  # Add spacing for tighter layout
        ),
        width=320,
        bgcolor="white",
        border_radius=10,
        padding=20,
        margin=ft.margin.symmetric(vertical=10),  # Reduced vertical margin
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.colors.GREY_400,
            offset=ft.Offset(2, 2)
        )
    )

    # Function to handle continue button click
    def handle_continue_click(e):
        print("Daily review session started!")
        page.views.clear()  # Clear the intro view
        page.update()
        review_session(page)  # Now show the questions

    # Continue button
    continue_button = ft.Container(
        content=ft.ElevatedButton(
            content=ft.Text("CONTINUE", color="white", weight=ft.FontWeight.BOLD, size=16),
            style=ft.ButtonStyle(
                bgcolor={"": "#0078D7"},
                shape=ft.RoundedRectangleBorder(radius=5),
            ),
            width=320,
            height=50,
            on_click=handle_continue_click
        ),
        margin=ft.margin.only(bottom=10)  # Reduced bottom margin
    )

    # Create the background with landscape image
    background = ft.Stack(
        [
            ft.Image(
                src="landscape_background.png",
                width=page.width,
                height=page.height,
                fit=ft.ImageFit.COVER,
            ),
            ft.Container(
                content=ft.Column(
                    [
                        card_content,
                        continue_button,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,  # Center everything
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,  # Reduce spacing between elements
                ),
                width=page.width,
                height=page.height,
                padding=20
            ),
        ],
        width=page.width,
        height=page.height,
    )
    
    # Function to handle resize events
    def page_resize(e):
        # Update the view to maintain layout on resize
        page.views.clear()
        page.views.append(
            ft.View(
                "/daily-review",
                [background],
                padding=0
            )
        )
        page.update()
    
    # Register the resize event handler
    page.on_resize = page_resize
    
    # Add the daily review screen as a view
    page.views.append(
        ft.View(
            "/daily-review",
            [background],
            padding=0
        )
    )
    page.update()