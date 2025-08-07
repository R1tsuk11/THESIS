import flet as ft

def lesson_photo_pick_page(page: ft.Page):
    """Image selection exercise page for language learning"""
    page.title = "Arami - Image Selection Exercise"
    page.padding = 0
    
    def go_back(e):
        """Navigate back to the lesson page"""
        page.go("/lesson")
    
    def next_exercise(e):
        """Navigate to the next exercise page and log the selection"""
        # Display in console which option was selected when NEXT is pressed
        if selected_option == 0:
            print("User selected Choice 1 (Morning/Sunrise image)")
        elif selected_option == 1:
            print("User selected Choice 2 (Night image)")
        else:
            print("User did not select any image")
            
        # Navigate to next page
        page.go("/lesson-tf")
    
    # Track which option is selected
    selected_option = None
    
    # Function to handle option selection
    def on_option_click(e, option_index):
        nonlocal selected_option
        selected_option = option_index
        
        # Update all options to reflect selection state
        for i, option in enumerate([image_option1, image_option2]):
            if i == selected_option:
                option.border = ft.border.all(3, "#0078D7")  # Blue border for selected
            else:
                option.border = ft.border.all(1, "#E0E0E0")  # Light gray border for unselected
                
        page.update()
    
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
    
    # Main content
    card_content = ft.Container(
        content=ft.Column(
            [
                # "Choose the correct image:" text
                ft.Container(
                    content=ft.Text(
                        "Choose the correct image:",
                        color="#0078D7",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    margin=ft.margin.only(top=20, bottom=15)
                ),
                
                # Word to match with image with audio button (similar to lesson_page)
                ft.Container(
                    content=ft.Row(
                        [
                            # Audio button
                            ft.IconButton(
                                icon=ft.icons.VOLUME_UP,
                                icon_color="#0078D7",
                                icon_size=24,
                                # You could add on_click to play audio here
                            ),
                            # Aga text
                            ft.Text(
                                "Aga",
                                color="black",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=5
                    ),
                    width=320,
                    bgcolor="#FFF9C4",  # Light yellow background
                    padding=ft.padding.symmetric(vertical=15),
                    border_radius=10,
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Image options
                ft.Container(
                    content=ft.Column(
                        [
                            # Option 1 - Morning/Sunrise image
                            image_option1 := ft.Container(
                                content=ft.Image(
                                    src="assets/morning.jpg",  # Path to sunrise/morning image
                                    width=320,
                                    height=180,
                                    fit=ft.ImageFit.COVER,
                                    border_radius=ft.border_radius.all(10),
                                ),
                                width=320,
                                height=180,
                                border=ft.border.all(1, "#E0E0E0"),
                                border_radius=ft.border_radius.all(10),
                                margin=ft.margin.only(bottom=15),
                                on_click=lambda e: on_option_click(e, 0)
                            ),
                            
                            # Option 2 - Night image
                            image_option2 := ft.Container(
                                content=ft.Image(
                                    src="assets/night.jpg",  # Path to night image
                                    width=320,
                                    height=180,
                                    fit=ft.ImageFit.COVER,
                                    border_radius=ft.border_radius.all(10),
                                ),
                                width=320,
                                height=180,
                                border=ft.border.all(1, "#E0E0E0"),
                                border_radius=ft.border_radius.all(10),
                                margin=ft.margin.only(bottom=15),
                                on_click=lambda e: on_option_click(e, 1)
                            ),
                        ],
                        spacing=0
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        ),
        padding=ft.padding.symmetric(horizontal=20)
    )
    
    # Progress indicator
    progress = ft.Container(
        content=ft.ProgressBar(value=0.5, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20, top=10)
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
                    width=70,
                    bgcolor="#F5F5F5",
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
            card_content,
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
            "/lesson-photo-pick",
            [stack],
            padding=0
        )
    )
    
    page.update()