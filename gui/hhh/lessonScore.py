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
    
    score_image_urls = [
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747653930/tryagain_j5tsjw.png",  # tryagain - 0
        "https://res.cloudinary.com/djm2qhi9f/image/upload/v1747653931/goodjob_jbi6dt.png",  # goodjob - 1
    ]
    
    def return_to_levels(e):
        """Navigate back to the levels page"""
        page.go("/levels")
    
    # Create top header with close button
    header = ft.Container(
        content=ft.Row(
            [
                ft.Container(width=50),  # Spacer
            ],
            alignment=ft.MainAxisAlignment.END
        ),
        padding=ft.padding.only(top=40) 
    )
    
    # Determine which image to show based on accuracy
    img1 = score_image_urls[1]  # goodjob
    img2 = score_image_urls[0]  # tryagain
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
                                    f"{round(accuracyPercentage)} %",
                                    color="white",
                                    size=40,
                                    weight=ft.FontWeight.BOLD
                                ),
                                padding=ft.padding.symmetric(vertical=8)   # Increased vertical padding
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
                    margin=ft.margin.only(top=15, bottom=30)
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        ),
        width=312,
        height=500,
        bgcolor="white",
        border_radius=10,
        border=ft.border.all(2, "#0078D7"),
        padding=15,
        margin=ft.margin.only(top=20, bottom=20),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.Colors.GREY_400,
            offset=ft.Offset(2, 2)
        )
    )
    
    scrollable_content = ft.ListView(
        controls=[card_content],
        expand=True,
        spacing=0,
        padding=0,
        auto_scroll=False
    )

    # Progress indicator - set na to 100% because i noticed nagloloko siya sa lesson score page only
    progress = ft.Container(
        content=ft.ProgressBar(value=1.0, bgcolor="#e0e0e0", color="#0078D7", width=300),
        margin=ft.margin.only(bottom=20)
    )
    
    # Bottom navigation - UPDATED to match lessonTrivia.py style
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Text(
                            "FINISH", 
                            color="#375a04",
                            weight=ft.FontWeight.BOLD,
                            size=16
                        ),
                        style=ft.ButtonStyle(
                            bgcolor={"": "#80ffbe"},
                            shape=ft.RoundedRectangleBorder(radius=30),
                        ),
                        width=280,
                        height=50,
                        on_click=return_to_levels 
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
                content=scrollable_content,
                alignment=ft.alignment.center,
                expand=True,  # Take available space
                width=312 
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
            src="THESIS-main/THESIS/gui/hhh/assets/landscape_background.png",
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