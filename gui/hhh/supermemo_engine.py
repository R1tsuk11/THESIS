import json
import os
import pymongo
from pymongo.errors import ConfigurationError
import sys
from datetime import datetime, timedelta
from qbank import module_bank

uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

def connect_to_mongoDB():
    try:
        arami = pymongo.MongoClient(uri)
        aramidb = arami["arami"]
        usercol = aramidb["users"]
        return usercol
    except ConfigurationError as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit("Terminating the program due to MongoDB connection failure.")

def has_review_questions(user_id):
    """Check if the user has any vocabulary items scheduled for review today"""
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    today = datetime.now().date()
    
    if not user or "supermemo" not in user:
        return False
        
    # Check needs_practice vocabulary
    for vocab, state in user["supermemo"].get("needs_practice", {}).items():
        if "next_review" in state:
            try:
                review_date = datetime.fromisoformat(state["next_review"]).date()
                if review_date <= today:
                    return True
            except (ValueError, TypeError):
                continue

    # Check mastered vocabulary
    for vocab, state in user["supermemo"].get("mastered", {}).items():
        if "next_review" in state:
            try:
                review_date = datetime.fromisoformat(state["next_review"]).date()
                if review_date <= today:
                    return True
            except (ValueError, TypeError):
                continue
        
    return False

def get_user_proficiency(user_id):
    """
    Fetches the user's proficiency from the database.
    This function should be implemented to return the user's proficiency level.
    """
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    if user and "proficiency" in user:
        return user["proficiency"]
    return 0  # Default proficiency if not found

def get_questions_for_vocab_list(vocab_list, module_ids=None):
    """
    Returns a list of question dicts from the question bank that match any vocab in vocab_list.
    Optionally filter by module_ids (list of ints).
    """
    questions = []
    # If you want to filter by specific modules, pass their IDs; otherwise, search all modules
    modules_to_search = module_bank.keys() if module_ids is None else module_ids
    for module_id in modules_to_search:
        module = module_bank[module_id]
        for lesson in module.values():
            for q in lesson:
                if q.get("vocabulary") in vocab_list and q.get("type") not in ["Lesson", "Cultural Trivia"]:
                    questions.append(q)
    return questions

def get_review_questions_for_user(user_id, vocab_list, proficiency):
    # Gather all questions from the question bank
    all_questions = []
    for module_id in module_bank.keys():
        module = module_bank[module_id]
        for lesson in module.values():
            all_questions.extend(lesson)
            
    # Filter out None values from vocab_list
    vocab_list = [vocab for vocab in vocab_list if vocab is not None]
    
    # For each vocab, select up to 4 questions
    review_questions = []
    for vocab in vocab_list:
        review_questions.extend(
            select_questions_for_vocab(vocab, all_questions, proficiency, max_per_vocab=4, include_lesson=False)
        )
    return review_questions

def select_questions_for_vocab(vocab, all_questions, proficiency, max_per_vocab=4, include_lesson=False):
    """
    Select appropriate questions for a vocabulary word based on user proficiency
    
    Args:
        vocab: The vocabulary word to find questions for
        all_questions: List of all question objects
        proficiency: User proficiency level (0-100)
        max_per_vocab: Maximum questions to select per vocabulary
        include_lesson: Whether to include lesson-type questions
    """
    # Check if vocab is None
    if vocab is None:
        print("[WARNING] select_questions_for_vocab called with None vocab")
        return []
    
    # First filter by vocabulary (case-insensitive)
    # Handle potential None values safely
    vocab_questions = [q for q in all_questions if 
                      q.get("vocabulary") is not None and 
                      vocab is not None and
                      q.get("vocabulary", "").lower() == vocab.lower()]
    
    # Optionally include lesson question
    lesson_q = []
    if include_lesson:
        lesson_q = [q for q in vocab_questions if q.get("type") == "Lesson"][:1]
    
    # Get non-lesson questions
    other_q = [q for q in vocab_questions if q.get("type") != "Lesson"]
    
    # Filter by proficiency and difficulty
    filtered_q = []
    for q in other_q:
        # Safely get difficulty with default value of 1
        difficulty = q.get("difficulty", 1)
        # Ensure difficulty is a valid number
        if difficulty is None:
            difficulty = 1
            
        # Apply difficulty filter based on proficiency
        if proficiency < 40 and difficulty <= 2:
            filtered_q.append(q)
        elif proficiency < 70 and difficulty <= 3:
            filtered_q.append(q)
        elif proficiency >= 70:  # No difficulty filter for high proficiency
            filtered_q.append(q)
    
    # Sort by difficulty (with safe handling of None)
    filtered_q.sort(key=lambda q: q.get("difficulty", 1) or 1)
    
    # Pick up to max_per_vocab questions
    selected = lesson_q + filtered_q[:max_per_vocab - len(lesson_q)]
    return selected

def get_all_bkt_predictions(user_id):
    print(f"[DEBUG] Fetching BKT predictions for user: {user_id}")
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    if user and "bkt_data" in user:
        bkt_data = user["bkt_data"]
        print(f"[DEBUG] bkt_data keys: {list(bkt_data.keys())}")
        predictions = []
        # Check if 'predictions' is a dict of vocabularies
        if "predictions" in bkt_data and isinstance(bkt_data["predictions"], dict):
            for vocab, data in bkt_data["predictions"].items():
                print(f"[DEBUG] predictions Key: {vocab}, Type: {type(data)}, Value: {data}")
                if isinstance(data, dict) and "p_mastery" in data:
                    predictions.append({"vocab": vocab, "p_mastery": data["p_mastery"]})
        else:
            # Fallback: check top-level keys (legacy structure)
            for vocab, data in bkt_data.items():
                print(f"[DEBUG] Key: {vocab}, Type: {type(data)}, Value: {data}")
                if isinstance(data, dict) and "p_mastery" in data and vocab not in ["predictions", "fitted", "refit_counter"]:
                    predictions.append({"vocab": vocab, "p_mastery": data["p_mastery"]})
        print(f"[DEBUG] Loaded predictions from DB (dict): {predictions}")
        return {item['vocab']: item['p_mastery'] for item in predictions}
    print("[DEBUG] No BKT predictions found.")
    return {}

def prioritize_vocabularies(predictions, threshold=0.85):
    print(f"[DEBUG] Prioritizing vocabularies with threshold {threshold}")
    print(f"[DEBUG] Raw predictions: {predictions}")
    needs_practice = [vocab for vocab, p in predictions.items() if p < threshold]
    mastered = [vocab for vocab, p in predictions.items() if p >= threshold]
    needs_practice = sorted(needs_practice, key=lambda v: predictions[v])
    mastered = sorted(mastered, key=lambda v: -predictions[v])
    print(f"[DEBUG] Needs practice: {needs_practice}")
    print(f"[DEBUG] Mastered: {mastered}")
    return needs_practice, mastered

def initialize_supermemo_state():
    today = datetime.now().date()
    state = {
        "interval": 1,
        "repetition": 0,
        "efactor": 2.5,
        "last_review": str(today),
        "next_review": str(today + timedelta(days=1))
    }
    print(f"[DEBUG] Initialized SuperMemo state: {state}")
    return state

def save_supermemo_schedule(user_id, needs_practice, mastered):
    print(f"[DEBUG] Saving SuperMemo schedule for user: {user_id}")
    print(f"[DEBUG] Needs practice: {needs_practice}")
    print(f"[DEBUG] Mastered: {mastered}")
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    supermemo_data = user.get("supermemo", {})

    needs_practice_states = supermemo_data.get("needs_practice", {})
    for vocab in needs_practice:
        if vocab not in needs_practice_states:
            needs_practice_states[vocab] = initialize_supermemo_state()

    mastered_states = supermemo_data.get("mastered", {})
    for vocab in mastered:
        if vocab not in mastered_states:
            mastered_states[vocab] = initialize_supermemo_state()

    supermemo_data["needs_practice"] = needs_practice_states
    supermemo_data["mastered"] = mastered_states

    print(f"[DEBUG] Final needs_practice_states: {needs_practice_states}")
    print(f"[DEBUG] Final mastered_states: {mastered_states}")

    usercol.update_one(
        {"user_id": user_id},
        {"$set": {"supermemo": supermemo_data}}
    )
    
    # Display the SuperMemo schedule
    print("\n=== SUPERMEMO SCHEDULE ===")
    display_supermemo_schedule(user_id)
    print("=========================\n")

def prepare_daily_review(user_id, threshold=0.85, max_questions=15):
    print(f"[DEBUG] Preparing daily review for user: {user_id}")
    predictions = get_all_bkt_predictions(user_id)
    # If there are no predictions, return empty list immediately
    if not predictions:
        print("[DEBUG] No BKT predictions found. Skipping review preparation.")
        return []
    
    needs_practice, mastered = prioritize_vocabularies(predictions, threshold=threshold)
    # If there are no vocabularies that need practice or are mastered, return empty list
    if not (needs_practice or mastered):
        print("[DEBUG] No vocabulary words to review.")
        return []
    save_supermemo_schedule(user_id, needs_practice, mastered)

    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    supermemo_data = user.get("supermemo", {})
    needs_practice_states = supermemo_data.get("needs_practice", {})
    mastered_states = supermemo_data.get("mastered", {})

    print(f"[DEBUG] Loaded needs_practice_states from DB: {needs_practice_states}")
    print(f"[DEBUG] Loaded mastered_states from DB: {mastered_states}")

    today = datetime.now().date()
    review_items = []

    if not any(state.get("last_review") for state in {**needs_practice_states, **mastered_states}.values()):
        all_vocab = list(needs_practice_states.items()) + list(mastered_states.items())
        print(f"[DEBUG] All vocabularies for first review: {all_vocab}")
        review_items = all_vocab[:max_questions]
    else:
        for vocab, state in {**needs_practice_states, **mastered_states}.items():
            if vocab and state and "next_review" in state:  # Safety check
                try:
                    review_date = datetime.fromisoformat(state["next_review"]).date()
                    if review_date <= today:
                        review_items.append((vocab, state))
                except (ValueError, TypeError):
                    print(f"[WARNING] Invalid next_review date for {vocab}: {state.get('next_review')}")
        print(f"[DEBUG] Vocabularies due for review: {review_items}")
        review_items = review_items[:max_questions]

    print(f"[DEBUG] Final review_items to return: {review_items}")
    
    # Filter out any None values safely
    vocab_list = [vocab for vocab, state in review_items if vocab is not None]
    
    # If vocab_list is empty, return empty list
    if not vocab_list:
        print("[WARNING] No vocabulary items are ready for review")
        return []
        
    proficiency = get_user_proficiency(user_id)
    review_questions = get_review_questions_for_user(user_id, vocab_list, proficiency)
    return review_questions

def update_supermemo_state(state, quality):
    """
    Updates the SuperMemo state for a vocab after a review.
    quality: int (0-5), 5 = perfect recall, 0 = complete blackout
    """
    assert 0 <= quality <= 5
    efactor = state["efactor"]
    repetition = state["repetition"]
    interval = state["interval"]

    if quality < 3:
        repetition = 0
        interval = 1
    else:
        if repetition == 0:
            interval = 1
        elif repetition == 1:
            interval = 6
        else:
            interval = int(interval * efactor)
        repetition += 1

    # Update efactor
    efactor = efactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if efactor < 1.3:
        efactor = 1.3

    today = datetime.now().date()
    state.update({
        "interval": interval,
        "repetition": repetition,
        "efactor": efactor,
        "last_review": str(today),
        "next_review": str(today + timedelta(days=interval))
    })
    return state

def get_due_for_review(user_id):
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    today = datetime.now().date()
    due = []
    if user and "supermemo" in user:
        for vocab, state in user["supermemo"].get("needs_practice", {}).items():
            if datetime.fromisoformat(state["next_review"]).date() <= today:
                due.append((vocab, state))
    return due

# Add this to supermemo_engine.py
def display_supermemo_schedule(user_id):
    """
    Formats and prints SuperMemo scheduling information in a readable table
    
    Args:
        user_id: User ID to check scheduling for
    """
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    
    if not user or "supermemo" not in user:
        print("\n┌───────────────────────────────────────┐")
        print("│         SUPERMEMO SCHEDULING           │")
        print("├───────────────────────────────────────┤")
        print("│ No scheduling data available           │")
        print("└───────────────────────────────────────┘")
        return
    
    supermemo_data = user["supermemo"]
    needs_practice = supermemo_data.get("needs_practice", {})
    mastered = supermemo_data.get("mastered", {})
    today = datetime.now().date()
    
    # Print header
    print("\n┌────────────────────────────────────────────────────────────────────────────────────────┐")
    print("│                                   SUPERMEMO SCHEDULING                                  │")
    print("├──────────────────────┬───────────┬────────────┬─────────────┬────────────┬─────────────┤")
    print("│ Vocabulary           │ Status    │ EFactor    │ Interval    │ Review     │ Due in      │")
    print("├──────────────────────┼───────────┼────────────┼─────────────┼────────────┼─────────────┤")
    
    # Combine and sort by next_review date
    all_vocabs = []
    for vocab, state in needs_practice.items():
        next_review = datetime.fromisoformat(state["next_review"]).date()
        days_until = (next_review - today).days
        all_vocabs.append((vocab, state, "Learning", days_until))
        
    for vocab, state in mastered.items():
        next_review = datetime.fromisoformat(state["next_review"]).date()
        days_until = (next_review - today).days
        all_vocabs.append((vocab, state, "Mastered", days_until))
        
    # Sort by days_until (due soonest first)
    all_vocabs.sort(key=lambda x: x[3])
    
    # Print each vocabulary item
    for vocab, state, status, days_until in all_vocabs:
        efactor = state.get("efactor", 0)
        interval = state.get("interval", 0)
        last_review = state.get("last_review", "Never")
        
        # Format the values
        vocab_display = vocab[:18] + '..' if len(vocab) > 20 else vocab.ljust(20)
        status_display = status
        if days_until <= 0:
            due_display = "TODAY!"
        else:
            due_display = f"{days_until} days"
        
        # Print the row
        print(f"│ {vocab_display:<20} │ {status:<9} │ {efactor:^10.2f} │ {interval:^11} │ {last_review:^10} │ {due_display:^11} │")
    
    print("└──────────────────────┴───────────┴────────────┴─────────────┴────────────┴─────────────┘")
    print("* EFactor: Memory strength (higher = better retained)")
    print("* Interval: Days between reviews")