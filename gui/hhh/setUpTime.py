import flet as ft
import urllib.parse
import pymongo
from pymongo.errors import ConfigurationError
import sys

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

def add_time_to_db(user_id, time):
    """Adds the selected time to the database."""
    usercol = connect_to_mongoDB()
    usercol.update_one({"user_id": user_id}, {"$set": {"time": time}})
    print(f"User {user_id} time updated to {time}")

def goto_login(page):
    """Navigates to the login page."""
    route = "/login"
    page.go(route)
    page.update()

def set_up_time_page(page: ft.Page, image_urls: list):
    """Defines the Setup Time Selection Page with Routing"""
    
    def get_user(page):
        """Retrieves user_id from previous page session."""
        page.session.get("user_id")  # Get user ID from session
        if page.session.get("user_id") is None:
            print("No user_id found in session.")
            return None
        return page.session.get("user_id")

    selected_card = None  # Store the selected time preference

    def on_card_click(e, card):
        """Handles selection of a time option, allowing only one to be highlighted."""
        nonlocal selected_card
        
        # Reset previous selection
        if selected_card:
            selected_card.bgcolor = selected_card.data  # Restore original color
            selected_card.border = None
        
        # Highlight new selection
        card.bgcolor = "#FFE48D"  # Darker yellow when selected
        card.border = ft.border.all(2, "#4285F4")  # Blue border
        selected_card = card
        page.update()

    def on_next_click(e):
        """Handles 'NEXT' button click, ensuring a selection is made before proceeding."""
        user_id = get_user(page)  # Get user ID from session
        time = None  # Default time value
        if selected_card:
            selected_text = selected_card.content.controls[0].content.value  # Get card level
            if selected_text == "A1":
                time = 0.083  # 5 minutes in hours
            elif selected_text == "A2":
                time = 0.167  # 10 minutes in hours
            elif selected_text == "A3":
                time = 0.25  # 15 minutes in hours
            elif selected_text == "A4":
                time = 0.333  # 20 minutes in hours
            print(f"Selected: {selected_text}")  # Show in output
            add_time_to_db(user_id, time)  # Add to DB
            goto_login(page)  # Navigate to time setup page
            page.open(ft.SnackBar(ft.Text(f"User successfully registered!"), bgcolor="#4CAF50", duration=2000))
        else:
            page.open(ft.SnackBar(ft.Text("Please select a target time."), bgcolor="#FF5722", duration=2000))

    page.views.append(
        ft.View(
            route="/setup-time",
            controls=[
                ft.Container(
                    expand=True,
                    padding=20,
                    bgcolor="white",  # White background as shown in image
                    content=ft.Column(
                        [
                            # Progress Bar
                            ft.Container(
                                bgcolor="#BBDEFB",  # Light blue progress bar
                                height=10,
                                width=350,
                                border_radius=10,
                                margin=ft.margin.only(top=30, bottom=30),
                            ),

                            # Title
                            ft.Text(
                                "How often do you want to learn?",
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                color="black",  # Black text
                                text_align=ft.TextAlign.CENTER,
                            ),
                            
                            # Space between title and cards
                            ft.Container(height=20),
                            
                            # Options for learning time - styled as in the image
                            create_time_option("A1", "5 minutes per day", "#3CEAB3", on_card_click),
                            
                            ft.Container(height=15),  # Gap between cards
                            
                            create_time_option("A2", "10 minutes per day", "#9EEB51", on_card_click),
                            
                            ft.Container(height=15),  # Gap between cards
                            
                            create_time_option("A3", "15 minutes per day", "#F3CA3E", on_card_click),
                            
                            ft.Container(height=15),  # Gap between cards
                            
                            create_time_option("A4", "20 minutes per day", "#F5833C", on_card_click),
                            
                            # Note text
                            ft.Container(
                                content=ft.Text(
                                    "You can change this later.",
                                    size=14,
                                    color="grey",
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                margin=ft.margin.only(top=15, bottom=15),
                            ),
                            
                            # Spacer to push button to bottom
                            ft.Container(expand=True),
                            
                            # Next Button at the bottom
                            ft.Container(
                                content=ft.Text(
                                    "NEXT", 
                                    size=16, 
                                    weight=ft.FontWeight.BOLD, 
                                    color="white", 
                                    text_align=ft.TextAlign.CENTER
                                ),
                                bgcolor="#4285F4",  # Blue button as in image
                                border_radius=10,
                                width=350,
                                height=50,
                                alignment=ft.alignment.center,
                                on_click=on_next_click,
                                margin=ft.margin.only(bottom=30),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                        expand=True
                    ),
                )
            ],
            bgcolor="white"
        )
    )

def create_time_option(level, text, badge_color, click_handler):
    """Creates a time option card with a colored badge as shown in the image."""
    
    card = ft.Container(
        content=ft.Row(
            [
                # Circular badge with level indicator
                ft.Container(
                    content=ft.Text(
                        level,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color="black",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    width=40,
                    height=40,
                    border_radius=20,  # Make it circular
                    bgcolor=badge_color,
                    alignment=ft.alignment.center,
                ),
                
                # Option text
                ft.Text(
                    text,
                    size=16,
                    color="black",
                )
            ],
            spacing=15,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.all(15),
        bgcolor="#FFF9C4",  # Light yellow background for all cards
        data="#FFF9C4",  # Store original color for reset
        border_radius=15,
        width=350,
        height=70,
        alignment=ft.alignment.center_left,  # Align content to the left
    )
    
    # Attach click handler to the card
    card.on_click = lambda e: click_handler(e, card)
    
    # Wrap in container for centering
    return ft.Container(
        content=card,
        alignment=ft.alignment.center,
        width=400
    )