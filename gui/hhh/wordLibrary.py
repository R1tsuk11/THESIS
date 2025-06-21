import flet as ft
from qbank import word_library
from flet_audio import Audio

AUDIO_URLS = {
    "maupay nga aga": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572609/maupay_nga_aga_urhv6g.mp3",
    "aga": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572617/aga_yrse5r.mp3",
    "gihapon": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572604/gihapon_qd9eky.mp3",
    "kamusta ka": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572607/kamusta_ka_tjidng.mp3",
    "ikaw": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572605/ikaw_h70yiy.mp3",
    "okay la ako": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572614/okay_la_ako_r9uavj.mp3",
    "maupay nga kulop": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572611/maupay_nga_kulop_vdaxud.mp3",
    "maupay": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572612/maupay_eix9qv.mp3",
    "diri": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572626/diri_brlstl.mp3",
    "it": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572605/it_drrhnr.mp3",
    "maupay nga gabi": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572610/maupay_nga_gabi_nhfibv.mp3",
    "gab-i": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572627/gab-i_e17xsu.mp3",
    "ano it imo ngaran": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572622/ano_it_imo_ngaran_jf1rih.mp3",
    "ngaran": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572613/ngaran_zuesqm.mp3",
    "ako hi": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572618/ako_hi_ovqdlr.mp3",
    "damo nga salamat": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572621/damo_nga_salamat_hgathz.mp3",
    "waray sapayan": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749573317/waray_sapayan_qixfxl.mp3",
    "pasylo-a ako": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572616/pasylo-a_ako_l0cvux.mp3",
    "maaram ka mag english": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572608/maaram_ka_mag_english_iuws71.mp3",
    "diri ako makarit ha waray": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572623/diri_ako_makarit_ha_waray_xoofdv.mp3",
    "ambot": "https://res.cloudinary.com/djm2qhi9f/video/upload/v1749572620/ambot_ws7epc.mp3"
}

def word_library_page(page: ft.Page, image_urls: list):
    """Word library page showing saved vocabulary words"""
    page.title = "Arami - Word Library"
    page.padding = 0
    page.bgcolor = "#FFFFFF"

    # Create audio players in advance
    audio_players = {}
    preloaded_audios = []
    
    # Create a silent audio for preload initialization WITH AUTOPLAY
    silent_audio = Audio(src="https://res.cloudinary.com/djm2qhi9f/video/upload/v1749580135/silent_pwwtrp.mp3", autoplay=True)
    preloaded_audios.append(silent_audio)
    
    # Preload all audio URLs to initialize the audio system
    for word, url in AUDIO_URLS.items():
        audio_player = Audio(src=url)
        audio_players[word] = audio_player
        preloaded_audios.append(audio_player)
    
    # Add all preloaded audios to page overlay right away
    page.overlay.extend(preloaded_audios)


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
    
    # FIX
    # Function to play audio
    def on_audio_click(e, word):
        """Handles audio icon click event."""
        word_lower = word.lower()
        print(f"Playing audio for {word}")
        
        # Get audio player from our preloaded dictionary
        audio_player = audio_players.get(word_lower)
        
        if audio_player:
            # Change button color for visual feedback
            e.control.bgcolor = "#FFA000"  # Darker color during playback
            page.update()
            
            # Play audio
            audio_player.play()
            
            # Reset button color after short delay
            def reset_button():
                import time
                time.sleep(0.8)
                e.control.bgcolor = "#FFCF32"  # Original color
                page.update()
                
            import threading
            threading.Thread(target=reset_button).start()
        else:
            # No audio found
            print(f"No audio found for word: {word}")
            page.open(ft.SnackBar(ft.Text(f"No audio available for '{word}'"), bgcolor="#FF9800"))

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

    # Load words from user's library and find translations in global dictionary
    def load_words_from_library(user_library):
        words = []
        seen_words = set()  # Track lowercase versions of words we've already added
        
        if not user_library or len(user_library) == 0:
            return words
            
        for word in user_library:
            # Handle both string-only and dictionary formats
            if isinstance(word, str):
                waray_word = word
                # Case-insensitive lookup in word_library dictionary
                english_translation = word_library.get(waray_word.lower(), None)
                if english_translation is None:
                    # Try original case if lowercase didn't work
                    english_translation = word_library.get(waray_word, "Translation not available")
            elif isinstance(word, dict) and "waray_word" in word and "english_translation" in word:
                waray_word = word["waray_word"]
                english_translation = word["english_translation"]
            else:
                # Skip invalid entries
                continue
            
            # Check if we've already seen this word (case-insensitive)
            word_lower = waray_word.lower()
            if word_lower in seen_words:
                # Skip duplicate words
                print(f"Skipping duplicate word: {waray_word} (already have {word_lower})")
                continue
                
            # Add to our tracking set and results
            seen_words.add(word_lower)
            words.append({"waray": waray_word, "english": english_translation})
        
        return words
    
    # Get user's library directly from session
    user_library = page.session.get("user_library")
    
    if user_library:
        # Use the library from the session
        word_data = load_words_from_library(user_library)
        print(f"Loaded {len(word_data)} words from session")
    else:
        # Fallback: Try to get from User object if not in session
        try:
            from mainmenu import get_user_id, User
            user_id = get_user_id(page)
            if user_id:
                user = User().load_data(user_id, page)
                word_data = load_words_from_library(user.library)
                print(f"Loaded {len(word_data)} words from user object")
            else:
                # Demo data for testing
                sample_words = ["Maupay nga aga", "gihapon", "kamusta ka", "ikaw?"]
                word_data = load_words_from_library(sample_words)
                print("Using sample words (no user found)")
        except Exception as e:
            print(f"Error loading word library: {e}")
            # Use sample data as fallback
            sample_words = ["Maupay nga aga", "gihapon", "kamusta ka", "ikaw?"]
            word_data = load_words_from_library(sample_words)
            print("Using sample words due to error")
    
    if not word_data:
        # Create a message for empty library
        empty_library_message = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        name=ft.icons.MENU_BOOK_OUTLINED,
                        size=70,
                        color="#CCCCCC"
                    ),
                    ft.Container(height=15),
                    ft.Text(
                        "Your word library is empty",
                        size=18,
                        color="#666666",
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "Complete lessons to build your vocabulary!",
                        size=14,
                        color="#999999",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=30),
                    ft.ElevatedButton(
                        content=ft.Text("Start Learning", size=14),
                        style=ft.ButtonStyle(
                            color={"": "white"},
                            bgcolor={"": "#30b4fc"},
                            elevation={"": 5},
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        on_click=lambda _: page.go("/main-menu")
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(30),
            margin=ft.margin.only(top=50),
            alignment=ft.alignment.center,
        )
        
        # Update the scrollable_list creation to include this message when empty
        scrollable_list = ft.ListView(
            controls=[empty_library_message],
            spacing=10,
            padding=ft.padding.only(bottom=80),
            expand=True,
        )
    else:
        # Original code for when there are words
        word_cards = []
        for word in word_data:
            card = create_word_card(word["waray"], word["english"])
            word_cards.append(card)
        
        # Create a ListView for scrollable content instead of a Column
        scrollable_list = ft.ListView(
            spacing=10,
            padding=ft.padding.only(bottom=80),  # Increased padding to prevent bottom nav overlap
            expand=True,
        )
        
        # Add word cards to the ListView
        for card in word_cards:
            scrollable_list.controls.append(card)

    # Display word cards - your existing code here...
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