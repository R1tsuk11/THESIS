import flet as ft


def achievement_page(page: ft.Page, image_urls: list):
    """Achievement page showing user progress, lessons completed, words learned, and achievements"""
    page.title = "Arami - My Progress"
    page.padding = 0
    page.bgcolor = "#f0f8ff"  # Light blue background
    page.theme_mode = ft.ThemeMode.LIGHT    

    # Get data from session
    achievement_data = page.session.get("achievement_data")
    
    if achievement_data:
        # Use session data
        username = achievement_data.get("username", "Guest")
        progress_percentage = achievement_data.get("progress_percentage", 0)
        lessons_completed = achievement_data.get("lessons_completed", 0)
        words_learned = achievement_data.get("words_learned", 0)
        language_proficiency = achievement_data.get("language_proficiency", 0)
        user_achievements = achievement_data.get("achievements", {})
    else:
        # Fallback to default data
        try:
            from mainmenu import get_user_id, User
            user_id = get_user_id(page)
            if user_id:
                user = User().load_data(user_id, page)
                username = user.user_name
                progress_percentage = user.completion_percentage
                lessons_completed = len([l for m in user.modules for l in m.levels if l.completed])
                words_learned = len(user.library)
                language_proficiency = user.proficiency if hasattr(user, 'proficiency') else 0
                user_achievements = user.achievements
            else:
                # Sample data if no user found
                username = "johndoe"
                progress_percentage = 4
                lessons_completed = 1
                words_learned = 4
                language_proficiency = 5.2
                user_achievements = {}
        except Exception as e:
            print(f"Error loading user data: {e}")
            username = "johndoe"
            progress_percentage = 4
            lessons_completed = 1
            words_learned = 4
            language_proficiency = 5.2
            user_achievements = {}
    
    # Convert achievements to the format needed for display
    achievements_data = []
    for achievement_id, achievement in user_achievements.items():
        if isinstance(achievement, dict):
            # If it's already a dictionary
            achievements_data.append({
                "title": achievement.get("name", "Unknown"),
                "description": achievement.get("description", ""),
                "icon": getattr(ft.Icons, achievement.get("icon", "STAR")),
                "color": "#0055b3"
            })
        else:
            # If it's an Achievement object
            achievements_data.append({
                "title": achievement.name,
                "description": achievement.description,
                "icon": getattr(ft.Icons, achievement.icon),
                "color": "#0055b3"
            })
    
    # If no achievements, add default one
    if not achievements_data:
        achievements_data = [
            {
                "title": "Makarit",
                "description": "Completed your first lesson",
                "icon": ft.Icons.STAR,
                "color": "#0055b3"
            },
        ]

    header = ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    "My Progress",
                    size=18,
                    color="#FFFFFF",
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    username,
                    size=14,
                    color="#FFFFFF",
                    weight=ft.FontWeight.NORMAL,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#0066FF", "#9370DB"],
        ),
        height=70,
        padding=ft.padding.symmetric(horizontal=30, vertical=10),
        width=page.width
    )

    # Image
    scenery_image = ft.Container(
        content=ft.Image(
            src=image_urls[7], 
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(15),
        ),
        height=180,
        width=320,  
        margin=ft.margin.symmetric(horizontal=20, vertical=10),
        border_radius=15,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, "grey"),
            offset=ft.Offset(0, 2),
        )
    )

    learning_progress_card = ft.Container(
        content=ft.Column([
            ft.Text(
                "Learning Progress",
                size=16,
                color="#FFFFFF",
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                f"{progress_percentage}%",
                size=36,
                color="#FFFFFF",
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Complete",
                size=16,
                color="#FFFFFF",
                text_align=ft.TextAlign.CENTER,
            ),
            # Progress bar
            ft.Container(
                content=ft.Stack([
                    ft.Container(
                        bgcolor="#FFFFFF",
                        border_radius=10,
                        height=10,
                        width=140,  # Adjusted for better centering
                    ),
                    ft.Container(
                        bgcolor="#FFFF00",  # Yellow progress
                        border_radius=10,
                        height=10,
                        width=progress_percentage * 1.4,  # Dynamic width based on percentage
                    ),
                ]),
                margin=ft.margin.only(top=10),
                alignment=ft.alignment.center,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=5,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor="#00CED1",  # Teal color
        height=230,
        width=160,  # Adjusted for better centering
        padding=ft.padding.all(15),
        border_radius=15,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.2, "grey"),
            offset=ft.Offset(0, 2),
        )
    )

    # Lessons completed card - orange color
    lessons_card = ft.Container(
        content=ft.Column([
            ft.Text(
                str(lessons_completed),
                size=36,
                color="#FFFFFF",
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Lessons",
                size=14,
                color="#FFFFFF",
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Completed",
                size=14,
                color="#FFFFFF",
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=2),
        bgcolor="#FFA500",  # Orange
        height=110,
        width=110,
        padding=ft.padding.all(10),
        border_radius=15,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.2, "grey"),
            offset=ft.Offset(0, 1),
        )
    )

    # Words learned card - purple color
    words_card = ft.Container(
        content=ft.Column([
            ft.Text(
                str(words_learned),
                size=36,
                color="#FFFFFF",
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Words Learned",
                size=14,
                color="#FFFFFF",
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=2),
        bgcolor="#9370DB",  # Medium purple
        height=110,
        width=110,
        padding=ft.padding.all(10),
        border_radius=15,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.2, "grey"),
            offset=ft.Offset(0, 2),
        )
    )

    # Language Proficiency card - UPDATED to match the image exactly
    language_proficiency_card = ft.Container(
        content=ft.Column([
            ft.Row(
                [
                    ft.Text(
                        "Language Proficiency",
                        size=15,
                        color="#FFFFFF",
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        f"{language_proficiency}%",
                        size=28,
                        color="#FFFFFF",
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            # Progress bar
            ft.Container(
                content=ft.Stack([
                    ft.Container(
                        bgcolor="#FFFFFF",
                        border_radius=10,
                        height=16,
                        width=260,  # Full width for the background
                    ),
                    ft.Container(
                        bgcolor="#4CAF50",  # Darker green progress as shown in image
                        border_radius=10,
                        height=16,
                        width=language_proficiency * 2.8,  # Dynamic width based on percentage
                    ),
                ]),
                margin=ft.margin.only(top=1,bottom=3),
                alignment=ft.alignment.center,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor="#8BC34A",  # Brighter lime green as shown in image
        height=95,
        width=300,  # Match width with other elements
        padding=ft.padding.symmetric(horizontal=20, vertical=15),
        border_radius=20,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.2, "grey"),
            offset=ft.Offset(0, 2),
        )
    )

    # Stats column with the two cards (stacked vertically as in the image)
    stats_column = ft.Column(
        [lessons_card, words_card],
        spacing=10,
        alignment=ft.MainAxisAlignment.START,
    )

    # Progress section containing both cards - with better centering
    progress_section = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [learning_progress_card, stats_column],
                    alignment=ft.MainAxisAlignment.CENTER,  # Center horizontally
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    spacing=15,  # Reduce spacing between cards
                ),
                # Add the language proficiency card
                ft.Container(
                    content=language_proficiency_card,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=15),
                ),
            ],
            spacing=0,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        margin=ft.margin.symmetric(horizontal=10, vertical=10),
        alignment=ft.alignment.center,
    )

    # Function to create achievement cards dynamically
    def create_achievement_card(achievement):
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(
                        name=achievement["icon"],
                        size=24,
                        color="#FFFFFF",
                    ),
                    bgcolor=achievement["color"],
                    border_radius=25,
                    width=40,
                    height=40,
                    alignment=ft.alignment.center,
                ),
                ft.Container(width=15),  # Spacing
                ft.Column([
                    ft.Text(
                        achievement["title"],
                        size=16,
                        color="#000000",
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        achievement["description"],
                        size=14,
                        color="#666666",
                    ),
                ], 
                spacing=2,
                expand=True),
            ]),
            padding=ft.padding.all(15),
            bgcolor="#FFFFFF",
            border_radius=15,
            width=320,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.1, "grey"),
                offset=ft.Offset(0, 2),
            ),
            margin=ft.margin.only(bottom=10),
        )

    # Create achievement cards list dynamically
    achievement_cards = [create_achievement_card(achievement) for achievement in achievements_data]

    # Achievements section
    achievements_section = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text(
                    "Achievements",
                    size=24,
                    color="#000000",
                    weight=ft.FontWeight.BOLD,
                ),
                margin=ft.margin.only(bottom=15),
                alignment=ft.alignment.center,
            ),
            # Dynamic achievement cards
            *achievement_cards,
            
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER),  # Center the achievement cards
        padding=ft.padding.symmetric(horizontal=20, vertical=25),
        bgcolor="#FFFACD",  # Light yellow background as in the image
        border_radius=ft.border_radius.only(top_left=30, top_right=30),
        margin=ft.margin.only(top=15, bottom=10),
        alignment=ft.alignment.top_center,
        expand=True,  # Allow the container to expand to fill remaining space
        shadow=ft.BoxShadow(
            spread_radius=2,
            blur_radius=20,
            color=ft.Colors.with_opacity(0.4, "grey"),
            offset=ft.Offset(0, -5),  # Negative Y offset for shadow coming from top
        ),
    )

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
                    width=50, 
                    height=50, 
                    alignment=ft.alignment.center, 
                    padding=0, 
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
                        icon=ft.Icons.PERSON,  
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
                    #bgcolor="#0077e6",  # Highlight color to show active tab
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.SETTINGS_OUTLINED,  
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
            vertical_alignment=ft.CrossAxisAlignment.CENTER, 
            height=60,  
        ),
        border_radius=25,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#30b4fc", "#2980b9"],
        ),
        height=70,  
        padding=ft.padding.symmetric(horizontal=15, vertical=5),
        margin=ft.margin.only(bottom=10, left=10, right=10),
        alignment=ft.alignment.center,
    )


    # Create the scrollable list view
    scrollable_list = ft.ListView(
        controls=[
            # Center the scenery image
            ft.Container(
                content=scenery_image,
                alignment=ft.alignment.center,
            ),
            progress_section,
            achievements_section,
        ],
        spacing=0,
        padding=ft.padding.only(bottom=70),  # Add padding for the nav bar
        expand=True,
    )

    # Main stack with content and bottom navigation
    main_stack = ft.Stack(
        [
            ft.Column(
                [
                    header,
                    ft.Container(
                        content=scrollable_list,
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            ft.Container(
                content=bottom_nav,
                bottom=0,
                left=0,
                right=0,
            ),
        ],
        expand=True,
    )
    
    # Use appropriate route
    if len(page.views) == 0:
        route = "/"
    else:
        route = "/progress"
        
    # Add view to page
    page.views.append(
        ft.View(
            route=route,
            controls=[main_stack],
            padding=0,
            bgcolor="#f0f8ff"
        )
    )
    page.update()