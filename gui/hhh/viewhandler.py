import flet as ft
from login import login_page
from register import register_page
from setUpProficiency import set_up_proficiency_page
from setUpPreference import set_up_preference_page
from setUpTime import set_up_time_page
from mainmenu import main_menu_page
from levels import levels_page
from lesson import lesson_page
from lessonTranslate import lesson_translate_page
from lessonTranslateSentence import lesson_translate_sentence_page
from lessonPronounce import lesson_pronounce_page

def main(page: ft.Page):
    page.title = "User Authentication"
    page.bgcolor = "#FFFFFF"

    def route_change(e):
        """Handles route changes to switch between pages."""
        page.views.clear()

        if page.route == "/register":
            register_page(page)
        elif page.route == "/setup-proficiency":
            set_up_proficiency_page(page)
        elif page.route == "/setup-time":
            set_up_time_page(page)
        elif page.route == "/main-menu":
            main_menu_page(page)
        elif page.route == "/levels":
            levels_page(page)
        elif page.route == "/lesson":
            lesson_page(page)
        elif page.route == "/lesson-translate":
            lesson_translate_page(page)
        elif page.route == "/lesson-translate-sentence":
            lesson_translate_sentence_page(page)
        elif page.route == "/lesson-pronounce":
            lesson_pronounce_page(page)
        else:
            login_page(page)

        page.update()

    page.on_route_change = route_change
    page.go("/")  # Default route

ft.app(target=main)