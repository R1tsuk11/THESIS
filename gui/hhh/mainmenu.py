import flet as ft
import pymongo
from pymongo.errors import ConfigurationError
import sys
import json
import os
from datetime import datetime, timedelta
from supermemo_engine import prepare_daily_review
import time
import threading
from supermemo_engine import mark_vocabulary_reviewed
from achievements_manager import check_and_unlock_achievements
import numpy as np

uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

# Constants for usage tracking
IDLE_THRESHOLD = 120  # 2 minutes in seconds
SAVE_INTERVAL = 300   # Save usage data every 5 minutes

# Global variables for tracking
user_active = True
usage_time_seconds = 0
idle_seconds = 0
last_save_time = 0
session_start_time = None

class NumpyEncoder(json.JSONEncoder):
    """Custom encoder for numpy data types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, '__dict__'):
            return {k: self.default(v) for k, v in obj.__dict__.items()}
        return super(NumpyEncoder, self).default(obj)

def get_session_library(user_id=None):
    """Get vocabulary library from session or temp file."""
    try:
        # First try temp_library.json
        if os.path.exists("temp_library.json"):
            with open("temp_library.json", "r") as f:
                return json.load(f)
        
        # Otherwise look in the database
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": int(user_id)})
        if user and "library" in user:
            return user["library"]
    except Exception as e:
        print(f"[ERROR] Failed to get session library: {e}")
    return []

def sync_user_progress(page, user_id):
    """Synchronize user progress data between session, objects, and database"""
    try:
        # Get current session data
        user_library = page.session.get("user_library") or []
        modules = page.session.get("modules") or []
        
        # ENHANCED: If modules data from session is incomplete, load directly from database
        if not modules or not any(hasattr(module, 'levels') for module in modules):
            print("[Progress] Modules data incomplete in session, loading from database")
            try:
                # Connect to database
                arami = pymongo.MongoClient(uri)["arami"]
                user_col = arami["users"]
                
                # Get user document
                user_doc = user_col.find_one({"user_id": int(user_id)})
                if user_doc and "modules" in user_doc:
                    # Load modules directly from database
                    from mainmenu import Module
                    modules = [Module(m) for m in user_doc["modules"]]
                    page.session.set("modules", modules)
            except Exception as e:
                print(f"[Error] Failed to load modules from database: {e}")
        
        # IMPROVED: Count completed lessons with better detection
        lessons_completed = 0
        for module in modules:
            for level in getattr(module, "levels", []):
                # Check all possible ways a level might be marked as completed
                level_completed = False
                
                # If level is a dictionary
                if isinstance(level, dict):
                    level_completed = level.get("completed", False)
                # If level is an object with completed attribute
                elif hasattr(level, "completed"):
                    level_completed = level.completed
                # If level has grade_percentage that indicates completion
                elif hasattr(level, "grade_percentage") and getattr(level, "grade_percentage", 0) > 0:
                    level_completed = True
                    
                if level_completed:
                    lessons_completed += 1
                    print(f"[DEBUG] Found completed level: {getattr(level, 'lesson_id', 'unknown')}")
        
        # Debug output to verify lesson count
        print(f"[Progress] Found {lessons_completed} completed lessons")
        
        # Get vocabulary count (case-insensitive unique words)
        unique_words = set(word.lower() for word in user_library if word)
        words_learned = len(unique_words)
        
        # Calculate progress percentage based on lessons completed
        # Find total lessons count
        total_lessons = 0
        for module in modules:
            if hasattr(module, 'levels'):
                total_lessons += len(module.levels)
                
        # Avoid division by zero
        progress_percentage = 0
        if total_lessons > 0:
            progress_percentage = int((lessons_completed / total_lessons) * 100)
            print(f"[Progress] Calculated: {lessons_completed}/{total_lessons} = {progress_percentage}%")
            
        # Update achievement_data in session with progress percentage
        achievement_data = page.session.get("achievement_data") or {}
        achievement_data.update({
            "lessons_completed": lessons_completed,
            "words_learned": words_learned,
            "progress_percentage": progress_percentage  # Add this line!
        })
        page.session.set("achievement_data", achievement_data)
        
        # Save to database
        usercol = connect_to_mongoDB()
        usercol.update_one(
            {"user_id": int(user_id)},
            {"$set": {
                "library": list(user_library),
                "lessons_completed": lessons_completed,
                "words_learned": words_learned
            }}
        )
        print(f"[Database] Updated user profile with {words_learned} words and {lessons_completed} lessons")
        
        return True
    except Exception as e:
        print(f"[Error] Failed to sync user progress: {e}")
        return False

def calculate_completion_percentage(user):
    """Calculate accurate completion percentage"""
    if not hasattr(user, 'modules') or not user.modules:
        return 0
        
    total_lessons = 0
    completed_lessons = 0
    
    # Count all lessons across all modules with better completion detection
    for module in user.modules:
        if hasattr(module, 'levels'):
            for level in module.levels:
                total_lessons += 1
                
                # Check all possible ways a level might be marked as completed
                level_completed = False
                
                if hasattr(level, "completed"):
                    level_completed = level.completed
                elif isinstance(level, dict):
                    level_completed = level.get("completed", False)
                elif hasattr(level, "grade_percentage") and getattr(level, "grade_percentage", 0) > 0:
                    level_completed = True
                    
                if level_completed:
                    completed_lessons += 1
                    print(f"[DEBUG] Counting completed level: {getattr(level, 'lesson_id', 'unknown')}")
    
    # Print detailed breakdown
    print(f"[Progress] Detailed calculation: {completed_lessons} completed of {total_lessons} total lessons")
    
    # Calculate percentage with proper float division and bounds
    if total_lessons > 0:
        percentage = int((float(completed_lessons) / float(total_lessons)) * 100)
        percentage = min(100, max(0, percentage))  # Cap between 0-100%
        return percentage
    return 0

def debug_achievement_progress(page):
    """Print debugging info about user's achievement progress"""
    user_id = page.session.get("user_id")
    if not user_id:
        return
        
    user = page.session.get("user")
    if not user:
        return
        
    print("\n=== ACHIEVEMENT DEBUG INFO ===")
    
    # Count completed lessons
    lessons_completed = 0
    modules_completed = 0
    
    for module in user.modules:
        module_complete = True
        level_count = 0
        completed_level_count = 0
        
        for level in module.levels:
            level_count += 1
            if getattr(level, "completed", False):
                completed_level_count += 1
                lessons_completed += 1
            else:
                module_complete = False
                
        print(f"Module {module.id}: {completed_level_count}/{level_count} levels completed")
        
        if module_complete:
            modules_completed += 1
    
    print(f"Total completed lessons: {lessons_completed}")
    print(f"Total completed modules: {modules_completed}")
    print(f"Vocabulary count: {len(user.library)}")
    print("============================\n")

def calculate_completion_percentage(user):
    """Calculate the correct completion percentage based on completed lessons"""
    total_lessons = 0
    completed_lessons = 0
    
    if hasattr(user, 'modules') and user.modules:
        for module in user.modules:
            if hasattr(module, 'levels') and module.levels:
                for level in module.levels:
                    total_lessons += 1
                    if hasattr(level, 'completed') and level.completed:
                        completed_lessons += 1
    
    if total_lessons > 0:
        return int((completed_lessons / total_lessons) * 100)
    return 0

def debug_achievement_progress(page):
    """Print debugging info about user's achievement progress"""
    user_id = page.session.get("user_id")
    if not user_id:
        return
        
    user = page.session.get("user")
    if not user:
        return
        
    print("\n=== ACHIEVEMENT DEBUG INFO ===")
    
    # Count completed lessons
    lessons_completed = 0
    modules_completed = 0
    
    for module in user.modules:
        module_complete = True
        level_count = 0
        completed_level_count = 0
        
        for level in module.levels:
            level_count += 1
            if getattr(level, "completed", False):
                completed_level_count += 1
                lessons_completed += 1
            else:
                module_complete = False
                
        print(f"Module {module.id}: {completed_level_count}/{level_count} levels completed")
        
        if module_complete:
            modules_completed += 1
    
    print(f"Total completed lessons: {lessons_completed}")
    print(f"Total completed modules: {modules_completed}")
    print(f"Vocabulary count: {len(user.library)}")
    print("============================\n")

def start_usage_timer(page):
    """Start a background thread to track usage time."""
    global session_start_time
    session_start_time = time.time()
    
    def timer_loop():
        global usage_time_seconds, idle_seconds, user_active, last_save_time
        while True:
            time.sleep(1)  # Update every second
            
            if user_active:
                # Increment usage time when user is active
                usage_time_seconds += 1
                idle_seconds += 1
                
                # Check if user has been idle too long
                if idle_seconds >= IDLE_THRESHOLD:
                    user_active = False
                    print(f"[Usage] User idle for {IDLE_THRESHOLD} seconds, pausing timer")
                    # Update UI to show paused state
                    if hasattr(page, 'usage_indicator') and page.usage_indicator:
                        page.usage_indicator.bgcolor = "#FF9800"  # Orange for paused
                        page.usage_indicator.tooltip = "Usage tracking paused - you're inactive"
                        page.update()
                
                # Periodically save usage data while active
                if usage_time_seconds - last_save_time >= SAVE_INTERVAL:
                    save_usage_data(page)
                    last_save_time = usage_time_seconds
            
            else:
                # Just wait when inactive
                time.sleep(1)
    
    # Start background thread
    tracking_thread = threading.Thread(target=timer_loop, daemon=True)
    tracking_thread.start()
    
    # Add activity event listeners to the page
    page.on_keyboard_event = reset_idle_timer
    page.on_mouse_event = reset_idle_timer
    
    # Create usage indicator
    page.usage_indicator = ft.Container(
        width=12,
        height=12,
        border_radius=6,
        bgcolor="#4CAF50",  # Green for active
        tooltip="Usage tracking active",
        margin=ft.margin.only(right=5)
    )
    
    # Add indicator to page appbar if it exists
    if hasattr(page, 'appbar') and page.appbar:
        if not hasattr(page.appbar, 'actions'):
            page.appbar.actions = []
        page.appbar.actions.insert(0, page.usage_indicator)
    
    print("[Usage] Usage tracking started")
    page.update()

def reset_idle_timer(e=None):
    """Reset the idle timer when user activity is detected."""
    global user_active, idle_seconds
    
    # If user was inactive and is now active again
    if not user_active:
        user_active = True
        print("[Usage] User activity detected, resuming timer")
        
        # Update UI to show active state
        if hasattr(e, 'page') and hasattr(e.page, 'usage_indicator') and e.page.usage_indicator:
            e.page.usage_indicator.bgcolor = "#4CAF50"  # Green for active
            e.page.usage_indicator.tooltip = "Usage tracking active"
            e.page.update()
    
    # Reset idle counter
    idle_seconds = 0

def save_usage_data(page):
    """Save usage data to the database."""
    global usage_time_seconds
    
    user_id = page.session.get("user_id")
    if not user_id:
        print("[Usage] Cannot save usage data - no user ID")
        return
    
    try:
        # Get database connection
        usercol = connect_to_mongoDB()
        
        # Get existing usage data
        user_data = usercol.find_one({"user_id": user_id})
        if not user_data:
            print(f"[Usage] User {user_id} not found in database")
            return
            
        # Update total usage time
        total_usage = user_data.get("total_usage_seconds", 0) + usage_time_seconds
        
        # Create usage history record
        today = datetime.now().strftime("%Y-%m-%d")
        usage_history = user_data.get("usage_history", {})
        
        if today in usage_history:
            usage_history[today] += usage_time_seconds
        else:
            usage_history[today] = usage_time_seconds
            
        # Save to database
        usercol.update_one(
            {"user_id": user_id},
            {"$set": {
                "total_usage_seconds": total_usage,
                "usage_history": usage_history,
                "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }}
        )
        
        print(f"[Usage] Saved usage data: {usage_time_seconds} seconds")
        
        # Reset session counter after saving
        usage_time_seconds = 0
        
    except Exception as e:
        print(f"[Usage] Error saving usage data: {e}")

def format_usage_time(seconds):
    """Format seconds into a readable time string."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def show_usage_stats(page):
    """Show a dialog with usage statistics."""
    global usage_time_seconds, session_start_time
    
    # Calculate current session time
    session_duration = int(time.time() - session_start_time)
    
    # Get user data
    user_id = page.session.get("user_id")
    if not user_id:
        return
        
    usercol = connect_to_mongoDB()
    user_data = usercol.find_one({"user_id": user_id})
    
    if not user_data:
        return
        
    total_usage = user_data.get("total_usage_seconds", 0) + usage_time_seconds
    usage_history = user_data.get("usage_history", {})
    
    # Calculate stats
    today = datetime.now().strftime("%Y-%m-%d")
    today_usage = usage_history.get(today, 0) + usage_time_seconds
    
    # Get usage for the last 7 days
    last_7_days = {}
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        if date in usage_history:
            last_7_days[date] = usage_history[date]
    
    # Create content for dialog
    content = ft.Column([
        ft.Text("Usage Statistics", weight=ft.FontWeight.BOLD, size=20),
        ft.Divider(),
        ft.Text(f"Current session: {format_usage_time(session_duration)}"),
        ft.Text(f"Today's usage: {format_usage_time(today_usage)}"),
        ft.Text(f"Total usage: {format_usage_time(total_usage)}"),
        ft.Divider(),
        ft.Text("Last 7 days:", weight=ft.FontWeight.BOLD)
    ])
    
    # Add last 7 days stats
    for date, time_used in sorted(last_7_days.items(), reverse=True):
        content.controls.append(
            ft.Text(f"{date}: {format_usage_time(time_used)}")
        )
    
    # Show dialog
    dialog = ft.AlertDialog(
        content=content,
        actions=[
            ft.TextButton("Close", on_click=lambda e: page.close(dialog))
        ]
    )
    
    page.open(dialog)

def is_first_login_today(last_login=None):
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"Today's date: {today_str}, Last login date: {last_login}")
    return today_str != last_login

def update_last_login_date(user):
    today_str = datetime.now().strftime("%Y-%m-%d")
    usercol = connect_to_mongoDB()
    usercol.update_one({"user_id": user.user_id}, {"$set": {"last_login_date": today_str}})

def on_daily_review_complete(e, page, user):
    """Handle completion of daily review - simplified version without streaks"""
    # Get user_id from context or page
    user_id = user.user_id if user else page.session.get("user_id")
    
    if not user_id:
        print("[ERROR] Cannot update proficiency - missing user_id")
        return
    
    try:
        # Connect to MongoDB
        import pymongo
        uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"
        arami = pymongo.MongoClient(uri)["arami"]
        users_col = arami["users"]
        
        # Get current user data - FORCE integer conversion
        user_data = users_col.find_one({"user_id": int(user_id)})
        if not user_data:
            print(f"[ERROR] User {user_id} not found")
            return
        
        # Get current reviews_completed count and increment it
        reviews_completed = user_data.get("reviews_completed", 0) + 1
        
        # Update review data
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Update critical dates to prevent repeat prompts
        users_col.update_one(
            {"user_id": int(user_id)},
            {"$set": {
                "reviews_completed": reviews_completed,
                "last_review_date": today,
                "last_login_date": today  # This prevents infinite prompts
            }}
        )
        
        print(f"[Review] Updated last_login_date to {today} to prevent repeat prompts")
        print(f"[Review] Updated review data - completed: {reviews_completed}")
        print(f"[SuperMemo] User now has completed {reviews_completed} reviews")
        
    except Exception as e:
        print(f"[ERROR] Failed to update review data: {str(e)}")
        import traceback
        traceback.print_exc()
    
def show_daily_review_overlay(page):
    overlay = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, color="#0078D7", size=60),
                    padding=ft.padding.only(top=40)
                ),
                ft.Container(
                    content=ft.Text(
                        "Daily Review Required!",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color="#0078D7",
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=ft.padding.only(bottom=5)
                ),
                ft.Container(
                    content=ft.Text(
                        "Please complete your daily review before proceeding.",
                        size=16,
                        color="#424242",
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=ft.padding.only(bottom=20)
                ),
                ft.ElevatedButton(
                    "Start Review",
                    width=200,
                    style=ft.ButtonStyle(
                        bgcolor={"": "#0078D7"},
                        color={"": "#FFFFFF"},
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    on_click=lambda e: (
                        page.overlay.clear(),
                        page.update(),
                        page.go("/daily-review")
                    )
                )
            ],
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        ),
        alignment=ft.alignment.center,
        bgcolor="#F5F5F5",
        width=page.width,
        height=page.height,
        border_radius=0,
        opacity=0.98,
        animate_opacity=200,
        padding=40
    )
    
    # Add the overlay to the page
    page.overlay.append(overlay)
    page.update()
    
def safe_float(value, default=0.0):
    """Convert value to float, handling None values and conversion errors."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

# Then update module_to_dict within cache_modules_to_temp
def cache_modules_to_temp(modules):
    def module_to_dict(module):
        return {
            "user_id": module.user_id,
            "id": module.id,
            "desc": module.desc,
            "eng_name": module.eng_name,
            "waray_name": module.waray_name,
            "completed": getattr(module, "completed", False),
            "levels": [
                {
                    "id": level.lesson_id,
                    "module_id": level.module_name,
                    "questions_answers": [q.__dict__ if hasattr(q, '__dict__') else q for q in level.questions_answers],
                    "completed": getattr(level, "completed", False),
                    "grade_percentage": safe_float(getattr(level, "grade_percentage", 0)),
                    "pass_threshold": safe_float(getattr(level, "pass_threshold", 0)),
                    "completion_time": safe_float(getattr(level, "completion_time", 0)),
                }
                for level in module.levels
            ],
            "chapter_test": {
                "module_id": module.chapter_test.module_id,
                "questions_answers": module.chapter_test.questions_answers,
                "completed": module.chapter_test.completed,
                "pass_threshold": safe_float(module.chapter_test.pass_threshold)
            }
        }
    
    with open("temp_modules.json", "w") as f:
        # Use the custom encoder for JSON serialization
        json.dump([module_to_dict(m) for m in modules], f, cls=NumpyEncoder)

def cache_library_to_temp(library):
    with open("temp_library.json", "w") as f:
        json.dump(library, f)

def clear_all_temp_files(user_id=None):
    """Clear all temporary files including BKT files"""
    import os
    import glob
    
    # Standard temp files
    temp_files = [
        "temp_library.json",
        "temp_modules.json",
        "temp_chaptertest_data.json",
        "temp_bkt_data.json",
        "temp_prof_history.json",
        "lstm_counter.json",
        "bkt_predictions.json",
        "bkt_input.csv",
        "temp_lstm_input.json",
    ]
    
    # Add user-specific files
    if user_id:
        user_specific_files = [
            f"lesson_bkt_predictions_{user_id}.json",
            f"lesson_bkt_predictions_{user_id}_processed.json",
            f"temp_lesson_bkt_data_{user_id}.json",
            f"bkt_sequence_{user_id}",
            f"temp_state_{user_id}.json",
            f"lesson_session_{user_id}.json",
            f"achievements_{user_id}.json",
        ]
        temp_files.extend(user_specific_files)
    
    # Also check for any remaining lesson files without user ID
    temp_files.extend([
        "lesson_bkt_predictions.json",
        "temp_lesson_bkt_data.json",
        "bkt_sequence",
        "temp_state.json",
        "lesson_session.json",
    ])
    
    # Use glob patterns to catch any missed files
    pattern_files = []
    if user_id:
        patterns = [
            f"*_{user_id}.json",
            f"*_{user_id}",
            f"lesson_*_{user_id}*",
            f"bkt_*_{user_id}*",
            f"temp_*_{user_id}*",
            f"achievements_{user_id}.json",
        ]
        
        for pattern in patterns:
            pattern_files.extend(glob.glob(pattern))
    
    # Combine all files and remove duplicates
    all_files = list(set(temp_files + pattern_files))
    
    # Remove all files
    removed_count = 0
    for file in all_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"[CLEANUP] Removed temp file: {file}")
                removed_count += 1
            except Exception as e:
                print(f"[CLEANUP] Error removing {file}: {e}")
    
    print(f"[CLEANUP] Total files removed: {removed_count}")
    
    # Also clean up any orphaned BKT files
    try:
        cleanup_orphaned_bkt_files()
    except Exception as e:
        print(f"[CLEANUP] Error cleaning orphaned BKT files: {e}")

def cleanup_orphaned_bkt_files():
    """Clean up any orphaned BKT-related files"""
    import os
    import glob
    
    # Patterns for BKT files that might be left behind
    bkt_patterns = [
        "lesson_bkt_predictions_*.json",
        "lesson_bkt_predictions_*_processed.json",
        "temp_lesson_bkt_data_*.json",
        "bkt_sequence_*",
        "temp_state_*.json",
        "lesson_session_*.json",
        "achievements_*.json",
    ]
    
    for pattern in bkt_patterns:
        files = glob.glob(pattern)
        for file in files:
            try:
                os.remove(file)
                print(f"[CLEANUP] Removed orphaned BKT file: {file}")
            except Exception as e:
                print(f"[CLEANUP] Error removing orphaned file {file}: {e}")

def connect_to_mongoDB():
    try:
        arami = pymongo.MongoClient(uri)["arami"]
        usercol = arami["users"]
        return usercol
    except ConfigurationError as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit("Terminating the program due to MongoDB connection failure.")

class Question:
    def __init__(self, question_data):
        self.question = question_data.get("question")
        self.answer = question_data.get("answer")
        self.vocabulary = question_data.get("vocabulary")
        self.type = question_data.get("type")
        self.choices = question_data.get("choices")
        self.correct_answer = question_data.get("correct_answer")
        self.difficulty = question_data.get("difficulty")
        self.response_time = question_data.get("response_time")
        self.word_to_translate = question_data.get("word_to_translate")
        self.image = question_data.get("image", None) 
        self.audio_file = question_data.get("audio_file", None)  # Optional audio field

    def to_dict(self):
        return {
            "question": self.question,
            "answer": self.answer,
            "vocabulary": self.vocabulary,
            "type": self.type,
            "choices": self.choices,
            "correct_answer": self.correct_answer,
            "difficulty": self.difficulty,
            "response_time": self.response_time,
            "word_to_translate": self.word_to_translate,
            "image": self.image,
            "audio_file": self.audio_file  # Include audio file if it exists
        }

class Level:  # Level class
    def __init__(self, level):
        self.module_name = level["module_name"]
        self.lesson_id = level["lesson_id"]
        self.completed = level["completed"]
        self.grade_percentage = level["grade_percentage"]
        self.completion_time = level["completion_time"]
        self.pass_threshold = level["pass_threshold"]
        self.questions_answers = self.load_questions(level)

    def to_dict(self):
        return {
            "lesson_id": self.lesson_id,
            "module_name": self.module_name,
            "questions_answers": [
                q.to_dict() if hasattr(q, 'to_dict') else {
                    "question": str(q)  # or however you want to serialize the question
                }
                for q in self.questions_answers
            ],
            "completed": self.completed,
            "grade_percentage": self.grade_percentage,
            "completion_time": self.completion_time,
            "pass_threshold": self.pass_threshold
        }

    def load_questions(self, level):
        questions = []
        for question_data in level["questions_answers"]:
            questions.append(Question(question_data))
        return questions

class Achievements: # Achievements class
    def __init__(self, achievement): # Initialize achievements
        self.id = achievement["id"]
        self.name = achievement["name"]
        self.description = achievement["description"]
        self.icon = achievement["icon"]
        self.completed = achievement["completed"]

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "completed": self.completed
        }

class ChapterTest: # Chapter Test class
    def __init__(self, chapter_test):
        self.module_id = chapter_test["module_id"]
        self.questions_answers = chapter_test["questions_answers"]
        self.completed = chapter_test["completed"]
        self.pass_threshold = chapter_test["pass_threshold"]

class Module:  # Module class
    def __init__(self, module):
        self.id = module["id"]
        self.waray_name = module["waray_name"]
        self.eng_name = module["eng_name"]
        self.desc = module["desc"]
        self.user_id = module["user_id"]
        self.completed = module["completed"]
        self.levels = self.load_levels(module["levels"])
        self.chapter_test = ChapterTest(module["chapter_test"])

    def to_dict(self):
        return {
            "id": self.id,
            "waray_name": self.waray_name,
            "eng_name": self.eng_name,
            "desc": self.desc,
            "user_id": self.user_id,
            "completed": self.completed,
            "chapter_test": {
                "module_id": self.chapter_test.module_id,
                "questions_answers": self.chapter_test.questions_answers,
                "completed": self.chapter_test.completed,
                "pass_threshold": self.chapter_test.pass_threshold
            },
            "levels": [level.to_dict() for level in self.levels]
        }

    def load_levels(self, levels):
        lessons = []
        for level_data in levels:
            level = Level(level_data)
            lessons.append(level)
        return lessons

class User:  # User class
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.user_name = None
        self.proficiency = 0
        self.password = None
        self.library = []
        self.questions_incorrect = {}
        self.questions_correct = {}
        self.chapter_test_records = {}
        self.achievements = {}
        self.modules = {}
        self.time = 0
        self.email = None
        self.bkt_data = {}
        self.completion_percentage = 0
        self.proficiency_history = []

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "email": self.email,
            "password": self.password,
            "proficiency": self.proficiency,
            "library": self.library,
            "questions_correct": {
                key: val.to_dict() if not isinstance(val, dict) else val
                for key, val in self.questions_correct.items()
            },
            "questions_incorrect": {
                key: val.to_dict() if not isinstance(val, dict) else val
                for key, val in self.questions_incorrect.items()
            },
            "chapter_test_records": {
                module_id: {
                    "grade_percentage": data["grade_percentage"],
                    "total_time_spent": data["total_time_spent"],
                    "questions_correct": {
                        q: qdata.to_dict() if hasattr(qdata, "to_dict") else qdata
                        for q, qdata in data.get("questions_correct", {}).items()
                    },
                    "questions_incorrect": {
                        q: qdata.to_dict() if hasattr(qdata, "to_dict") else qdata
                        for q, qdata in data.get("questions_incorrect", {}).items()
                    }
                }
                for module_id, data in self.chapter_test_records.items()
            },
            "achievements": {
                key: val if isinstance(val, dict) else val.to_dict()
                for key, val in self.achievements.items()
            },
            "modules": [m.to_dict() for m in self.modules],
            "time": self.time,
            "bkt_data": self.bkt_data,
            "completion_percentage": self.completion_percentage,
            "proficiency_history": self.proficiency_history
        }

    def get_user(self, user_id):
        """Retrieves user data from the database."""
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": user_id})
        if user:
            self.user_id = user["user_id"]
            self.user_name = user["user_name"]
            self.email = user["email"]
            self.proficiency = user["proficiency"]
            self.password = user["password"]
            self.library = user["library"]
            self.questions_incorrect = user["questions_incorrect"]
            self.questions_correct = user["questions_correct"]
            self.chapter_test_records = user["chapter_test_records"]
            self.achievements = user["achievements"]
            self.modules = user["modules"]
            self.time = user["time"]
            self.bkt_data = user["bkt_data"]
            self.completion_percentage = user["completion_percentage"]
            self.proficiency_history = user["proficiency_history"]
        else:
            print("User not found in database.")
            return None
        
    def load_achievements(self, achievement_data):
        """Converts raw achievement data from the database into class instances."""
        loaded_achievements = {}

        for key, value in achievement_data.items():
            # Check if value is a dictionary and has necessary fields
            if isinstance(value, dict) and all(field in value for field in ["id", "name", "description", "icon", "completed"]):
                achievement_instance = Achievements(value)
                loaded_achievements[key] = achievement_instance
            else:
                print(f"Skipping invalid achievement format for {key}: {value}")

        self.achievements = loaded_achievements

    def sync_achievements_from_session(self, page):
        """Sync achievements from session to user object before database save"""
        session_achievements = page.session.get("user_achievements")
        if session_achievements:
            # Update the user's achievements with session data
            print(f"[DEBUG] Syncing {len(session_achievements)} achievements from session to user")
            self.achievements = session_achievements
            return True
        return False

    def load_data(self, user_id, page):
        """Loads user data from the session or database."""
        updated_user = page.session.get("user")

        if updated_user and updated_user.user_id == user_id:
            print("Loaded updated user from session.")
            self.__dict__.update(updated_user.__dict__)

            correct_answers = page.session.get("correct_answers")
            incorrect_answers = page.session.get("incorrect_answers")
            if correct_answers or incorrect_answers:
                # Append new correct answers to the existing ones
                for k, v in correct_answers.items():
                    if k not in self.questions_correct:
                        self.questions_correct[k] = Question(v) if isinstance(v, dict) else v

                # Append new incorrect answers to the existing ones
                for k, v in incorrect_answers.items():
                    if k not in self.questions_incorrect:
                        self.questions_incorrect[k] = Question(v) if isinstance(v, dict) else v

            if os.path.exists("temp_chaptertest_data.json"):
                with open("temp_chaptertest_data.json", "r") as f:
                    chapter_test_data = json.load(f)

                    # Convert each question dict to Question object
                    raw_questions = chapter_test_data.get("questions_answers", {})
                    converted_questions = {
                        qtext: Question(qdata) for qtext, qdata in raw_questions.items()
                    }

                    module_id = str(chapter_test_data["module_id"])

                    # Replace the raw dict with object instances
                    chapter_test_data["questions_answers"] = converted_questions

                    # Debug: print a sample entry to verify conversion
                    print("\n[DEBUG] Converted Questions for Module ID", module_id)
                    for qtext, obj in converted_questions.items():
                        print(f"- {qtext}: {type(obj)}")

                    # Save it in user records
                    self.chapter_test_records[module_id] = chapter_test_data

            if self.user_id:
                from supermemo_engine import merge_duplicate_vocab_entries
                merge_duplicate_vocab_entries(self.user_id)
                
            return self
        else:
            # Fallback to DB
            self.get_user(user_id)

            # Make sure modules and achievements are properly restored
            self.modules = [Module(m) if isinstance(m, dict) else m for m in self.modules]
            self.achievements = {k: Achievements(v) if isinstance(v, dict) else v for k, v in self.achievements.items()}

            page.session.set("user", self)  # Cache it for later updates
            page.open(ft.SnackBar(ft.Text("Successfully loaded data!"), bgcolor="#4CAF50"))

            if self.user_id:
                from supermemo_engine import merge_duplicate_vocab_entries
                merge_duplicate_vocab_entries(self.user_id)

            return self

    def save_library(self):
        if os.path.exists("temp_library.json"):
            with open("temp_library.json", "r") as f:
                self.library = json.load(f)
        else:
            print("No temp library cache found.")

    def save_bkt_data(self):
        if os.path.exists("temp_bkt_data.json"):
            with open("temp_bkt_data.json", "r") as f:
                self.bkt_data = json.load(f)
        else:
            print("No temp library cache found.")

    def save_prof_history(self):
        """Save proficiency history from new folder structure"""
        # Check for user-specific history file first
        user_history_path = f"lstm_history/temp_prof_history_{self.user_id}.json"
        if os.path.exists(user_history_path):
            try:
                with open(user_history_path, "r") as f:
                    history = json.load(f)
                    self.proficiency_history = history
                    
                    # Extract most recent proficiency
                    if history and len(history) > 0:
                        last_entry = history[-1]
                        
                        # Convert to float if possible
                        if isinstance(last_entry, (int, float)):
                            self.proficiency = float(last_entry)
                        elif isinstance(last_entry, dict) and "proficiency" in last_entry:
                            self.proficiency = float(last_entry["proficiency"])
                        
                        # Scale to percentage if it's a decimal
                        if 0 < self.proficiency < 1:
                            self.proficiency = self.proficiency * 100
                    
                    print(f"[Proficiency] Loaded history from {user_history_path}, current: {self.proficiency:.2f}%")
                    return
            except Exception as e:
                print(f"[Proficiency] Error loading from {user_history_path}: {e}")
        
        # Fall back to legacy file
        if os.path.exists("temp_prof_history.json"):
            with open("temp_prof_history.json", "r") as f:
                self.proficiency_history = json.load(f)
                
                # Get the last proficiency value
                if self.proficiency_history and len(self.proficiency_history) > 0:
                    self.proficiency = float(self.proficiency_history[-1])
                    if 0 < self.proficiency < 1:
                        self.proficiency *= 100
                
                print(f"[Proficiency] Loaded from legacy file, current: {self.proficiency:.2f}%")
        else:
            print("[Proficiency] No proficiency history found.")

    def save_lstm_counter(self):
        """Save LSTM counter from new folder structure"""
        # Check for user-specific counter file first
        user_counter_path = f"lstm_counters/lstm_counter_{self.user_id}.json"
        if os.path.exists(user_counter_path):
            try:
                with open(user_counter_path, "r") as f:
                    lstm_counter = json.load(f)
                    usercol = connect_to_mongoDB()
                    usercol.update_one(
                        {"user_id": self.user_id},
                        {"$set": {"lstm_counter": lstm_counter}}
                    )
                    print(f"[LSTM] Saved counter from {user_counter_path} to database")
                    return
            except Exception as e:
                print(f"[LSTM] Error saving counter from {user_counter_path}: {e}")
        
        # Fall back to legacy file
        if os.path.exists("lstm_counter.json"):
            with open("lstm_counter.json", "r") as f:
                lstm_counter = json.load(f)
                usercol = connect_to_mongoDB()
                usercol.update_one(
                    {"user_id": self.user_id},
                    {"$set": {"lstm_counter": lstm_counter}}
                )
                print("[LSTM] Saved counter from legacy file to database")
        else:
            print("[LSTM] No LSTM counter found.")

    def save_user(self, page):
        """Saves user data to the database."""
        self.save_library()
        self.save_bkt_data()
        self.save_prof_history()
        self.save_lstm_counter()
        
        # Add code to save LSTM mastery and proficiency to database
        lstm_proficiency = page.session.get("lstm_proficiency")
        lstm_mastery = page.session.get("lstm_mastery")
        
        if lstm_proficiency is not None or lstm_mastery is not None:
            # Safe formatting that handles None values
            prof_str = f"{lstm_proficiency:.4f}" if lstm_proficiency is not None else "None"
            mastery_str = f"{lstm_mastery:.4f}" if lstm_mastery is not None else "None"
            print(f"[LSTM] Saving mastery ({mastery_str}) and proficiency ({prof_str}) to database")
            
            # Update the user object
            if lstm_proficiency is not None:
                self.proficiency = lstm_proficiency
            
            # Also save directly to database
            usercol = connect_to_mongoDB()
            update_data = {}
            if lstm_proficiency is not None:
                update_data["proficiency"] = lstm_proficiency
                update_data["lstm_proficiency"] = lstm_proficiency
            if lstm_mastery is not None:
                update_data["lstm_mastery"] = lstm_mastery
                
            if update_data:
                usercol.update_one(
                    {"user_id": self.user_id},
                    {"$set": update_data}
                )

        # Save usage data before logout
        global usage_time_seconds
        if usage_time_seconds > 0:
            save_usage_data(page)
            
        # NEW: Sync achievements from session before saving to database
        self.sync_achievements_from_session(page)
        
        # Get achievement JSON file if it exists for this user
        achievement_file = f"achievements_{self.user_id}.json"
        if os.path.exists(achievement_file):
            try:
                with open(achievement_file, "r") as f:
                    achievements = json.load(f)
                    print(f"[Achievements] Loaded {len(achievements)} achievements from file")
                    self.achievements = achievements
            except Exception as e:
                print(f"[Achievements] Error loading from file: {e}")

        # Add this code to ensure vocabulary scheduling happens during logout
        print("[SuperMemo] Scheduling vocabulary before logout")
        from supermemo_engine import schedule_pending_vocabulary
        schedule_pending_vocabulary(self.user_id)

        print(f"[Usage] Session usage time: {format_usage_time(usage_time_seconds)}")
        
        usercol = connect_to_mongoDB()
        user_data = self.to_dict()

        result = usercol.update_one(
            {"user_id": self.user_id},
            {"$set": user_data},
            upsert=True
        )

        print("Matched:", result.matched_count,
            "Modified:", result.modified_count,
            "Upserted ID:", result.upserted_id)

        try:
            clear_all_temp_files()
        except FileNotFoundError:
            print("No temp file to clear.")

        page.open(ft.SnackBar(ft.Text("User data saved successfully!"), bgcolor="#4CAF50"))
        page.update()
        page.session.clear()
        page.go("/login")


def get_user_id(page):
        """Retrieves user_id from previous page session."""
        page.session.get("user_id")  # Get user ID from session
        if page.session.get("user_id") is None:
            print("No user ID found in session.")
            return None
        return page.session.get("user_id")

# Add this to the main_menu_page function or where sessions are initialized
def check_for_unscheduled_vocabulary(user_id):
    """Check and schedule any unscheduled vocabulary when user returns"""
    if user_id:
        from supermemo_engine import schedule_pending_vocabulary
        
        # Check if this is the first time we're scheduling today
        usercol = connect_to_mongoDB()
        user_data = usercol.find_one({"user_id": user_id})
        if user_data and "last_schedule_date" in user_data:
            last_scheduled = user_data["last_schedule_date"]
            today = datetime.now().strftime("%Y-%m-%d")
            
            if last_scheduled == today:
                print(f"[SuperMemo] Already scheduled vocabulary today ({today}), skipping")
                return False
        
        # Schedule vocabulary and update the last scheduling date
        result = schedule_pending_vocabulary(user_id)
        
        # Update the last schedule date
        if result:  # Only update if scheduling actually happened
            usercol.update_one(
                {"user_id": user_id},
                {"$set": {"last_schedule_date": datetime.now().strftime("%Y-%m-%d")}}
            )
        return result
    return False

def main_menu_page(page: ft.Page, image_urls: list):
    """Main menu page with module cards"""

    import bkt_engine
    bkt_engine.uid = page.session.get("user_id")
    print(f"[USER] Set global BKT user ID to: {bkt_engine.uid}")

    # ----- HEADER with image -----
    header_column = ft.Column(
        controls=[
            ft.Container(
                content=ft.Row([], alignment=ft.MainAxisAlignment.CENTER),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["#0066FF", "#9370DB"],
                ),
                height=70,
            ),
        ],
        spacing=0
    )
    header = ft.Container(
        content=ft.Stack(
            controls=[
                header_column,
                ft.Container(
                    content=ft.Image(
                        src=image_urls[1], width=120,
                        fit=ft.ImageFit.COVER
                    ),
                    alignment=ft.alignment.top_center,
                    margin=ft.Margin(top=20, left=0, right=0, bottom=15),
                )
            ]
        ),
    )

    # Create modules title
    modules_title = ft.Container(
        content=ft.Text(
            "Modules",
            size=15,
            color="#FFFFFF",  # White text
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        bgcolor="#397BFF", 
        width=300,
        height=45,
        border_radius=25,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, "#000000"),
            offset=ft.Offset(0, 0),
        ),
        margin=ft.Margin(top=0, left=0, right=0, bottom=10)
    )

    def on_profile_click(e):
        """Handles profile icon click event."""
        print("Profile icon clicked")
        
    def navigate_to_levels(e, user, module_id):
        """Navigates to levels page if prerequisites are met."""
        # Find the index of the selected module
        module_ids = [m.id for m in user.modules]
        try:
            idx = module_ids.index(module_id)
        except ValueError:
            page.open(ft.SnackBar(ft.Text("Module not found."), bgcolor="#FF5252"))
            return

        selected_module = user.modules[idx]

        # Check if selected module is already completed
        if getattr(selected_module, "completed", False):
            page.open(ft.SnackBar(ft.Text("This module is already completed."), bgcolor="#FFC107"))
            return

        # Check if all previous modules are completed
        if idx > 0:
            for prev_module in user.modules[:idx]:
                if not getattr(prev_module, "completed", False):
                    page.open(ft.SnackBar(ft.Text("Please complete previous modules first."), bgcolor="#FF5252"))
                    return

        # Proceed if allowed
        cache_modules_to_temp(user.modules)  # Cache modules to temp file
        cache_library_to_temp(user.library)  # Cache library to temp file
        page.session.set("modules", user.modules)
        page.session.set("module_id", module_id)
        page.go("/levels")

    # Function to create a module card
    def create_module_card(module_id, main_button_text, sub_button_text, main_color, sub_color, bg_color="#2A2A2A", is_locked=False):
        # Create the background container with image
        module_id = int(module_id) if isinstance(module_id, str) and module_id.isdigit() else module_id
        
        # Set colors and background image based on module_id
        if module_id == 1:      # KAMUSTAHAY
            bg_image = image_urls[2] 
            main_color = "#FFC124"
            sub_color = "#FFE850"
        elif module_id == 2:    # KALAKAT
            bg_image = image_urls[3]
            main_color = "#3FEA8C"
            sub_color = "#79E17F"
        elif module_id == 3:    # PAMALIT
            bg_image = image_urls[4]
            main_color = "#FFAD60"
            sub_color = "#D1D1A7"
        elif module_id == 4:     # PANGAON
            bg_image = image_urls[5]
            main_color = "#86C8CD"
            sub_color = "#6CCDB9"
        elif module_id == 5:    # SLANG
            bg_image = image_urls[6]
            main_color = "#86C8CD"
            sub_color = "#FFE850"
        else:
            bg_image = image_urls[2]
            main_color = "#86C8CD"
            sub_color = "#FFE850"

        # If module is locked, override colors with gray
        if is_locked:
            main_color = "#757575"  # Dark gray
            sub_color = "#9E9E9E"   # Medium gray
        
        # Image container without unsupported color_filter_matrix
        image_container = ft.Image(
            src=bg_image,
            width=300,
            height=150, 
            fit=ft.ImageFit.COVER,
            opacity=0.7 if is_locked else 1.0,
            error_content=ft.Container(
                width=300,
                height=150,
                bgcolor="gray" if is_locked else "orange",
                border_radius=15
            )
        )
        
        # If locked, add grayscale effect with an overlay container
        if is_locked:
            bg_container = ft.Stack([
                image_container,
                # Add gray overlay to simulate grayscale
                ft.Container(
                    width=300,
                    height=150,
                    bgcolor=ft.colors.with_opacity(0.5, "#808080"),
                    border_radius=15
                )
            ])
        else:
            bg_container = image_container
        
        # Wrap in a container for border radius
        bg_container = ft.Container(
            content=bg_container,
            border_radius=15,
            width=300,
            height=150
        )
        
        # Main content container with title and description
        content_container = ft.Container(
            content=ft.Column(
                [
                    # TITLE
                    ft.Container(
                        content=ft.Text(
                            main_button_text,
                            color="#FFFFFF",
                            weight=ft.FontWeight.BOLD,
                            size=16,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        bgcolor=main_color,
                        border_radius=15,
                        padding=5,
                        width=180,
                        margin=ft.margin.only(top=15),
                        alignment=ft.alignment.center,
                    ),
                    # DESCRIPTION
                    ft.Container(
                        content=ft.Text(
                            sub_button_text,
                            color="#FFFFFF",
                            size=11,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        bgcolor=ft.Colors.with_opacity(0.7, sub_color),
                        border_radius=10,
                        padding=8,
                        width=200,
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(top=8),
                    ),
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
        )
        
        # Lock icon for locked modules, arrow for unlocked
        icon_container = ft.Container(
            content=ft.Icon(
                ft.Icons.LOCK if is_locked else ft.Icons.ARROW_FORWARD,
                color="#FFFFFF",
                size=20,
            ),
            alignment=ft.alignment.top_right,
            padding=10
        )
        
        # Final card container with shadow
        return ft.Container(
            content=ft.Stack(
                controls=[
                    bg_container,
                    content_container,
                    icon_container
                ]
            ),
            border_radius=15,
            width=300,
            height=150,
            margin=ft.margin.only(bottom=15),
            shadow=ft.BoxShadow(
                blur_radius=8,
                color=ft.Colors.BLACK26,
                offset=ft.Offset(0, 4),
                spread_radius=1,
            ),
            on_click=lambda e, module_id=module_id: navigate_to_levels(e, user, module_id),
        )

    # Create the module cards with updated colors
    cards = []
    user_id = get_user_id(page)  # Get user ID from session
    user = User().load_data(user_id, page)  # Load user data
    debug_achievement_progress(page)
    page.session.set("user", user)
    page.session.set("user_library", user.library)  # Cache library for later use

    # Check which modules should be unlocked
    for i, module in enumerate(user.modules):
        # First module is always unlocked
        if i == 0:
            is_locked = False
        else:
            # Check if all previous modules are completed
            is_locked = any(not getattr(prev_module, "completed", False) 
                            for prev_module in user.modules[:i])
        
        card = create_module_card(
            module.id, 
            module.waray_name, 
            module.eng_name, 
            "#FFB74D", "#FF9800", 
            is_locked=is_locked
        )
        cards.append(card)

    # Logout button
    logout_button = ft.IconButton(
        icon=ft.Icons.LOGOUT,
        icon_color="#FFFFFF",
        icon_size=24,
        tooltip="Logout",
        on_click=lambda e: user.save_user(page)  # Navigate to login page on logout
    )

    def calculate_completion_percentage(user):
        """Calculate accurate completion percentage based on completed lessons"""
        if not hasattr(user, 'modules') or not user.modules:
            return 0
            
        total_lessons = 0
        completed_lessons = 0
        
        # Count all lessons across all modules
        for module in user.modules:
            if hasattr(module, 'levels'):
                for level in module.levels:
                    total_lessons += 1
                    if getattr(level, 'completed', False):
                        completed_lessons += 1
        
        # Calculate percentage (prevent division by zero)
        if total_lessons > 0:
            percentage = int((completed_lessons / (total_lessons + 5)) * 100)
            print(f"[Progress] Calculated: {completed_lessons}/{total_lessons} = {percentage}%")
            return percentage
        return 0

    def navigate_to_achievements(e, user):
        # Calculate the correct completion percentage
        completion_percentage = calculate_completion_percentage(user)
        
        # Update the user's completion_percentage attribute
        user.completion_percentage = completion_percentage
        unique_words = set(w.lower() for w in user.library)
        words_learned = len(unique_words)
        
        # Store in user data
        try:
            arami = pymongo.MongoClient(uri)["arami"]
            users_col = arami["users"]
            users_col.update_one(
                {"user_id": int(user.user_id)},
                {"$set": {"completion_percentage": completion_percentage}}
            )
            print(f"[Progress] Updated completion percentage: {completion_percentage}%")
        except Exception as e:
            print(f"Error updating completion percentage: {e}")
        
        # Extract proficiency properly regardless of format
        prof_value = user.proficiency
        print(f"[DEBUG] Raw proficiency value: {prof_value}, type: {type(prof_value)}")
        
        # Handle dictionary format
        if isinstance(prof_value, dict):
            if "proficiency" in prof_value:
                prof_value = float(prof_value["proficiency"])
            elif "value" in prof_value:
                prof_value = float(prof_value["value"])
            else:
                # Find any numeric value in the dict
                for key, val in prof_value.items():
                    if isinstance(val, (int, float)):
                        prof_value = float(val)
                        break
                else:
                    prof_value = 0
        
        # Convert to float and scale if needed
        try:
            prof_value = float(prof_value)
            # Scale to percentage if decimal
            if 0 < prof_value < 1:
                prof_value *= 100
        except (ValueError, TypeError):
            print(f"[WARNING] Could not convert proficiency: {prof_value}")
            prof_value = 0
            
        print(f"[DEBUG] Final proficiency value: {prof_value}%")
        
        # Create the achievement data dictionary with the fixed proficiency value
        achievement_data = {
            "username": user.user_name,
            "progress_percentage": completion_percentage,
            "lessons_completed": len([l for m in user.modules for l in m.levels if 
                                    (hasattr(l, "completed") and l.completed) or 
                                    (isinstance(l, dict) and l.get("completed", False))]),
            "words_learned": len(set(w.lower() for w in user.library if w)),  # Ensure non-empty words
            "language_proficiency": prof_value,
            "achievements": user.achievements
        }
        
        # Store in session
        page.session.set("achievement_data", achievement_data)
        page.go("/achievements")

    def navigate_to_word_library(e, user_library):
        # Store just the library in the page session
        page.go("/word-library")

    # Create the bottom navigation bar
    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.MENU_BOOK_OUTLINED,
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=lambda e: navigate_to_word_library(e, user.library)  # Pass library directly
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
                        icon=ft.Icons.PERSON,  
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=lambda e: navigate_to_achievements(e, user)  # Use the new function
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

    # Main content with centered items
    # Scrollable Cards only
    scrollable_cards = ft.Container(
        content=ft.ListView(
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            *cards  
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,  
                    ),
                    padding=ft.padding.all(10),
                ),
            ],
            spacing=0,
            padding=ft.padding.all(0),
        ),
        expand=True,
    )

    centered_modules_title = ft.Container(
        content=modules_title,
        alignment=ft.alignment.center,
        padding=ft.padding.symmetric(vertical=10),
    )

    content = ft.Column(
        [
            header, #fixed lang
            centered_modules_title,
            scrollable_cards,
            # fixed bottom navigation (removed logout_button bc idk if still needed here sa main menu page pero pwede lang naman mabalik)
            bottom_nav,
        ],
        spacing=0,
        expand=True,
        tight=True,
    )

    page.padding = 0
    page.bgcolor = "#FFFFFF" 
    
    page.views.append(ft.View("/main-menu", controls=[content], padding=0, bgcolor="#FFFFFF"))
    page.update()

    start_usage_timer(page)

    from supermemo_engine import merge_duplicate_vocab_entries
    merge_duplicate_vocab_entries(get_user_id(page))

    check_for_unscheduled_vocabulary(get_user_id(page))  # Check for unscheduled vocabulary

    # Attach reset_idle_timer to user interactions
    page.on_pointer_move = reset_idle_timer
    page.on_keyboard_event = reset_idle_timer
    page.on_click = reset_idle_timer

    # Retrieve last_login_date from database for the current user
    usercol = connect_to_mongoDB()
    user_db = usercol.find_one({"user_id": user.user_id})
    last_login = user_db.get("last_login_date") if user_db else None

    if is_first_login_today(last_login):
        print("Triggering daily review popup!")
        review_questions = prepare_daily_review(user.user_id)
        print("Review questions:", review_questions)
        page.session.set("daily_review_questions", review_questions)
        page.session.set("daily_review_needed", True)
        show_daily_review_overlay(page)

    # Add Usage Statistics button to toolbar (or header)
    stats_button = ft.ElevatedButton(
        "Usage Statistics",
        icon=ft.icons.TIMER,
        on_click=lambda e: show_usage_stats(page)
    )
    # Add the stats button to the header_column
    header_column.controls.append(stats_button)

    page.update()