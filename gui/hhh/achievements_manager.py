import flet as ft
from datetime import datetime
import time
import json
import os
from qbank import achievement_bank as ACHIEVEMENTS

def check_and_unlock_achievements(user_id, page=None):
    """Check and unlock achievements based on session data"""
    if page is None:
        print("Page object is required for session-based achievements")
        return False
        
    # Get modules directly from page.session with proper error handling
    modules = []
    raw_modules = page.session.get("modules")
    if raw_modules:
        modules = raw_modules
    
    # Get user library with proper error handling
    user_library = []
    raw_library = page.session.get("user_library")
    if raw_library:
        user_library = raw_library
        
    # Get user achievements with proper error handling
    user_achievements = {}
    raw_achievements = page.session.get("user_achievements")
    if raw_achievements:
        user_achievements = raw_achievements
    else:
        # Initialize achievements using the imported achievement_bank
        user_achievements = {}
        for achievement_id, achievement in ACHIEVEMENTS.items():
            user_achievements[achievement_id] = achievement.copy()  # Use copy to avoid modifying original
    
    # Get reviews completed with proper error handling
    reviews_completed = 0
    raw_reviews = page.session.get("reviews_completed")
    if raw_reviews is not None:
        reviews_completed = raw_reviews
    
    # Track newly unlocked achievements
    newly_unlocked = []
    
    # Count completed lessons and modules - FIXED COUNTING LOGIC
    completed_lessons = 0
    completed_modules = 0
    
    for module in modules:
        module_completed = True
        module_level_count = 0
        module_completed_levels = 0
        
        for level in getattr(module, "levels", []):
            module_level_count += 1
            # Handle both dictionary and object styles
            level_completed = False
            
            if isinstance(level, dict):
                level_completed = level.get("completed", False)
            else:
                level_completed = getattr(level, "completed", False)
                
            if level_completed:
                completed_lessons += 1
                module_completed_levels += 1
            else:
                module_completed = False
        
        # Only count a module as completed if all levels are completed
        if module_completed and module_level_count > 0 and module_level_count == module_completed_levels:
            completed_modules += 1
            
    print(f"[Achievements] Found {completed_lessons} completed lessons, {completed_modules} completed modules")
    
    # Count vocabulary words
    vocabulary_count = len(user_library) if user_library else 0
    print(f"[Achievements] Found {vocabulary_count} vocabulary words")
    
    # Check for achievements
    for achievement_id, achievement in ACHIEVEMENTS.items():
        # Skip already completed achievements
        if user_achievements.get(achievement_id, {}).get("completed", False):
            continue
            
        unlocked = False
        
        # Check based on achievement type
        if achievement["type"] == "lesson_completion":
            if completed_lessons >= achievement["requirement"]:
                unlocked = True
                print(f"[Achievements] Unlocked {achievement['name']} - completed {completed_lessons} lessons")
                
        elif achievement["type"] == "module_completion":
            if completed_modules >= achievement["requirement"]:
                unlocked = True
                print(f"[Achievements] Unlocked {achievement['name']} - completed {completed_modules} modules")
                
        elif achievement["type"] == "vocabulary":
            if vocabulary_count >= achievement["requirement"]:
                unlocked = True
                print(f"[Achievements] Unlocked {achievement['name']} - learned {vocabulary_count} words")
                
        elif achievement["type"] == "score":
            # Check if any lesson has perfect score
            for module in modules:
                for level in getattr(module, "levels", []):
                    grade_percentage = None
                    if isinstance(level, dict):
                        grade_percentage = level.get("grade_percentage")
                    else:
                        grade_percentage = getattr(level, "grade_percentage", None)
                        
                    if grade_percentage is not None and float(grade_percentage) >= achievement["requirement"]:
                        unlocked = True
                        print(f"[Achievements] Unlocked {achievement['name']} - got perfect score {grade_percentage}%")
                        break
                if unlocked:
                    break
                    
        elif achievement["type"] == "review":
            if reviews_completed >= achievement["requirement"]:
                unlocked = True
                print(f"[Achievements] Unlocked {achievement['name']} - completed {reviews_completed} reviews")
                
        elif achievement["type"] == "time":
            # Check for fast completion time
            for module in modules:
                for level in getattr(module, "levels", []):
                    completion_time = None
                    if isinstance(level, dict):
                        completion_time = level.get("completion_time")
                    else:
                        completion_time = getattr(level, "completion_time", None)
                        
                    if completion_time is not None and float(completion_time) <= achievement["requirement"]:
                        unlocked = True
                        print(f"[Achievements] Unlocked {achievement['name']} - completed in {completion_time} seconds")
                        break
                if unlocked:
                    break
        
        # Update achievement if unlocked
        if unlocked:
            try:
                user_achievements[achievement_id]["completed"] = True
                user_achievements[achievement_id]["date_earned"] = datetime.now().strftime("%Y-%m-%d")
                newly_unlocked.append(achievement_id)
            except KeyError:
                # Create the achievement entry if it doesn't exist
                user_achievements[achievement_id] = {
                    "id": achievement_id,
                    "name": ACHIEVEMENTS[achievement_id]["name"],
                    "description": ACHIEVEMENTS[achievement_id]["description"],
                    "icon": ACHIEVEMENTS[achievement_id]["icon"],
                    "completed": True,
                    "date_earned": datetime.now().strftime("%Y-%m-%d")
                }
                newly_unlocked.append(achievement_id)
    
    # Save achievements back to session
    page.session.set("user_achievements", user_achievements)
    
    # Also save directly to database for immediate persistence
    if newly_unlocked:
        try:
            from mainmenu import connect_to_mongoDB
            usercol = connect_to_mongoDB()
            usercol.update_one(
                {"user_id": user_id},
                {"$set": {"achievements": user_achievements}}
            )
            print(f"[DEBUG] Saved {len(newly_unlocked)} new achievements directly to database")
        except Exception as e:
            print(f"Error saving achievements to database: {e}")
    
    # Cache achievements to file for persistence between sessions
    try:
        with open(f"achievements_{user_id}.json", "w") as f:
            json.dump(user_achievements, f)
    except Exception as e:
        print(f"Error caching achievements: {e}")
    
    # Show notifications for new achievements
    if newly_unlocked:
        print(f"[Achievements] Showing notifications for {len(newly_unlocked)} new achievements")
        show_achievement_notification(page, newly_unlocked, user_achievements)
    
    return bool(newly_unlocked)

def load_cached_achievements(user_id, page):
    """Load achievements from database or cache file"""
    # First try to get from database
    try:
        from mainmenu import connect_to_mongoDB
        usercol = connect_to_mongoDB()
        user_data = usercol.find_one({"user_id": user_id})
        
        if user_data and "achievements" in user_data and user_data["achievements"]:
            # Use achievements from database
            user_achievements = user_data["achievements"]
            page.session.set("user_achievements", user_achievements)
            print(f"[DEBUG] Loaded {len(user_achievements)} achievements from database")
            return True
    except Exception as e:
        print(f"Error loading achievements from database: {e}")
    
    # Fall back to file cache if database fails
    try:
        if os.path.exists(f"achievements_{user_id}.json"):
            with open(f"achievements_{user_id}.json", "r") as f:
                user_achievements = json.load(f)
                page.session.set("user_achievements", user_achievements)
                print(f"[DEBUG] Loaded {len(user_achievements)} achievements from file cache")
                return True
    except Exception as e:
        print(f"Error loading cached achievements from file: {e}")
        
    return False

def show_achievement_notification(page, achievement_ids, user_achievements):
    """Show notification for newly unlocked achievements"""
    for achievement_id in achievement_ids:
        achievement = user_achievements.get(achievement_id, {})
        
        def close_dialog(e):
            page.dialog.open = False
            page.update()

        achievement_dialog = ft.AlertDialog(
            title=ft.Text("Achievement Unlocked! 🏆", weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Icon(name=getattr(ft.icons, achievement.get("icon", "STAR")), size=60, color="#FFD700"),
                ft.Text(achievement.get("name", "Unknown"), weight=ft.FontWeight.BOLD, size=20),
                ft.Text(achievement.get("description", ""), size=16)
            ], tight=True, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton("AWESOME!", on_click=close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER
        )
        
        # Show the dialog
        page.dialog = achievement_dialog
        page.dialog.open = True
        page.update()
        
        # Wait a bit before showing the next achievement
        time.sleep(0.5)