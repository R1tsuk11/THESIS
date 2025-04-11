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
    
def goto_proficiency(page, username):
    """Navigates to the proficiency setup page with username as a route parameter."""
    page.session.set("username", username)  # Store username in session
    route = f"/setup-proficiency"
    page.go(route)
    page.update()
    
def register_user(username, email, password):
    """Register a new user in the database."""
    usercol = connect_to_mongoDB()
    user_id = get_next_user_id()  # Get the next user ID
    usercol.insert_one({"user_id": user_id, "user_name": username, "email": email, "password": password})
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
        if user_exists:
            register_user(username, email, password)  # Function to register the user in the database
            page.update()
            goto_proficiency(page, username)
            page.update()
        else:
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
                page.open(ft.SnackBar(ft.Text(f"Error!"), bgcolor="#4CAF50"))
                page.update()
                return
    
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