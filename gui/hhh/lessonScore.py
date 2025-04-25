import flet as ft
import os

def lesson_score(page: ft.Page, accuracyPercentage=50, noOfCorrect=0, noOfIncorrect=0, responseTime="3:01"):
    """
    Score summary page displaying lesson results
    
    Parameters:
    - accuracyPercentage: int - Percentage of correct answers (0-100)
    - noOfCorrect: int - Number of correct answers
    - noOfIncorrect: int - Number of incorrect answers
    - responseTime: str - Total response time formatted as "M:SS"
    """
    page.title = "Arami - Lesson Score"
    page.padding = 0
    correct = len(noOfCorrect)
    incorrect = len(noOfIncorrect)
    
    def go_back(e): # To be voided
        """Navigate back to the previous page"""
        page.go("/levels")
    
    def return_to_levels(e):
        """Navigate back to the levels page"""
        page.go("/levels")
    
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
    
    # Determine which image to show based on accuracy
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_PATH = os.path.join(BASE_DIR, "assets")
    img1 = os.path.join(ASSETS_PATH, os.path.basename("assets/goodjob.png"))
    img2 = os.path.join(ASSETS_PATH, os.path.basename("assets/tryagain.png"))
    celebration_image = img1 if accuracyPercentage >= 50 else img2
    
    # Card content
    card_content = ft.Container(
        content=ft.Column(
            [
                # SCORE header with lines
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Divider(color="grey", thickness=1),
                            width=60
                        ),
                        ft.Container(
                            content=ft.Text("SCORE", color="grey", size=14, weight=ft.FontWeight.W_500),
                            padding=ft.padding.symmetric(horizontal=10)
                        ),
                        ft.Container(
                            content=ft.Divider(color="grey", thickness=1),
                            width=60
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                
                # Accuracy box - INCREASED HEIGHT and better padding
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "ACCURACY",
                                color="white",
                                size=14,
                                weight=ft.FontWeight.W_500
                            ),
                            ft.Container(
                                content=ft.Text(
                                    f"{accuracyPercentage} %",
                                    color="white",
                                    size=40,
                                    weight=ft.FontWeight.BOLD
                                ),
                                padding=ft.padding.symmetric(vertical=8)  # Increased vertical padding
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=3
                    ),
                    width=250,
                    height=95,  # Increased height from 80 to 95
                    bgcolor="#75B0FF",  # Lighter blue
                    border_radius=15,  # More rounded
                    padding=ft.padding.all(10),
                    margin=ft.margin.only(top=10, bottom=15)
                ),
                
                # Celebration image - conditionally shows goodjob.png or tryagain.png
                ft.Container(
                    content=ft.Image(
                        src=celebration_image,
                        width=120,
                        height=117,
                        fit=ft.ImageFit.CONTAIN
                    ),
                    margin=ft.margin.only(bottom=15)
                ),
                
                # Correct and Incorrect counters row
                ft.Row(
                    [
                        # Correct counter - using variable
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        correct,
                                        color="#3A5D30",  # Darker green text
                                        size=36,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        "CORRECT",
                                        color="#3A5D30",  # Darker green text
                                        size=12,
                                        weight=ft.FontWeight.W_500
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=0
                            ),
                            width=100,
                            height=90,
                            bgcolor="#C2F2A5",  # Lighter green background
                            border_radius=8,
                            padding=ft.padding.all(10)
                        ),
                        
                        ft.Container(width=15),  # Spacer
                        
                        # Incorrect counter - using variable
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        incorrect,
                                        color="#95353A",  # Darker red text
                                        size=36,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        "INCORRECT",
                                        color="#95353A",  # Darker red text
                                        size=12,
                                        weight=ft.FontWeight.W_500
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=0
                            ),
                            width=100,
                            height=90,
                            bgcolor="#FFB7B7",  # More accurate pink/red background
                            border_radius=8,
                            padding=ft.padding.all(10)
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                
                # Response time - using variable
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(
                                        "RESPONSE",
                                        color="#847B00",  # Darker yellow/gold text
                                        size=12,
                                        weight=ft.FontWeight.W_500,
                                        text_align=ft.TextAlign.LEFT
                                    ),
                                    ft.Text(
                                        "TIME:",
                                        color="#847B00",  # Darker yellow/gold text
                                        size=12,
                                        weight=ft.FontWeight.W_500,
                                        text_align=ft.TextAlign.LEFT
                                    )
                                ],
                                spacing=0,
                                alignment=ft.MainAxisAlignment.CENTER
                            ),
                            ft.Container(width=25),  # Spacer
                            ft.Text(
                                responseTime,  # Using the variable
                                color="#847B00",  # Darker yellow/gold text
                                size=36,
                                weight=ft.FontWeight.BOLD
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    width=250,
                    height=60,
                    bgcolor="#FDFDBC",  # More accurate pale yellow background
                    border_radius=12,
                    padding=ft.padding.all(5),
                    margin=ft.margin.only(top=15)
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        ),
        width=312,
        height=500,
        bgcolor="white",
        border_radius=10,
        border=ft.border.all(2, "#0078D7"),
        padding=15,
        margin=ft.margin.only(top=20, bottom=20)
    )
    
    # Progress indicator - calculate based on accuracy for more meaningful progress
    progress_value = min(1.0, max(0.1, accuracyPercentage / 100))
    progress = ft.Container(
        content=ft.ProgressBar(value=progress_value, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20)
    )
    
    # Bottom navigation - UPDATED to match lessonTrivia.py style
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
                            shape=ft.RoundedRectangleBorder(radius=30),  # Rounded corners like lessonTrivia.py
                        ),
                        width=200,
                        height=50,
                        on_click=return_to_levels  # Navigate back to levels page
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
            "/lesson-score",
            [stack],
            padding=0
        )
    )
    
    page.update()