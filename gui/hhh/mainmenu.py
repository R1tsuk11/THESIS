import flet as ft

def main_menu_page(page: ft.Page):
    """Main menu page with module cards"""

    def navigate_to_levels(e):
        """Navigates to levels page"""
        page.go("/levels")

    # Header - empty blue container with no text
    header = ft.Container(
        content=ft.Row([], alignment=ft.MainAxisAlignment.CENTER),  # Empty row
        bgcolor="#0066FF",  # Blue color matching the image
        height=60,
        padding=10
    )

    # Create modules title
    modules_title = ft.Container(
        content=ft.Text(
            "Modules",
            size=18,
            color="#FFFFFF",  # White text
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        bgcolor="#4285F4",  # Blue button color from image
        width=300,
        height=50,
        border_radius=25,
        alignment=ft.alignment.center,
        margin=ft.margin.symmetric(vertical=10)
    )

    # Function to create a module card
    def create_module_card(main_button_text, sub_button_text, main_color, sub_color, bg_color="#2A2A2A"):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(
                                    main_button_text,
                                    color="#000000",
                                    weight=ft.FontWeight.BOLD,
                                    size=16,
                                    text_align=ft.TextAlign.CENTER,  # Center text
                                ),
                                bgcolor=main_color,
                                border_radius=15,
                                padding=10,
                                width=180,
                                alignment=ft.alignment.center,  # Center content
                            ),
                            ft.Icon(
                                ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                                color="#FFFFFF",  # White arrow
                                size=20,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,  # Keep arrow at right
                    ),
                    ft.Container(
                        content=ft.Text(
                            sub_button_text,
                            color="#FFFFFF",  # White text
                            size=14,
                            text_align=ft.TextAlign.CENTER,  # Center text
                        ),
                        bgcolor=sub_color,
                        border_radius=15,
                        padding=10,
                        width=200,
                        alignment=ft.alignment.center,  # Center content
                        margin=ft.margin.only(top=10),  # Remove left margin to center it
                    ),
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,  # Center column contents
            ),
            bgcolor=bg_color,  # Dark card background
            border_radius=15,
            padding=15,
            margin=ft.margin.only(bottom=15),
            width=300,
            on_click=navigate_to_levels,  # Navigates to Levels when clicked
        )

    # Create the module cards with updated colors
    kamustahay_card = create_module_card("Kamustahay!", "Greetings and Introductions", "#FFD580", "#8B7E4F")
    oras_card = create_module_card("Oras", "Time / Date", "#74CFCF", "#7A9E9E")
    pagkain_card = create_module_card("Pangaan", "Ordering Food", "#74CFCF", "#7A9E9E")

    # Create the bottom navigation bar
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.MILITARY_TECH_OUTLINED,
                    icon_color="#FFFFFF",
                    icon_size=24,
                ),
                ft.IconButton(
                    icon=ft.Icons.MENU_BOOK_OUTLINED,
                    icon_color="#FFFFFF",
                    icon_size=24,
                ),
                ft.IconButton(
                    icon=ft.Icons.HOME_OUTLINED,
                    icon_color="#FFFFFF",
                    icon_size=24,
                ),
                ft.IconButton(
                    icon=ft.Icons.PERSON_OUTLINED,
                    icon_color="#FFFFFF",
                    icon_size=24,
                ),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    icon_color="#FFFFFF",
                    icon_size=24,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
        bgcolor="#280082",  # Dark purple color
        height=60,
        padding=10
    )

    # Main content with centered items
    content = ft.Column(
        [
            header,
            ft.Container(
                content=ft.Column(
                    [
                        modules_title,
                        kamustahay_card,
                        oras_card,
                        pagkain_card,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True
            ),
            bottom_nav,
        ],
        spacing=0,
        expand=True,
    )

    # Configure page settings
    page.padding = 0
    page.bgcolor = "#FFFFFF"  # Set page background to white
    
    # Add view with updated styling
    page.views.append(ft.View("/main-menu", controls=[content], padding=0, bgcolor="#FFFFFF"))  # White background
    page.update()