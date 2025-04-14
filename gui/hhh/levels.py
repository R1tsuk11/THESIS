import flet as ft

def get_module_data(page):
    modules = page.session.get("modules")
    module_id = page.session.get("module_id")

    if not modules:
        print("Modules not found in session.")
        return None

    if not module_id:
        print("Module ID not found in session.")
        return None

    # Make sure module_id type matches (e.g., string vs int)
    for module in modules:
        if str(module.id) == str(module_id):  # safe type comparison
            return module.levels, module.desc, module.waray_name

    print(f"No matching module with ID {module_id} found.")
    return None

def levels_page(page: ft.Page):
    """Levels selection page"""
    selected_module_levels, selected_module_desc, selected_module_name = get_module_data(page)
    page.title = f"Arami - \"{selected_module_name}\" Levels"
    page.bgcolor = "#FFFFFF"
    page.padding = 0
    level_rows = []
    row = []

    def go_back(e):
        """Navigate back to the main menu"""
        page.go("/main-menu")

    def level_select(e, level_num):
        """Handles level selection and navigates to the lesson page."""
        level_data = selected_module_levels[int(level_num) - 1]
        page.session.set("level_data", level_data)  # Store selected level data in session
        print(f"Selected level {level_num}")
        page.go("/lesson")

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
            on_click=lambda e: level_select(page, level_number)
        )

    for index, level in enumerate(selected_module_levels, start=1):
        level_button = create_level_button(index)

        row.append(level_button)

        # When we have 3 buttons, or it's the last button, add the row
        if len(row) == 3 or index == len(selected_module_levels):
            level_rows.append(
                ft.Row(
                    row,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10
                )
            )
            row = []  # reset for the next row

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
            selected_module_desc,
            color="#000000",
            size=14,
            text_align=ft.TextAlign.CENTER,
        ),
        margin=ft.margin.symmetric(vertical=15, horizontal=20),
        alignment=ft.alignment.center,
    )

    level_grid = ft.Container(
        content=ft.Column(
            level_rows,
            spacing=10, 
        alignment=ft.MainAxisAlignment.CENTER),
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
