import flet as ft
import pymongo
from pymongo.errors import ConfigurationError
import sys
from qbank import module_bank

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
    page.session.set("user_id", user_id)  # Store username in session
    route = f"/setup-proficiency"
    page.go(route)
    page.update()
    
class Level:  # Level class
    def __init__(self, module_name, lesson_number):
        self.module_name = module_name
        self.lesson_name = str(lesson_number)
        self.completed = False
        self.pass_threshold = 50
        self.questions_answers = self.create_questions()

    def create_questions(self):
        """Fetches questions from the specified module and lesson in module_bank."""
        global module_bank
        if self.module_name in module_bank:
            module = module_bank[self.module_name]
            # Add "Lesson" here when looking up in module_bank
            lesson_key = f"Lesson {self.lesson_name}"
            if lesson_key in module:
                return module[lesson_key]
            else:
                # Suppress the "not found" message since we're loading from DB
                return []
        else:
            # Suppress the "not found" message since we're loading from DB
            return []

class Question: # Question class
    def __init__(self, qbank):
        self.id = qbank["id"]
        self.type = qbank["type"]
        self.question = qbank["question"]
        self.choices = qbank["choices"]
        self.correct_answer = qbank["correct_answer"]
        self.vocabulary = qbank["vocabulary"]

class ChapterTest: # Chapter Test class
    def __init__(self, questions_answers):
        self.questions_answers = questions_answers
        self.completed = False
        self.pass_threshold = 70

class Module:  # Module class
    def __init__(self, name, user_id, lesson_count):
        self.name = name
        self.user_id = user_id
        self.completed = False
        self.levels = self.create_levels(lesson_count)
        self.chapter_test = self.create_chapter_test()

    def create_levels(self, lesson_count):  # Create levels
        levels = [Level(self.name, lesson_number) for lesson_number in range(1, lesson_count + 1)]
        return levels

    def insert_levels(self, levels):
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": self.user_id})
        if user:
            user["modules"] = user.get("modules", [])
            for level in levels:
                level_data = {
                    "lesson_name": level.lesson_name,
                    "module_name": level.module_name,
                    "completed": level.completed,
                    "pass_threshold": level.pass_threshold,
                    "questions_answers": level.questions_answers
                }
                for module in user["modules"]:
                    if module["name"] == self.name:
                        module["levels"].append(level_data)
                        break
                else:
                    user["modules"].append({
                        "name": self.name,
                        "user_id": self.user_id,  # Ensure user_id is included
                        "completed": self.completed,
                        "levels": [level_data],
                        "chapter_test": self.chapter_test.__dict__
                    })
            usercol.update_one({"user_id": self.user_id}, {"$set": {"modules": user["modules"]}})

    def create_chapter_test(self):  # Create chapter test
        all_questions = {}
        for level in self.levels:
            for question in level.questions_answers:
                if "correct_answer" in question:
                    all_questions[question["question"]] = question["correct_answer"]
        return ChapterTest(all_questions)

def register_user(user_id, username, email, password):
    usercol = connect_to_mongoDB()
    new_user = {
        "user_id": user_id,
        "user_name": username,
        "email": email,
        "password": password,
        "modules": [],
        "questions_correct": [],
        "questions_incorrect": []
    }
    usercol.insert_one(new_user)

    # Now insert all modules into the new user's profile
    for module_name in module_bank:
        module = Module(name=module_name, user_id=user_id, lesson_count=len(module_bank[module_name]))
        module.insert_levels(module.levels)

    print(f"User {username} registered successfully!")

def register_page(page: ft.Page):
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
        """Handles the Register button click event."""
        username = username_field.value
        email = email_field.value
        password = password_field.value
        retype_password = retype_password_field.value

        user_exists = check_user(username)  # Check if the username already exists
        if not username or not email or not password or not retype_password:
                page.open(ft.SnackBar(ft.Text(f"Please fill in all fields!"), bgcolor="#4CAF50"))
                page.update()
                return
        elif password != retype_password:
            page.open(ft.SnackBar(ft.Text(f"Passwords do not match!"), bgcolor="#4CAF50"))
            page.update()
            return
        elif not user_exists:
            page.open(ft.SnackBar(ft.Text(f"Username already exists!"), bgcolor="#4CAF50"))
            page.update()
            return
        else:
            user_id = get_next_user_id()  # Get the next user ID
            register_user(user_id, username, email, password)  # Function to register the user in the database
            page.update()
            goto_proficiency(page, user_id)  # Navigate to proficiency setup page
            page.update()
            
    
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