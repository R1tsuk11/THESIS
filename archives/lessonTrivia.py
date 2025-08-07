import flet as ft

def lesson_trivia(page: ft.Page):
    """Trivia page for displaying interesting facts about the language"""
    page.title = "Arami - Did You Know?"
    page.padding = 0
    
    def go_back(e):
        """Navigate back to the previous page"""
        page.go("/lesson")
    
    def next_screen(e):
        """Navigate to the next page"""
        page.go("/lesson-translate")
    
    # Define text variables
    trivia_header = "DID YOU KNOW?"
    trivia_content = "Waraynons also use \"Maupay!\" when trying to call a person when there is no bantay putekpaano ba sabihin"
    
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
    
    # Card content - set to fixed size matching the screenshot
    card_content = ft.Container(
        content=ft.Column(
            [
                # DID YOU KNOW? header with lines
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Divider(color="grey", thickness=1),
                            width=60
                        ),
                        ft.Container(
                            content=ft.Text(trivia_header, color="grey", size=14, weight=ft.FontWeight.W_500),
                            padding=ft.padding.symmetric(horizontal=10)
                        ),
                        ft.Container(
                            content=ft.Divider(color="grey", thickness=1),
                            width=60
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                
                # Trivia content - now with bold text
                ft.Container(
                    content=ft.Text(
                        trivia_content,
                        text_align=ft.TextAlign.CENTER,
                        size=16,
                        weight=ft.FontWeight.BOLD,  # Changed to BOLD
                        color="#0078D7"
                    ),
                    margin=ft.margin.only(top=20, bottom=20),
                    padding=ft.padding.symmetric(horizontal=10)
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        ),
        width=312,  # Fixed width
        height=280,  # Fixed height matching screenshot
        bgcolor="white",
        border_radius=10,
        padding=20,
        margin=ft.margin.only(top=20, bottom=20)
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
                        on_click=next_screen
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
            "/lesson-trivia",
            [stack],
            padding=0
        )
    )
    
    page.update()