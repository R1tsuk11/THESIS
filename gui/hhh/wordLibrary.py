import flet as ft

def word_library_page(page: ft.Page, image_urls: list):
    """Word library page showing saved vocabulary words"""
    page.title = "Arami - Word Library"
    page.padding = 0
    page.bgcolor = "#FFFFFF"

    
    header = ft.Container(
        content=ft.Stack(
            controls=[
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Row([], alignment=ft.MainAxisAlignment.CENTER),
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right,
                                colors=["#0066FF", "#9370DB"],
                            ),
                            height=70,
                            # padding=10,
                        ),
                    ],
                    spacing=0
                ),
                ft.Container(
                    content=ft.Image(
                        src=image_urls[1], 
                        width=120,
                        # height=65,
                        fit=ft.ImageFit.COVER
                    ),
                    alignment=ft.alignment.top_center,
                    margin=ft.Margin(top=20, left=0, right=0, bottom=15),
                )
            ]
        ),
        # width=500
    )
    

    library_title = ft.Container(
        content=ft.Text(
            "My Word Library",
            size=18,
            color="#FFFFFF",
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        bgcolor="#397BFF",  
        width=310,  
        height=40,
        border_radius=25,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, "#000000"),
            offset=ft.Offset(0, 0),
        ),
        margin=ft.margin.only(top=2,bottom=15)
    )

    # Adding a container to center the library title
    centered_title = ft.Container(
        content=library_title,
        alignment=ft.alignment.center,
        width=page.width
    )

    # "Words" subtitle with underline
    words_subtitle = ft.Container(
        content=ft.Column([
            ft.Text(
                "Words",
                size=16,
                color="#000000",
                weight=ft.FontWeight.BOLD,
            ),
            ft.Container(
                bgcolor="#673AB7",
                height=2,
                width=60,
                margin=ft.margin.only(top=2)
            )
        ]),
        margin=ft.margin.only(left=20, bottom=10, top=5)
    )

    def on_profile_click(e):
        """Handles profile icon click event."""
        print("Profile icon clicked")
    
    def on_audio_click(e, word):
        """Handles audio icon click event."""
        print(f"Playing audio for {word}")

    # Function to create a word card that exactly matches the reference image
    def create_word_card(waray_word, english_translation):
        # Audio button with dark yellow circle and black icon
        audio_button = ft.Container(
            content=ft.Icon(
                name=ft.Icons.VOLUME_UP,
                size=20,
                color="#000000",  # Black icon
            ),
            width=40,
            height=40,
            border_radius=20,
            bgcolor="#FFCF32",  # Dark yellow background
            alignment=ft.alignment.center,
            on_click=lambda e: on_audio_click(e, waray_word)
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    # First row with Waray word and audio button
                    ft.Row(
                        [
                            ft.Text(
                                waray_word,
                                size=16,
                                color="#000000",
                                weight=ft.FontWeight.BOLD,
                            ),
                            audio_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    # Divider line
                    ft.Container(
                        bgcolor="#FFCF32", 
                        height=1,
                        width=page.width - 60,  
                        margin=ft.margin.symmetric(vertical=5),
                    ),
                    # English translation
                    ft.Text(
                        english_translation,
                        size=14,
                        color="#666666",
                    ),
                ],
                spacing=0,  
            ),
            bgcolor="#FFFFFF",  # White background
            border=ft.border.all(2, "#FFCF32"),  # Yellow border
            border_radius=15,  # Rounded corners
            padding=ft.padding.all(15),
            margin=ft.margin.symmetric(horizontal=20, vertical=5),
            width=page.width - 40,
        )

    # Load words from user's library
    def load_words_from_library(user_library):
        words = []
        for word in user_library:
            waray_word = word.get("waray_word", "")
            english_translation = word.get("english_translation", "")
            words.append({"waray": waray_word, "english": english_translation})
        return words
    
    # Example library data (in a real app, this would come from user data)
    sample_library = [
        {"waray_word": "Aga", "english_translation": "Morning"},
        {"waray_word": "Gihapon", "english_translation": "Too"},
        {"waray_word": "Maupay", "english_translation": "Good"},
        {"waray_word": "Ngaran", "english_translation": "Name"},
        # Adding more sample words to demonstrate scrolling
        {"waray_word": "Salamat", "english_translation": "Thank you"},
        {"waray_word": "Kamusta", "english_translation": "How are you"},
        {"waray_word": "Halipot", "english_translation": "Short"},
        {"waray_word": "Hataas", "english_translation": "Long"},
        {"waray_word": "Bugsay", "english_translation": "Paddle"},
        {"waray_word": "Kaon", "english_translation": "Eat"},
    ]
    
    # Get user's library - in the real app, this would use:
    # user_id = get_user_id(page)
    # user = User().load_data(user_id, page)
    # word_data = load_words_from_library(user.library)
    word_data = load_words_from_library(sample_library)
    
    # Create the word cards
    word_cards = []
    for word in word_data:
        card = create_word_card(word["waray"], word["english"])
        word_cards.append(card)

    # Bottom navigation bar
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.MENU_BOOK_OUTLINED,
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=lambda _: page.go("/word-library")
                    ),
                    border_radius=20,
                    width=50,  # Fixed width to ensure consistent spacing
                    height=50,  # Fixed height to ensure proper display
                    alignment=ft.alignment.center,  # Center the icon in its container
                    padding=0,  # Remove padding that might cause overflow
                    margin=5,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.HOME_OUTLINED,
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=lambda _: page.go("/main-menu")
                    ),
                    border_radius=20,
                    width=50,
                    height=50,
                    alignment=ft.alignment.center,
                    padding=0,
                    margin=5,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.PERSON_OUTLINED,
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=lambda _: page.go("/achievements")
                    ),
                    border_radius=20,
                    width=50,
                    height=50,
                    alignment=ft.alignment.center,
                    padding=0,
                    margin=5,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.SETTINGS_OUTLINED,  # Note the proper capitalization: SETTINGS_OUTLINED
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=lambda _: page.go("/settings")
                    ),
                    border_radius=20,
                    width=50,
                    height=50,
                    alignment=ft.alignment.center,
                    padding=0,
                    margin=5,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,  # Ensure vertical centering
            height=60,  # Set explicit height for the row
        ),
        border_radius=25,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#30b4fc", "#2980b9"],
        ),
        height=70,  # Slightly reduced height to avoid any overflow
        padding=ft.padding.symmetric(horizontal=15, vertical=5),
        margin=ft.margin.only(bottom=10, left=10, right=10),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, "#000000"),
            offset=ft.Offset(0, 0),
        ),
        # Ensure the container aligns its content in the center
        alignment=ft.alignment.center,
    )

    # Create a ListView for scrollable content instead of a Column
    scrollable_list = ft.ListView(
        spacing=10,
        padding=ft.padding.only(bottom=80),  # Increased padding to prevent bottom nav overlap
        expand=True,
    )
    
    # Add word cards to the ListView
    for card in word_cards:
        scrollable_list.controls.append(card)
    
    # Content area that will be scrollable
    content_area = ft.Container(
        content=scrollable_list,
        expand=True,
    )
    
    # Main content layout
    content_container = ft.Column(
        [
            centered_title,
            words_subtitle,
            content_area,  # This will be scrollable
        ],
        expand=True,
    )
    
    # Stack for fixed header, scrollable content, and fixed footer
    main_stack = ft.Stack(
        [
            # First add the content that should stretch full height
            ft.Column(
                [
                    header,
                    content_container,
                ],
                spacing=0,
                expand=True,
            ),
            # Then position the bottom nav at the bottom
            ft.Container(
                content=bottom_nav,
                bottom=0,
                left=0,
                right=0,
            ),
        ],
        expand=True,
    )
    
    # Add view to page
    page.views.append(
        ft.View(
            "/word-library",
            [main_stack],
            padding=0,
            bgcolor="#FFFFFF"
        )
    )
    page.update()