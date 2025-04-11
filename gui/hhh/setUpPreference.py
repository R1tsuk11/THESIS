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
        card.bgcolor = "#FFE48D"  # Highlight with darker yellow when selected
        selected_card = card  
        page.update()

    def on_next_click(e):
        """Handles 'NEXT' button click to navigate to setUpTime page."""
        if selected_card:
            selected_text = selected_card.content.controls[0].value  # Get selected preference
            print(f"Selected Learning Preference: {selected_text}")  # Show in output
            page.go("/setup-time")  # Navigate to setUpTime.py - keeping original routing
    
    # Create selection cards with proper styling
    auditory_visual_card = create_preference_card(
        "AUDITORY and VISUAL", "Recommended.", 
        "Modules will be a perfect balance of auditory and visual learning.", "#FFF9C4", on_card_click
    )
    
    auditory_card = create_preference_card(
        "AUDITORY", "", 
        "Modules will focus more on hearing and voice rather than visuals.", "#FFF9C4", on_card_click
    )

    visual_card = create_preference_card(
        "VISUAL", "", 
        "Modules will focus more on visual elements rather than auditory.", "#FFF9C4", on_card_click
    )

    page.views.append(
        ft.View(
            route="/setup-preference",
            controls=[
                ft.Container(
                    expand=True,
                    padding=20,
                    bgcolor="white",  # White background as shown in the image
                    content=ft.Column(
                        [
                            # Progress Bar
                            ft.Container(
                                bgcolor="#BBDEFB",  # Light blue progress bar as in image
                                height=10,
                                width=350,
                                border_radius=10,
                                margin=ft.margin.only(top=30, bottom=30),
                            ),

                            # Title
                            ft.Text(
                                "I would prefer to learn through:",
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                color="black",  # Black text as in image
                                text_align=ft.TextAlign.CENTER,
                            ),
                            
                            # Space between title and cards
                            ft.Container(height=20),
                            
                            # Card container to center the cards horizontally
                            ft.Container(
                                content=auditory_visual_card,
                                alignment=ft.alignment.center,
                                width=400  # Make sure container is wide enough
                            ),
                            
                            ft.Container(height=15),  # Gap between cards
                            
                            ft.Container(
                                content=auditory_card,
                                alignment=ft.alignment.center,
                                width=400
                            ),
                            
                            ft.Container(height=15),  # Gap between cards
                            
                            ft.Container(
                                content=visual_card,
                                alignment=ft.alignment.center,
                                width=400
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

def create_preference_card(title, subtitle, description, color, click_handler):
    """Creates a learning preference selection card with proper sizing."""
    
    # Combine subtitle and description if both exist
    content_list = [
        ft.Text(
            title, 
            size=16, 
            weight=ft.FontWeight.BOLD, 
            color="black",
            text_align=ft.TextAlign.CENTER
        )
    ]
    
    if subtitle:
        content_list.append(
            ft.Text(
                subtitle, 
                size=14, 
                color="black",
                text_align=ft.TextAlign.CENTER
            )
        )
    
    if description:
        content_list.append(
            ft.Text(
                description, 
                size=14, 
                color="black",
                text_align=ft.TextAlign.CENTER
            )
        )
    
    card = ft.Container(
        content=ft.Column(
            content_list,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        padding=20,
        bgcolor=color,
        data=color,  # Store original color for reset
        border_radius=10,
        width=350,  # Match the width in the image
        height=130 if subtitle and description else 100,  # Taller for cards with more content
        alignment=ft.alignment.center,
        margin=0,  # Remove margin as we're handling spacing with container parents
    )

    card.on_click = lambda e: click_handler(e, card)
    return card