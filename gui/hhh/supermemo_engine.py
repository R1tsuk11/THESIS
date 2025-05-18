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

def prepare_daily_review(user_id, threshold=0.85, max_questions=10):
    print(f"[DEBUG] Preparing daily review for user: {user_id}")
    predictions = get_all_bkt_predictions(user_id)
    needs_practice, mastered = prioritize_vocabularies(predictions, threshold=threshold)
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
            if datetime.fromisoformat(state["next_review"]).date() <= today:
                review_items.append((vocab, state))
        print(f"[DEBUG] Vocabularies due for review: {review_items}")
        review_items = review_items[:max_questions]

    print(f"[DEBUG] Final review_items to return: {review_items}")
    vocab_list = [vocab for vocab, state in review_items]
    review_questions = get_questions_for_vocab_list(vocab_list)
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