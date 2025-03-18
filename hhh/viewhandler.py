import flet as ft
from login import login_page
from register import register_page
from setUpProficiency import set_up_proficiency_page
from setUpPreference import set_up_preference_page
from setUpTime import set_up_time_page
from mainmenu import main_menu_page
from levels import levels_page

def main(page: ft.Page):
    page.title = "User Authentication"
    page.bgcolor = "#000000"

    def route_change(e):
        """Handles route changes to switch between pages."""
        page.views.clear()

        if page.route == "/register":
            register_page(page)
        elif page.route == "/setup-proficiency":
            set_up_proficiency_page(page)
        elif page.route == "/setup-preference":
            set_up_preference_page(page)
        elif page.route == "/setup-time":
            set_up_time_page(page)
        elif page.route == "/main-menu":
            main_menu_page(page)
        elif page.route == "/levels":
            levels_page(page)
        else:
            login_page(page)  # Default: Login Page

        page.update()

    page.on_route_change = route_change
    page.go("/")  # Default route

ft.app(target=main)
