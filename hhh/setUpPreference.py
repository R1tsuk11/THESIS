import flet as ft

def set_up_preference_page(page: ft.Page):
    """Defines the Setup Preference Page with Routing"""
    
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
        """Handles 'NEXT' button click to navigate to setUpTime page."""
        if selected_card:
            selected_text = selected_card.content.controls[0].value  # Get selected preference
            print(f"Selected Learning Preference: {selected_text}")  # Show in output
            page.go("/setup-time")  # Navigate to setUpTime.py

    
    # Create selection cards
    auditory_visual_card = create_preference_card(
        "AUDITORY and VISUAL", "Recommended.", 
        "Modules will be a perfect balance of auditory and visual learning.", "#FFC107", on_card_click
    )
    
    auditory_card = create_preference_card(
        "AUDITORY", "", 
        "Modules will focus more on hearing and voice rather than visuals.", "#FFD54F", on_card_click
    )

    visual_card = create_preference_card(
        "VISUAL", "", 
        "Modules will focus more on visuals rather than hearing.", "#FFD54F", on_card_click
    )

    page.views.append(
        ft.View(
            route="/setup-preference",
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
                                "I would prefer to learn through:",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color="white",
                                text_align=ft.TextAlign.CENTER,
                            ),

                            # Preference Selection Cards (Centered)
                            auditory_visual_card,
                            auditory_card,
                            visual_card,

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
                                on_click=on_next_click,  # Prints only when Next is clicked
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

def create_preference_card(title, subtitle, description, color, click_handler):
    """Creates a learning preference selection card."""
    
    card = ft.Container(
        content=ft.Column(
            [
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color="black"),
                ft.Text(subtitle, size=12, color="black"),
                ft.Text(description, size=14, color="black"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5,
        ),
        padding=15,
        bgcolor=color,
        data=color,  # Store original color for reset
        border_radius=10,
        width=300,
        height=120,
        alignment=ft.alignment.center,
        margin=ft.margin.only(bottom=10),
    )

    card.on_click = lambda e: click_handler(e, card)  # Ensure only one card is selected at a time
    return card
