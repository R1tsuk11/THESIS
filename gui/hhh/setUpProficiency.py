import urllib.parse
import flet as ft
import pymongo
from pymongo.errors import ConfigurationError
import sys
import time
import asyncio
from qbank import pretest_data

correct_answers = {}
incorrect_answers = {}
grade_percentage = 0.0
total_response_time = 0.0
formatted_time = ""

uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

class Question:
    def __init__(self, question_data):
        self.question = question_data.get("question")
        self.answer = question_data.get("answer")
        self.vocabulary = question_data.get("vocabulary")
        self.type = question_data.get("type")
        self.choices = question_data.get("choices")
        self.correct_answer = question_data.get("correct_answer")
        self.difficulty = question_data.get("difficulty")
        self.response_time = question_data.get("response_time")
        self.word_to_translate = question_data.get("word_to_translate")
        self.image = question_data.get("image", None) 

def get_user_id(page):
    """Retrieves user_id from previous page session."""
    page.session.get("user_id")  # Get user ID from session
    if page.session.get("user_id") is None:
        print("No user ID found in session.")
        return None
    return page.session.get("user_id")

def get_questions(page):
    """Retrieves questions for the pre-test and converts them to Question objects."""
    try:
        questions_data = pretest_data
        if not questions_data:
            print("Pre-test data not found in system.")
            return None
        
        # Convert each dictionary to a Question object
        questions = []
        for q_dict in questions_data:
            question_obj = Question(q_dict)
            questions.append(question_obj)
            
        print(f"Loaded {len(questions)} pre-test questions")
        return questions
    except Exception as e:
        print(f"Error loading pre-test questions: {e}")
        return None

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

def build_wordselect_question(page, question_data, progress_value, on_next, on_back, current_question_index):
    start_time = time.time()
    options = question_data.choices
    word_to_translate = question_data.word_to_translate
    instruction = question_data.question
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
            unique_key = f"{question_data.question}__{question_data.type}__{current_question_index['value']}"
            correct_answers[unique_key] = question_data

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

def build_translate_sentence_question(page, question_data, progress_value, on_next, on_back, current_question_index):
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
            unique_key = f"{question_data.question}__{question_data.type}__{current_question_index['value']}"
            correct_answers[unique_key] = question_data

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

def render_question_layout(page, question_data, progress_value, on_next, on_back, current_index):
    question_type = question_data.type
    
    if question_type == "Word Select":
        return build_wordselect_question(page, question_data, progress_value, on_next, on_back, current_index)
    elif question_type == "Translate Sentence":
        return build_translate_sentence_question(page, question_data, progress_value, on_next, on_back, current_index)
    else:
        return ft.Text("Unknown question type.")

def connect_to_mongoDB():
    try:
        arami = pymongo.MongoClient(uri)
        aramidb = arami["arami"]
        usercol = aramidb["users"]
        return usercol
    except ConfigurationError as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit("Terminating the program due to MongoDB connection failure.")

def add_proficiency_to_db(user_id, proficiency):
    """Adds the selected proficiency to the database."""
    usercol = connect_to_mongoDB()
    usercol.update_one({"user_id": user_id}, {"$set": {"proficiency": proficiency}})
    print(f"User {user_id} proficiency updated to {proficiency}")

def goto_time(page, user_id):
    """Navigates to the time setup page and passes the user_id data via session."""
    page.session.set("user_id", user_id)  # Store id in session
    route = "/setup-time"
    page.go(route)
    page.update()

def pretest_landing_page(page: ft.Page, image_urls: list):
    """Creates a landing page explaining the pre-test purpose before starting"""
    page.title = "Arami - Pre-test Introduction"
    page.padding = 0
    
    # Background with landscape image
    background = ft.Container(
        content=ft.Image(
            src=image_urls[8],  # Using the same background as other pages
            width=page.width,
            height=page.height,
            fit=ft.ImageFit.COVER
        ),
        expand=True
    )
    
    # Card content with explanation
    card_content = ft.Container(
        content=ft.Column(
            [
                # Pretest header with lines
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Divider(color="grey", thickness=1),
                            width=60
                        ),
                        ft.Container(
                            content=ft.Text("PRE-TEST", color="grey", size=14, weight=ft.FontWeight.W_500),
                            padding=ft.padding.symmetric(horizontal=10)
                        ),
                        ft.Container(
                            content=ft.Divider(color="grey", thickness=1),
                            width=60
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                
                # Small icon/image
                ft.Container(
                    content=ft.Icon(
                        name=ft.icons.QUIZ_ROUNDED,
                        color="#0078D7",
                        size=60
                    ),
                    margin=ft.margin.only(top=20, bottom=15),
                    alignment=ft.alignment.center
                ),
                
                # Title
                ft.Container(
                    content=ft.Text(
                        "Let's Assess Your Level",
                        color="#0078D7",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    margin=ft.margin.only(bottom=25),
                    alignment=ft.alignment.center
                ),
                
                # Explanation text
                ft.Container(
                    content=ft.Text(
                        "Before we begin, let's take a quick pre-test to determine "
                        "your current knowledge of Waray.\n\n"
                        "This will help us personalize your learning experience "
                        "and provide appropriate challenges based on your level.",
                        color="black",
                        size=16,
                        text_align=ft.TextAlign.CENTER
                    ),
                    margin=ft.margin.only(bottom=25),
                    padding=ft.padding.symmetric(horizontal=10),
                    alignment=ft.alignment.center
                ),
                
                # What to expect
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "What to expect:",
                            color="#0078D7",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.LEFT
                        ),
                        ft.Container(height=5),
                        ft.Row([
                            ft.Icon(name=ft.icons.CHECK_CIRCLE, color="#0078D7", size=16),
                            ft.Container(width=8),
                            ft.Text("6 simple questions", size=14)
                        ]),
                        ft.Container(height=5),
                        ft.Row([
                            ft.Icon(name=ft.icons.CHECK_CIRCLE, color="#0078D7", size=16),
                            ft.Container(width=8),
                            ft.Text("Takes about 2 minutes", size=14)
                        ]),
                        ft.Container(height=5),
                        ft.Row([
                            ft.Icon(name=ft.icons.CHECK_CIRCLE, color="#0078D7", size=16),
                            ft.Container(width=8),
                            ft.Text("No pressure - just try your best!", size=14)
                        ]),
                    ]),
                    margin=ft.margin.only(bottom=30),
                    padding=ft.padding.symmetric(horizontal=20),
                    alignment=ft.alignment.center_left
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        ),
        width=312,
        bgcolor="white",
        border_radius=10,
        border=ft.border.all(2, "#0078D7"),
        padding=20,
        margin=ft.margin.symmetric(vertical=20),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.Colors.GREY_400,
            offset=ft.Offset(2, 2)
        )
    )
    
    # Bottom button
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Text(
                            "START PRE-TEST", 
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
                        on_click=lambda e: page.go("/setup-proficiency")
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        padding=ft.padding.only(bottom=20)
    )
    
    # Main content
    main_content = ft.Column(
        [
            ft.Container(height=30),  # Top spacing
            ft.Container(
                content=card_content,
                alignment=ft.alignment.center,
            ),
            ft.Container(expand=True),  # Flexible space
            bottom_nav
        ],
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
        expand=True
    )
    
    # Full page stack
    stack = ft.Stack(
        [background, main_content],
        expand=True
    )
    
    # Add the view to the page
    page.views.append(
        ft.View(
            "/pretest-intro",
            [stack],
            padding=0
        )
    )
    
    page.update()

def set_up_proficiency_page(page: ft.Page, image_urls: list):
    """Defines the Setup Proficiency Page with Routing"""

    questions = get_questions(page)
    total_questions = len(questions)
    current_question_index = {"value": 0}
    progress_value = (current_question_index["value"] + 1) / total_questions
    get_user_id(page)
    if not questions:
        page.views.append(ft.View("/setup-proficiency", [ft.Text("No questions available.")]))
        return
    
    # EXIT ALERT
    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text(
            "Return to registration page?",
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
                          on_click=lambda e: page.go("/register")),
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

    def render_current_question(progress_value):
        page.views.clear()  # Optional: clear previous view
        question = questions[current_question_index["value"]]
        
        content = render_question_layout(
            page = page,
            question_data=question,
            progress_value=progress_value,
            on_next=next_question,
            on_back=go_back,
            current_index = current_question_index
        )

        page.views.append(
            ft.View(
                "/setup-proficiency",
                [ft.Stack([background, content], expand=True)],
                padding=0
            )
        )
        page.update()

    def next_question(e=None):
        # Get the current question
        current_question = questions[current_question_index["value"]]

        current_question_index["value"] += 1
        progress_value = (current_question_index["value"] + 1) / total_questions
        if current_question_index["value"] < len(questions):
            render_current_question(progress_value)
        else:
            # Debug what's happening with the counts
            print("\n--- QUESTION COUNT DIAGNOSTIC ---")
            print(f"Total questions: {total_questions}")
            print(f"Correct answers: {len(correct_answers)}")
            print(f"Incorrect answers: {len(incorrect_answers)}")

            # Calculate grade based on how many questions were correctly answered out of those presented
            if len(questions) > 0:
                grade_percentage = round((len(correct_answers) / len(questions)) * 100, 2)
                grade_percentage = min(grade_percentage, 100)
            else:
                grade_percentage = 0
                
            print(f"Final grade percentage: {grade_percentage}%")
                    
            formatted_time = f"{int(total_response_time // 60)}:{int(total_response_time % 60):02d}"
            correct_answers_serialized = {k: v.__dict__ if hasattr(v, "__dict__") else v for k, v in correct_answers.items()}
            incorrect_answers_serialized = {k: v.__dict__ if hasattr(v, "__dict__") else v for k, v in incorrect_answers.items()}
            pretest_score(page, grade_percentage, correct_answers, incorrect_answers, formatted_time)
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

def pretest_score(page: ft.Page, accuracyPercentage=50, noOfCorrect=0, noOfIncorrect=0, responseTime="3:01"):
    """
    Score summary page displaying lesson results
    
    Parameters:
    - accuracyPercentage: int - Percentage of correct answers (0-100)
    - noOfCorrect: int - Number of correct answers
    - noOfIncorrect: int - Number of incorrect answers
    - responseTime: str - Total response time formatted as "M:SS"
    """
    page.title = "Arami - Pre-test Score"
    page.padding = 0
    correct = len(noOfCorrect)
    incorrect = len(noOfIncorrect)
    user_id = get_user_id(page)

    # Calculate percentage threshold
    percentage = (4 / 6) * 100  # This will be 66.67
    
    # Determine proficiency level based on score
    proficiency_value = 0.05 if accuracyPercentage > percentage else 0.0
    proficiency_text = "BEGINNER" if proficiency_value == 0.05 else "STARTER"
    proficiency_color = "#75B0FF" if proficiency_value == 0.05 else "#FFB7B7"
    
    # Add proficiency to database
    add_proficiency_to_db(user_id, proficiency_value)

    score_image_urls = [
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747653930/tryagain_j5tsjw.png",  # tryagain - 0
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747653931/goodjob_jbi6dt.png",  # goodjob - 1
    ]
    
    # Create top header with close button
    header = ft.Container(
        content=ft.Row(
            [
                ft.Container(width=50),  # Spacer
            ],
            alignment=ft.MainAxisAlignment.END
        ),
        padding=ft.padding.only(top=40) 
    )
    
    # Determine which image to show based on accuracy
    img1 = score_image_urls[1]  # goodjob
    img2 = score_image_urls[0]  # tryagain
    celebration_image = img1 if accuracyPercentage >= percentage else img2
    
    # Card content
    card_content = ft.Container(
        content=ft.Column(
            [
                # SCORE header with lines
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Divider(color="grey", thickness=1),
                            width=60
                        ),
                        ft.Container(
                            content=ft.Text("SCORE", color="grey", size=14, weight=ft.FontWeight.W_500),
                            padding=ft.padding.symmetric(horizontal=10)
                        ),
                        ft.Container(
                            content=ft.Divider(color="grey", thickness=1),
                            width=60
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                
                # Accuracy box - INCREASED HEIGHT and better padding
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "ACCURACY",
                                color="white",
                                size=14,
                                weight=ft.FontWeight.W_500
                            ),
                            ft.Container(
                                content=ft.Text(
                                    f"{round(accuracyPercentage)} %",
                                    color="white",
                                    size=40,
                                    weight=ft.FontWeight.BOLD
                                ),
                                padding=ft.padding.symmetric(vertical=8)
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=3
                    ),
                    width=250,
                    height=95,
                    bgcolor="#75B0FF",  # Lighter blue
                    border_radius=15,
                    padding=ft.padding.all(10),
                    margin=ft.margin.only(top=10, bottom=15)
                ),
                
                # NEW: Proficiency level
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "PROFICIENCY LEVEL",
                                color="white",
                                size=14,
                                weight=ft.FontWeight.W_500
                            ),
                            ft.Container(
                                content=ft.Text(
                                    proficiency_text,
                                    color="white",
                                    size=24,
                                    weight=ft.FontWeight.BOLD
                                ),
                                padding=ft.padding.symmetric(vertical=8)
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=3
                    ),
                    width=250,
                    height=70,
                    bgcolor=proficiency_color,
                    border_radius=15,
                    padding=ft.padding.all(8),
                    margin=ft.margin.only(bottom=15)
                ),
                
                # Celebration image
                ft.Container(
                    content=ft.Image(
                        src=celebration_image,
                        width=120,
                        height=100,  # Reduced height to fit new content
                        fit=ft.ImageFit.CONTAIN
                    ),
                    margin=ft.margin.only(bottom=15)
                ),
                
                # Correct and Incorrect counters row
                ft.Row(
                    [
                        # Correct counter - using variable
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        correct,
                                        color="#3A5D30",
                                        size=36,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        "CORRECT",
                                        color="#3A5D30",
                                        size=12,
                                        weight=ft.FontWeight.W_500
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=0
                            ),
                            width=100,
                            height=90,
                            bgcolor="#C2F2A5",
                            border_radius=8,
                            padding=ft.padding.all(10)
                        ),
                        
                        ft.Container(width=15),  # Spacer
                        
                        # Incorrect counter - using variable
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        incorrect,
                                        color="#95353A",
                                        size=36,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        "INCORRECT",
                                        color="#95353A",
                                        size=12,
                                        weight=ft.FontWeight.W_500
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=0
                            ),
                            width=100,
                            height=90,
                            bgcolor="#FFB7B7",
                            border_radius=8,
                            padding=ft.padding.all(10)
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                
                # Response time - using variable
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(
                                        "RESPONSE",
                                        color="#847B00",
                                        size=12,
                                        weight=ft.FontWeight.W_500,
                                        text_align=ft.TextAlign.LEFT
                                    ),
                                    ft.Text(
                                        "TIME:",
                                        color="#847B00",
                                        size=12,
                                        weight=ft.FontWeight.W_500,
                                        text_align=ft.TextAlign.LEFT
                                    )
                                ],
                                spacing=0,
                                alignment=ft.MainAxisAlignment.CENTER
                            ),
                            ft.Container(width=25),  # Spacer
                            ft.Text(
                                responseTime,
                                color="#847B00",
                                size=36,
                                weight=ft.FontWeight.BOLD
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    width=250,
                    height=60,
                    bgcolor="#FDFDBC",
                    border_radius=12,
                    padding=ft.padding.all(5),
                    margin=ft.margin.only(top=15, bottom=15)  # Reduced bottom margin
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        ),
        width=312,
        height=570,  # Increased height to accommodate new content
        bgcolor="white",
        border_radius=10,
        border=ft.border.all(2, "#0078D7"),
        padding=15,
        margin=ft.margin.only(top=20, bottom=20),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.Colors.GREY_400,
            offset=ft.Offset(2, 2)
        )
    )
    
    scrollable_content = ft.ListView(
        controls=[card_content],
        expand=True,
        spacing=0,
        padding=0,
        auto_scroll=False
    )

    # Progress indicator
    progress = ft.Container(
        content=ft.ProgressBar(value=1.0, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20)
    )
    
    # Bottom navigation button
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Text(
                            "FINISH", 
                            color="#375a04",
                            weight=ft.FontWeight.BOLD,
                            size=16
                        ),
                        style=ft.ButtonStyle(
                            bgcolor={"": "#80ffbe"},
                            shape=ft.RoundedRectangleBorder(radius=30),
                        ),
                        width=280,
                        height=50,
                        on_click=lambda e: goto_time(page, user_id)
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
                content=scrollable_content,
                alignment=ft.alignment.center,
                expand=True,
                width=312 
            ),
            progress,
            bottom_nav
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
        expand=True
    )
    
    # Background with landscape image
    background = ft.Container(
        content=ft.Image(
            src="THESIS-main/THESIS/gui/hhh/assets/landscape_background.png",
            width=page.width,
            height=page.height,
            fit=ft.ImageFit.COVER
        ),
        expand=True
    )
    
    # Use Stack with background
    stack = ft.Stack(
        [
            background,
            main_content
        ],
        expand=True
    )
    
    # Add the view to the page
    page.views.append(
        ft.View(
            "/pretest-score",
            [stack],
            padding=0
        )
    )
    
    page.update()