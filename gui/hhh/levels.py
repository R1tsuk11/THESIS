import flet as ft
import json
import os
from bkt_engine import update_bkt, get_all_p_masteries
import pymongo
import threading
import subprocess

uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

def run_bkt_and_lstm(page, completion, user_id, correct_answers, incorrect_answers):
    update_bkt(user_id, correct_answers, incorrect_answers)

    # 1. Gather bkt_sequence and completion_percentage
    bkt_sequence = get_all_p_masteries()  # List of floats
    print("[DEBUG] get_all_p_masteries() returns:", bkt_sequence)
    completion = compute_completion(page)  # Float (0-100 or 0-1)

    # 2. Save bkt_sequence and completion to temp file
    with open("temp_lstm_input.json", "w") as f:
        json.dump({
            "bkt_sequence": bkt_sequence,
            "completion_percentage": completion
        }, f)

    # 3. Ensure proficiency history file exists
    prof_history_path = "temp_prof_history.json"
    if not os.path.exists(prof_history_path):
        arami = pymongo.MongoClient(uri)["arami"]
        usercol = arami["users"]

        proficiency_history = usercol.find_one({"user_id": page.session.get("user_id")}).get("proficiency_history", [])
        if proficiency_history:
            with open(prof_history_path, "w") as f:
                json.dump(proficiency_history, f)
        else:
            proficiency = usercol.find_one({"user_id": page.session.get("user_id")}).get("proficiency", 0)
            with open(prof_history_path, "w") as f:
                json.dump([{"proficiency": proficiency}], f)

    # 4. Run LSTM in subprocess
    result = subprocess.run(
        ["python", "lstm_engine_runner.py", "temp_lstm_input.json", prof_history_path],
        capture_output=True, text=True
    )
    if result.stdout:
        try:
            output = json.loads(result.stdout)
            print("[LSTM subprocess] Output:", output)
            proficiency = output.get("proficiency")
            page.session.set("proficiency", proficiency)
        except Exception as e:
            print("[LSTM subprocess] Failed to parse output:", e)
    if result.stderr:
        print("[LSTM subprocess] Error:", result.stderr)

def compute_completion(page):
    modules = page.session.get("modules")

    if not modules:
        try:
            with open("temp_modules.json", "r") as f:
                modules = json.load(f)
        except FileNotFoundError:
            print("Temp module cache not found.")
            return None

    total = 0
    completed = 0
    for module in modules:
        # Count levels
        total += len(module.levels)
        completed += sum(1 for lvl in module.levels if getattr(lvl, "completed", False))
        # Count chapter test
        if hasattr(module, "chapter_test"):
            total += 1
            if getattr(module.chapter_test, "completed", False):
                completed += 1
    if total == 0:
        return 0
    return round((completed / total) * 100, 2)

def merge_answer_data(existing, new):
    """Merge dictionaries while preserving key structure and merging nested values."""
    for k, v in new.items():
        if k in existing and isinstance(existing[k], dict) and isinstance(v, dict):
            existing[k].update(v)  # Shallow merge
        else:
            existing[k] = v  # Add or replace
    return existing

def get_module_data(page):
    modules = page.session.get("modules")
    module_id = page.session.get("module_id")

    if not modules:
        try:
            with open("temp_modules.json", "r") as f:
                modules = json.load(f)
        except FileNotFoundError:
            print("Temp module cache not found.")
            return None

    if not module_id:
        print("Module ID not found in session.")
        return None

    for module in modules:
        if str(module.id) == str(module_id):
            return module.levels, module.desc, module.waray_name, module.user_id

    print(f"No matching module with ID {module_id} found.")
    return None

def get_chapter_test(page):
    modules = page.session.get("modules")
    module_id = page.session.get("module_id")

    if not modules:
        try:
            with open("temp_modules.json", "r") as f:
                modules = json.load(f)
        except FileNotFoundError:
            print("Temp module cache not found.")
            return None

    if not module_id:
        print("Module ID not found in session.")
        return None

    for module in modules:
        if str(module.id) == str(module_id):
            return module.chapter_test  # <-- now it's safe!

    print(f"No matching module with ID {module_id} found.")
    return None

def get_updated_data(page):
    updated_data = page.session.get("updated_data")
    if not updated_data:
        return None

    grade_percentage, formatted_time, total_response_time, correct_answers, incorrect_answers, updated_questions = updated_data
    return {
        "grade": grade_percentage,
        "time": formatted_time,
        "correct": correct_answers,
        "incorrect": incorrect_answers,
        "questions": updated_questions,
        "total_response_time": total_response_time,
    }

def clear_temp_module_cache():
    if os.path.exists("temp_modules.json"):
        os.remove("temp_modules.json")

def levels_page(page: ft.Page, image_urls: list):
    """Levels selection page"""
    selected_module_levels, selected_module_desc, selected_module_name, user_id = get_module_data(page)
    page.title = f"Arami - \"{selected_module_name}\" Levels"
    page.bgcolor = "#FFFFFF"
    page.padding = 0
    level_rows = []
    row = []

    updated = get_updated_data(page)

    if updated and updated["questions"]:
        # Get any question to extract identifying info (safe if list isn't empty)
        first_question = updated["questions"][0]
        
        completion_time = updated["total_response_time"]
        grade_percentage = updated["grade"]

        for level in selected_module_levels:
            if level.lesson_id == first_question.lesson_id and level.module_name == first_question.module_name:
                level.questions_answers = updated["questions"]
                level.completed = updated["grade"] >= level.pass_threshold
                level.completion_time = completion_time
                level.grade_percentage = grade_percentage
                break

    completion = compute_completion(page)

    if completion:
        print("DEBUG (levels.py) Completion:", completion)
    else:
        print("DEBUG (levels.py) Completion is None")

    if os.path.exists("temp_chaptertest_data.json"):
        with open("temp_chaptertest_data.json", "r") as f:
            chaptertest_data = json.load(f)
        # Call BKT update just for chapter test data

        correct_answers = page.session.get("correct_answers")
        incorrect_answers = page.session.get("incorrect_answers")

        if correct_answers and incorrect_answers:
            # Merge with existing data
            correct_answers = merge_answer_data(correct_answers, chaptertest_data.get("questions_correct", {}))
            incorrect_answers = merge_answer_data(incorrect_answers, chaptertest_data.get("questions_incorrect", {}))
        else:
            # Connect to MongoDB
            arami = pymongo.MongoClient(uri)["arami"]
            usercol = arami["users"]
            # Retrieve questions_correct and questions_incorrect from MongoDB
            user_data = usercol.find_one({"user_id": user_id})
            if not user_data:
                print(f"User with ID {user_id} not found in MongoDB.")
                return
            questions_correct = user_data.get("questions_correct", {})
            questions_incorrect = user_data.get("questions_incorrect", {})
            # Merge with existing data
            correct_answers = merge_answer_data(questions_correct, chaptertest_data.get("questions_correct", {}))
            incorrect_answers = merge_answer_data(questions_incorrect, chaptertest_data.get("questions_incorrect", {}))
        
        threading.Thread(target=run_bkt_and_lstm, args=(page, completion, user_id, correct_answers, incorrect_answers)).start()

    elif updated:
        # Load previous session data (initialize if none)
        correct_answers = page.session.get("correct_answers")
        incorrect_answers = page.session.get("incorrect_answers")
        if correct_answers:
            correct_answers = merge_answer_data(correct_answers, updated["correct"])
        else:
            correct_answers = updated["correct"]
            page.session.set("correct_answers", correct_answers)   

        if incorrect_answers:
            incorrect_answers = merge_answer_data(incorrect_answers, updated["incorrect"])
        else:
            incorrect_answers = updated["incorrect"]
            page.session.set("incorrect_answers", incorrect_answers)

        completion_time = updated["total_response_time"]
        grade_percentage = updated["grade"]

        print("DEBUG (levels.py) correct_answers:", correct_answers)
        print("DEBUG (levels.py) incorrect_answers:", incorrect_answers)
        print("DEBUG (levels.py) correct_answers keys:", list(correct_answers.keys()))
        print("DEBUG (levels.py) incorrect_answers keys:", list(incorrect_answers.keys()))
        print("DEBUG (levels.py) correct_answers values:", list(correct_answers.values()))
        print("DEBUG (levels.py) incorrect_answers values:", list(incorrect_answers.values()))

        page.session.set("correct_answers", correct_answers)
        page.session.set("incorrect_answers", incorrect_answers)

        threading.Thread(target=run_bkt_and_lstm, args=(page, completion, user_id, correct_answers, incorrect_answers)).start()

    def go_back(e):
        """Navigate back to the main menu"""
        selected_module_levels = page.session.get("module_levels")
        modules = page.session.get("modules")
        module_id = page.session.get("module_id")
 
        if modules and selected_module_levels and module_id:
            for module in modules:
                if str(module.id) == str(module_id):
                    # Update levels in the matched module
                    updated_levels = []
                    for lvl in selected_module_levels:
                        if getattr(lvl, "type", "") != "chaptertest":  # skip chaptertest
                            updated_levels.append(lvl)
                    module.levels = updated_levels
                    break

            # Save updated modules back to the user
            user = page.session.get("user")
            if user:
                user.modules = modules
                page.session.set("user", user)
            else:
                print("User not found in session. Cannot save updated modules.")

        clear_temp_module_cache()
        page.go("/main-menu")

    def level_select(e, level_num):
        level_index = int(level_num) - 1
        level_data = selected_module_levels[level_index]

        # Debug print initial data
        print(f"[DEBUG] Starting level_select for level {level_num}")
        print(f"[DEBUG] Level data: {level_data}")

        # Prerequisite and completion checks...
        prerequisite_levels = selected_module_levels[:level_index]
        all_prerequisites_completed = all(level.completed for level in prerequisite_levels)

        if not all_prerequisites_completed:
            print("[DEBUG] Prerequisites not completed")
            page.open(ft.SnackBar(ft.Text("You must complete previous levels first."), bgcolor="#FF0000"))
            page.update()
            return

        # Prevent re-entering a finished level
        if level_data.completed:
            print("[DEBUG] Level already completed")
            page.open(ft.SnackBar(ft.Text("Level already completed!"), bgcolor="#FF0000"))
            page.update()
            return

        # Fetch current proficiency
        user_id = page.session.get("user_id")
        from supermemo_engine import get_user_proficiency
        proficiency = get_user_proficiency(user_id)
        print(f"[DEBUG] User proficiency: {proficiency}")

        # Use the questions stored in the user's level data
        all_questions = level_data.questions_answers
        print(f"[DEBUG] Total questions in level: {len(all_questions)}")
        
        # Debug print some question sample
        for i, q in enumerate(all_questions[:3]):  # Print first 3 questions for debugging
            print(f"[DEBUG] Sample question {i+1}: type={getattr(q, 'type', 'unknown')}, "
                f"vocab={getattr(q, 'vocabulary', 'unknown')}, "
                f"difficulty={getattr(q, 'difficulty', 'unknown')}")

        # Get all unique vocabularies in this lesson
        # Get all unique vocabularies in this lesson - preserve original case
        vocab_dict = {}
        for q in all_questions:
            if q.vocabulary:
                # Use lowercase as key for case-insensitive matching, but store original case
                vocab_key = q.vocabulary.lower()
                vocab_dict[vocab_key] = q.vocabulary  # Store original case
        
        # Get sorted list of vocabularies with original casing preserved
        vocab_list = [vocab_dict[key] for key in sorted(vocab_dict.keys())]
        print(f"[DEBUG] Vocabularies in this level: {vocab_list}")

        def select_lesson_and_practice_questions(all_questions, vocab, proficiency):
            # Match using lowercase for case-insensitive matching but keep original case for display
            lesson_q = [q for q in all_questions if getattr(q, "vocabulary", "").lower() == vocab.lower() and getattr(q, "type", "") == "Lesson"]
            print(f"[DEBUG] Found {len(lesson_q)} lesson questions for vocab '{vocab}'")
            
            if proficiency < 40:
                practice_q = [q for q in all_questions if getattr(q, "vocabulary", "").lower() == vocab.lower() and getattr(q, "type", "") != "Lesson" and getattr(q, "difficulty", 1) <= 2]
                print(f"[DEBUG] Found {len(practice_q)} practice questions (diff <= 2) for vocab '{vocab}' (proficiency < 40)")
            elif proficiency < 70:
                practice_q = [q for q in all_questions if getattr(q, "vocabulary", "").lower() == vocab.lower() and getattr(q, "type", "") != "Lesson" and getattr(q, "difficulty", 1) <= 3]
                print(f"[DEBUG] Found {len(practice_q)} practice questions (diff <= 3) for vocab '{vocab}' (40 <= proficiency < 70)")
            else:
                practice_q = [q for q in all_questions if getattr(q, "vocabulary", "").lower() == vocab.lower() and getattr(q, "type", "") != "Lesson"]
                print(f"[DEBUG] Found {len(practice_q)} practice questions (any diff) for vocab '{vocab}' (proficiency >= 70)")
                
            practice_q.sort(key=lambda q: getattr(q, "difficulty", 1))
            
            # Only take the lesson and practice questions we need
            selected = []
            # Always include lesson questions first if available
            if lesson_q:
                selected.extend(lesson_q[:1])
            # Then add practice questions
            selected.extend(practice_q[:3])
            
            print(f"[DEBUG] Selected {len(lesson_q[:1]) if lesson_q else 0} lesson + {min(len(practice_q), 3)} practice questions for vocab '{vocab}'")
            return selected

        # Process vocabularies in order and keep questions grouped
        questions = []
        for vocab in vocab_list:
            # Get all questions for this vocab
            vocab_questions = select_lesson_and_practice_questions(all_questions, vocab, proficiency)
            questions.extend(vocab_questions)

        # Debug final question set
        print(f"[DEBUG] Final question count: {len(questions)}")
        for i, q in enumerate(questions):
            print(f"[DEBUG] Question {i+1}: type={getattr(q, 'type', 'unknown')}, "
                f"vocab={getattr(q, 'vocabulary', 'unknown')}, "
                f"difficulty={getattr(q, 'difficulty', 'unknown')}")
            q.lesson_id = level_data.lesson_id
            q.module_name = level_data.module_name

        level_data.questions_answers = questions

        page.session.set("level_data", level_data)
        print(f"Selected level {level_num} (proficiency: {proficiency})")
        page.go("/lesson")

    def chapter_test_select(page):
        all_levels_completed = all(level.completed for level in selected_module_levels)
        ct_level = get_chapter_test(page)

        if not all_levels_completed:
            page.open(ft.SnackBar(ft.Text("You must complete all levels first."), bgcolor="#FF0000"))
            page.update()
            return
        
        if ct_level.completed:
            page.open(ft.SnackBar(ft.Text("Chapter Test already completed!"), bgcolor="#FF0000"))
            page.update()
            return
        
        # Proceed to the chapter test
        page.session.set("ct_data", ct_level)
        page.go("/chaptertest")

    def create_level_button(level_number, is_available=True):
        # Use dark gray for unavailable levels, blue for available ones
        color = "#4285F4" if is_available else "#666666"
        
        return ft.Container(
            content=ft.Text(
                str(level_number),
                color="#FFFFFF",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=color,
            width=60,
            height=60,
            border_radius=10,
            alignment=ft.alignment.center,
            data=level_number,
            # Always keep the click handler, but handle availability inside level_select
            on_click=lambda e: level_select(e, level_number)
        )

    # Check if all levels are completed to determine chapter test button color
    all_levels_completed = all(level.completed for level in selected_module_levels)
    chapter_test_color = "#4285F4" if all_levels_completed else "#666666"
    
    # Icon instead of "CT"
    chapter_test_button = ft.Container(
        content=ft.Icon(
            name=ft.Icons.GRADING,  
            color="#FFFFFF",
            size=28,
        ),
        bgcolor=chapter_test_color,
        width=60,
        height=60,
        border_radius=10,
        alignment=ft.alignment.center,
        data="chaptertest",
        on_click=lambda e: chapter_test_select(page)
    )

        # Process level buttons
    level_count = 0
    for index, level in enumerate(selected_module_levels, start=1):
        # Check if all prerequisites for this level are completed
        prerequisite_levels = selected_module_levels[:index-1]
        all_prerequisites_completed = all(level.completed for level in prerequisite_levels)
        
        # Create button with appropriate color based on availability
        level_button = create_level_button(index, all_prerequisites_completed)

        row.append(level_button)
        level_count += 1

        # Add chapter test button next to level 5
        if index == 5:
            row.append(chapter_test_button)
            
        # When we have 3 buttons, or it's the last button, add the row
        if len(row) == 3 or index == len(selected_module_levels):
            level_rows.append(
                ft.Row(
                    row,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10
                )
            )
            row = []  # reset for the next row

    # If we didn't add the chapter test button yet (in case there are fewer than 5 levels)
    if level_count < 5 and not any(chapter_test_button in r.controls for r in level_rows):
        if row:  # If there's an incomplete row
            row.append(chapter_test_button)
            level_rows.append(
                ft.Row(
                    row,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10
                )
            )
        else:  # Start a new row for the chapter test button
            level_rows.append(
                ft.Row(
                    [chapter_test_button],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10
                )
            )

    # Header with gradient background and title
    header = ft.Container(
        content=ft.Stack([
            ft.Container(
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["#0066FF", "#9370DB"],
                ),
                height=170,
            ),
            ft.Container(
                bgcolor="#4285F4",
                padding=ft.padding.symmetric(vertical=1, horizontal=16),
                margin=ft.margin.only(top=150),
                width=300,
                height=75,
            ),
            ft.Container(
                content=ft.Text(
                    selected_module_name,
                    size=26,
                    color="#FFFFFF",
                    weight=ft.FontWeight.W_900,
                    text_align=ft.TextAlign.LEFT,
                ),
                bgcolor="#4285F4",
                border_radius=30,
                padding=ft.padding.symmetric(vertical=1, horizontal=16),
                margin=ft.margin.only(top=150),
                width=350,
                height=75,
                alignment=ft.alignment.center_left,
            ),
            
            # Button in top-right
            ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="#FFFFFF",
                    icon_size=24,
                    on_click=lambda _: page.go("/main-menu")
                    ),
                alignment=ft.alignment.top_left,
                padding=10,  # Space from the edges
            )
        ]),
        height=230,
    )

    explanation = ft.Container(
        content=ft.Text(
            selected_module_desc,
            color="#000000",
            size=14,
            text_align=ft.TextAlign.CENTER,
        ),
        margin=ft.margin.only(top=10,bottom=15,left=10, right=10),
        alignment=ft.alignment.center,
    )

    level_grid = ft.Container(
        content=ft.Column(
            level_rows,
            spacing=10, 
        alignment=ft.MainAxisAlignment.CENTER),
        margin=ft.margin.only(top=10),
    )

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

    content = ft.Column(
        [
            header,
            explanation,
            level_grid,
            ft.Container(expand=True),
            bottom_nav,
        ],
        spacing=0,
        expand=True,
    )

    page.views.append(ft.View(
        "/levels",
        controls=[content],
        bgcolor="#FFFFFF",
        padding=0
    ))
    page.update()
