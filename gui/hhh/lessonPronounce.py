import flet as ft

def lesson_pronounce_page(page: ft.Page):
    """Pronunciation exercise page for language learning"""
    page.title = "Arami - Pronunciation Exercise"
    page.padding = 0
    
    def go_back(e):
        """Navigate back to the lesson-translate-sentence page"""
        page.go("/lesson-translate-sentence")
    
    def next_exercise(e):
        """Handle progression to the next exercise"""
        # This would typically navigate to another exercise
        print("Moving to next exercise")
        # Future routing could be added here
    
    # Define text variables
    instruction_text = "Pronounce the word:"
    word_text = "Aga"
    translation_text = "Morning"
    tap_record_text = "Tap to record"
    next_button_text = "NEXT"
    
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
    
    # Function to handle microphone button press
    def on_mic_press(e):
        """Handle microphone recording button press"""
        print("Recording started")
        # Microphone recording logic would go here
        page.update()
    
    # Card content
    card_content = ft.Container(
        content=ft.Column(
            [
                # Instruction text
                ft.Container(
                    content=ft.Text(
                        instruction_text,
                        color="#0078D7",  # Blue color
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    margin=ft.margin.only(bottom=15)
                ),
                
                # Word to pronounce
                ft.Container(
                    content=ft.Row(
                        [
                            # Sound icon
                            ft.Icon(
                                name=ft.icons.VOLUME_UP_ROUNDED,
                                color="black",
                                size=20
                            ),
                            
                            # Word text
                            ft.Text(
                                word_text,
                                color="black",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10
                    ),
                    width=320,
                    bgcolor="#FFF9C4",  # Light yellow background
                    padding=ft.padding.symmetric(vertical=15, horizontal=10),
                    border_radius=10,
                    margin=ft.margin.only(bottom=15)
                ),
                
                # Translation text
                ft.Container(
                    content=ft.Text(
                        translation_text,
                        color="black",
                        size=16,
                        text_align=ft.TextAlign.CENTER
                    ),
                    margin=ft.margin.only(bottom=30)
                ),
                
                # Microphone button
                ft.Container(
                    content=ft.Column(
                        [
                            # Circular yellow button with microphone
                            ft.Container(
                                content=ft.Icon(
                                    name=ft.icons.MIC,
                                    color="black",
                                    size=40
                                ),
                                width=120,
                                height=120,
                                bgcolor="#FFC107",  # Yellow color
                                border_radius=60,  # Half of width/height for circle
                                alignment=ft.alignment.center,
                                on_click=on_mic_press,
                                margin=ft.margin.only(bottom=20),
                                # Add glow effect with box shadow
                                shadow=ft.BoxShadow(
                                    spread_radius=1,
                                    blur_radius=15,
                                    color=ft.colors.YELLOW_100,
                                    offset=ft.Offset(0, 0)
                                )
                            ),
                            
                            # "Tap to record" text
                            ft.Text(
                                tap_record_text,
                                color="black",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    margin=ft.margin.only(bottom=30)
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        ),
        padding=ft.padding.only(top=20)
    )
    
    # Progress indicator
    progress = ft.Container(
        content=ft.ProgressBar(value=0.33, bgcolor="#e0e0e0", color="#0078D7", width=300),
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
                    bgcolor="#F5F5F5",
                    border_radius=ft.border_radius.all(30),
                    padding=5
                ),
                ft.Container(width=10),  # Spacer
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Text(
                            next_button_text,
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
                        on_click=next_exercise
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
    
    # Add a blue bar at the top
    blue_bar = ft.Container(
        height=10,
        bgcolor="#0078D7",
        width=page.width
    )
    
    # Wrap everything in a stack
    stack = ft.Stack(
        [
            # White background
            ft.Container(bgcolor="white", expand=True),
            # Stack the blue bar and main content
            ft.Column([blue_bar, main_content], spacing=0, expand=True)
        ],
        expand=True
    )
    
    # Add the view to the page
    page.views.append(
        ft.View(
            "/lesson-pronounce",
            [stack],
            padding=0
        )
    )
    
    page.update()