import flet as ft

def set_up_proficiency_page(page: ft.Page):
    """Defines the Setup Proficiency Page with Routing"""
    
    selected_card = None  # Store the currently selected card

    def on_card_click(e, card):
        """Handles card selection, ensuring only one is highlighted."""
        nonlocal selected_card
        
        # Reset previous selection
        if selected_card:
            selected_card.bgcolor = selected_card.data  # Restore original color

        # Set new selection
        card.bgcolor = "#B39DDB"  # Highlight selected card
        selected_card = card  
        page.update()

    def on_next_click(e):
        """Navigates to setUpPreference.py and prints the selected card."""
        if selected_card:
            selected_text = selected_card.content.controls[0].value  # Get card title
            print(f"Selected: {selected_text}")  # Show in output
            page.go("/setup-preference")  # Navigate to setUpPreference.py

    # Create selection cards
    starter_card = create_proficiency_card(
        "STARTER", "First time to learn this language.", 
        "Diri ako maaram!", "#FFC107", on_card_click
    )
    
    beginner_card = create_proficiency_card(
        "BEGINNER", "I know some words.", 
        "Guti la it akon aram.", "#FFD54F", on_card_click
    )

    page.views.append(
        ft.View(
            route="/setup-proficiency",
            controls=[
                ft.Container(
                    expand=True,  # Makes the container take the full height of the screen
                    alignment=ft.alignment.center,  # Vertically center the content
                    content=ft.Column(
                        [
                            # Progress Bar
                            ft.Container(
                                bgcolor="#A078F1",
                                height=6,
                                width=250,
                                border_radius=10,
                                margin=ft.margin.only(bottom=20),
                            ),

                            # Title
                            ft.Text(
                                "How much can you speak Waray?",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color="white",
                                text_align=ft.TextAlign.CENTER,
                            ),

                            # Proficiency Selection Cards (Centered)
                            starter_card,
                            beginner_card,

                            # Next Button
                            ft.Container(
                                content=ft.Text(
                                    "NEXT", 
                                    size=16, 
                                    weight=ft.FontWeight.BOLD, 
                                    color="white", 
                                    text_align=ft.TextAlign.CENTER
                                ),
                                bgcolor="#A078F1",
                                border_radius=10,
                                width=250,
                                height=50,
                                alignment=ft.alignment.center,
                                on_click=on_next_click,  # Navigates to setUpPreference.py
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,  # Vertically center content
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20  # Adjust spacing for better balance
                    ),
                )
            ],
        )
    )

def create_proficiency_card(title, description, sample_text, color, click_handler):
    """Creates a proficiency selection card."""
    
    card = ft.Container(
        content=ft.Column(
            [
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color="black"),
                ft.Text(description, size=12, color="black"),
                ft.Text(f"\"{sample_text}\"", size=14, italic=True, color="black"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5,
        ),
        padding=15,
        bgcolor=color,
        data=color,  # Store original color for reset
        border_radius=10,
        width=250,
        height=100,
        alignment=ft.alignment.center,
        margin=ft.margin.only(bottom=10),
    )

    card.on_click = lambda e: click_handler(e, card)  # Ensure only one card is selected at a time
    return card
