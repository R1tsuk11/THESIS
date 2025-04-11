import flet as ft

def levels_page(page: ft.Page):
    """Levels selection page"""
    page.title = "Arami - Kamustahay Levels"
    page.bgcolor = "#FFFFFF"
    page.padding = 0

    def go_back(e):
        """Navigate back to the main menu"""
        page.go("/main-menu")

    def level_select(e):
        """Handles level selection and navigates to the lesson page."""
        level_num = e.control.data
        print(f"Selected level {level_num}")
        page.go("/lesson")

    # Header with gradient background and title
    header = ft.Container(
        content=ft.Stack([
            ft.Container(
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["#0066FF", "#9370DB"],
                ),
                height=130,
            ),
            ft.Container(
                content=ft.Text(
                    "Kamustahay",
                    size=20,
                    color="#FFFFFF",
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor="#4285F4",
                border_radius=20,
                padding=ft.padding.symmetric(vertical=8, horizontal=16),
                margin=ft.margin.only(top=100),
                width=240,
                alignment=ft.alignment.center,
            ),
        ]),
        height=130,
    )

    explanation = ft.Container(
        content=ft.Text(
            "This part is a brief explanation about the module.",
            color="#000000",
            size=14,
            text_align=ft.TextAlign.CENTER,
        ),
        margin=ft.margin.symmetric(vertical=15, horizontal=20),
        alignment=ft.alignment.center,
    )

    def create_level_button(level_number, color="#4285F4"):
        return ft.Container(
            content=ft.Text(
                str(level_number),
                color="#FFFFFF",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=color,
            width=60,
            height=60,
            border_radius=10,
            alignment=ft.alignment.center,
            data=level_number,
            on_click=level_select
        )

    level_grid = ft.Container(
        content=ft.Column([
            ft.Row(
                [create_level_button(1, "#0066FF"), create_level_button(2), create_level_button(3), create_level_button(4)],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            ),
            ft.Row(
                [create_level_button(5), create_level_button(6)],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            ),
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
        bgcolor="#280082",
        height=60,
        padding=10
    )

    content = ft.Column(
        [
            header,
            explanation,
            level_grid,
            ft.Container(expand=True),
            bottom_nav,
        ],
        spacing=0,
        expand=True,
    )

    page.views.append(ft.View(
        "/levels",
        controls=[content],
        bgcolor="#FFFFFF",
        padding=0
    ))
    page.update()
