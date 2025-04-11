import flet as ft

def lesson_page(page: ft.Page):
    """Lesson page for displaying language learning content"""
    page.title = "Arami - Lesson"
    page.padding = 0
    
    def go_back(e):
        """Navigate back to the levels page"""
        page.go("/levels")
    
    def next_lesson(e):
        """Navigate to the translation exercise page"""
        page.go("/lesson-translate")
    
    # Define text variables
    greeting_header = "NEW GREETING"
    waray_greeting = "Maupay nga aga"
    english_translation = "Good morning"
    full_definition = "Maupay nga aga means \"Good morning\" in Waray."
    
    # Create top header with close button
    header = ft.Container(
        content=ft.Row(
            [
                ft.Container(width=50),  # Spacer
                ft.Container(
                    width=50, 
                    content=ft.IconButton(
                        icon=ft.icons.CLOSE, 
                        icon_color="black",
                        on_click=go_back
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.END
        ),
        padding=ft.padding.only(top=10, right=10)
    )
    
    # Card content
    card_content = ft.Container(
        content=ft.Column(
            [
                # NEW GREETING header with lines
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Divider(color="grey", thickness=1),
                            width=60
                        ),
                        ft.Container(
                            content=ft.Text(greeting_header, color="grey", size=14, weight=ft.FontWeight.W_500),
                            padding=ft.padding.symmetric(horizontal=10)
                        ),
                        ft.Container(
                            content=ft.Divider(color="grey", thickness=1),
                            width=60
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                
                # Audio icon and greeting text
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.icons.VOLUME_UP,
                            icon_color="#0078D7",
                            icon_size=24,
                            # You could add on_click to play audio here
                        ),
                        ft.Text(
                            waray_greeting,
                            color="#0078D7",
                            size=24,
                            weight=ft.FontWeight.BOLD
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5
                ),
                
                # English translation
                ft.Container(
                    content=ft.Text(
                        english_translation,
                        color="grey",
                        size=16
                    ),
                    margin=ft.margin.only(bottom=20)
                ),
                
                ft.Container(
                    content=ft.Image(
                        src="assets/L1.png",
                        width=250,
                        height=150,
                        fit=ft.ImageFit.CONTAIN
                    ),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Definition text
                ft.Container(
                    content=ft.Text(
                        full_definition,
                        text_align=ft.TextAlign.CENTER,
                        size=16,
                        weight=ft.FontWeight.W_500,
                        color="black"
                    ),
                    margin=ft.margin.only(bottom=20)
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        ),
        width=312,
        bgcolor="white",
        border_radius=10,
        padding=20,
        margin=ft.margin.only(top=20, bottom=20)
    )
    
    # Progress indicator
    progress = ft.Container(
        content=ft.ProgressBar(value=0.3, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20)
    )
    
    # Bottom navigation
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        icon_color="grey",
                        on_click=go_back
                    ),
                    width=100,
                    bgcolor="white",
                    border_radius=ft.border_radius.all(30),
                    padding=5
                ),
                ft.Container(width=10),  # Spacer
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Text(
                            "NEXT",
                            color="white",
                            weight=ft.FontWeight.BOLD,
                            size=16
                        ),
                        style=ft.ButtonStyle(
                            bgcolor={"": "#0078D7"},
                            shape=ft.RoundedRectangleBorder(radius=30),
                        ),
                        width=200,
                        height=50,
                        on_click=next_lesson
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        padding=ft.padding.only(bottom=20)
    )
    
    # Main content column
    main_content = ft.Column(
        [
            header,
            ft.Container(
                content=card_content,
                alignment=ft.alignment.center
            ),
            progress,
            bottom_nav
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
        expand=True
    )
    
    # Background with landscape image
    background = ft.Container(
        content=ft.Image(
            src="assets/landscape_background.png",
            width=page.width,
            height=page.height,
            fit=ft.ImageFit.COVER
        ),
        expand=True
    )
    
    # Use Stack with background
    stack = ft.Stack(
        [
            background,
            main_content
        ],
        expand=True
    )
    
    # Add the view to the page
    page.views.append(
        ft.View(
            "/lesson",
            [stack],
            padding=0
        )
    )
    
    page.update()