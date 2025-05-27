import flet as ft
from flet import Theme, PageTransitionsTheme, PageTransitionTheme
from mainmenu import connect_to_mongoDB, clear_all_temp_files


def settings_page(page: ft.Page):
    """Settings page showing user profile and app settings"""
    # Set page properties (these will be overridden by main if this is the main page)
    page.title = "Arami - Settings"
    page.padding = 0
    page.bgcolor = "#FFFFFF"
    page.theme_mode = ft.ThemeMode.LIGHT    
    page.theme = ft.Theme(font_family="Poppins")

    user_id = page.session.get("user_id")
    
    if user_id:
        from mainmenu import User
        user = User().load_data(user_id, page)
        nameHolder = user.user_name
        emailHolder = user.email or "No email provided"
    else:
        nameHolder = "Guest User"
        emailHolder = "Not logged in"

    # Header with logo and back button
    header = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="#FFFFFF",
                    icon_size=24,
                    on_click=lambda _: page.go("/main-menu")
                ),
                ft.Text(
                    "Settings",
                    size=18,
                    color="#FFFFFF",
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                # Empty container for spacing to center the title
                ft.Container(width=48)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#0066FF", "#9370DB"],
        ),
        height=70,
        padding=10,
        width=page.width
    )

    # User profile section
    def on_edit_profile(e):
        """Handles edit profile button click event."""
        print("Edit profile clicked")

    profile_picture = ft.Container(
        content=ft.Icon(
            name=ft.Icons.PERSON,
            color="#FFFFFF",
            size=40
        ),
        bgcolor="#30b4fc",  # Light blue, same as navbar
        border_radius=30,
        width=60,
        height=60,
        alignment=ft.alignment.center,
        margin=ft.margin.only(right=15)
    )

    profile_section = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    profile_picture,
                    ft.Column([
                        ft.Text(
                            nameHolder,
                            size=18,
                            color="#000000",
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(name=ft.Icons.EMAIL_OUTLINED, size=14, color="#0055b3"),
                                ft.Text(
                                    emailHolder,
                                    size=14,
                                    color="#0055b3",
                                ),
                            ]),
                            padding=ft.padding.only(top=4)
                        ),
                    ]),
                ]),
                margin=ft.margin.only(bottom=15)
            ),
            ft.Container(
                content=ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(name=ft.Icons.EDIT_OUTLINED, color="#0055b3", size=16),
                        ft.Text("Edit Profile", color="#0055b3"),
                    ]),
                    style=ft.ButtonStyle(
                        bgcolor="#FFFFFF",
                        color="#0055b3",
                        side=ft.BorderSide(width=1, color="#0055b3"),
                        shape=ft.RoundedRectangleBorder(radius=20),
                    ),
                    on_click=on_edit_profile,
                    height=40,
                ),
                width=page.width - 40,
                alignment=ft.alignment.center,
            ),
        ]),
        padding=ft.padding.symmetric(horizontal=20, vertical=15),
        bgcolor="#FFFFFF",
    )

    # App settings section
    app_settings_label = ft.Container(
        content=ft.Text(
            "APP SETTINGS",
            size=12,
            color="#0055b3",
            weight=ft.FontWeight.BOLD,
        ),
        margin=ft.margin.only(left=20, top=10, bottom=5)
    )

    # Setting Items
    def create_setting_item(icon, label, trailing=None, on_click=None, divider=True):
        item = ft.Container(
            content=ft.Column([
                ft.ListTile(
                    leading=ft.Icon(icon, color="#000000"),
                    title=ft.Text(label, size=16),
                    trailing=trailing,
                    on_click=on_click,
                    hover_color="#F5F5F5",  # Light gray when hovered
                ),
                ft.Divider(height=1, color="#EEEEEE") if divider else ft.Container(),
            ]),
            padding=ft.padding.only(left=5, right=5),
            bgcolor="#FFFFFF",  
        )
        return item

    # Settings items with on_click handlers
    change_password = create_setting_item(
        ft.Icons.LOCK_OUTLINE, 
        "Change Password",
        trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#0055b3"),
        on_click=lambda e: show_change_password_dialog(e)
        )
    
    def validate_password(password):
        """
        Validates password strength:
        - At least 8 characters long
        - Contains at least one digit
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one special character
        """
        # Check length
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        # Check for digit
        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one digit"
        
        # Check for uppercase letter
        if not any(char.isupper() for char in password):
            return False, "Password must contain at least one uppercase letter"
        
        # Check for lowercase letter
        if not any(char.islower() for char in password):
            return False, "Password must contain at least one lowercase letter"
        
        # Check for special character
        special_chars = "!@#$%^&*()-_=+[]{}|;:'\",.<>/?`~"
        if not any(char in special_chars for char in password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong"
        
    def show_change_password_dialog(e):
        """Show dialog for changing password with strength validation"""
        # Create password fields
        current_password = ft.TextField(
            label="Current Password",
            password=True,
            border_color="#0055b3",
            focused_border_color="#0055b3",
            width=300
        )
        
        new_password = ft.TextField(
            label="New Password",
            password=True,
            border_color="#0055b3",
            focused_border_color="#0055b3",
            width=300
        )
        
        confirm_password = ft.TextField(
            label="Confirm New Password",
            password=True,
            border_color="#0055b3",
            focused_border_color="#0055b3",
            width=300
        )
        
        # Password requirements helper text
        password_requirements = ft.Text(
            "Password must be at least 8 characters and include uppercase, lowercase, number, and special character",
            size=12,
            color="#666666",
            italic=True,
            text_align=ft.TextAlign.LEFT
        )
        
        # Function to handle password change
        def change_password(e):
            # Check if passwords match
            if new_password.value != confirm_password.value:
                page.open(ft.SnackBar(ft.Text("Passwords do not match!"), bgcolor="#F44336"))
                return
            
            # Validate password strength
            is_valid, message = validate_password(new_password.value)
            if not is_valid:
                page.open(ft.SnackBar(ft.Text(message), bgcolor="#F44336"))
                return
                
            # Check if current password is valid
            user_id = page.session.get("user_id")
            if not user_id:
                page.open(ft.SnackBar(ft.Text("User session expired!"), bgcolor="#F44336"))
                return
                
            usercol = connect_to_mongoDB()
            user = usercol.find_one({"user_id": user_id})
            
            if not user or user["password"] != current_password.value:
                page.open(ft.SnackBar(ft.Text("Current password is incorrect!"), bgcolor="#F44336"))
                return
                
            # Update password in database
            usercol.update_one(
                {"user_id": user_id},
                {"$set": {"password": new_password.value}}
            )
            
            # Close dialog and show confirmation
            page.close(password_dialog)
            page.open(ft.SnackBar(ft.Text("Password changed successfully!"), bgcolor="#4CAF50"))
        
        # Create dialog with enhanced content including password requirements
        password_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Change Password", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Column([
                current_password,
                ft.Container(height=5),  # Spacing
                new_password,
                password_requirements,  # Add requirements text
                ft.Container(height=5),  # Spacing
                confirm_password,
            ], spacing=10, width=300, height=240),  # Increased height to accommodate the requirements text
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.close(password_dialog)),
                ft.TextButton("Change Password", on_click=change_password)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page.open(password_dialog)

    acknowledgements = create_setting_item(
        ft.Icons.INFO_OUTLINE, 
        "Acknowledgements",
        on_click=lambda e: acknowledgements_page(page)
    )
    
    # Modified to navigate to about page when clicked
    about = create_setting_item(
        ft.Icons.INFO_OUTLINE, 
        "About",
        on_click=lambda e: about_page(page, image_urls=[]),  # Pass empty list for now
    )
    
    notifications = create_setting_item(
        ft.Icons.NOTIFICATIONS_OUTLINED, 
        "Notifications",
        # trailing=ft.Text("All active", size=14, color="#0055b3"),
        on_click=lambda e: print("Notifications clicked")
    )
    
    # Logout confirmation dialog
    def logoutConfirmation(e):
        page.open(logout_dialog)

    # In a real app, perform actual logout operations      
    # Replace the existing perform_logout function with this:
    def perform_logout(e):
        if user_id:
            user = User().load_data(user_id, page)
            user.save_user(page)
        else:
            # If no user is found, just redirect to login
            page.session.clear()
            page.go("/login")
        
    # LOGOUT DIALOG ALERT
    logout_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(
            "Log Out",
            size=20,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        content=ft.Text(
            "Are you sure you want to log out from ARAMI?",
            size=14,
            color="#0055b3",
            text_align=ft.TextAlign.CENTER,
        ),
        actions=[
            ft.Container(
                content=ft.OutlinedButton(
                    "Cancel",
                    style=ft.ButtonStyle(
                        color="#0055b3",
                        side=ft.BorderSide(width=1, color="#0055b3"),
                        shape=ft.RoundedRectangleBorder(radius=20),
                    ),
                    width=100,
                    on_click=lambda e: page.close(logout_dialog)
                ),
                padding=ft.padding.only(right=5)
            ),
            ft.Container(
                content=ft.ElevatedButton(
                    "Yes",
                    style=ft.ButtonStyle(
                        bgcolor="#0055b3",
                        color="#FFFFFF",
                        shape=ft.RoundedRectangleBorder(radius=20),
                    ),
                    width=100,
                    on_click=perform_logout
                ),
                padding=ft.padding.only(left=5)
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
        bgcolor="#FFFFFF",
        content_padding=ft.padding.all(20),
    )
    
    log_out = create_setting_item(
        ft.Icons.LOGOUT, 
        "Log Out",
        on_click=logoutConfirmation,
        divider=True
    )
    
    # Delete account -- go into a new frame (?). must type password before yes or no
    
    delete_account = create_setting_item(
        ft.Icons.DELETE_OUTLINE, 
        "Delete Account",
        on_click=lambda e: show_delete_account_dialog(e),
        divider=False
    )
    
    def show_delete_account_dialog(e):
    # Create password field for confirmation
        password = ft.TextField(
            label="Enter your password to confirm",
            password=True,
            border_color="#F44336",
            focused_border_color="#F44336",
            width=300
        )
        
        # Create warning text
        warning_text = ft.Text(
            "Warning: This action cannot be undone. All your data will be permanently deleted.",
            color="#F44336",
            size=14,
            text_align=ft.TextAlign.CENTER
        )
        
        # Function to handle account deletion
        def delete_account(e):
            from mainmenu import connect_to_mongoDB, clear_all_temp_files
            
            user_id = page.session.get("user_id")
            if not user_id:
                page.open(ft.SnackBar(ft.Text("User session expired!"), bgcolor="#F44336"))
                return
                
            usercol = connect_to_mongoDB()
            user = usercol.find_one({"user_id": user_id})
            
            if not user or user["password"] != password.value:
                page.open(ft.SnackBar(ft.Text("Password is incorrect!"), bgcolor="#F44336"))
                return
                
            # Delete account from database
            usercol.delete_one({"user_id": user_id})
            
            # Clean up temporary files
            clear_all_temp_files()
            
            # Close dialog and redirect to login
            page.close(delete_dialog)
            page.session.clear()
            page.go("/login")
        
        # Create dialog
        delete_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Account", size=20, weight=ft.FontWeight.BOLD, color="#F44336"),
            content=ft.Column([
                warning_text,
                ft.Divider(),
                password
            ], spacing=20, width=350, height=150),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.close(delete_dialog)),
                ft.TextButton("Delete Account", 
                            on_click=delete_account, 
                            style=ft.ButtonStyle(color={"": "#F44336"}))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page.open(delete_dialog)

    # Red texts for log out and delete acc
    log_out_text = log_out.content.controls[0].title
    log_out_text.color = "#F44336"  # Red color
    
    delete_account_text = delete_account.content.controls[0].title
    delete_account_text.color = "#F44336"  # Red color

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
                        icon=ft.Icons.PERSON_OUTLINED,
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
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, "#000000"),
            offset=ft.Offset(0, 0),
        ),
        alignment=ft.alignment.center,
    )

    scrollable_list = ft.ListView(
        [
            profile_section,
            app_settings_label,
            change_password,
            acknowledgements,
            about,
            notifications,
            ft.Divider(height=1, thickness=1, color="#DDDDDD"),
            log_out,
            delete_account
        ],
        spacing=0,
        padding=ft.padding.only(bottom=80),  
        expand=True,
    )
    
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
    
    # If this is the first view, use the "/" route as main
    if len(page.views) == 0:
        route = "/"
    else:
        route = "/settings"
        
    # Add view to page
    page.views.append(
        ft.View(
            route,
            [main_stack],
            padding=0,
            bgcolor="#FFFFFF"
        )
    )
    page.update()

# Function to go to the about page
def go_to_about_page(page):
    # First check if the about page view already exists
    for view in page.views:
        if view.route == "/about":
            # If it exists, just navigate to it
            page.go("/about")
            return
            
    # If the about page doesn't exist yet, create it
    about_page(page)
    page.go("/about")

def about_page(page: ft.Page, image_urls: list):
    """About page showing team information for Arami app"""
    page.title = "Arami - About"
    page.padding = 0
    page.bgcolor = "#FFFFFF"
    page.theme = ft.Theme(font_family="Poppins", 
    )
    
    header = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="#000000",
                    on_click=lambda _: settings_page(page) # Changed to go back to settings instead of main menu
                ),
                ft.Text(
                    "About",
                    size=18,
                    color="#000000",
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(width=48)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        bgcolor="#FFFFFF",
        height=60,
        padding=10,
        margin=ft.margin.only(top=15) # Added margin at the top
    )    
    
    # Blue banner at the top (matching the reference image)
    blue_banner = ft.Container(
        bgcolor="#0055b3",
        height=40,
        width=page.width
    )
    
    thin_line = ft.Container(
        bgcolor="#DDDDDD",  
        height=1, 
        width=page.width - 60,  
        margin=ft.margin.only(left=30, right=30)
    )
    
    # App name section
    app_name = ft.Container(
        content=ft.Text(
            "ARAMI",
            size=24,
            color="#000000",
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.LEFT,
        ),
        margin=ft.margin.only(left=30, top=10, bottom=10)  # Reduced top margin
    )
    
    # App description card
    app_description = ft.Container(
        content=ft.Text(
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Maecenas mattis risus et libero ultrices, in lobortis sapien consectetur.",
            size=14,
            color="#FFFFFF",
            text_align=ft.TextAlign.LEFT,
        ),
        bgcolor="#0055b3",  # Dark blue background
        border_radius=15,
        padding=ft.padding.all(20),
        margin=ft.margin.symmetric(horizontal=30),
        width=page.width - 40,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=5,
            color=ft.Colors.BLACK54,
            offset=ft.Offset(0, 2),
        ),
    )
    
    # Team section title
    team_title = ft.Container(
        content=ft.Text(
            "The Team Behind Arami",
            size=18,
            color="#000000",
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.LEFT,
        ),
        margin=ft.margin.only(left=30, top=30, bottom=15)
    )
    
    # Function to create a team member profile card that exactly matches the photo reference
    def create_profile_card(name, role, email, image_url=None):
        profile_image = ft.Image(
            src="THESIS-main/THESIS/gui/hhh/assets/sampleID.jpg",
            width=220,
            height=220,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(5),
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    profile_image,
                    ft.Container(height=10),  # Space between image and name
                    ft.Text(
                        name,
                        size=16,
                        color="#FFFFFF",
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        role,
                        size=14,
                        color="#FFFFFF",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=5),  # Space between role and email
                    ft.Container(
                        bgcolor="#DDDDDD",  
                        height=1, 
                        width=175,  
                        margin=10,
                    ),
                    ft.Text(
                        email,
                        size=12,
                        color="#FFFFFF",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor="#0055b3",  # Dark blue background
            border_radius=15,
            padding=ft.padding.symmetric(vertical=20, horizontal=15),
            margin=ft.margin.symmetric(horizontal=20, vertical=10),
            width=240,
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=5,
                color=ft.Colors.BLACK54,
                offset=ft.Offset(0, 2),
            ),
        )
    
    # Team member data
    team_members = [
        {
            "name": "Arquiza, Miguelin III.",
            "role": "Lead Programmer",
            "email": "adamtumaning@gmail.com",
            "image": "/api/placeholder/150/150"
        },
        {
            "name": "Creer, Chelsea Anne",
            "role": "UI/UX Designer",
            "email": "minji.lee@gmail.com",
            "image": "/api/placeholder/150/150"
        },
        {
            "name": "Flores, Robert Gabriel",
            "role": "Language Expert",
            "email": "mgarcia@gmail.com",
            "image": "/api/placeholder/150/150"
        },
        {
            "name": "Tumaning, Benedict Adam",
            "role": "Project Manager",
            "email": "emily.smith@gmail.com",
            "image": "/api/placeholder/150/150"
        },
    ]
    
    # Create team member profile cards
    profile_cards = []
    for member in team_members:
        card = create_profile_card(
            member["name"],
            member["role"],
            member["email"],
            member["image"]
        )
        profile_cards.append(card)
    
    # Create a ListView for scrollable content
    scrollable_list = ft.ListView(
        spacing=10,
        padding=ft.padding.only(bottom=80),  # Increased padding to prevent bottom nav overlap
        expand=True,
    )

    # Create a Row with center alignment for profile cards
    profile_card_row = ft.Row(
        profile_cards,
        alignment=ft.MainAxisAlignment.CENTER,
        wrap=True,
        spacing=10,
    )

    # Add content to the ListView
    scrollable_list.controls.extend([
        thin_line,  # Added thin line
        app_name,
        app_description,
        team_title,
        profile_card_row  # Now using the centered row instead of individual cards
    ])
    
    # Content area that will be scrollable
    content_area = ft.Container(
        content=scrollable_list,
        expand=True,
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
                    width=50,  # Fixed width to ensure consistent spacing
                    height=50,  # Fixed height to ensure proper display
                    alignment=ft.alignment.center,  # Center the icon in its container
                    padding=0,  # Remove padding that might cause overflow
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
                        icon=ft.Icons.PERSON_OUTLINED,
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
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.SETTINGS_OUTLINED,  # Note the proper capitalization: SETTINGS_OUTLINED
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
            vertical_alignment=ft.CrossAxisAlignment.CENTER,  # Ensure vertical centering
            height=60,  # Set explicit height for the row
        ),
        border_radius=25,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#30b4fc", "#2980b9"],
        ),
        height=70,  # Slightly reduced height to avoid any overflow
        padding=ft.padding.symmetric(horizontal=15, vertical=5),
        margin=ft.margin.only(bottom=10, left=10, right=10),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, "#000000"),
            offset=ft.Offset(0, 0),
        ),
        # Ensure the container aligns its content in the center
        alignment=ft.alignment.center,
    )
    
    # Stack for fixed header, blue banner, scrollable content, and fixed footer
    main_stack = ft.Stack(
        [
            # First add the content that should stretch full height
            ft.Column(
                [
                    # blue_banner,  # Blue banner at the top
                    header,  # Header with back button and title
                    content_area,  # Scrollable content
                ],
                spacing=0,
                expand=True,
            ),
            # Then position the bottom nav at the bottom
            ft.Container(
                content=bottom_nav,
                bottom=0,
                left=0,
                right=0,
            ),
        ],
        expand=True,
    )
    
    # Add view to page
    page.views.append(
        ft.View(
            "/about",
            [main_stack],
            padding=0,
            bgcolor="#FFFFFF"
        )
    )
    page.update()

def acknowledgements_page(page: ft.Page):
    """About page showing acknowledgements for Arami app"""
    page.title = "Arami - About"
    page.padding = 0
    page.bgcolor = "#FFFFFF"
    page.theme = ft.Theme(font_family="Poppins", 

    )
    
    header = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="#000000",
                    on_click=lambda _: settings_page(page) # Changed to go back to settings instead of main menu
                ),
                ft.Text(
                    "Acknowledgements",
                    size=18,
                    color="#000000",
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(width=48)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        bgcolor="#FFFFFF",
        height=60,
        padding=10,
        margin=ft.margin.only(top=15) # Added margin at the top
    )    

    
    thin_line = ft.Container(
        bgcolor="#DDDDDD",  
        height=1, 
        width=page.width - 60,  
        margin=ft.margin.only(left=30, right=30, top=10)
    )
    
    # Acknowledgements card
    app_acknowledgements = ft.Container(
        content=ft.Text(
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Maecenas mattis risus et libero ultrices, in lobortis sapien consectetur.",
            size=14,
            color="#FFFFFF",
            text_align=ft.TextAlign.LEFT,
        ),
        bgcolor="#0055b3",  # Dark blue background
        border_radius=15,
        padding=ft.padding.all(20),
        margin=ft.margin.symmetric(horizontal=30, vertical=30),
        width=page.width - 40,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=5,
            color=ft.Colors.BLACK54,
            offset=ft.Offset(0, 2),
        ),
    )
    
    
    # Create a ListView for scrollable content
    scrollable_list = ft.ListView(
        spacing=10,
        padding=ft.padding.only(bottom=80),  # Increased padding to prevent bottom nav overlap
        expand=True,
    )

    # Add content to the ListView
    scrollable_list.controls.extend([
        thin_line,  # Added thin line
        app_acknowledgements
    ])
    
    # Content area that will be scrollable
    content_area = ft.Container(
        content=scrollable_list,
        expand=True,
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
                    width=50,  # Fixed width to ensure consistent spacing
                    height=50,  # Fixed height to ensure proper display
                    alignment=ft.alignment.center,  # Center the icon in its container
                    padding=0,  # Remove padding that might cause overflow
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
                        icon=ft.Icons.PERSON_OUTLINED,
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
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.SETTINGS_OUTLINED,  # Note the proper capitalization: SETTINGS_OUTLINED
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
            vertical_alignment=ft.CrossAxisAlignment.CENTER,  # Ensure vertical centering
            height=60,  # Set explicit height for the row
        ),
        border_radius=25,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#30b4fc", "#2980b9"],
        ),
        height=70,  # Slightly reduced height to avoid any overflow
        padding=ft.padding.symmetric(horizontal=15, vertical=5),
        margin=ft.margin.only(bottom=10, left=10, right=10),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, "#000000"),
            offset=ft.Offset(0, 0),
        ),
        # Ensure the container aligns its content in the center
        alignment=ft.alignment.center,
    )
    
    # Stack for fixed header, blue banner, scrollable content, and fixed footer
    main_stack = ft.Stack(
        [
            # First add the content that should stretch full height
            ft.Column(
                [
                    # blue_banner,  # Blue banner at the top
                    header,  # Header with back button and title
                    content_area,  # Scrollable content
                ],
                spacing=0,
                expand=True,
            ),
            # Then position the bottom nav at the bottom
            ft.Container(
                content=bottom_nav,
                bottom=0,
                left=0,
                right=0,
            ),
        ],
        expand=True,
    )
    
    # Add view to page
    page.views.append(
        ft.View(
            "/about",
            [main_stack],
            padding=0,
            bgcolor="#FFFFFF"
        )
    )
    page.update()
