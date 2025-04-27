import flet as ft
import pymongo
from pymongo.errors import ConfigurationError
import sys
import json
import pprint
import os

uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

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

    def to_dict(self):
        return {
            "question": self.question,
            "answer": self.answer,
            "vocabulary": self.vocabulary,
            "type": self.type,
            "choices": self.choices,
            "correct_answer": self.correct_answer,
            "difficulty": self.difficulty,
            "response_time": self.response_time
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
            "time": self.time
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

        if os.path.exists("temp_chaptertest_data.json"):
            with open("temp_chaptertest.json", "r") as f:
                chapter_test_data = json.load(f)

            module_id = chapter_test_data["module_id"]

            self.chapter_test_records[module_id] = chapter_test_data

        if updated_user and updated_user.user_id == user_id:
            print("Loaded updated user from session.")
            self.__dict__.update(updated_user.__dict__)

            correct_answers = page.session.get("correct_answers")
            incorrect_answers = page.session.get("incorrect_answers")
            if correct_answers and incorrect_answers:
                questions_correct = {k: Question(v) if isinstance(v, dict) else v for k, v in correct_answers.items()}
                questions_incorrect = {k: Question(v) if isinstance(v, dict) else v for k, v in incorrect_answers.items()}
                self.questions_correct = questions_correct
                self.questions_incorrect = questions_incorrect
                
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

    def save_user(self, page):
        """Saves user data to the database."""
        self.save_library()
        
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

def main_menu_page(page: ft.Page):
    """Main menu page with module cards"""

    # Header - empty blue container with no text
    header = ft.Container(
        content=ft.Row([], alignment=ft.MainAxisAlignment.CENTER),  # Empty row
        bgcolor="#0066FF",  # Blue color matching the image
        height=60,
        padding=10
    )

    # Create modules title
    modules_title = ft.Container(
        content=ft.Text(
            "Modules",
            size=18,
            color="#FFFFFF",  # White text
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        bgcolor="#4285F4",  # Blue button color from image
        width=300,
        height=50,
        border_radius=25,
        alignment=ft.alignment.center,
        margin=ft.margin.symmetric(vertical=10)
    )

    def on_profile_click(e):
        """Handles profile icon click event."""
        print("Profile icon clicked")
        
    def navigate_to_levels(e, user, module_id):
        """Navigates to levels page"""
        cache_modules_to_temp(user.modules)  # Cache modules to temp file
        cache_library_to_temp(user.library)  # Cache library to temp file
        page.session.set("modules", user.modules)
        page.session.set("module_id", module_id)
        page.go("/levels")

    # Function to create a module card
    def create_module_card(module_id, main_button_text, sub_button_text, main_color, sub_color, bg_color="#2A2A2A"):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(
                                    main_button_text,
                                    color="#000000",
                                    weight=ft.FontWeight.BOLD,
                                    size=16,
                                    text_align=ft.TextAlign.CENTER,  # Center text
                                ),
                                bgcolor=main_color,
                                border_radius=15,
                                padding=10,
                                width=180,
                                alignment=ft.alignment.center,  # Center content
                            ),
                            ft.Icon(
                                ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                                color="#FFFFFF",  # White arrow
                                size=20,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,  # Keep arrow at right
                    ),
                    ft.Container(
                        content=ft.Text(
                            sub_button_text,
                            color="#FFFFFF",  # White text
                            size=14,
                            text_align=ft.TextAlign.CENTER,  # Center text
                        ),
                        bgcolor=sub_color,
                        border_radius=15,
                        padding=10,
                        width=200,
                        alignment=ft.alignment.center,  # Center content
                        margin=ft.margin.only(top=10),  # Remove left margin to center it
                    ),
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,  # Center column contents
            ),
            bgcolor=bg_color,  # Dark card background
            border_radius=15,
            padding=15,
            margin=ft.margin.only(bottom=15),
            width=300,
            on_click=lambda e: navigate_to_levels(e, user, module_id),  # Navigates to Levels when clicked
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
    # Create the bottom navigation bar
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.MILITARY_TECH_OUTLINED,
                    icon_color="#FFFFFF",
                    icon_size=24,
                ),
                ft.IconButton(
                    icon=ft.Icons.MENU_BOOK_OUTLINED,
                    icon_color="#FFFFFF",
                    icon_size=24,
                ),
                ft.IconButton(
                    icon=ft.Icons.HOME_OUTLINED,
                    icon_color="#FFFFFF",
                    icon_size=24,
                    on_click=on_profile_click(page)
                ),
                ft.IconButton(
                    icon=ft.Icons.PERSON_OUTLINED,
                    icon_color="#FFFFFF",
                    icon_size=24,
                ),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    icon_color="#FFFFFF",
                    icon_size=24,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
        bgcolor="#280082",  # Dark purple color
        height=60,
        padding=10
    )

    # Main content with centered items
    content = ft.Column(
        [
            header,
            logout_button,
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