import flet as ft

def lesson_translate_sentence_page(page: ft.Page):
    """Translation exercise page for sentences in language learning"""
    page.title = "Arami - Sentence Translation Exercise"
    page.padding = 0
    
    def go_back(e):
        """Navigate back to the lesson-translate page"""
        page.go("/lesson-translate")
    
    def next_exercise(e):
        """Handle progression to the next exercise"""
        # Navigate to the pronunciation exercise
        page.go("/lesson-pronounce")
    
    # Define text variables
    question_text = "How do you say Good morning, Mulay! in Waray?"
    display_sentence = ""  # Initially empty
    instruction_text = "Choose the correct sentence:"
    option1_text = "Maupay nga kulop, Mulay!"
    option2_text = "Maupay nga aga, Mulay!"
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
    
    # Create the sentence display text
    sentence_text = ft.Text(
        display_sentence,
        color="black",
        size=18,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER
    )
    
    # Create the sentence display container
    sentence_display = ft.Container(
        content=sentence_text,
        width=320,
        border=ft.border.all(1, "#FFC107"),  # Yellow border
        border_radius=10,
        padding=ft.padding.symmetric(vertical=15),
        margin=ft.margin.only(bottom=20),
        alignment=ft.alignment.center  # Center the text horizontally
    )
    
    # Track which option is selected
    selected_option = None
    
    # Function to handle option selection
    def on_option_click(e, option_index):
        nonlocal selected_option
        selected_option = option_index
        
        # Update the sentence display with the selected option
        if option_index == 0:
            sentence_text.value = option1_text
        else:
            sentence_text.value = option2_text
        
        # Update all options to reflect selection state
        for i, option in enumerate([option1, option2]):
            if i == selected_option:
                option.border = ft.border.all(2, "black")
                option.bgcolor = "white"
            else:
                option.border = None
                option.bgcolor = "#F5F5F5"
                
        page.update()
    
    # Card content
    card_content = ft.Container(
        content=ft.Column(
            [
                # Question text
                ft.Container(
                    content=ft.Text(
                        question_text,
                        color="black",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    width=320,
                    bgcolor="#FFF9C4",  # Light yellow background
                    padding=ft.padding.symmetric(vertical=15, horizontal=10),
                    border_radius=10,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Display sentence (initially empty)
                sentence_display,
                
                # Divider line
                ft.Container(
                    content=ft.Divider(color="grey", thickness=1),
                    width=280,
                    margin=ft.margin.only(bottom=10)
                ),
                
                # "Choose the correct sentence:" text
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
                
                # Options buttons
                ft.Container(
                    content=ft.Column(
                        [
                            # Option 1
                            option1 := ft.Container(
                                content=ft.Text(
                                    option1_text,
                                    color="black",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER
                                ),
                                width=320,
                                bgcolor="#F5F5F5",  # Light gray background
                                padding=ft.padding.symmetric(vertical=15),
                                border_radius=10,
                                margin=ft.margin.only(bottom=10),
                                on_click=lambda e: on_option_click(e, 0)
                            ),
                            
                            # Option 2
                            option2 := ft.Container(
                                content=ft.Text(
                                    option2_text,
                                    color="black",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER
                                ),
                                width=320,
                                bgcolor="#F5F5F5",  # Light gray background (not selected by default)
                                padding=ft.padding.symmetric(vertical=15),
                                border_radius=10,
                                margin=ft.margin.only(bottom=20),
                                on_click=lambda e: on_option_click(e, 1)
                            ),
                        ]
                    )
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
        content=ft.ProgressBar(value=0.5, bgcolor="#e0e0e0", color="#0078D7", width=300),
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
            "/lesson-translate-sentence",
            [stack],
            padding=0
        )
    )
    
    page.update()