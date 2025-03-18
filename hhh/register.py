import flet as ft

def register_page(page: ft.Page):
    """Defines the Register Page with Routing"""
    
    def on_register_click(e):
        print("Register clicked")  # Show in output
        page.go("/setup-proficiency")  # Navigate to proficiency setup page
    
    page.views.append(
        ft.View(
            route="/register",
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            # Back to Login Button
                            ft.Row(
                                [
                                    ft.TextButton(
                                        "← Back to Login",
                                        on_click=lambda _: page.go("/"),
                                        style=ft.ButtonStyle(
                                            color="#9965FF",
                                            padding=ft.Padding(0, 5, 0, 10),  # Adjust spacing
                                        ),
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.START  # Align to left
                            ),

                            # Title & Subtitle
                            ft.Text("Register", size=28, weight=ft.FontWeight.BOLD, color="white"),
                            ft.Text("To start learning Waray!", size=14, color="#AAAAAA"),

                            # Input Fields
                            ft.Text("Username", color="white"),
                            ft.TextField(bgcolor="black", hint_text="Example: johndoe", border_color="white", border_radius=8, color="white"),

                            ft.Text("Email Address", color="white"),
                            ft.TextField(bgcolor="black", hint_text="Example: johndoe@gmail.com", border_color="white", border_radius=8, color="white"),

                            ft.Text("Password", color="white"),
                            ft.TextField(bgcolor="black", password=True, hint_text="********", border_color="white", border_radius=8, color="white"),

                            ft.Text("Retype Password", color="white"),
                            ft.TextField(bgcolor="black", password=True, hint_text="********", border_color="white", border_radius=8, color="white"),

                            # Register Button
                            ft.Container(
                                content=ft.ElevatedButton(
                                    "Register",
                                    width=350,
                                    bgcolor="#9965FF",
                                    color="white",
                                    on_click=on_register_click,  # Calls function to print and navigate
                                    icon=ft.icons.ARROW_FORWARD,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=20),
                                        padding=ft.Padding(10, 15, 10, 15),
                                    ),
                                ),
                                margin=ft.Margin(0, 20, 0, 0)  # Add space before button
                            )
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.START
                    ),
                    padding=ft.padding.symmetric(horizontal=20, vertical=50),  # Adjust margins
                    width=400  # Match width in the image
                )
            ],
        )
    )