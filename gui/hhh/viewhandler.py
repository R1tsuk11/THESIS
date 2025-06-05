import flet as ft
import asyncio
from login import login_page
from register import register_page
from setUpProficiency import set_up_proficiency_page, pretest_landing_page, pretest_score
from setUpTime import set_up_time_page
from mainmenu import main_menu_page
from levels import levels_page
from lesson import lesson_page
from chapterTest import chapter_test_page
from reviewFrame import review_session
from wordLibrary import word_library_page
from settings import settings_page, about_page, acknowledgements_page
from achievements import achievement_page
from flet import Theme, PageTransitionsTheme, PageTransitionTheme

async def main(page: ft.Page):
    page.title = "User Authentication"
    page.bgcolor = "#FFFFFF"
    page.fonts = {
        "Poppins": "fonts/Poppins-Regular.ttf"
    }

    page.theme = ft.Theme(font_family="Poppins", 
        page_transitions=ft.PageTransitionsTheme(
            android=ft.PageTransitionTheme.OPEN_UPWARDS,
            ios=ft.PageTransitionTheme.CUPERTINO,
            macos=ft.PageTransitionTheme.FADE_UPWARDS,
            windows=ft.PageTransitionTheme.FADE_UPWARDS
        )
    )

    image_urls = [
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747639160/logo1_tkfwwq.png", #blue logo - 0
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747639363/logo_roygvs.png", #purple logo - 1
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747642327/kamustahayPic_l8q9m7.jpg", #kamustahay card - 2
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747642327/kalakatPic_lhx9x8.jpg", #kalakat - 3
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747642327/pamalitPic_wufwce.png", #pamalit - 4
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747642328/pangaonPic_tuterr.png", #pangaon - 5
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747653515/urusturyaPic_uio1qv.png", #urusturya - 6
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747653929/aga_zbtuat.jpg", #my progress photo - 7
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747653842/landscape_background_vppv58.png", #landscape background - 8
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747653843/reviewPic_kxjqm3.png", #review card - 9


    ]

    # Preload images in a hidden container
    preload_container = ft.Column(
        controls=[ft.Image(src=url, visible=False) for url in image_urls]
    )

    page.add(preload_container)

    # Splash screen function
    async def show_splash_screen():

        page.controls.clear()
        
        splash_image = ft.Image(
            src=image_urls[0],  # Use the first image URL
            width=180,
            height=180,
            fit=ft.ImageFit.CONTAIN
        )
        
        # Loading indicator (optional)
        progress_ring = ft.ProgressRing(
            width=20,
            height=20,
            stroke_width=2,
            color="#4285F4"
        )
        
        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        splash_image,
                        ft.Container(height=5),  # Spacing
                        progress_ring
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                ),
                alignment=ft.alignment.center,
                expand=True,
                bgcolor="white"  # White bg
            )
        )
        
        page.update()
        
        await asyncio.sleep(4)
        page.go("/login")

    def route_change(e):
        """Handles route changes to switch between pages."""
        page.views.clear()

        if page.route == "/register":
            register_page(page, image_urls)
        elif page.route == "/setup-proficiency":
            set_up_proficiency_page(page, image_urls)
        elif page.route == "/setup-time":
            set_up_time_page(page, image_urls)
        elif page.route == "/main-menu":
            main_menu_page(page, image_urls)
        elif page.route == "/levels":
            levels_page(page, image_urls)
        elif page.route == "/lesson":
            lesson_page(page, image_urls)
        elif page.route == "/chaptertest":
            chapter_test_page(page, image_urls)
        elif page.route == "/daily-review":
            review_session(page, image_urls)
        elif page.route == "/word-library":
            word_library_page(page, image_urls)
        elif page.route == "/settings":
            settings_page(page)
        elif page.route == "/about":
            about_page(page, image_urls)
        elif page.route == "/acknowledgements":
            acknowledgements_page(page)
        elif page.route == "/achievements":
            achievement_page(page, image_urls)
        elif page.route == "/pretest-intro":
            pretest_landing_page(page, image_urls)
        elif page.route == "/pretest-score":
            pretest_score(page, image_urls)
        else:
            login_page(page, image_urls)  # Default to login page

        page.update()

    page.on_route_change = route_change
    await show_splash_screen()

ft.app(target=main)