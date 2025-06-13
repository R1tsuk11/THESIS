import json
import os
import pymongo
from pymongo.errors import ConfigurationError
import sys
from datetime import datetime, timedelta
from qbank import module_bank
from bkt_engine import get_vocab_mastery

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
    """Check if user has any vocabulary scheduled for review"""
    # Connect to the database
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    if not user:
        print(f"[DEBUG] User {user_id} not found in database")
        return False
        
    # Check if user has supermemo data
    if "supermemo" not in user:
        print(f"[DEBUG] User {user_id} has no supermemo data")
        return False
        
    supermemo_data = user["supermemo"]
    
    # Check both needs_practice and mastered for due items
    for category in ["needs_practice", "mastered"]:
        if category not in supermemo_data:
            continue
            
        for vocab, state in supermemo_data[category].items():
            # Debug what we're checking
            print(f"[DEBUG] Checking {vocab} in {category}: {state}")
            
            # Parse dates with error handling
            try:
                next_review = datetime.strptime(state["next_review"], "%Y-%m-%d").date()
                today = datetime.now().date()
                
                if next_review <= today:
                    print(f"[DEBUG] Found due vocab: {vocab}, due on {next_review}")
                    return True
            except (KeyError, ValueError) as e:
                print(f"[DEBUG] Error checking dates for {vocab}: {e}")
                
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

def schedule_pending_vocabulary(user_id, session_data=None, force=False):
    """
    Schedule any newly learned vocabulary that hasn't been scheduled yet
    
    Args:
        user_id: The user ID
        session_data: Optional session data containing correct_answers
        force: If True, ignore the "already scheduled today" check
    """
    print(f"[SuperMemo] Scheduling pending vocabulary for user {user_id}")
    
    # Get user data
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    if not user:
        print(f"[SuperMemo] User {user_id} not found")
        return False
    
    # Get user's vocabulary learning history from DB
    correct_answers = user.get("questions_correct", {})
    
    # If session data is provided, merge it with the DB data
    if session_data and "correct_answers" in session_data:
        session_correct = session_data.get("correct_answers", {})
        print(f"[SuperMemo] Adding {len(session_correct)} items from session")
        # Merge session data with DB data
        for q_id, q_data in session_correct.items():
            if q_id not in correct_answers:
                correct_answers[q_id] = q_data
    
    # Get current SuperMemo data with proper initialization
    supermemo_data = user.get("supermemo", {})
    
    # Ensure the required structure exists
    if "needs_practice" not in supermemo_data:
        supermemo_data["needs_practice"] = {}
    
    if "mastered" not in supermemo_data:
        supermemo_data["mastered"] = {}
    
    # Track how many items were scheduled
    scheduled_count = 0
    
    # Look for vocabulary in correct answers that aren't yet in SuperMemo
    for question_id, question_data in correct_answers.items():
        vocab = question_data.get('vocabulary')
        if not vocab:
            continue
            
        # Check if this vocab is already in SuperMemo
        in_needs_practice = vocab in supermemo_data["needs_practice"]
        in_mastered = vocab in supermemo_data["mastered"]
        
        # If vocab isn't scheduled yet, add it
        if not in_needs_practice and not in_mastered:
            print(f"[SuperMemo] Scheduling new vocabulary: {vocab}")
            mastery = get_vocab_mastery(vocab, user_id=user_id)
            
            # Create initial SuperMemo state
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)  # Schedule for tomorrow
            
            state = {
                "interval": 1,              # Start with 1-day interval
                "repetition": 0,            # No repetitions yet
                "efactor": 2.5,             # Default easiness factor
                "last_review": str(today),  # Mark as "reviewed" today
                "next_review": str(tomorrow)  # Schedule for tomorrow
            }
            
            # Decide whether it goes to needs_practice or mastered
            if mastery >= 0.7:  # If decent mastery, consider it "mastered"
                supermemo_data["mastered"][vocab] = state
            else:  # Otherwise needs more practice
                supermemo_data["needs_practice"][vocab] = state
                
            scheduled_count += 1
    
    # Save updated SuperMemo data if any changes were made
    if scheduled_count > 0:
        usercol.update_one(
            {"user_id": user_id},
            {"$set": {"supermemo": supermemo_data}}
        )
        print(f"[SuperMemo] Scheduled {scheduled_count} new vocabulary items for user {user_id}")
        return True
    else:
        print(f"[SuperMemo] No new vocabulary items to schedule for user {user_id}")
        return False

def register_new_vocabulary(user_id, vocabulary_item):
    """Register a newly learned vocabulary immediately after a lesson"""
    print(f"[SuperMemo] Registering new vocabulary: {vocabulary_item}")
    
    # Get user data
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    if not user:
        print(f"[SuperMemo] User {user_id} not found")
        return False
    
    # Get current SuperMemo data with proper initialization
    supermemo_data = user.get("supermemo", {})
    
    # Ensure the required structure exists
    if "needs_practice" not in supermemo_data:
        supermemo_data["needs_practice"] = {}
    
    if "mastered" not in supermemo_data:
        supermemo_data["mastered"] = {}
    
    # Check if this vocab is already in SuperMemo
    if vocabulary_item in supermemo_data["needs_practice"] or vocabulary_item in supermemo_data["mastered"]:
        print(f"[SuperMemo] Vocabulary '{vocabulary_item}' already scheduled")
        return False
        
    # Get basic BKT prediction to determine initial placement
    mastery = get_vocab_mastery(vocabulary_item, user_id=user_id)
    
    # Create initial SuperMemo state
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)  # Schedule for tomorrow
    
    state = {
        "interval": 1,              # Start with 1-day interval
        "repetition": 0,            # No repetitions yet
        "efactor": 2.5,             # Default easiness factor
        "last_review": str(today),  # Mark as "reviewed" today
        "next_review": str(tomorrow)  # Schedule for tomorrow
    }
    
    # Decide whether it goes to needs_practice or mastered
    if mastery >= 0.7:  # If decent mastery, consider it "mastered"
        supermemo_data["mastered"][vocabulary_item] = state
    else:  # Otherwise needs more practice
        supermemo_data["needs_practice"][vocabulary_item] = state
    
    # Save updated SuperMemo data
    usercol.update_one(
        {"user_id": user_id},
        {"$set": {"supermemo": supermemo_data}}
    )
    
    print(f"[SuperMemo] Registered vocabulary '{vocabulary_item}' for user {user_id}")
    return True

def register_new_vocabulary_batch(user_id, vocabulary_items):
    """Register multiple vocabulary items at once for efficiency"""
    if not vocabulary_items:
        return
        
    print(f"[SuperMemo] Batch registering {len(vocabulary_items)} vocabulary items")
    
    # Get user data
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    if not user:
        print(f"[SuperMemo] User {user_id} not found")
        return False
    
    # Get current SuperMemo data with proper initialization
    supermemo_data = user.get("supermemo", {})
    
    # Ensure the required structure exists
    if "needs_practice" not in supermemo_data:
        supermemo_data["needs_practice"] = {}
    
    if "mastered" not in supermemo_data:
        supermemo_data["mastered"] = {}
        
    # Process each vocabulary item
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    updates_made = False
    
    for vocab in vocabulary_items:
        # Skip if already scheduled
        if vocab in supermemo_data["needs_practice"] or vocab in supermemo_data["mastered"]:
            print(f"[SuperMemo] Vocabulary '{vocab}' already scheduled")
            continue
            
        # Get mastery level
        try:
            # Use cached BKT predictor to avoid reloading for each word
            mastery = get_vocab_mastery(vocab, user_id=user_id)
        
            # Create initial SuperMemo state
            state = {
                "interval": 1,
                "repetition": 0,
                "efactor": 2.5,
                "last_review": str(today),
                "next_review": str(tomorrow)
            }
            
            # Add to appropriate category
            if mastery >= 0.7:
                supermemo_data["mastered"][vocab] = state
            else:
                supermemo_data["needs_practice"][vocab] = state
                
            updates_made = True
            print(f"[SuperMemo] Registered vocabulary '{vocab}' for user {user_id}")
            
        except Exception as e:
            print(f"[SuperMemo] Error registering vocabulary '{vocab}': {e}")
    
    # Save updated data if changes were made
    if updates_made:
        usercol.update_one(
            {"user_id": user_id},
            {"$set": {"supermemo": supermemo_data}}
        )
    
    print(f"[SuperMemo] Batch registration complete")
    return updates_made

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
    
    # For each vocab, select ONLY ONE question
    review_questions = []
    used_ids = set()  # Track used question IDs to avoid duplicates
    
    for vocab in vocab_list:
        questions = select_questions_for_vocab(vocab, all_questions, proficiency, max_per_vocab=1, include_lesson=False)
        for question in questions:
            # Skip questions with duplicate IDs
            if question.get('id') in used_ids:
                print(f"[WARNING] Skipping duplicate question ID: {question.get('id')} for vocab: {vocab}")
                continue
                
            review_questions.append(question)
            used_ids.add(question.get('id'))
    
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

    if "needs_practice" not in supermemo_data:
        supermemo_data["needs_practice"] = {}
    
    if "mastered" not in supermemo_data:
        supermemo_data["mastered"] = {}

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

def prepare_daily_review(user_id, threshold=0.85, max_questions=10):
    """Prepare daily review with improved selection algorithm"""
    print(f"[DEBUG] Preparing daily review for user: {user_id}")
    
    # Get user data
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    supermemo_data = user.get("supermemo", {})
    needs_practice_states = supermemo_data.get("needs_practice", {})
    mastered_states = supermemo_data.get("mastered", {})
    
    if "needs_practice" not in supermemo_data:
        supermemo_data["needs_practice"] = {}
    
    if "mastered" not in supermemo_data:
        supermemo_data["mastered"] = {}

    # Get the "last reviewed" tracking data
    review_history = user.get("review_history", {})
    
    # Today's date
    today = datetime.now().date()
    
    # Gather all vocabulary items that need review
    review_candidates = []
    
    for vocab_type, states in [("needs_practice", needs_practice_states), 
                              ("mastered", mastered_states)]:
        for vocab, state in states.items():
            if vocab and state and "next_review" in state:
                try:
                    review_date = datetime.fromisoformat(state["next_review"]).date()
                    
                    # Calculate days overdue (negative if not due yet)
                    days_overdue = (today - review_date).days
                    
                    # Get days since last reviewed (default to 100 if never reviewed)
                    last_reviewed = review_history.get(vocab, {}).get("last_reviewed")
                    if last_reviewed:
                        days_since_last_review = (today - datetime.fromisoformat(last_reviewed).date()).days
                    else:
                        days_since_last_review = 100  # High number for never reviewed
                    
                    # Get number of times this item was skipped
                    times_skipped = review_history.get(vocab, {}).get("times_skipped", 0)
                    
                    # Calculate priority score
                    # Higher priority for:
                    # 1. Items that are more days overdue
                    # 2. Items that haven't been reviewed in a long time
                    # 3. Items that have been skipped multiple times
                    # 4. Items that need practice (vs. mastered items)
                    priority_score = (
                        max(0, days_overdue) * 10 +  # Overdue days (if any)
                        days_since_last_review * 2 +  # Days since last review
                        times_skipped * 5 +           # Skip penalty
                        (20 if vocab_type == "needs_practice" else 0)  # Needs practice bonus
                    )
                    
                    review_candidates.append({
                        "vocab": vocab,
                        "state": state,
                        "priority_score": priority_score,
                        "days_overdue": days_overdue,
                        "vocab_type": vocab_type
                    })
                    
                except (ValueError, TypeError) as e:
                    print(f"[WARNING] Error processing {vocab}: {e}")
                    
    # Sort candidates by priority score
    review_candidates.sort(key=lambda x: x["priority_score"], reverse=True)
    
    # Select candidates for today's review
    selected_candidates = review_candidates[:max_questions]
    
    # Update skip counter for items that were due but not selected
    unselected_due = [item for item in review_candidates[max_questions:] 
                     if item["days_overdue"] >= 0]
    
    # Update the review history
    for item in unselected_due:
        vocab = item["vocab"]
        if vocab not in review_history:
            review_history[vocab] = {"times_skipped": 1}
        else:
            review_history[vocab]["times_skipped"] = review_history[vocab].get("times_skipped", 0) + 1
    
    # Update review history for selected items
    for item in selected_candidates:
        vocab = item["vocab"]
        if vocab not in review_history:
            review_history[vocab] = {}
        review_history[vocab]["times_skipped"] = 0  # Reset skip counter
    
    # Save updated review history
    usercol.update_one(
        {"user_id": user_id},
        {"$set": {"review_history": review_history}}
    )
    
    # Get vocabulary list from selected candidates
    vocab_list = [item["vocab"] for item in selected_candidates]
    
    # Generate questions
    if not vocab_list:
        print("[WARNING] No vocabulary items ready for review")
        return []
    
    proficiency = get_user_proficiency(user_id)
    review_questions = get_review_questions_for_user(user_id, vocab_list, proficiency)
    
    print(f"[DEBUG] Selected {len(selected_candidates)} items for review")
    print(f"[DEBUG] {len(unselected_due)} due items couldn't be included today")
    
    return review_questions

def mark_vocabulary_reviewed(user_id, vocab, performance_quality):
    """
    Mark a vocabulary item as reviewed with its quality rating
    
    Args:
        user_id: The user who completed the review
        vocab: The vocabulary word that was reviewed
        performance_quality: Quality rating (0-5) of recall, where 5 is perfect recall
    """
    print(f"[SuperMemo] Marking '{vocab}' as reviewed with quality {performance_quality}")
    
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    
    if not user:
        print(f"[ERROR] User {user_id} not found in database")
        return False
        
    # Get review history
    review_history = user.get("review_history", {})
    if vocab not in review_history:
        review_history[vocab] = {}
    
    # Update last reviewed date
    today = datetime.now().date()
    review_history[vocab]["last_reviewed"] = str(today)
    
    # Track performance quality
    review_history[vocab]["last_quality"] = performance_quality
    
    # Reset skip counter since item was reviewed
    review_history[vocab]["times_skipped"] = 0
    
    # Update in database
    usercol.update_one(
        {"user_id": user_id},
        {"$set": {"review_history": review_history}}
    )
    
    # Also update the SuperMemo state based on performance
    update_vocab_supermemo_state(user_id, vocab, performance_quality)
    
    return True

def update_vocab_supermemo_state(user_id, vocab, quality):
    """Update SuperMemo state for a specific vocabulary item based on review quality"""
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    
    if not user or "supermemo" not in user:
        print(f"[ERROR] User {user_id} not found or has no SuperMemo data")
        return False
        
    supermemo_data = user["supermemo"]
    
    # Check if in needs_practice or mastered
    if vocab in supermemo_data.get("needs_practice", {}):
        state = supermemo_data["needs_practice"][vocab]
        # Update the state
        state = update_supermemo_state(state, quality)
        # Save back to database
        usercol.update_one(
            {"user_id": user_id},
            {"$set": {f"supermemo.needs_practice.{vocab}": state}}
        )
        return True
        
    if vocab in supermemo_data.get("mastered", {}):
        state = supermemo_data["mastered"][vocab]
        # Update the state
        state = update_supermemo_state(state, quality)
        # Save back to database
        usercol.update_one(
            {"user_id": user_id},
            {"$set": {f"supermemo.mastered.{vocab}": state}}
        )
        return True
        
    print(f"[WARNING] Vocabulary '{vocab}' not found in SuperMemo data")
    return False

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
        
    # NEW: Cap interval at 7 days (1 week)
    MAX_INTERVAL = 7  # 1 week maximum
    if interval > MAX_INTERVAL:
        print(f"[SuperMemo] Capping interval from {interval} to {MAX_INTERVAL} days")
        interval = MAX_INTERVAL

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