import flet as ft

def login_page(page: ft.Page):
    page.views.append(
        ft.View(
            route="/",
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            # Logo aligned to the right
                            ft.Row(
                                [ft.Image(src="https://i.ibb.co/d4HCpDD6/arami-logo-removebg-preview.png", height=120)],
                                alignment=ft.MainAxisAlignment.END
                            ),

                            # Welcome Text
                            ft.Text("Let's Login!", size=26, weight=ft.FontWeight.BOLD, color="white"),
                            ft.Text("Maupay nga pagbalik!", size=14, color="white"),

                            # Username & Password Fields
                            ft.Text("Username", color="white"),
                            ft.TextField(hint_text="Example: johndoe", bgcolor="black", border_color="white", border_radius=8, color="white"),
                            ft.Container(height=10),  # Padding
                            ft.Text("Password", color="white"),
                            ft.TextField(hint_text="********", bgcolor="black", password=True, border_color="white", border_radius=8, color="white"),

                            # Forgot Password
                            ft.Row(
                                [ft.TextButton("Forgot Password", on_click=lambda _: print("Forgot Password clicked"), style=ft.ButtonStyle(color="#9965FF"))],
                                alignment=ft.MainAxisAlignment.START
                            ),

                        # Centered Login Section
                        ft.Container(
                            content=ft.Column(
                                [
                                    # Login Button
                                    ft.ElevatedButton(
                                        "Login",
                                        width=300,
                                        bgcolor="#9965FF",  # Matched color
                                        color="white",
                                        on_click=lambda _: print("Login clicked"),
                                        icon=ft.icons.ARROW_FORWARD,
                                        style=ft.ButtonStyle(
                                            shape=ft.RoundedRectangleBorder(radius=20)
                                        )
                                    ),

                                    # "Or" Divider
                                    ft.Container(
                                        content=ft.Text("Or", color="white", text_align=ft.TextAlign.CENTER),
                                        padding=ft.padding.only(top=10, bottom=10),
                                    ),

                                    # Register Link
                                    ft.TextButton(
                                        "First time here? Register here",
                                        on_click=lambda _: page.go("/register"),
                                        style=ft.ButtonStyle(color="#9965FF")  # Matched color
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            alignment=ft.alignment.center,
                            expand=True
                        )
                    ],
                    spacing=10,
                    alignment=ft.MainAxisAlignment.START
                ),
                padding=ft.padding.only(top=50),
                width=350
                )
            ],
        )
    )