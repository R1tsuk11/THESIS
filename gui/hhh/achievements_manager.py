import flet as ft
from datetime import datetime
import time
import json
import os

# Achievement definitions
ACHIEVEMENTS = {
    "first_lesson": {
        "id": "first_lesson",
        "name": "First Steps",
        "description": "Complete your first lesson",
        "icon": "SCHOOL",
        "requirement": 1,
        "type": "lesson_completion"
    },
    "lesson_master": {
        "id": "lesson_master",
        "name": "Lesson Master",
        "description": "Complete 5 lessons",
        "icon": "WORKSPACE_PREMIUM",
        "requirement": 5,
        "type": "lesson_completion"
    },
    "module_complete": {
        "id": "module_complete",
        "name": "Module Champion",
        "description": "Complete your first module",
        "icon": "MILITARY_TECH",
        "requirement": 1,
        "type": "module_completion"
    },
    "vocabulary_beginner": {
        "id": "vocabulary_beginner",
        "name": "Word Collector",
        "description": "Learn 10 vocabulary words",
        "icon": "MENU_BOOK",
        "requirement": 10,
        "type": "vocabulary"
    },
    "vocabulary_intermediate": {
        "id": "vocabulary_intermediate",
        "name": "Vocabulary Builder",
        "description": "Learn 25 vocabulary words",
        "icon": "AUTO_STORIES",
        "requirement": 25,
        "type": "vocabulary"
    },
    "perfect_score": {
        "id": "perfect_score",
        "name": "Perfect Scholar",
        "description": "Get 100% on a lesson",
        "icon": "GRADE",
        "requirement": 100,
        "type": "score"
    },
    "first_review": {
        "id": "first_review",
        "name": "Review Champion",
        "description": "Complete your first daily review",
        "icon": "REPEAT",
        "requirement": 1,
        "type": "review"
    },
    "fast_learner": {
        "id": "fast_learner",
        "name": "Quick Learner",
        "description": "Complete a lesson in under 60 seconds",
        "icon": "TIMER",
        "requirement": 60,
        "type": "time"
    }
}

def check_and_unlock_achievements(user_id, page=None):
    """Check and unlock achievements based on session data"""
    if page is None:
        print("Page object is required for session-based achievements")
        return False
        
    # Get user achievements from session or initialize them
    user_achievements = page.session.get("user_achievements")
    if not user_achievements:
        print("Initializing user achievements in session")
        user_achievements = {
            achievement_id: {
                "id": achievement["id"],
                "name": achievement["name"],
                "description": achievement["description"],
                "icon": achievement["icon"],
                "completed": False,
                "date_earned": None
            }
            for achievement_id, achievement in ACHIEVEMENTS.items()
        }
    
    # Get user data from session - fix all these calls to remove default values
    modules = page.session.get("modules")
    if modules is None:
        modules = []
    
    user_library = page.session.get("user_library")
    if user_library is None:
        user_library = []
    
    reviews_completed = page.session.get("reviews_completed")
    if reviews_completed is None:
        reviews_completed = 0
    
    # Track newly unlocked achievements
    newly_unlocked = []
    
    # Count completed lessons and modules
    completed_lessons = 0
    completed_modules = 0
    
    for module in modules:
        module_completed = True
        for level in getattr(module, "levels", []):
            if getattr(level, "completed", False):
                completed_lessons += 1
            else:
                module_completed = False
        
        if module_completed:
            completed_modules += 1
    
    print(f"[Achievements] Found {completed_lessons} completed lessons, {completed_modules} completed modules")
    
    # Count vocabulary words
    vocabulary_count = len(user_library)
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
                    grade_percentage = getattr(level, "grade_percentage", 0)
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