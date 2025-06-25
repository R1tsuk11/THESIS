import json
import os
import pymongo
from pymongo.errors import ConfigurationError
import sys
import threading
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

def has_completed_reviews(user_id):
    """Check if user has completed any daily reviews."""
    try:
        # Handle None user_id gracefully
        if user_id is None:
            print("[SuperMemo] User ID is None, can't check review completion")
            return False
            
        # Convert to int safely - handle string or numeric inputs
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            print(f"[SuperMemo] Invalid user_id format: {user_id}")
            return False
            
        uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"
        arami = pymongo.MongoClient(uri)["arami"]
        usercol = arami["users"]
        
        user = usercol.find_one({"user_id": user_id})
        if not user:
            print(f"[SuperMemo] User {user_id} not found")
            return False
            
        reviews_completed = user.get("reviews_completed", 0)
        
        # Debug output to trace what's happening
        print(f"[SuperMemo] User {user_id} has completed {reviews_completed} reviews - Using confidence: {reviews_completed > 0}")
        
        # Explicitly return comparison result
        return reviews_completed > 0
        
    except Exception as e:
        print(f"[SuperMemo] Error checking review completion status: {e}")
        return False
def process_review_items_in_background(user_id, vocab_list, quality_scores):
    """
    Process a batch of review items in a background thread
    
    Args:
        user_id: The user ID
        vocab_list: List of vocabulary items to mark as reviewed
        quality_scores: Dictionary mapping vocabulary to quality scores
    """
    # Create a background thread for processing
    thread = threading.Thread(
        target=_process_review_items_thread,
        args=(user_id, vocab_list, quality_scores),
        daemon=True  # Make it a daemon thread so it doesn't block program exit
    )
    thread.start()
    print(f"[SuperMemo] Started background processing thread for {len(vocab_list)} items")
    return thread

def _process_review_items_thread(user_id, vocab_list, quality_scores):
    """Thread target function to process review items"""
    print(f"[SuperMemo] Processing {len(vocab_list)} review items in background thread")
    
    try:
        for vocab in vocab_list:
            # Get quality score for this vocabulary (default to 3 if not specified)
            quality = quality_scores.get(vocab, 2)
            
            # Mark as reviewed (reusing existing function)
            mark_vocabulary_reviewed(user_id, vocab, quality)
        
        print(f"[SuperMemo] Background processing complete for {len(vocab_list)} items")
    except Exception as e:
        print(f"[SuperMemo] Error in background thread: {str(e)}")

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
    Handles both dictionary and numeric values.
    """
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    if user and "proficiency" in user:
        # Handle case where proficiency is a dictionary
        if isinstance(user["proficiency"], dict):
            # Extract the value you need - modify this based on your dictionary structure
            if "prediction" in user["proficiency"]:
                return user["proficiency"]["prediction"] * 100  # Converting to percentage
            else:
                print(f"[WARNING] Proficiency dictionary missing expected fields: {user['proficiency']}")
                return 50  # Default if dictionary doesn't have expected structure
        # Handle numeric case
        elif isinstance(user["proficiency"], (int, float)):
            return user["proficiency"]
        else:
            print(f"[WARNING] Unknown proficiency format: {type(user['proficiency'])}")
            return 50  # Default for unknown format
    return 50  # Updated default proficiency if not found

def get_daily_review_completion_count(user_id):
    """Get the number of completed daily reviews"""
    try:
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": user_id})
        
        if user:
            # Check multiple sources for review completion
            review_data = user.get("review_data", {})
            completed_reviews = review_data.get("completed", 0)
            
            # Also check review_history
            review_history = user.get("review_history", {})
            
            # Count vocabularies that have been reviewed at least once
            reviewed_vocab_count = len([vocab for vocab, data in review_history.items() 
                                      if data.get("times_reviewed", 0) > 0])
            
            # Use the higher of the two counts
            total_reviews = max(completed_reviews, reviewed_vocab_count)
            
            print(f"[SuperMemo] Daily review completion check: completed={completed_reviews}, reviewed_vocab={reviewed_vocab_count}, using={total_reviews}")
            return total_reviews
    except Exception as e:
        print(f"[SuperMemo] Error checking daily review completion: {e}")
    
    return 0

def get_supermemo_confidence(user_id):
    """Calculate SuperMemo confidence based on daily review completion"""
    try:
        from confidence_scoring import get_daily_review_completion_count
        daily_review_count = get_daily_review_completion_count(user_id)
        if daily_review_count > 0:
            # Calculate a basic SuperMemo score based on completion
            # Start at 0.5, add 0.1 for each completed review, max 0.9
            supermemo_score = min(0.9, 0.5 + (daily_review_count * 0.1))
            print(f"[SuperMemo] Calculated confidence from {daily_review_count} completed reviews: {supermemo_score:.2f}")
            return supermemo_score
        else:
            print(f"[SuperMemo] No daily reviews completed yet")
            return None
    except Exception as e:
        print(f"[SuperMemo] Error getting SuperMemo confidence: {e}")
        return None

def get_initial_quality_from_mastery(mastery):
    if mastery < 0.3:
        return 1
    elif mastery < 0.5:
        return 2
    elif mastery < 0.7:
        return 3
    elif mastery < 0.85:
        return 4
    else:
        return 5

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
    review_history = user.get("review_history", {})  # <-- Add this line
    
    # Ensure the required structure exists
    if "needs_practice" not in supermemo_data:
        supermemo_data["needs_practice"] = {}
    
    if "mastered" not in supermemo_data:
        supermemo_data["mastered"] = {}
    
    # Track how many items were scheduled
    scheduled_count = 0
    
    # Look for vocabulary in correct answers that aren't yet in SuperMemo
    for question_id, question_data in correct_answers.items():
        vocab = normalize_vocab(question_data.get('vocabulary'))
        if not vocab:
            continue
            
        # Check if this vocab is already in SuperMemo
        in_needs_practice = vocab in supermemo_data["needs_practice"]
        in_mastered = vocab in supermemo_data["mastered"]
        
        # If vocab isn't scheduled yet, add it
        if not in_needs_practice and not in_mastered:
            print(f"[SuperMemo] Scheduling new vocabulary: {vocab}")
            mastery = get_vocab_mastery(vocab, user_id=user_id)
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            initial_quality = get_initial_quality_from_mastery(mastery)

            state = {
                "interval": 1,
                "repetition": 0,
                "efactor": 2.5,
                "last_review": str(today),
                "next_review": str(tomorrow),
                "quality": initial_quality
            }

            # --- Initialize review_history for this vocab ---
            review_history[vocab] = {
                "last_reviewed": str(today),
                "quality": initial_quality,
                "last_quality": initial_quality,
                "times_reviewed": 0,
                "times_skipped": 0
            }

            if mastery >= 0.7:
                supermemo_data["mastered"][vocab] = state
            else:
                supermemo_data["needs_practice"][vocab] = state

            scheduled_count += 1

    # Save updated SuperMemo data and review_history if any changes were made
    if scheduled_count > 0:
        usercol.update_one(
            {"user_id": user_id},
            {"$set": {"supermemo": supermemo_data, "review_history": review_history}}
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
    review_history = user.get("review_history", {})  # <-- Add this line
    
    # Ensure the required structure exists
    if "needs_practice" not in supermemo_data:
        supermemo_data["needs_practice"] = {}
    
    if "mastered" not in supermemo_data:
        supermemo_data["mastered"] = {}
    
    # Check if this vocab is already in SuperMemo
    vocabulary_item = normalize_vocab(vocabulary_item)
    if vocabulary_item in supermemo_data["needs_practice"] or vocabulary_item in supermemo_data["mastered"]:
        print(f"[SuperMemo] Vocabulary '{vocabulary_item}' already scheduled")
        return False

    mastery = get_vocab_mastery(vocabulary_item, user_id=user_id)
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    initial_quality = get_initial_quality_from_mastery(mastery)

    state = {
        "interval": 1,
        "repetition": 0,
        "efactor": 2.5,
        "last_review": str(today),
        "next_review": str(tomorrow),
        "quality": initial_quality
    }

    # --- Initialize review_history for this vocab ---
    review_history[vocabulary_item] = {
        "last_reviewed": str(today),
        "quality": initial_quality,
        "last_quality": initial_quality,
        "times_reviewed": 0,
        "times_skipped": 0
    }

    if mastery >= 0.7:
        supermemo_data["mastered"][vocabulary_item] = state
    else:
        supermemo_data["needs_practice"][vocabulary_item] = state

    usercol.update_one(
        {"user_id": user_id},
        {"$set": {"supermemo": supermemo_data, "review_history": review_history}}
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
    review_history = user.get("review_history", {})
    
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
        vocab = normalize_vocab(vocab)
        # Skip if already scheduled
        if vocab in supermemo_data["needs_practice"] or vocab in supermemo_data["mastered"]:
            print(f"[SuperMemo] Vocabulary '{vocab}' already scheduled")
            continue
            
        # Get mastery level
        try:
            # Use cached BKT predictor to avoid reloading for each word
            mastery = get_vocab_mastery(vocab, user_id=user_id)
            initial_quality = get_initial_quality_from_mastery(mastery)
        
            # Create initial SuperMemo state
            state = {
                "interval": 1,
                "repetition": 0,
                "efactor": 2.5,
                "last_review": str(today),
                "next_review": str(tomorrow),
                "quality": 3
            }
            
            review_history[vocab] = {
                "last_reviewed": str(today),
                "quality": initial_quality,
                "last_quality": initial_quality,
                "times_reviewed": 0,
                "times_skipped": 0
            }
            if mastery >= 0.7:
                supermemo_data["mastered"][vocab] = state
            else:
                supermemo_data["needs_practice"][vocab] = state
                updates_made = True
                print(f"[SuperMemo] Registered vocabulary '{vocab}' for user {user_id}")
                # Save updated data if changes were made
            if updates_made:
                usercol.update_one(
                    {"user_id": user_id},
                    {"$set": {"supermemo": supermemo_data, "review_history": review_history}}
                )
            
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
            
    # Fetch review history for quality lookup
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    review_history = user.get("review_history", {}) if user else {}

    review_questions = []
    used_ids = set()
    
    for vocab in vocab_list:
        # Get recent quality for this vocab (default to 1 if missing)
        quality = review_history.get(vocab, {}).get("quality", 1)
        # Map quality to target difficulty (clamp between 1 and 5)
        target_difficulty = max(1, min(5, int(quality)))
        # Select questions matching this difficulty
        questions = [q for q in all_questions if
                     q.get("vocabulary", "").lower() == vocab.lower() and
                     q.get("type") != "Lesson" and q.get("type") != "Image Picker" and q.get("type") != "Pronunciation" and
                     q.get("difficulty", 1) == target_difficulty]
        # Fallback: any question for this vocab
        if not questions:
            questions = [q for q in all_questions if
                         q.get("vocabulary", "").lower() == vocab.lower() and
                         q.get("type") != "Lesson" and q.get("type") != "Image Picker" and q.get("type") != "Pronunciation"]
        # Pick the first unused question
        for question in questions:
            if question.get('id') not in used_ids:
                review_questions.append(question)
                used_ids.add(question.get('id'))
                break  # Only one per vocab

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

def initialize_supermemo_state(mastery=0.5):
    today = datetime.now().date()
    quality = get_initial_quality_from_mastery(mastery)
    state = {
        "interval": 1,
        "repetition": 0,
        "efactor": 2.5,
        "last_review": str(today),
        "next_review": str(today + timedelta(days=1)),
        "quality": quality
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
            mastery = get_vocab_mastery(vocab, user_id=user_id)  # <-- Fetch mastery here
            needs_practice_states[vocab] = initialize_supermemo_state(mastery)

    mastered_states = supermemo_data.get("mastered", {})
    for vocab in mastered:
        if vocab not in mastered_states:
            mastery = get_vocab_mastery(vocab, user_id=user_id)  # <-- Fetch mastery here
            mastered_states[vocab] = initialize_supermemo_state(mastery)

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

def reset_outdated_review_dates(user_id):
    """Reset outdated dates for a specific user only"""
    try:
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": user_id})
        
        if not user or "supermemo" not in user:
            return
            
        # Only process this specific user
        supermemo_data = user["supermemo"]
        needs_practice = supermemo_data.get("needs_practice", {})
        mastered = supermemo_data.get("mastered", {})
        today = datetime.now().date()
        updated = False

        # Reset outdated next_review dates for needs_practice
        for vocab, state in needs_practice.items():
            try:
                next_review = datetime.fromisoformat(state.get("next_review", str(today))).date()
                if next_review < today:
                    print(f"[SuperMemo] Resetting next_review for '{vocab}' (was {next_review})")
                    state["next_review"] = str(today)
                    updated = True
            except Exception as e:
                print(f"[SuperMemo] Error parsing next_review for '{vocab}': {e}")

        # Reset outdated next_review dates for mastered
        for vocab, state in mastered.items():
            try:
                next_review = datetime.fromisoformat(state.get("next_review", str(today))).date()
                if next_review < today:
                    print(f"[SuperMemo] Resetting next_review for '{vocab}' (was {next_review})")
                    state["next_review"] = str(today)
                    updated = True
            except Exception as e:
                print(f"[SuperMemo] Error parsing next_review for '{vocab}': {e}")

        if updated:
            usercol.update_one(
                {"user_id": user_id},
                {"$set": {"supermemo.needs_practice": needs_practice, "supermemo.mastered": mastered}}
            )
        
    except Exception as e:
        print(f"[SuperMemo] Error resetting dates for user {user_id}: {e}")

def calculate_priority_score(vocab, state, review_history, days_overdue, bkt_proficiency, vocab_type):
    """Calculate priority score based on multiple factors"""
    vocab_history = review_history.get(vocab, {})
    
    # Get days since last reviewed
    last_reviewed = vocab_history.get("last_reviewed")
    if last_reviewed:
        days_since_last_review = (datetime.now().date() - datetime.fromisoformat(last_reviewed).date()).days
    else:
        days_since_last_review = 100
    
    # Get skip count
    times_skipped = vocab_history.get("times_skipped", 0)
    
    # Base priority calculation
    priority_score = (
        max(0, days_overdue) * 15 +           # Overdue penalty (increased weight)
        days_since_last_review * 3 +          # Recency factor
        times_skipped * 8 +                   # Skip penalty (increased)
        (25 if vocab_type == "needs_practice" else 5)  # Type bonus
    )
    
    # PROFICIENCY-BASED ADJUSTMENT
    # Lower proficiency = higher priority (inverse relationship)
    proficiency_factor = (1.0 - bkt_proficiency) * 20
    priority_score += proficiency_factor
    
    # EFactor consideration (lower EFactor = more difficult = higher priority)
    efactor = state.get("efactor", 2.5)
    efactor_factor = (2.5 - efactor) * 10  # Lower EFactor gets more priority
    priority_score += efactor_factor
    
    return priority_score

def select_balanced_review_items(candidates, max_questions):
    """Select review items with proficiency balance"""
    if len(candidates) <= max_questions:
        return candidates
    
    # Sort candidates into proficiency buckets
    low_prof = [c for c in candidates if c["bkt_proficiency"] < 0.4]      # Struggling
    med_prof = [c for c in candidates if 0.4 <= c["bkt_proficiency"] < 0.7]  # Learning  
    high_prof = [c for c in candidates if c["bkt_proficiency"] >= 0.7]    # Strong
    
    # Allocate slots: prioritize low proficiency, but include variety
    selected = []
    
    # 60% for low proficiency (struggling vocabs)
    low_slots = min(len(low_prof), max(1, int(max_questions * 0.6)))
    selected.extend(low_prof[:low_slots])
    
    # 30% for medium proficiency
    remaining_slots = max_questions - len(selected)
    med_slots = min(len(med_prof), max(0, int(remaining_slots * 0.75)))
    selected.extend(med_prof[:med_slots])
    
    # Remaining slots for high proficiency or overflow
    remaining_slots = max_questions - len(selected)
    if remaining_slots > 0:
        remaining_candidates = high_prof + low_prof[low_slots:] + med_prof[med_slots:]
        selected.extend(remaining_candidates[:remaining_slots])
    
    print(f"[PRIORITY] Selected: {len([s for s in selected if s['bkt_proficiency'] < 0.4])} low-prof, "
          f"{len([s for s in selected if 0.4 <= s['bkt_proficiency'] < 0.7])} med-prof, "
          f"{len([s for s in selected if s['bkt_proficiency'] >= 0.7])} high-prof")
    
    return selected[:max_questions]

def prepare_daily_review(user_id, threshold=0.85, max_questions=10):
    """Prepare daily review with proficiency-based selection"""
    # Reset any outdated review dates first
    reset_outdated_review_dates(user_id)

    # Get user data
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    supermemo_data = user.get("supermemo", {}) 
    review_history = user.get("review_history", {})
    
    # FIXED: Get BKT proficiency scores and convert to dictionary
    bkt_predictions = {}
    try:
        from bkt_engine import get_all_p_masteries, get_custom_bkt
        mastery_list = get_all_p_masteries(user_id)
        
        if mastery_list and isinstance(mastery_list, list):
            # Get vocabulary order to map list to dictionary
            custom_bkt = get_custom_bkt(user_id)
            if custom_bkt and hasattr(custom_bkt, 'get_vocabulary_in_order'):
                ordered_vocab = custom_bkt.get_vocabulary_in_order()
                if len(ordered_vocab) == len(mastery_list):
                    bkt_predictions = dict(zip(ordered_vocab, mastery_list))
                    print(f"[DEBUG] Created BKT predictions dict with {len(bkt_predictions)} items")
                else:
                    print(f"[DEBUG] Vocab count mismatch: {len(ordered_vocab)} vs {len(mastery_list)}")
            
        if not bkt_predictions:
            print("[DEBUG] Could not create BKT predictions dict, using empty dict")
            bkt_predictions = {}
            
    except Exception as e:
        print(f"[DEBUG] Error getting BKT predictions: {e}")
        bkt_predictions = {}
    
    today = datetime.now().date()
    review_candidates = []
    
    # Process needs_practice items (higher priority)
    for vocab, state in supermemo_data.get("needs_practice", {}).items():
        if vocab and state and "next_review" in state:
            try:
                review_date = datetime.fromisoformat(state["next_review"]).date()
                days_overdue = (today - review_date).days
                
                # FIXED: Now bkt_predictions is a dictionary
                bkt_proficiency = bkt_predictions.get(vocab, 0.3)  # Default low proficiency
                
                # Calculate enhanced priority score
                priority_score = calculate_priority_score(
                    vocab, state, review_history, days_overdue, bkt_proficiency, "needs_practice"
                )
                
                review_candidates.append({
                    "vocab": vocab,
                    "state": state,
                    "priority_score": priority_score,
                    "bkt_proficiency": bkt_proficiency,
                    "days_overdue": days_overdue,
                    "vocab_type": "needs_practice"
                })
                
            except (ValueError, TypeError) as e:
                print(f"[WARNING] Error processing {vocab}: {e}")
    
    # Process mastered items (lower priority unless overdue)
    for vocab, state in supermemo_data.get("mastered", {}).items():
        if vocab and state and "next_review" in state:
            try:
                review_date = datetime.fromisoformat(state["next_review"]).date()
                days_overdue = (today - review_date).days
                
                # Only include mastered items if they're significantly overdue
                if days_overdue >= 1:
                    bkt_proficiency = bkt_predictions.get(vocab, 0.8)  # Default high proficiency
                    
                    priority_score = calculate_priority_score(
                        vocab, state, review_history, days_overdue, bkt_proficiency, "mastered"
                    )
                    
                    review_candidates.append({
                        "vocab": vocab,
                        "state": state,
                        "priority_score": priority_score,
                        "bkt_proficiency": bkt_proficiency,
                        "days_overdue": days_overdue,
                        "vocab_type": "mastered"
                    })
                    
            except (ValueError, TypeError) as e:
                print(f"[WARNING] Error processing {vocab}: {e}")
    
    # Sort by priority score (highest first)
    review_candidates.sort(key=lambda x: x["priority_score"], reverse=True)
    
    # Select candidates with balanced proficiency distribution
    selected_candidates = select_balanced_review_items(review_candidates, max_questions)
    
    print(f"[DEBUG] Selected {len(selected_candidates)} items for review")
    print(f"[DEBUG] {len(review_candidates) - len(selected_candidates)} due items scheduled for later")
    
    # Generate questions
    vocab_list = [item["vocab"] for item in selected_candidates]
    if not vocab_list:
        return []
    
    proficiency = get_user_proficiency(user_id)
    review_questions = get_review_questions_for_user(user_id, vocab_list, proficiency)
    
    return review_questions

def mark_vocabulary_batch_reviewed(user_id, vocab_quality_map):
    """
    Process multiple vocabulary items in a single database operation
    
    Args:
        user_id: User ID
        vocab_quality_map: Dictionary mapping vocabulary words to quality scores
    """
    if not vocab_quality_map:
        return False
        
    try:
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": user_id})
        
        if not user:
            print(f"[ERROR] User {user_id} not found in database")
            return False
            
        # Get review history and SuperMemo data
        review_history = user.get("review_history", {})
        supermemo_data = user.get("supermemo", {})
        
        # Ensure structure exists
        if "needs_practice" not in supermemo_data:
            supermemo_data["needs_practice"] = {}
        if "mastered" not in supermemo_data:
            supermemo_data["mastered"] = {}
        
        # Prepare updates
        today = datetime.now().date()
        updates = {}
        
        # Track items that need to move categories
        move_to_mastered = []
        move_to_needs_practice = []
        
        # Track schedule changes for better visibility
        schedule_changes = []
        
        # Process each vocabulary
        for vocab, quality in vocab_quality_map.items():
            vocab = normalize_vocab(vocab)
            
            # Update review history
            if vocab not in review_history:
                review_history[vocab] = {}
                
            review_history[vocab]["last_reviewed"] = str(today)
            review_history[vocab]["quality"] = quality  # <-- Add this line
            review_history[vocab]["last_quality"] = quality
            review_history[vocab]["times_reviewed"] = review_history[vocab].get("times_reviewed", 0) + 1
            review_history[vocab]["times_skipped"] = 0
            
            # Update SuperMemo state and check for movement
            if vocab in supermemo_data.get("needs_practice", {}):
                state = supermemo_data["needs_practice"][vocab]
                old_next_review = state.get("next_review", "unknown")
                state = update_supermemo_state(state, quality)
                updates[f"supermemo.needs_practice.{vocab}"] = state
                
                # Track schedule change
                schedule_changes.append({
                    "vocab": vocab,
                    "category": "needs_practice",
                    "old_next_review": old_next_review,
                    "new_next_review": state["next_review"],
                    "interval": state["interval"],
                    "quality": quality
                })
                
                # Check if should move to mastered
                if state.get("should_move_to_mastered", False):
                    move_to_mastered.append((vocab, state))
                    
            elif vocab in supermemo_data.get("mastered", {}):
                state = supermemo_data["mastered"][vocab]
                old_next_review = state.get("next_review", "unknown")
                state = update_supermemo_state(state, quality)
                updates[f"supermemo.mastered.{vocab}"] = state
                
                # Track schedule change
                schedule_changes.append({
                    "vocab": vocab,
                    "category": "mastered",
                    "old_next_review": old_next_review,
                    "new_next_review": state["next_review"],
                    "interval": state["interval"],
                    "quality": quality
                })
                
                # Check if should move to needs practice
                if state.get("should_move_to_needs_practice", False):
                    move_to_needs_practice.append((vocab, state))
            else:
                # Vocabulary not in SuperMemo yet - shouldn't happen in batch review
                print(f"[WARNING] Vocabulary '{vocab}' not found in SuperMemo data during batch review")
        
        # Perform category movements
        for vocab, state in move_to_mastered:
            # Remove from needs_practice and add to mastered
            del supermemo_data["needs_practice"][vocab]
            clean_state = {k: v for k, v in state.items() if not k.startswith("should_move")}
            supermemo_data["mastered"][vocab] = clean_state
            updates[f"supermemo.mastered.{vocab}"] = clean_state
            updates[f"supermemo.needs_practice.{vocab}"] = None  # Mark for deletion
            print(f"[SUPERMEMO] ✅ Moved '{vocab}' from needs_practice to mastered")
        
        for vocab, state in move_to_needs_practice:
            # Remove from mastered and add to needs_practice
            del supermemo_data["mastered"][vocab]
            clean_state = {k: v for k, v in state.items() if not k.startswith("should_move")}
            supermemo_data["needs_practice"][vocab] = clean_state
            updates[f"supermemo.needs_practice.{vocab}"] = clean_state
            updates[f"supermemo.mastered.{vocab}"] = None  # Mark for deletion
            print(f"[SUPERMEMO] ⚠️ Moved '{vocab}' from mastered to needs_practice")
        
        # Add review history to updates
        updates["review_history"] = review_history
        
        # Apply all updates at once (set operations)
        if updates:
            usercol.update_one(
                {"user_id": user_id},
                {"$set": {k: v for k, v in updates.items() if v is not None}}
            )
        
        # Apply deletions (unset operations) - separate operation required
        delete_ops = {k: "" for k, v in updates.items() if v is None}
        if delete_ops:
            usercol.update_one(
                {"user_id": user_id},
                {"$unset": delete_ops}
            )
        
        # Display schedule summary
        print("\n=== SUPERMEMO BATCH UPDATE SUMMARY ===")
        print(f"Processed {len(vocab_quality_map)} vocabulary items")
        
        if schedule_changes:
            print("\nSchedule Changes:")
            for change in schedule_changes:
                interval_text = f"{change['interval']} day{'s' if change['interval'] != 1 else ''}"
                print(f"  • {change['vocab']} ({change['category']}): Q{change['quality']} → next review {change['new_next_review']} ({interval_text})")
        
        if move_to_mastered:
            print(f"\n✅ Promoted to mastered: {', '.join([vocab for vocab, _ in move_to_mastered])}")
        
        if move_to_needs_practice:
            print(f"\n⚠️ Demoted to needs_practice: {', '.join([vocab for vocab, _ in move_to_needs_practice])}")
        
        print("=====================================\n")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error in batch update: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def mark_vocabulary_reviewed(user_id, vocab, performance_quality):
    """
    Mark a vocabulary item as reviewed with its quality rating
    
    Args:
        user_id: The user who completed the review
        vocab: The vocabulary word that was reviewed
        performance_quality: Quality rating (0-5) of recall, where 5 is perfect recall
    """
    vocab = normalize_vocab(vocab)
    print(f"[SuperMemo] Marking '{vocab}' as reviewed with quality {performance_quality}")
    
    try:
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
        review_history[vocab]["quality"] = performance_quality  # <-- Add this line
        
        # Reset skip counter since item was reviewed
        review_history[vocab]["times_skipped"] = 0
        
        # Batch update in database - combine with SuperMemo state update
        # to reduce database operations
        
        # Get current SuperMemo state
        supermemo_data = user.get("supermemo", {})
        updates = {"review_history": review_history}
        
        # Update SuperMemo state based on performance
        vocab_updated = False
        
        # Check if in needs_practice or mastered
        if vocab in supermemo_data.get("needs_practice", {}):
            state = supermemo_data["needs_practice"][vocab]
            # Update the state
            state = update_supermemo_state(state, performance_quality)
            # Add to updates
            updates[f"supermemo.needs_practice.{vocab}"] = state
            vocab_updated = True
            
        elif vocab in supermemo_data.get("mastered", {}):
            state = supermemo_data["mastered"][vocab]
            # Update the state
            state = update_supermemo_state(state, performance_quality)
            # Add to updates
            updates[f"supermemo.mastered.{vocab}"] = state
            vocab_updated = True
            
        # Apply all updates at once
        usercol.update_one(
            {"user_id": user_id},
            {"$set": updates}
        )
        
        if not vocab_updated:
            print(f"[WARNING] Vocabulary '{vocab}' not found in SuperMemo data")
            
        return True
        
    except Exception as e:
        print(f"[ERROR] Error updating vocabulary '{vocab}': {str(e)}")
        return False

def mark_vocabulary_batch_reviewed(user_id, vocab_quality_map):
    """
    Process multiple vocabulary items in a single database operation
    
    Args:
        user_id: User ID
        vocab_quality_map: Dictionary mapping vocabulary words to quality scores
    """
    if not vocab_quality_map:
        return
        
    try:
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": user_id})
        
        if not user:
            print(f"[ERROR] User {user_id} not found in database")
            return False
            
        # Get review history and SuperMemo data
        review_history = user.get("review_history", {})
        supermemo_data = user.get("supermemo", {})
        
        # Prepare updates
        today = datetime.now().date()
        updates = {}
        
        # Process each vocabulary
        for vocab, quality in vocab_quality_map.items():
            vocab = normalize_vocab(vocab)
            
            # Update review history
            if vocab not in review_history:
                review_history[vocab] = {}
                
            review_history[vocab]["last_reviewed"] = str(today)
            review_history[vocab]["last_quality"] = quality
            review_history[vocab]["times_skipped"] = 0
            
            # Update SuperMemo state
            if vocab in supermemo_data.get("needs_practice", {}):
                state = supermemo_data["needs_practice"][vocab]
                state = update_supermemo_state(state, quality)
                updates[f"supermemo.needs_practice.{vocab}"] = state
                
            elif vocab in supermemo_data.get("mastered", {}):
                state = supermemo_data["mastered"][vocab]
                state = update_supermemo_state(state, quality)
                updates[f"supermemo.mastered.{vocab}"] = state
        
        # Add review history to updates
        updates["review_history"] = review_history
        
        # Apply all updates at once
        usercol.update_one(
            {"user_id": user_id},
            {"$set": updates}
        )
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error in batch update: {str(e)}")
        return False

def update_vocab_supermemo_state(user_id, vocab, quality):
    """Update SuperMemo state for a specific vocabulary item based on review quality"""
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    
    if not user or "supermemo" not in user:
        print(f"[ERROR] User {user_id} not found or has no SuperMemo data")
        return False
        
    supermemo_data = user["supermemo"]
    
    # Check if in needs_practice or mastered
    vocab = normalize_vocab(vocab)
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
    """Update SuperMemo state with enhanced category movement logic"""
    assert 0 <= quality <= 5
    efactor = state.get("efactor", 2.5)
    repetition = state.get("repetition", 0)
    interval = state.get("interval", 1)
    consecutive_correct = state.get("consecutive_correct", 0)

    if quality < 3:
        repetition = 0
        interval = 1
        consecutive_correct = 0
    else:
        if repetition == 0:
            interval = 1
        elif repetition == 1:
            interval = 6
        else:
            interval = int(interval * efactor)
        repetition += 1
        consecutive_correct += 1

    # Update efactor with more sensitivity
    efactor = efactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if efactor < 1.3:
        efactor = 1.3

    # Enhanced interval capping with quality consideration
    MAX_INTERVAL = 7 if quality >= 4 else 5
    if interval > MAX_INTERVAL:
        interval = MAX_INTERVAL

    today = datetime.now().date()
    next_review_date = today + timedelta(days=interval)
    
    state.update({
        "interval": interval,
        "repetition": repetition,
        "efactor": efactor,
        "last_review": str(today),
        "next_review": str(next_review_date),
        "consecutive_correct": consecutive_correct,
        "recent_quality": quality
    })
    
    # ENHANCED CATEGORY MOVEMENT LOGIC
    # Move to mastered: require more evidence of mastery
    state["should_move_to_mastered"] = (
        consecutive_correct >= 4 and  # Increased from 3
        quality >= 4 and 
        efactor >= 2.3 and  # Slightly higher threshold
        repetition >= 3  # Must have some repetition history
    )
    
    # Move to needs practice: more forgiving, focus on recent performance
    state["should_move_to_needs_practice"] = (
        quality <= 2 or 
        (efactor <= 1.5 and consecutive_correct == 0) or
        (quality <= 3 and efactor <= 1.6 and repetition >= 2)  # Struggling repeatedly
    )
    
    return state

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

# Add to supermemo_engine.py
def normalize_vocab(vocabulary):
    """Normalize vocabulary to prevent case-sensitive duplicates"""
    if not vocabulary:
        return None
    return vocabulary.lower().strip()

def merge_duplicate_vocab_entries(user_id):
    """Find and merge vocabulary entries that differ only by capitalization"""
    print(f"[SuperMemo] Checking for duplicate vocabulary entries for user {user_id}")
    
    # Connect to MongoDB
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_id": user_id})
    if not user or "supermemo" not in user:
        print(f"[SuperMemo] No SuperMemo data found for user {user_id}")
        return False
        
    supermemo_data = user["supermemo"]
    needs_practice = supermemo_data.get("needs_practice", {})
    mastered = supermemo_data.get("mastered", {})
    
    # Create temporary dictionaries using normalized case
    normalized_needs_practice = {}
    normalized_mastered = {}
    
    # Track changes that need to be made
    changes_needed = False
    
    # Process needs_practice entries
    for vocab, state in needs_practice.items():
        normalized = normalize_vocab(vocab)
        if normalized in normalized_needs_practice:
            print(f"[SuperMemo] Found duplicate in needs_practice: '{vocab}' and '{normalized}'")
            changes_needed = True
            # Keep entry with latest review date or higher EFactor
            existing = normalized_needs_practice[normalized]
            if compare_states(state, existing):
                normalized_needs_practice[normalized] = state
        else:
            normalized_needs_practice[normalized] = state
            
    # Process mastered entries
    for vocab, state in mastered.items():
        normalized = normalize_vocab(vocab)
        if normalized in normalized_mastered:
            print(f"[SuperMemo] Found duplicate in mastered: '{vocab}' and '{normalized}'")
            changes_needed = True
            # Keep entry with latest review date or higher EFactor
            existing = normalized_mastered[normalized]
            if compare_states(state, existing):
                normalized_mastered[normalized] = state
        else:
            normalized_mastered[normalized] = state
    
    # Check for duplicates across categories
    for vocab in list(normalized_needs_practice.keys()):
        if vocab in normalized_mastered:
            print(f"[SuperMemo] Found duplicate across categories: '{vocab}'")
            changes_needed = True
            # Keep in mastered if mastery is high, otherwise in needs_practice
            needs_practice_state = normalized_needs_practice[vocab]
            mastered_state = normalized_mastered[vocab]
            if compare_states(mastered_state, needs_practice_state):
                # Mastered entry is better, remove from needs_practice
                del normalized_needs_practice[vocab]
            else:
                # Needs practice entry is better, remove from mastered
                del normalized_mastered[vocab]
    
    # If changes needed, update the database
    if changes_needed:
        print(f"[SuperMemo] Updating user {user_id} with merged vocabulary data")
        supermemo_data["needs_practice"] = normalized_needs_practice
        supermemo_data["mastered"] = normalized_mastered
        usercol.update_one(
            {"user_id": user_id},
            {"$set": {"supermemo": supermemo_data}}
        )
        return True
    else:
        print(f"[SuperMemo] No duplicate entries found for user {user_id}")
        return False

def compare_states(state1, state2):
    """Compare two SuperMemo states to determine which is more advantageous
    Returns True if state1 is better than state2, False otherwise"""
    
    # If one has a later review date, it's more up-to-date
    try:
        date1 = datetime.strptime(state1.get("last_review", "2000-01-01"), "%Y-%m-%d").date()
        date2 = datetime.strptime(state2.get("last_review", "2000-01-01"), "%Y-%m-%d").date()
        if date1 > date2:
            return True
        if date2 > date1:
            return False
    except (ValueError, TypeError):
        pass  # If dates can't be compared, fall back to other criteria
    
    # Higher EFactor is better (stronger memory)
    if state1.get("efactor", 0) > state2.get("efactor", 0):
        return True
    
    # Higher repetition count is better
    if state1.get("repetition", 0) > state2.get("repetition", 0):
        return True
        
    # Default to state2 if no clear winner
    return False

# Add these functions if they don't exist

def get_average_efactor(user_id):
    """Get average efactor only if user has completed reviews"""
    try:
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": user_id})
        
        if user:
            review_history = user.get("review_history", {})
            
            # Check if any vocabulary has actually been reviewed
            total_reviews = 0
            total_efactor = 0
            
            for vocab, data in review_history.items():
                times_reviewed = data.get("times_reviewed", 0)
                if times_reviewed > 0:  # Only count if actually reviewed
                    efactor = data.get("efactor", 2.5)
                    total_efactor += efactor
                    total_reviews += 1
            
            if total_reviews > 0:
                avg_efactor = total_efactor / total_reviews
                print(f"[SuperMemo] Average efactor from {total_reviews} reviewed items: {avg_efactor:.3f}")
                return avg_efactor
            else:
                print(f"[SuperMemo] No items have been reviewed yet")
                return None  # Return None instead of default value
                
    except Exception as e:
        print(f"[SuperMemo] Error getting average efactor: {e}")
    
    return None  # Return None instead of default value

def get_completion_rate(user_id):
    """
    Get vocabulary completion rate based on mastered vs. total
    
    Returns:
        Completion rate (0-1)
    """
    try:
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": int(user_id)})
        
        if not user or "supermemo" not in user:
            return 0
            
        supermemo_data = user["supermemo"]
        mastered_count = len(supermemo_data.get("mastered", {}))
        needs_practice_count = len(supermemo_data.get("needs_practice", {}))
        
        total = mastered_count + needs_practice_count
        
        if total == 0:
            return 0
            
        return mastered_count / total
        
    except Exception as e:
        print(f"[SuperMemo] Error getting completion rate: {e}")
        return 0
    
def reset_user_outdated_dates(user_id):
    """Reset outdated dates for a specific user only"""
    try:
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": user_id})
        
        if not user or "supermemo" not in user:
            return
            
        # Only process this specific user
        # ... reset logic for single user only
        
    except Exception as e:
        print(f"[SuperMemo] Error resetting dates for user {user_id}: {e}")

# Add this function to reviewFrame.py after the imports
def calculate_dynamic_quality(user_id, question_data, is_correct, response_time=None, review_history=None, is_daily_review=False):
    """Calculate SuperMemo quality with moderated scoring for daily reviews"""
    vocab = getattr(question_data, 'vocabulary', None)
    if not vocab:
        return 3 if is_correct else 2  # More moderate defaults
    
    vocab = vocab.lower().strip()
    difficulty = getattr(question_data, 'difficulty', 2)
    question_type = getattr(question_data, 'type', 'Unknown')
    
    # Get BKT proficiency for this vocabulary
    try:
        from bkt_engine import get_vocab_mastery
        vocab_mastery = get_vocab_mastery(vocab, user_id=user_id)
    except:
        vocab_mastery = 0.5
    
    # Get user's review history for this vocab
    if not review_history:
        try:
            from bkt_engine import connect_to_mongoDB
            usercol = connect_to_mongoDB()
            user = usercol.find_one({"user_id": user_id})
            review_history = user.get("review_history", {}).get(vocab, {}) if user else {}
        except:
            review_history = {}
    
    times_reviewed = review_history.get("times_reviewed", 0)
    last_quality = review_history.get("quality", 3)
    
    print(f"[QUALITY] Calculating for '{vocab}': correct={is_correct}, difficulty={difficulty}, mastery={vocab_mastery:.2f}, daily_review={is_daily_review}")
    
    # MODERATED BASE QUALITY for daily reviews
    if is_daily_review:
        # More conservative quality range for daily reviews (2-4 instead of 0-5)
        base_quality = 3.5 if is_correct else 2.5
        print(f"[QUALITY] Daily review mode - using moderated base quality: {base_quality}")
    else:
        # Full range for lessons (0-5)
        base_quality = 4 if is_correct else 1
    
    # FACTOR 1: Response Time Analysis (reduced impact for daily reviews)
    time_factor = 0
    time_weight = 0.5 if is_daily_review else 1.0  # Reduce time factor impact for daily reviews
    
    if response_time is not None:
        expected_times = {
            'True or False': 3.0,
            'Word Select': 4.0,
            'Image Picker': 5.0,
            'Translate Sentence': 8.0,
            'Pronunciation': 6.0,
            'Lesson': 10.0
        }
        
        expected_time = expected_times.get(question_type, 5.0)
        time_ratio = response_time / expected_time
        
        if time_ratio <= 0.5:
            time_factor = +1 * time_weight
            print(f"[QUALITY] Fast response: +{time_factor}")
        elif time_ratio <= 1.0:
            time_factor = 0
            print(f"[QUALITY] Normal response time: +{time_factor}")
        elif time_ratio <= 2.0:
            time_factor = -0.5 * time_weight  # Reduced penalty for daily reviews
            print(f"[QUALITY] Slow response: {time_factor}")
        else:
            time_factor = -1 * time_weight  # Reduced penalty for daily reviews
            print(f"[QUALITY] Very slow response ({response_time:.1f}s): {time_factor}")
    else:
        print(f"[QUALITY] Normal response time: +0")
    
    # FACTOR 2: Difficulty vs Mastery (reduced impact for daily reviews)
    difficulty_factor = 0
    difficulty_weight = 0.5 if is_daily_review else 1.0
    
    if is_correct:
        if difficulty >= 4 and vocab_mastery < 0.5:
            difficulty_factor = +1 * difficulty_weight
            print(f"[QUALITY] Hard question with low mastery: +{difficulty_factor}")
        elif difficulty <= 2 and vocab_mastery > 0.8:
            difficulty_factor = -0.5 * difficulty_weight  # Reduced penalty
            print(f"[QUALITY] Easy question for high mastery: {difficulty_factor}")
    else:
        if difficulty <= 2:
            difficulty_factor = -1 * difficulty_weight  # Reduced penalty for daily reviews
            print(f"[QUALITY] Failed easy question: {difficulty_factor}")
        elif difficulty >= 4:
            difficulty_factor = +0.5 * difficulty_weight
            print(f"[QUALITY] Failed hard question: +{difficulty_factor}")
    
    # FACTOR 3: Learning Progression (same logic but reduced impact)
    progression_factor = 0
    progression_weight = 0.7 if is_daily_review else 1.0
    
    if times_reviewed > 0:
        if is_correct and last_quality <= 2:
            progression_factor = +0.5 * progression_weight
            print(f"[QUALITY] Improved from poor performance: +{progression_factor}")
        elif not is_correct and last_quality >= 4:
            progression_factor = -1 * progression_weight
            print(f"[QUALITY] Regressed from good performance: {progression_factor}")
        elif is_correct and times_reviewed >= 3 and last_quality >= 4:
            progression_factor = +0.5 * progression_weight
            print(f"[QUALITY] Consistent good performance: +{progression_factor}")
    
    # Calculate final quality with moderation
    final_quality = base_quality + time_factor + difficulty_factor + progression_factor
    
    # CRITICAL: Different clamping for daily reviews vs lessons
    if is_daily_review:
        final_quality = max(2, min(4, final_quality))  # Clamp to 2-4 for daily reviews
        print(f"[QUALITY] Daily review final (clamped 2-4): {final_quality}")
    else:
        final_quality = max(0, min(5, final_quality))  # Full range for lessons
        print(f"[QUALITY] Lesson final (clamped 0-5): {final_quality}")
    
    print(f"[QUALITY] Final calculation: base={base_quality} + time={time_factor} + difficulty={difficulty_factor} + progression={progression_factor} = {final_quality}")
    
    return int(round(final_quality))  # Return integer quality