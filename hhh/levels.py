import flet as ft

def levels_page(page: ft.Page):
    """Levels selection page"""
    page.title = "Arami - Kamustahay Levels"
    page.bgcolor = "#000000"
    page.padding = 0

    def go_back(e):
        """Navigate back to the main menu"""
        page.go("/main-menu")

    def level_select(e):
        """Handles level selection"""
        level_num = e.control.data
        print(f"Selected level {level_num}")

    # Header with back button and title
    header = ft.Container(
        content=ft.Stack([
            ft.Container(
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["#FFB347", "#FFCC99", "#FF9966", "#E6A8D7", "#C8A2C8"],
                ),
                border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30),
                height=200,
            ),
            ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="#000000",
                    on_click=go_back,
                ),
                margin=ft.margin.only(left=10, top=10),
                alignment=ft.alignment.top_left,
            ),
            ft.Container(
                content=ft.Text(
                    "Kamustahay",
                    size=26,
                    color="#FFFFFF",
                    weight=ft.FontWeight.BOLD,
                ),
                bgcolor="#A17BFB",
                border_radius=30,
                padding=ft.padding.symmetric(vertical=10, horizontal=20),
                margin=ft.margin.only(top=160),
                width=280,
                alignment=ft.alignment.center,
            ),
        ]),
        height=220,
    )

    explanation = ft.Container(
        content=ft.Text(
            "This part is a brief explanation about the module. Explanation about module.",
            color="#FFFFFF",
            size=14,
            text_align=ft.TextAlign.CENTER,
        ),
        margin=ft.margin.symmetric(vertical=15, horizontal=20),
        alignment=ft.alignment.center,
    )

    # Function to create level buttons
    def create_level_button(level_number, is_active=True):
        return ft.ElevatedButton(
            text=str(level_number),
            bgcolor="#D3D3D3" if is_active else "#808080",
            color="#000000",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            width=60,
            height=60,
            data=level_number,
            on_click=level_select
        )

    level_grid = ft.Container(
        content=ft.Column([
            ft.Row([create_level_button(1), create_level_button(2)], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Row([create_level_button(3), create_level_button(4)], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
        margin=ft.margin.only(top=10),
    )

    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(icon=ft.Icons.MILITARY_TECH_OUTLINED, icon_color="#FFFFFF", icon_size=24),
                ft.IconButton(icon=ft.Icons.MENU_BOOK_OUTLINED, icon_color="#FFFFFF", icon_size=24),
                ft.IconButton(icon=ft.Icons.HOME_OUTLINED, icon_color="#FFFFFF", icon_size=24),
                ft.IconButton(icon=ft.Icons.PERSON_OUTLINED, icon_color="#FFFFFF", icon_size=24),
                ft.IconButton(icon=ft.Icons.SETTINGS_OUTLINED, icon_color="#FFFFFF", icon_size=24),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
        bgcolor="#2B0B5F",
        height=60,
        padding=10
    )

    content = ft.Column(
        [
            header,
            explanation,
            level_grid,  # Level buttons added
            ft.Container(expand=True),
            bottom_nav,
        ],
        spacing=0,
        expand=True,
    )

    page.views.append(ft.View("/levels", controls=[content], bgcolor="#000000"))
    page.update()
