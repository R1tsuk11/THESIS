import flet as ft
import pymongo
from pymongo.errors import ConfigurationError
import sys
import asyncio

uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

def connect_to_mongoDB():
    try:
        arami = pymongo.MongoClient(uri)
        aramidb = arami["arami"]
        usercol = aramidb["users"]
        return usercol
    except ConfigurationError as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit("Terminating the program due to MongoDB connection failure.")

def check_user(username, password):
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_name": username, "password": password})
    if user:
        return user, user["user_id"]  # Return user data and user ID
    else:
        return None

def goto_main_menu(page, user_id):
    """Navigates to the main menu with the logged in user."""
    page.session.set("user_id", user_id)  # Store user ID in session
    route = "/main-menu"
    page.go(route)
    page.update()

def goto_register(page):
    page.go("/register")
    page.update()

def login_page(page: ft.Page, image_urls: list):
    username_field = ft.TextField(
        hint_text="Example: johndoe", 
        bgcolor="white", 
        border_color="lightgrey", 
        border_radius=8, 
        color="black"
    )
    password_field = ft.TextField(
        hint_text="********", 
        bgcolor="white", 
        password=True, 
        border_color="lightgrey", 
        border_radius=8, 
        color="black"
    )

    async def on_login_click(e):
        print("Login button clicked")
        username = username_field.value
        password = password_field.value
        user_exists = check_user(username, password)  # Function to check if user exists in the database

        if user_exists:
            page.open(ft.SnackBar(ft.Text(f"Welcome {username}!"), bgcolor="#4CAF50", duration=2000))
            page.update()
            await asyncio.sleep(2)
            goto_main_menu(page, user_exists[1])  # Pass user ID to the main menu
            page.update()
        else:
            page.open(ft.SnackBar(ft.Text(f"Invalid Credentials!"), bgcolor="#FF0000"))
            page.update()

    # Content container with the form elements
    login_content = ft.Container(
        content=ft.Column(
            [
                # Logo aligned to the right
                ft.Row(
                    [ft.Image(src=image_urls[1], height=70)],
                    alignment=ft.MainAxisAlignment.END
                ),
                # Welcome Text
                ft.Text("Let's Login!", size=26, weight=ft.FontWeight.BOLD, color="black"),
                ft.Text("Maupay nga pagbalik!", size=14, color="black"),
                # Username & Password Fields
                ft.Text("Username", color="black"),
                username_field,
                ft.Container(height=10),  # Padding
                ft.Text("Password", color="black"),
                password_field,
                # Forgot Password
                ft.Row(
                    [ft.TextButton(
                        "Forgot Password", 
                        on_click=lambda _: print("Forgot Password clicked"), 
                        style=ft.ButtonStyle(color="#4285F4")  # Blue color
                    )],
                    alignment=ft.MainAxisAlignment.START
                ),
                # Centered Login Section
                ft.Container(
                    content=ft.Column(
                        [
                # Login Button
                ft.ElevatedButton(
                    "Login",
                    width=300,
                    bgcolor="#4285F4",  # Blue color
                    color="white",
                    on_click=on_login_click,
                    icon=ft.Icons.ARROW_FORWARD,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=20)
                    )
                ),
                            # "Or" Divider
                            ft.Container(
                                content=ft.Text("Or", color="black", text_align=ft.TextAlign.CENTER),
                                padding=ft.padding.only(top=10, bottom=10),
                            ),
                            # Register Link
                            ft.TextButton(
                                "First time here? Register here",
                                on_click=lambda _: goto_register(page),
                                style=ft.ButtonStyle(color="#4285F4")  # Blue color
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    alignment=ft.alignment.center,
                    expand=True
                )
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START
        ),
        padding=ft.padding.all(25),
        width=400,
        bgcolor="white",
        border_radius=15
    )

    # Main container that centers the login content
    centered_container = ft.Container(
        content=login_content,
        alignment=ft.alignment.center,
        margin=ft.margin.only(top=50),  # Margin to center vertically
        expand=True  # Make container take all available space
    )

    page.views.append(
        ft.View(
            route="/login",
            controls=[centered_container],
            bgcolor="white"
        )
    )

    page.update()