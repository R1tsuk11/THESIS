import flet as ft
import pymongo
from pymongo.errors import ConfigurationError
import sys

uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

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

class Level:  # Level class
    def __init__(self, level):
        self.module_name = level["module_name"]
        self.lesson_name = level["lesson_name"]
        self.completed = level["completed"]
        self.pass_threshold = level["pass_threshold"]
        self.questions_answers = self.load_questions(level)

    def load_questions(self, level):
        for question_data in level["questions_answers"]:
            Question(question_data)

class Achievements: # Achievements class
    def __init__(self, achievement): # Initialize achievements
        self.id = achievement["id"]
        self.name = achievement["name"]
        self.description = achievement["description"]
        self.icon = achievement["icon"]
        self.completed = achievement["completed"]

class ChapterTest: # Chapter Test class
    def __init__(self, chapter_test):
        self.questions_answers = chapter_test["questions_answers"]
        self.completed = chapter_test["completed"]
        self.pass_threshold = chapter_test["pass_threshold"]

class Module:  # Module class
    def __init__(self, module):
        self.name = module["name"]
        self.user_id = module["user_id"]
        self.completed = module["completed"]
        self.levels = self.load_levels(module["levels"])
        self.chapter_test = ChapterTest(module["chapter_test"])

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
        self.achievements = {}
        self.modules = {}

    def get_user(self, user_id):
        """Retrieves user data from the database."""
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": user_id})
        if user:
            self.user_id = user["user_id"]
            self.user_name = user["user_name"]
            self.proficiency = user["proficiency"]
            self.password = user["password"]
            self.library = user["library"]
            self.questions_incorrect = user["questions_incorrect"]
            self.questions_correct = user["questions_correct"]
            self.achievements = user["achievements"]
            self.modules = user["modules"]
        else:
            print("User not found in database.")
            return None
        
    def load_data(self, user_id, page):
        """Loads user data from the database."""
        self.get_user(user_id)
        if self.modules:
            for module in self.modules:
                Module(module)
            page.open(ft.SnackBar(ft.Text(f"Successfully loaded data!"), bgcolor="#4CAF50"))
        else:
            print("No modules found for this user.")
            return None
        
        if self.achievements:
            for _, achievement in self.achievements.items():
                Achievements(achievement)
            page.open(ft.SnackBar(ft.Text(f"Successfully loaded achievements!"), bgcolor="#4CAF50"))
        else:
            print("No achievements found for this user.")

    def save_user(self):
        """Saves user data to the database."""
        usercol = connect_to_mongoDB()
        user_data = {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "proficiency": self.proficiency,
            "password": self.password,
            "word_library": self.word_library,
            "questions_wrong": self.questions_wrong,
            "questions_correct": self.questions_correct,
            "achievements": self.achievements,
            "modules": self.modules
        }
        usercol.update_one({"user_id": self.user_id}, {"$set": user_data}, upsert=True)

def get_user_id(page):
        """Retrieves user_id from previous page session."""
        page.session.get("user_id")  # Get user ID from session
        if page.session.get("user_id") is None:
            print("No user ID found in session.")
            return None
        return page.session.get("user_id")

def main_menu_page(page: ft.Page):
    """Main menu page with module cards"""

    def on_profile_click(e):
        """Handles profile icon click event."""
        print("Profile icon clicked")
        user_id = get_user_id(page)  # Get user ID from session
        User().load_data(user_id, page)  # Load user data with user_id 1 for demonstration

    def navigate_to_levels(e):
        """Navigates to levels page"""
        page.go("/levels")

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

    # Function to create a module card
    def create_module_card(main_button_text, sub_button_text, main_color, sub_color, bg_color="#2A2A2A"):
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
            on_click=navigate_to_levels,  # Navigates to Levels when clicked
        )

    # Create the module cards with updated colors
    kamustahay_card = create_module_card("Kamustahay!", "Greetings and Introductions", "#FFD580", "#8B7E4F")
    oras_card = create_module_card("Oras", "Time / Date", "#74CFCF", "#7A9E9E")
    pagkain_card = create_module_card("Pangaan", "Ordering Food", "#74CFCF", "#7A9E9E")

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
            ft.Container(
                content=ft.Column(
                    [
                        modules_title,
                        kamustahay_card,
                        oras_card,
                        pagkain_card,
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