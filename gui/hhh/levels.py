import flet as ft
import json
import os
from bkt_engine import threaded_update_bkt, get_all_p_masteries, bkt_thread
from lstm_engine import overall_proficiency
import pymongo
import threading
import subprocess

uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

def run_lstm_after_bkt(page, completion):
    from bkt_engine import bkt_thread, get_all_p_masteries
    if bkt_thread is not None and bkt_thread.is_alive():
        print("[LSTM] Waiting for BKT thread to finish...")
        bkt_thread.join()
    print("[LSTM] BKT thread finished, running LSTM in subprocess...")
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             
    # Save p_masteries to a temp file
    p_masteries = get_all_p_masteries()
    with open("temp_lstm_input.json", "w") as f:
        json.dump({"p_masteries": p_masteries}, f)

    # Run the LSTM subprocess
    result = subprocess.run(
        ["python", "lstm_engine_runner.py", "temp_lstm_input.json", str(completion)],
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

def levels_page(page: ft.Page):
    """Levels selection page"""
    selected_module_levels, selected_module_desc, selected_module_name, user_id = get_module_data(page)
    page.title = f"Arami - \"{selected_module_name}\" Levels"
    page.bgcolor = "#FFFFFF"
    page.padding = 0
    level_rows = []
    row = []

    updated = get_updated_data(page)

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
        threaded_update_bkt(
            user_id,
            correct_answers,
            incorrect_answers,
        )

    if updated:
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

        threaded_update_bkt(user_id, correct_answers, incorrect_answers)
        completion = compute_completion(page)

        if completion:
            print("DEBUG (levels.py) Completion:", completion)
        else:
            print("DEBUG (levels.py) Completion or Proficiency is None")

        threading.Thread(target=run_lstm_after_bkt, args=(page, completion)).start()

        page.session.set("completion", completion)
        page.session.set("correct_answers", correct_answers)
        page.session.set("incorrect_answers", incorrect_answers)
    if updated and updated["questions"]:
        # Get any question to extract identifying info (safe if list isn't empty)
        first_question = updated["questions"][0]

        for level in selected_module_levels:
            if level.lesson_id == first_question.lesson_id and level.module_name == first_question.module_name:
                level.questions_answers = updated["questions"]
                level.completed = updated["grade"] >= level.pass_threshold
                level.completion_time = completion_time
                level.grade_percentage = grade_percentage
                break

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
        """Handles level selection and navigates to the lesson page."""
        level_index = int(level_num) - 1
        level_data = selected_module_levels[level_index]

        # Check all previous levels (prerequisites)
        prerequisite_levels = selected_module_levels[:level_index]
        all_prerequisites_completed = all(level.completed for level in prerequisite_levels)

        if not all_prerequisites_completed:
            page.open(ft.SnackBar(ft.Text("You must complete previous levels first."), bgcolor="#FF0000"))
            page.update()
            return

        # Optional: prevent re-entering a finished level
        if level_data.completed:
            page.open(ft.SnackBar(ft.Text("Level already completed!"), bgcolor="#FF0000"))
            page.update()
            return

        # Proceed to the lesson
        page.session.set("level_data", level_data)
        print(f"Selected level {level_num}")
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

    def create_level_button(level_number, color="#4285F4"):
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
            on_click=lambda e: level_select(page, level_number)
        )

    for index, level in enumerate(selected_module_levels, start=1):
        level_button = create_level_button(index)

        row.append(level_button)

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

    # Header with gradient background and title
    header = ft.Container(
        content=ft.Stack([
            ft.Container(
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["#0066FF", "#9370DB"],
                ),
                height=130,
            ),
            ft.Container(
                content=ft.Text(
                    selected_module_name,
                    size=20,
                    color="#FFFFFF",
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor="#4285F4",
                border_radius=20,
                padding=ft.padding.symmetric(vertical=8, horizontal=16),
                margin=ft.margin.only(top=100),
                width=240,
                alignment=ft.alignment.center,
            ),
        ]),
        height=130,
    )

    explanation = ft.Container(
        content=ft.Text(
            selected_module_desc,
            color="#000000",
            size=14,
            text_align=ft.TextAlign.CENTER,
        ),
        margin=ft.margin.symmetric(vertical=15, horizontal=20),
        alignment=ft.alignment.center,
    )

    level_grid = ft.Container(
        content=ft.Column(
            level_rows,
            spacing=10, 
        alignment=ft.MainAxisAlignment.CENTER),
        margin=ft.margin.only(top=10),
    )

    back_button = ft.Container(
        content=ft.ElevatedButton(
            text="Back",
            on_click=go_back,
            bgcolor="#4285F4",
            color="#FFFFFF",
            width=100,
            height=40,
        ),
        alignment=ft.alignment.center,
        margin=ft.margin.only(bottom=10),
    )

    chapter_test = ft.Container(
            content=ft.Text(
                "CT",
                color="#FFFFFF",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor="#4285F4",
            width=60,
            height=60,
            border_radius=10,
            alignment=ft.alignment.center,
            data="chaptertest",
            on_click=lambda e: chapter_test_select(page)
        )

    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(icon=ft.Icons.MILITARY_TECH_OUTLINED, icon_color="#FFFFFF", icon_size=24),
                ft.IconButton(icon=ft.Icons.MENU_BOOK_OUTLINED, icon_color="#FFFFFF", icon_size=24),
                ft.IconButton(icon=ft.Icons.HOME_OUTLINED, icon_color="#FFFFFF", icon_size=24),
                ft.IconButton(icon=ft.Icons.PERSON_OUTLINED, icon_color="#FFFFFF", icon_size=24),
                ft.IconButton(icon=ft.Icons.SETTINGS_OUTLINED, icon_color="#FFFFFF", icon_size=24),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
        bgcolor="#280082",
        height=60,
        padding=10
    )

    content = ft.Column(
        [
            header,
            back_button,
            explanation,
            level_grid,
            chapter_test,
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
