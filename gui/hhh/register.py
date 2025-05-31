import flet as ft
import pymongo
from pymongo.errors import ConfigurationError
import sys
from qbank import module_bank, achievement_bank, eng_name_bank, waray_name_bank, desc_bank
from datetime import datetime
import re

uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

def connect_to_mongoDB():
    try:
        arami = pymongo.MongoClient(uri)["arami"]
        usercol = arami["users"]
        return usercol
    except ConfigurationError as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit("Terminating the program due to MongoDB connection failure.")

def get_next_user_id():
    arami = pymongo.MongoClient(uri)["arami"]
    aramidb = arami["counter"]
    
    # Ensure the initial value is set
    aramidb.update_one(
        {"_id": "user_id"},
        {"$setOnInsert": {"seq": 0}},
        upsert=True
    )
    
    ctr = aramidb.find_one_and_update(
        {"_id": "user_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=pymongo.ReturnDocument.AFTER
    )
    return ctr["seq"]

def check_user(username):
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_name": username})
    if user:
        return False # User already exists
    else:
        return True
    
def goto_proficiency(page, user_id):
    """Navigates to the proficiency setup page with username as a route parameter."""
    page.session.set("user_id", user_id)  # Store user ID in session
    route = "/setup-proficiency"
    page.go(route)
    page.update()
    
class Level:  # Level class
    def __init__(self, module_id, lesson_number):
        self.module_id = module_id
        self.lesson_id = lesson_number
        self.grade_percentage = 0
        self.completion_time = None
        self.completed = False
        self.pass_threshold = 50
        self.questions_answers = self.create_questions()

    def create_questions(self):
        """Fetches questions from the specified module and lesson in module_bank."""
        global module_bank
        if self.module_id in module_bank:
            module = module_bank[self.module_id]
            # Add "Lesson" here when looking up in module_bank
            lesson_key = f"Lesson {self.lesson_id}"
            if lesson_key in module:
                return module[lesson_key]
            else:
                # Suppress the "not found" message since we're loading from DB
                return []
        else:
            # Suppress the "not found" message since we're loading from DB
            return []

class Achievements: # Achievements class
    def __init__(self, achievement): # Initialize achievements
        self.id = achievement["id"]
        self.name = achievement["name"]
        self.description = achievement["description"]
        self.icon = achievement["icon"]
        self.completed = achievement["completed"]

class ChapterTest: # Chapter Test class
    def __init__(self, questions_answers, module_id):
        self.module_id = module_id
        self.questions_answers = questions_answers
        self.completed = False
        self.pass_threshold = 70

class Module:  # Module class
    def __init__(self, id, user_id, lesson_count):
        self.id = id
        self.eng_name = self.get_eng_name(id)
        self.waray_name = self.get_waray_name(id)
        self.desc = self.get_desc(id)
        self.user_id = user_id
        self.completed = False
        self.levels = self.create_levels(lesson_count)
        self.chapter_test = self.create_chapter_test()

    def get_eng_name(self, id):
        return eng_name_bank.get(id)

    def get_waray_name(self, id):
        return waray_name_bank.get(id)
    
    def get_desc(self, id):
        return desc_bank.get(id)

    def create_levels(self, lesson_count):  # Create levels
        levels = [Level(self.id, lesson_number) for lesson_number in range(1, lesson_count + 1)]
        return levels

    def insert_levels(self, levels):
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": self.user_id})
        if user:
            user["modules"] = user.get("modules", [])
            for level in levels:
                level_data = {
                    "lesson_id": level.lesson_id,
                    "module_name": level.module_id,
                    "completed": level.completed,
                    "pass_threshold": level.pass_threshold,
                    "questions_answers": level.questions_answers,
                    "grade_percentage": level.grade_percentage,
                    "completion_time": level.completion_time,
                }
                for module in user["modules"]:
                    if module["id"] == self.id:
                        module["levels"].append(level_data)
                        break
                else:
                    user["modules"].append({
                        "id": self.id,
                        "eng_name": self.eng_name,
                        "waray_name": self.waray_name,
                        "desc": self.desc,
                        "user_id": self.user_id,  # Ensure user_id is included
                        "completed": self.completed,
                        "levels": [level_data],
                        "chapter_test": self.chapter_test.__dict__
                    })
            usercol.update_one({"user_id": self.user_id}, {"$set": {"modules": user["modules"]}})

    def create_chapter_test(self):
        """Creates a chapter test using dedicated chapter test questions instead of random selection"""
        # Define mapping of module IDs to their dedicated chapter test dictionaries
        chapter_test_mapping = {
            "module_1": "chapterTest_mod1",
            "module_2": "chapterTest_mod2",
            "module_3": "chapterTest_mod3",
            "module_4": "chapterTest_mod4",
            "module_5": "chapterTest_mod5"
        }
        
        # Try to get dedicated chapter test questions
        try:
            # Import the dedicated chapter test dictionaries
            from qbank import chapterTest_mod1, chapterTest_mod2, chapterTest_mod3, chapterTest_mod4, chapterTest_mod5
            
            # Map module ID to the appropriate chapter test dictionary
            test_dict_name = chapter_test_mapping.get(self.id, None)
            if test_dict_name and test_dict_name in globals():
                # Get the dedicated test questions
                test_questions = globals()[test_dict_name]
                
                # Convert to dictionary with unique IDs as keys
                questions_dict = {}
                for question in test_questions:
                    question_key = str(question.get("id", hash(str(question))))
                    questions_dict[question_key] = question
                    
                print(f"Using dedicated chapter test for {self.id} with {len(questions_dict)} questions")
                return ChapterTest(questions_dict, self.id)
                
        except (ImportError, AttributeError) as e:
            print(f"Dedicated chapter test not found for {self.id}: {e}. Using fallback method.")
        
        # Fallback to the old method if dedicated tests aren't available
        all_questions = {}
        for level in self.levels:
            for question in level.questions_answers:
                # Only include questions that have a correct answer and aren't lesson type
                if "correct_answer" in question and question.get("type", "") != "Lesson":
                    # Use id as a unique key instead of question text
                    question_key = str(question.get("id", hash(str(question))))
                    all_questions[question_key] = question
        
        # Limit to 20 questions if we have more
        if len(all_questions) > 20:
            import random
            # Get a random selection of 20 questions
            selected_keys = random.sample(list(all_questions.keys()), 20)
            limited_questions = {key: all_questions[key] for key in selected_keys}
            return ChapterTest(limited_questions, self.id)
        else:
            # Use all questions if we have 20 or fewer
            return ChapterTest(all_questions, self.id)

def register_user(user_id, username, email, password):
    usercol = connect_to_mongoDB()
    new_user = {
        "user_id": user_id,
        "user_name": username,
        "email": email,
        "password": password,
        "modules": [],
        "library": [],
        "achievements": {},
        "questions_correct": {},
        "questions_incorrect": {},
        "chapter_test_records": {},
        "bkt_data": {
            "predictions": {},
            "fitted": False,
            "refit_counter": 0,
            "p_mastery": 0.5,
            "guess": 0.2,
            "slip": 0.1
        },
        "completion_percentage": 0,
        "proficiency_history": [],
        "lstm_counter": 0,
        "supermemo": {},
        "last_login_date": datetime.now().strftime("%Y-%m-%d"),
    }
    usercol.insert_one(new_user)

    # Now insert all modules into the new user's profile
    for module_id in module_bank:
        module = Module(id=module_id, user_id=user_id, lesson_count=len(module_bank[module_id]))
        module.insert_levels(module.levels)

    for _, achievement in achievement_bank.items():
        achievements = Achievements(achievement)
        usercol.update_one(
        {"user_id": user_id},
        {"$set": {f"achievements.{achievement['id']}": achievements.__dict__}}
        )

    print(f"User {username} registered successfully!")

def validate_email(email):
    """Validates that the email follows standard email format"""
    # Regular expression for basic email validation
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_regex, email))

def validate_password(password):
    """
    Validates password strength:
    - At least 8 characters long
    - Contains at least one digit
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one special character
    """
    # Check length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Check for digit
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one digit"
    
    # Check for uppercase letter
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for lowercase letter
    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check for special character
    special_chars = "!@#$%^&*()-_=+[]{}|;:'\",.<>/?`~"
    if not any(char in special_chars for char in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def validate_username(username):
    """
    Validates username:
    - Between 3-20 characters
    - Only contains letters, numbers, underscores, or hyphens
    - Doesn't start with a number
    """
    # Check length
    if len(username) < 3 or len(username) > 20:
        return False, "Username must be between 3-20 characters"
    
    # Check if starts with a number
    if username[0].isdigit():
        return False, "Username cannot start with a number"
    
    # Check characters
    username_regex = r'^[a-zA-Z][a-zA-Z0-9_-]*$'
    if not re.match(username_regex, username):
        return False, "Username can only contain letters, numbers, underscores, or hyphens"
    
    return True, "Username is valid"

def register_page(page: ft.Page, image_urls: list):
    """Defines the Register Page with Routing"""
    
    username_field = ft.TextField(
        bgcolor="white", 
        hint_text="Example: johndoe", 
        border_color="lightgrey", 
        border_radius=8, 
        color="black"
    )

    email_field = ft.TextField(
        bgcolor="white", 
        hint_text="Example: johndoe@gmail.com", 
        border_color="lightgrey", 
        border_radius=8, 
        color="black"
    )
        
    password_field = ft.TextField(
        bgcolor="white", 
        password=True,
        can_reveal_password=True,
        hint_text="********", 
        border_color="lightgrey", 
        border_radius=8, 
        color="black"
    )

    retype_password_field = ft.TextField(
        bgcolor="white", 
        password=True, 
        can_reveal_password=True,
        hint_text="********", 
        border_color="lightgrey", 
        border_radius=8, 
        color="black"
    )

    def on_register_click(e):
        """Handles the Register button click event with enhanced validation."""
        username = username_field.value
        email = email_field.value
        password = password_field.value
        retype_password = retype_password_field.value

        # Check if all fields are filled
        if not username or not email or not password or not retype_password:
            page.open(ft.SnackBar(ft.Text("Please fill in all fields!"), bgcolor="#F44336"))
            page.update()
            return
        
        # Validate username format
        username_valid, username_message = validate_username(username)
        if not username_valid:
            page.open(ft.SnackBar(ft.Text(username_message), bgcolor="#F44336"))
            page.update()
            return
            
        # Check if username exists
        user_exists = check_user(username)
        if not user_exists:
            page.open(ft.SnackBar(ft.Text("Username already exists!"), bgcolor="#F44336"))
            page.update()
            return
        
        # Validate email format
        if not validate_email(email):
            page.open(ft.SnackBar(ft.Text("Please enter a valid email address!"), bgcolor="#F44336"))
            page.update()
            return
        
        # Validate password strength
        password_valid, password_message = validate_password(password)
        if not password_valid:
            page.open(ft.SnackBar(ft.Text(password_message), bgcolor="#F44336"))
            page.update()
            return
        
        # Check if passwords match
        if password != retype_password:
            page.open(ft.SnackBar(ft.Text("Passwords do not match!"), bgcolor="#F44336"))
            page.update()
            return
        
        # All validations passed, proceed with registration
        user_id = get_next_user_id()
        register_user(user_id, username, email, password)
        page.update()
        goto_proficiency(page, user_id)
        page.update()
            
    password_requirements = ft.Text(
        "Password must be at least 8 characters and include uppercase, lowercase, number, and special character",
        size=10,
        color="#666666",
        italic=True
    )

    page.views.append(
        ft.View(
            route="/register",
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            # Back to Login Button
                            ft.Row(
                                [
                                    ft.TextButton(
                                        "← Back to Login",
                                        on_click=lambda _: page.go("/"),
                                        style=ft.ButtonStyle(
                                            color="#4285F4",  # Blue color for back button
                                            padding=ft.Padding(0, 5, 0, 10),  # Adjust spacing
                                        ),
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.START  # Align to left
                            ),

                            # Title & Subtitle
                            ft.Text("Register", size=28, weight=ft.FontWeight.BOLD, color="black"),
                            ft.Text("To start learning Waray!", size=14, color="#666666"),  # Dark gray for subtitle

                            # Input Fields
                            ft.Text("Username", color="black"),
                            username_field,

                            ft.Text("Email Address", color="black"),
                            email_field,

                            ft.Text("Password", color="black"),
                            password_field,
                            password_requirements,  # Add password requirements text

                            ft.Text("Retype Password", color="black"),
                            retype_password_field,

                            # Register Button
                            ft.Container(
                                content=ft.ElevatedButton(
                                    "Register",
                                    width=350,
                                    bgcolor="#4285F4",  # Blue register button
                                    color="white",
                                    on_click=on_register_click,
                                    icon=ft.icons.ARROW_FORWARD,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=20),
                                        padding=ft.Padding(10, 15, 10, 15),
                                    ),
                                ),
                                margin=ft.Margin(0, 20, 0, 0)  # Add space before button
                            )
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.START
                    ),
                    padding=ft.padding.symmetric(horizontal=20, vertical=50),  # Adjust margins
                    width=400,  # Match width in the image
                    bgcolor="white"  # White background
                )
            ],
            bgcolor="white"  # White background for the entire view
        )
    )