import flet as ft

def main_menu_page(page: ft.Page):
    """Main menu page with module cards"""

    def navigate_to_levels(e):
        """Navigates to levels page"""
        page.go("/levels")

    # Header
    header = ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    "arami",
                    size=24,
                    color="#4169E1",
                    weight=ft.FontWeight.BOLD,
                    italic=True
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        bgcolor="#2B0B5F",
        height=60,
        border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
        padding=10
    )

    # Create modules title
    modules_title = ft.Container(
        content=ft.Text(
            "Modules",
            size=18,
            color="#000000",
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        bgcolor="#A17BFB",
        width=300,
        height=50,
        border_radius=25,
        alignment=ft.alignment.center,
        margin=ft.margin.symmetric(vertical=10)
    )

    # Function to create a module card
    def create_module_card(main_button_text, sub_button_text, main_color="#FFD580", sub_color="#DDDDDD"):
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
                                ),
                                bgcolor=main_color,
                                border_radius=15,
                                padding=10,
                                width=180,
                                alignment=ft.alignment.center,
                            ),
                            ft.Icon(
                                ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                                color="#000000",
                                size=20,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(
                        content=ft.Text(
                            sub_button_text,
                            color="#000000",
                            size=14,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        bgcolor=sub_color,
                        border_radius=15,
                        padding=10,
                        width=200,
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(top=10, left=10),
                    ),
                ],
                spacing=5,
            ),
            bgcolor="#E6B9B9",
            border_radius=15,
            padding=15,
            margin=ft.margin.only(bottom=15),
            width=300,
            on_click=navigate_to_levels,  # Navigates to Levels when clicked
        )

    # Create the module cards
    kamustahay_card = create_module_card("Kamustahay!", "Greetings and Introductions", "#FFD580")
    oras_card = create_module_card("Oras", "Time / Date", "#74CFCF", "#B5D8D8")
    pagkain_card = create_module_card("Pagkain", "Ordering Food", "#74CFCF", "#B5D8D8")

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
        bgcolor="#2B0B5F",
        height=60,
        border_radius=ft.border_radius.only(top_left=20, top_right=20),
        padding=10
    )

    # Main content
    content = ft.Column(
        [
            header,
            modules_title,
            kamustahay_card,
            oras_card,
            pagkain_card,
            ft.Container(expand=True),
            bottom_nav,
        ],
        spacing=0,
        expand=True,
    )

    page.views.append(ft.View("/main-menu", controls=[content], bgcolor="#000000"))
    page.update()
