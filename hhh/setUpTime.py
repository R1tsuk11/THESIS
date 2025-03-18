import flet as ft

def set_up_time_page(page: ft.Page):
    """Defines the Setup Time Selection Page with Routing"""
    
    selected_card = None  # Store the selected time preference

    def on_card_click(e):
        """Handles selection of a time option, allowing only one to be highlighted."""
        nonlocal selected_card
        card = e.control  # Get the clicked card
        
        # Reset previous selection
        if selected_card:
            selected_card.border = None  # Remove selection border
            selected_card.bgcolor = selected_card.data  # Restore original color
        
        # Highlight new selection
        card.border = ft.border.all(2, "gold")
        card.bgcolor = "#26A69A"  # Selected card highlight
        selected_card = card
        page.update()

    def on_next_click(e):
        """Handles 'NEXT' button click, ensuring a selection is made before proceeding."""
        if selected_card:
            selected_text = selected_card.content.controls[1].value  # Get selected option
            print(f"Selected Learning Time: {selected_text}")  # Show in output
            page.go("/main-menu")  # Replace with the next page route

    # Progress Bar
    progress_bar = ft.Container(
        bgcolor="#A078F1",
        height=6,
        width=250,
        border_radius=10,
        margin=ft.margin.only(bottom=20),
    )

    # Title
    header = ft.Text(
        "How often do you want to learn?",
        size=20,
        weight=ft.FontWeight.BOLD,
        color="white",
        text_align=ft.TextAlign.CENTER,
    )

    # Options for learning time
    options = [
        ("A1", "5 minutes per day", "#26A69A"),
        ("A2", "10 minutes per day", "#388E3C"),
        ("B1", "5 minutes every other day", "#FBC02D"),
        ("B2", "10 minutes every other day", "#D84315"),
    ]

    cards = []
    for level, text, color in options:
        card = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Text(level, size=14, weight=ft.FontWeight.BOLD, color="white"),
                        bgcolor=color,
                        padding=ft.padding.symmetric(vertical=5, horizontal=10),
                        border_radius=10,
                    ),
                    ft.Text(text, size=14, color="white"),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
            ),
            padding=15,
            bgcolor="#1E1E1E",
            data="#1E1E1E",  # Store original color
            border_radius=10,
            width=250,
            on_click=on_card_click,  # Handle click event
        )
        cards.append(card)

    # Note
    note = ft.Text(
        "You can change this later.",
        size=12,
        color="gray",
    )

    # Next Button
    next_button = ft.Container(
        content=ft.Text("NEXT", size=16, weight=ft.FontWeight.BOLD, color="white", text_align=ft.TextAlign.CENTER),
        bgcolor="#A078F1",
        border_radius=10,
        width=250,
        height=50,
        alignment=ft.alignment.center,
        on_click=on_next_click,  # Handle click event
    )

    # Add page view
    page.views.append(
        ft.View(
            route="/setup-time",
            controls=[
                ft.Container(
                    expand=True,
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        [
                            progress_bar,
                            header,
                            *cards,
                            note,
                            next_button,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15,
                    ),
                )
            ],
        )
    )
