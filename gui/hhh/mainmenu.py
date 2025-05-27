import flet as ft
import pymongo
from pymongo.errors import ConfigurationError
import sys
import json
import pprint
import os
from datetime import datetime
from supermemo_engine import prepare_daily_review
import time
import threading

uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

user_active = True
usage_time_seconds = 0
idle_seconds = 0
IDLE_THRESHOLD = 120  # 2 minutes

def start_usage_timer(page):
    def timer_loop():
        global usage_time_seconds, idle_seconds, user_active
        while True:
            time.sleep(1)
            if user_active:
                usage_time_seconds += 1
                idle_seconds += 1
                # Optionally update UI or save to session/db periodically
                if idle_seconds >= IDLE_THRESHOLD:
                    user_active = False  # User is now idle
                    print("[DEBUG] User is idle, pausing usage timer.")
            else:
                # Wait for activity to resume
                time.sleep(1)
    threading.Thread(target=timer_loop, daemon=True).start()

def reset_idle_timer(e=None):
    global user_active, idle_seconds
    user_active = True
    idle_seconds = 0
    print("[DEBUG] User is active again, resuming usage timer.")

def show_daily_review_overlay(page):
    overlay = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, color="#0078D7", size=60),
                    padding=ft.padding.only(top=40)
                ),
                ft.Container(
                    content=ft.Text(
                        "Daily Review Required!",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color="#0078D7",
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=ft.padding.only(bottom=5)
                ),
                ft.Container(
                    content=ft.Text(
                        "Please complete your daily review before proceeding.",
                        size=16,
                        color="#424242",
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=ft.padding.only(bottom=20)
                ),
                ft.ElevatedButton(
                    "Start Review",
                    width=200,
                    style=ft.ButtonStyle(
                        bgcolor={"": "#0078D7"},
                        color={"": "#FFFFFF"},
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    on_click=lambda e: (
                        page.overlay.clear(),
                        page.update(),
                        page.go("/daily-review")
                    )
                )
            ],
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        ),
        alignment=ft.alignment.center,
        bgcolor="#F5F5F5",
        width=page.width,
        height=page.height,
        border_radius=0,
        opacity=0.98,
        animate_opacity=200,
        padding=40
    )
    page.overlay.clear()
    page.overlay.append(overlay)
    page.update()

def is_first_login_today(last_login=None):
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"Today's date: {today_str}, Last login date: {last_login}")
    return today_str != last_login

def update_last_login_date(user):
    today_str = datetime.now().strftime("%Y-%m-%d")
    usercol = connect_to_mongoDB()
    usercol.update_one({"user_id": user.user_id}, {"$set": {"last_login_date": today_str}})

def cache_modules_to_temp(modules):
    def module_to_dict(module):
        return {
            "user_id": module.user_id,
            "id": module.id,
            "desc": module.desc,
            "eng_name": module.eng_name,
            "waray_name": module.waray_name,
            "completed": getattr(module, "completed", False),
            "levels": [
                {
                    "id": level.lesson_id,
                    "module_id": level.module_name,
                    "questions_answers": [q.__dict__ for q in level.questions_answers],
                    "completed": getattr(level, "completed", False),
                    "grade_percentage": getattr(level, "grade_percentage", 0),
                    "pass_threshold": getattr(level, "pass_threshold", 0),
                    "completion_time": getattr(level, "completion_time", 0),
                }
                for level in module.levels
            ],
            "chapter_test": {
                "module_id": module.chapter_test.module_id,
                "questions_answers": module.chapter_test.questions_answers,
                "completed": module.chapter_test.completed,
                "pass_threshold": module.chapter_test.pass_threshold
            }
        }

    with open("temp_modules.json", "w") as f:
        json.dump([module_to_dict(m) for m in modules], f)

def cache_library_to_temp(library):
    with open("temp_library.json", "w") as f:
        json.dump(library, f)

def clear_temp_library_cache():
    if os.path.exists("temp_library.json"):
        os.remove("temp_library.json")

def clear_temp_chaptertest_cache():
    if os.path.exists("temp_chaptertest_data.json"):
        os.remove("temp_chaptertest_data.json")

def connect_to_mongoDB():
    try:
        arami = pymongo.MongoClient(uri)["arami"]
        usercol = arami["users"]
        return usercol
    except ConfigurationError as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit("Terminating the program due to MongoDB connection failure.")

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

    def to_dict(self):
        return {
            "question": self.question,
            "answer": self.answer,
            "vocabulary": self.vocabulary,
            "type": self.type,
            "choices": self.choices,
            "correct_answer": self.correct_answer,
            "difficulty": self.difficulty,
            "response_time": self.response_time,
            "word_to_translate": self.word_to_translate
        }

class Level:  # Level class
    def __init__(self, level):
        self.module_name = level["module_name"]
        self.lesson_id = level["lesson_id"]
        self.completed = level["completed"]
        self.grade_percentage = level["grade_percentage"]
        self.completion_time = level["completion_time"]
        self.pass_threshold = level["pass_threshold"]
        self.questions_answers = self.load_questions(level)

    def to_dict(self):
        return {
            "lesson_id": self.lesson_id,
            "module_name": self.module_name,
            "questions_answers": [
                q.to_dict() if hasattr(q, 'to_dict') else {
                    "question": str(q)  # or however you want to serialize the question
                }
                for q in self.questions_answers
            ],
            "completed": self.completed,
            "grade_percentage": self.grade_percentage,
            "completion_time": self.completion_time,
            "pass_threshold": self.pass_threshold
        }

    def load_questions(self, level):
        questions = []
        for question_data in level["questions_answers"]:
            questions.append(Question(question_data))
        return questions

class Achievements: # Achievements class
    def __init__(self, achievement): # Initialize achievements
        self.id = achievement["id"]
        self.name = achievement["name"]
        self.description = achievement["description"]
        self.icon = achievement["icon"]
        self.completed = achievement["completed"]

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "completed": self.completed
        }

class ChapterTest: # Chapter Test class
    def __init__(self, chapter_test):
        self.module_id = chapter_test["module_id"]
        self.questions_answers = chapter_test["questions_answers"]
        self.completed = chapter_test["completed"]
        self.pass_threshold = chapter_test["pass_threshold"]

class Module:  # Module class
    def __init__(self, module):
        self.id = module["id"]
        self.waray_name = module["waray_name"]
        self.eng_name = module["eng_name"]
        self.desc = module["desc"]
        self.user_id = module["user_id"]
        self.completed = module["completed"]
        self.levels = self.load_levels(module["levels"])
        self.chapter_test = ChapterTest(module["chapter_test"])

    def to_dict(self):
        return {
            "id": self.id,
            "waray_name": self.waray_name,
            "eng_name": self.eng_name,
            "desc": self.desc,
            "user_id": self.user_id,
            "completed": self.completed,
            "chapter_test": {
                "module_id": self.chapter_test.module_id,
                "questions_answers": self.chapter_test.questions_answers,
                "completed": self.chapter_test.completed,
                "pass_threshold": self.chapter_test.pass_threshold
            },
            "levels": [level.to_dict() for level in self.levels]
        }

    def load_levels(self, levels):
        lessons = []
        for level_data in levels:
            level = Level(level_data)
            lessons.append(level)
        return lessons

class User:  # User class
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.user_name = None
        self.proficiency = 0
        self.password = None
        self.library = []
        self.questions_incorrect = {}
        self.questions_correct = {}
        self.chapter_test_records = {}
        self.achievements = {}
        self.modules = {}
        self.time = 0
        self.email = None
        self.bkt_data = {}
        self.completion_percentage = 0
        self.proficiency_history = []

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "email": self.email,
            "password": self.password,
            "proficiency": self.proficiency,
            "library": self.library,
            "questions_correct": {
                key: val.to_dict() if not isinstance(val, dict) else val
                for key, val in self.questions_correct.items()
            },
            "questions_incorrect": {
                key: val.to_dict() if not isinstance(val, dict) else val
                for key, val in self.questions_incorrect.items()
            },
            "chapter_test_records": {
                module_id: {
                    "grade_percentage": data["grade_percentage"],
                    "total_time_spent": data["total_time_spent"],
                    "questions_correct": {
                        q: qdata.to_dict() if hasattr(qdata, "to_dict") else qdata
                        for q, qdata in data.get("questions_correct", {}).items()
                    },
                    "questions_incorrect": {
                        q: qdata.to_dict() if hasattr(qdata, "to_dict") else qdata
                        for q, qdata in data.get("questions_incorrect", {}).items()
                    }
                }
                for module_id, data in self.chapter_test_records.items()
            },
            "achievements": {
                key: val if isinstance(val, dict) else val.to_dict()
                for key, val in self.achievements.items()
            },
            "modules": [m.to_dict() for m in self.modules],
            "time": self.time,
            "bkt_data": self.bkt_data,
            "completion_percentage": self.completion_percentage,
            "proficiency_history": self.proficiency_history
        }

    def get_user(self, user_id):
        """Retrieves user data from the database."""
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": user_id})
        if user:
            self.user_id = user["user_id"]
            self.user_name = user["user_name"]
            self.email = user["email"]
            self.proficiency = user["proficiency"]
            self.password = user["password"]
            self.library = user["library"]
            self.questions_incorrect = user["questions_incorrect"]
            self.questions_correct = user["questions_correct"]
            self.chapter_test_records = user["chapter_test_records"]
            self.achievements = user["achievements"]
            self.modules = user["modules"]
            self.time = user["time"]
            self.bkt_data = user["bkt_data"]
            self.completion_percentage = user["completion_percentage"]
            self.proficiency_history = user["proficiency_history"]
        else:
            print("User not found in database.")
            return None
        
    def load_achievements(self, achievement_data):
        """Converts raw achievement data from the database into class instances."""
        loaded_achievements = {}

        for key, value in achievement_data.items():
            # Check if value is a dictionary and has necessary fields
            if isinstance(value, dict) and all(field in value for field in ["id", "name", "description", "icon", "completed"]):
                achievement_instance = Achievements(value)
                loaded_achievements[key] = achievement_instance
            else:
                print(f"Skipping invalid achievement format for {key}: {value}")

        self.achievements = loaded_achievements

    def load_data(self, user_id, page):
        """Loads user data from the session or database."""
        updated_user = page.session.get("user")

        if updated_user and updated_user.user_id == user_id:
            print("Loaded updated user from session.")
            self.__dict__.update(updated_user.__dict__)

            correct_answers = page.session.get("correct_answers")
            incorrect_answers = page.session.get("incorrect_answers")
            if correct_answers or incorrect_answers:
                # Append new correct answers to the existing ones
                for k, v in correct_answers.items():
                    if k not in self.questions_correct:
                        self.questions_correct[k] = Question(v) if isinstance(v, dict) else v

                # Append new incorrect answers to the existing ones
                for k, v in incorrect_answers.items():
                    if k not in self.questions_incorrect:
                        self.questions_incorrect[k] = Question(v) if isinstance(v, dict) else v

            if os.path.exists("temp_chaptertest_data.json"):
                with open("temp_chaptertest_data.json", "r") as f:
                    chapter_test_data = json.load(f)

                    # Convert each question dict to Question object
                    raw_questions = chapter_test_data.get("questions_answers", {})
                    converted_questions = {
                        qtext: Question(qdata) for qtext, qdata in raw_questions.items()
                    }

                    module_id = str(chapter_test_data["module_id"])

                    # Replace the raw dict with object instances
                    chapter_test_data["questions_answers"] = converted_questions

                    # Debug: print a sample entry to verify conversion
                    print("\n[DEBUG] Converted Questions for Module ID", module_id)
                    for qtext, obj in converted_questions.items():
                        print(f"- {qtext}: {type(obj)}")

                    # Save it in user records
                    self.chapter_test_records[module_id] = chapter_test_data
                
            return self
        else:
            # Fallback to DB
            self.get_user(user_id)

            # Make sure modules and achievements are properly restored
            self.modules = [Module(m) if isinstance(m, dict) else m for m in self.modules]
            self.achievements = {k: Achievements(v) if isinstance(v, dict) else v for k, v in self.achievements.items()}

            page.session.set("user", self)  # Cache it for later updates
            page.open(ft.SnackBar(ft.Text("Successfully loaded data!"), bgcolor="#4CAF50"))
            return self

    def save_library(self):
        if os.path.exists("temp_library.json"):
            with open("temp_library.json", "r") as f:
                self.library = json.load(f)
        else:
            print("No temp library cache found.")

    def save_bkt_data(self):
        if os.path.exists("temp_bkt_data.json"):
            with open("temp_bkt_data.json", "r") as f:
                self.bkt_data = json.load(f)
        else:
            print("No temp library cache found.")

    def save_prof_history(self):
        if os.path.exists("temp_prof_history.json"):
            with open("temp_prof_history.json", "r") as f:
                self.proficiency_history = json.load(f)
                self.proficiency = self.proficiency_history[-1] if self.proficiency_history else 0
        else:
            print("No temp library cache found.")

    def save_lstm_counter(self):
        if os.path.exists("lstm_counter.json"):
            with open("lstm_counter.json", "r") as f:
                lstm_counter = json.load(f)
                usercol = connect_to_mongoDB()
                usercol.update_one(
                    {"user_id": self.user_id},
                    {"$set": {"lstm_counter": lstm_counter}},
                    upsert=True
                )
        else:
            print("No temp lstm counter cache found.")

    def save_user(self, page):
        """Saves user data to the database."""
        self.save_library()
        self.save_bkt_data()
        self.save_prof_history()

        print(f"[TEST] Usage time (seconds): {usage_time_seconds}, (minutes): {usage_time_seconds // 60}")
        
        usercol = connect_to_mongoDB()
        user_data = self.to_dict()

        result = usercol.update_one(
            {"user_id": self.user_id},
            {"$set": user_data},
            upsert=True
        )

        print("Matched:", result.matched_count,
            "Modified:", result.modified_count,
            "Upserted ID:", result.upserted_id)

        try:
            clear_temp_library_cache()
            clear_temp_chaptertest_cache()
        except FileNotFoundError:
            print("No temp file to clear.")

        page.open(ft.SnackBar(ft.Text("User data saved successfully!"), bgcolor="#4CAF50"))
        page.update()
        page.session.clear()
        page.go("/login")


def get_user_id(page):
        """Retrieves user_id from previous page session."""
        page.session.get("user_id")  # Get user ID from session
        if page.session.get("user_id") is None:
            print("No user ID found in session.")
            return None
        return page.session.get("user_id")

def main_menu_page(page: ft.Page, image_urls: list):
    """Main menu page with module cards"""

    # ----- HEADER with image -----
    header = ft.Container(
        content=ft.Stack(
            controls=[
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Row([], alignment=ft.MainAxisAlignment.CENTER),
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right,
                                colors=["#0066FF", "#9370DB"],
                            ),
                            height=70,
                            # padding=10,
                        ),
                    ],
                    spacing=0
                ),
                ft.Container(
                    content=ft.Image(
                        src=image_urls[1], #purple logo
                        width=120,
                        # height=65,
                        fit=ft.ImageFit.COVER
                    ),
                    alignment=ft.alignment.top_center,
                    margin=ft.Margin(top=20, left=0, right=0, bottom=15),
                )
            ]
        ),
        # width=500
    )

    # Create modules title
    modules_title = ft.Container(
        content=ft.Text(
            "Modules",
            size=15,
            color="#FFFFFF",  # White text
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        bgcolor="#397BFF", 
        width=300,
        height=45,
        border_radius=25,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, "#000000"),
            offset=ft.Offset(0, 0),
        ),
        margin=ft.Margin(top=0, left=0, right=0, bottom=10)
    )

    def on_profile_click(e):
        """Handles profile icon click event."""
        print("Profile icon clicked")
        
    def navigate_to_levels(e, user, module_id):
        """Navigates to levels page if prerequisites are met."""
        # Find the index of the selected module
        module_ids = [m.id for m in user.modules]
        try:
            idx = module_ids.index(module_id)
        except ValueError:
            page.open(ft.SnackBar(ft.Text("Module not found."), bgcolor="#FF5252"))
            return

        selected_module = user.modules[idx]

        # Check if selected module is already completed
        if getattr(selected_module, "completed", False):
            page.open(ft.SnackBar(ft.Text("This module is already completed."), bgcolor="#FFC107"))
            return

        # Check if all previous modules are completed
        if idx > 0:
            for prev_module in user.modules[:idx]:
                if not getattr(prev_module, "completed", False):
                    page.open(ft.SnackBar(ft.Text("Please complete previous modules first."), bgcolor="#FF5252"))
                    return

        # Proceed if allowed
        cache_modules_to_temp(user.modules)  # Cache modules to temp file
        cache_library_to_temp(user.library)  # Cache library to temp file
        page.session.set("modules", user.modules)
        page.session.set("module_id", module_id)
        page.go("/levels")

    # Function to create a module card
    def create_module_card(module_id, main_button_text, sub_button_text, main_color, sub_color, bg_color="#2A2A2A"):
        # Create the background container with image
        module_id = int(module_id) if isinstance(module_id, str) and module_id.isdigit() else module_id
        
        # Set colors and background image based on module_id
        if module_id == 1:      # KAMUSTAHAY
            bg_image = image_urls[2] 
            main_color = "#FFC124"
            sub_color = "#FFE850"
        elif module_id == 2:    # KALAKAT
            bg_image = image_urls[3]
            main_color = "#3FEA8C"
            sub_color = "#79E17F"
        elif module_id == 3:    # PAMALIT
            bg_image = image_urls[4]
            main_color = "#FFAD60"
            sub_color = "#D1D1A7"
        elif module_id == 4:     # PANGAON
            bg_image = image_urls[5]
            main_color = "#86C8CD"
            sub_color = "#6CCDB9"
        elif module_id == 5:    # SLANG
            bg_image = image_urls[6]
            main_color = "#86C8CD"
            sub_color = "#FFE850"
        else:
            bg_image = image_urls[2]
            main_color = "#86C8CD"
            sub_color = "#FFE850"

        # Background image container
        bg_container = ft.Container(
            content=ft.Image(
                src=bg_image,
                width=300,
                height=150,
                fit=ft.ImageFit.COVER,
                error_content=ft.Container(
                    width=300,
                    height=150,
                    bgcolor="orange",
                    border_radius=15
                )
            ),
            border_radius=15,
            width=300,
            height=150
        )
        
        # Main content container with title and description
        content_container = ft.Container(
            content=ft.Column(
                [
                    # TITLE
                    ft.Container(
                        content=ft.Text(
                            main_button_text,
                            color="#FFFFFF",
                            weight=ft.FontWeight.BOLD,
                            size=16,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        bgcolor=main_color,
                        border_radius=15,
                        padding=5,
                        width=180,
                        margin=ft.margin.only(top=15),
                        alignment=ft.alignment.center,
                    ),
                    # DESCRIPTION
                    ft.Container(
                        content=ft.Text(
                            sub_button_text,
                            color="#FFFFFF",
                            size=11,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        bgcolor=ft.Colors.with_opacity(0.7,sub_color),
                        border_radius=10,
                        padding=8,
                        width=200,
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(top=8),
                    ),
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
        )
        
        # Arrow icon container
        arrow_container = ft.Container(
            content=ft.Icon(
                ft.Icons.ARROW_FORWARD,
                color="#FFFFFF",
                size=20,
            ),
            alignment=ft.alignment.top_right,
            padding=10
        )
        
        # Final card container with shadow
        return ft.Container(
            content=ft.Stack(
                controls=[
                    bg_container,
                    content_container,
                    arrow_container
                ]
            ),
            border_radius=15,
            width=300,
            height=150,
            margin=ft.margin.only(bottom=15),
            shadow=ft.BoxShadow(
                blur_radius=8,
                color=ft.Colors.BLACK26,
                offset=ft.Offset(0, 4),
                spread_radius=1,
            ),
            # Keep your existing navigation logic
            on_click=lambda e, module_id=module_id: navigate_to_levels(e, user, module_id),
        )

    # Create the module cards with updated colors
    cards = []
    user_id = get_user_id(page)  # Get user ID from session
    user = User().load_data(user_id, page)  # Load user data
    pprint.pprint(user.to_dict())
    for module in user.modules:
        card = create_module_card(module.id, module.waray_name, module.eng_name, "#FFB74D", "#FF9800")
        cards.append(card)

    # Logout button
    logout_button = ft.IconButton(
        icon=ft.Icons.LOGOUT,
        icon_color="#FFFFFF",
        icon_size=24,
        tooltip="Logout",
        on_click=lambda e: user.save_user(page)  # Navigate to login page on logout
    )

    def navigate_to_achievements(e, user):
        # Extract needed data from user
        achievement_data = {
            "username": user.user_name,
            "progress_percentage": user.completion_percentage,
            "lessons_completed": len([l for m in user.modules for l in m.levels if l.completed]),
            "words_learned": len(user.library),
            "language_proficiency": user.proficiency if hasattr(user, 'proficiency') else 0,
            "achievements": user.achievements
        }
        
        # Store in session
        page.session.set("achievement_data", achievement_data)
        page.go("/achievements")

    def navigate_to_word_library(e, user_library):
        # Store just the library in the page session
        page.session.set("user_library", user_library)
        page.go("/word-library")

    # Create the bottom navigation bar
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.MENU_BOOK_OUTLINED,
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=lambda e: navigate_to_word_library(e, user.library)  # Pass library directly
    ),
                    border_radius=20,
                    width=50, 
                    height=50, 
                    alignment=ft.alignment.center, 
                    padding=0, 
                    margin=5,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.HOME_OUTLINED,
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=lambda _: page.go("/main-menu")
                    ),
                    border_radius=20,
                    width=50,
                    height=50,
                    alignment=ft.alignment.center,
                    padding=0,
                    margin=5,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.PERSON,  
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=lambda e: navigate_to_achievements(e, user)  # Use the new function
                    ),
                    border_radius=20,
                    width=50,
                    height=50,
                    alignment=ft.alignment.center,
                    padding=0,
                    margin=5,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.SETTINGS_OUTLINED,  
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=lambda _: page.go("/settings")
                    ),
                    border_radius=20,
                    width=50,
                    height=50,
                    alignment=ft.alignment.center,
                    padding=0,
                    margin=5,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            vertical_alignment=ft.CrossAxisAlignment.CENTER, 
            height=60,  
        ),
        border_radius=25,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#30b4fc", "#2980b9"],
        ),
        height=70,  
        padding=ft.padding.symmetric(horizontal=15, vertical=5),
        margin=ft.margin.only(bottom=10, left=10, right=10),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, "#000000"),
            offset=ft.Offset(0, 0),
        ),
        alignment=ft.alignment.center,
    )

    # Main content with centered items
    content = ft.Column(
        [
            header,
            ft.Container(
                content=ft.Column(
                    [
                        modules_title,
                        *cards  # Iterate and insert all module cards
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True
            ),
            logout_button,
            bottom_nav,
        ],
        spacing=0,
        expand=True,
    )

    # Configure page settings
    page.padding = 0
    page.bgcolor = "#FFFFFF"  # Set page background to white
    
    # Add view with updated styling
    page.views.append(ft.View("/main-menu", controls=[content], padding=0, bgcolor="#FFFFFF"))  # White background
    page.update()

    start_usage_timer(page)

    # Attach reset_idle_timer to user interactions
    page.on_pointer_move = reset_idle_timer
    page.on_keyboard_event = reset_idle_timer
    page.on_click = reset_idle_timer

    # Retrieve last_login_date from database for the current user
    usercol = connect_to_mongoDB()
    user_db = usercol.find_one({"user_id": user.user_id})
    last_login = user_db.get("last_login_date") if user_db else None

    if is_first_login_today(last_login):
        print("Triggering daily review popup!")
        review_questions = prepare_daily_review(user.user_id)
        print("Review questions:", review_questions)
        page.session.set("daily_review_questions", review_questions)
        show_daily_review_overlay(page)
        update_last_login_date(user)