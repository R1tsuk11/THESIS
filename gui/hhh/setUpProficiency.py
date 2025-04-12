import urllib.parse
import flet as ft
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

def set_up_proficiency_page(page: ft.Page):
    """Defines the Setup Proficiency Page with Routing"""

    def get_user_id(page):
        """Retrieves user_id from previous page session."""
        page.session.get("user_id")  # Get user ID from session
        if page.session.get("user_id") is None:
            print("No user ID found in session.")
            return None
        return page.session.get("user_id")

    selected_card = None  # Store the currently selected card

    def on_card_click(e, card):
        """Handles card selection, ensuring only one is highlighted."""
        nonlocal selected_card
        
        # Reset previous selection
        if selected_card:
            selected_card.bgcolor = selected_card.data  # Restore original color
            selected_card.border = None  # Remove border

        # Set new selection
        card.bgcolor = "#FFE48D"  # Highlight with darker yellow when selected
        card.border = ft.border.all(2, "#4285F4")  # Add blue border
        selected_card = card  
        page.update()

    def on_next_click(e):
        """Navigates to setTime.py and prints the selected card."""
        user_id = get_user_id(page)  # Get user ID from session
        proficiency = None  # Default proficiency value
        if selected_card:
            selected_text = selected_card.content.controls[0].value  # Get card title
            if selected_text == "STARTER":
                proficiency = 0
            elif selected_text == "BEGINNER":
                proficiency = 0.5
            print(f"Selected: {selected_text}")  # Show in output
            add_proficiency_to_db(user_id, proficiency)  # Add to DB
            goto_time(page, user_id)  # Navigate to time setup page
        else:
            page.open(ft.SnackBar(ft.Text("Please select a proficiency level."), bgcolor="#FF5722", duration=2000))

    # Create selection cards with updated styling
    starter_card = create_proficiency_card(
        "STARTER", "First time to learn this language.", 
        "Diri ako maaram!", "#FFF9C4", on_card_click  # Light yellow color
    )
    
    beginner_card = create_proficiency_card(
        "BEGINNER", "I know some words.", 
        "Guti la it akon aram.", "#FFF9C4", on_card_click  # Same light yellow
    )

    page.views.append(
        ft.View(
            route="/setup-proficiency",
            controls=[
                ft.Container(
                    expand=True,
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
                                "How much can you speak Waray?",
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                color="black",
                                text_align=ft.TextAlign.CENTER,
                            ),
                            
                            # Space between title and cards
                            ft.Container(height=20),
                            
                            # Proficiency Selection Cards
                            starter_card,
                            
                            # Small gap between cards
                            ft.Container(height=15),
                            
                            beginner_card,
                            
                            # Spacer to push button to bottom
                            ft.Container(
                                expand=True
                            ),

                            # Next Button at the bottom
                            ft.Container(
                                content=ft.Text(
                                    "NEXT", 
                                    size=16, 
                                    weight=ft.FontWeight.BOLD, 
                                    color="white", 
                                    text_align=ft.TextAlign.CENTER
                                ),
                                bgcolor="#4285F4",  # Blue button
                                border_radius=10,
                                width=350,
                                height=50,
                                alignment=ft.alignment.center,
                                on_click=on_next_click,
                                margin=ft.margin.only(bottom=30),  # Add margin at bottom
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,  # Control spacing via Container height elements
                        expand=True  # Allow column to expand to fill space
                    ),
                    padding=20,
                    bgcolor="white"  # White background
                )
            ],
            bgcolor="white"  # White background for the entire view
        )
    )

def create_proficiency_card(title, description, sample_text, color, click_handler):
    """Creates a proficiency selection card with updated styling."""
    
    card = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    title, 
                    size=16, 
                    weight=ft.FontWeight.BOLD, 
                    color="black", 
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    description, 
                    size=14, 
                    color="black", 
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    f"\"{sample_text}\"", 
                    size=14, 
                    italic=True, 
                    color="black", 
                    text_align=ft.TextAlign.CENTER
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,  # Center vertically
            spacing=8,
        ),
        padding=20,
        bgcolor=color,
        border=None,  # No border by default
        border_radius=10,
        width=350,
        height=110,
        alignment=ft.alignment.center,
        data=color,  # Store original color for reset
    )

    card.on_click = lambda e: click_handler(e, card)
    return card