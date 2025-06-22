"""
Test script to verify that the lesson BKT engine works correctly
and that data is merged (not overwritten) in the database.
"""

import os
import json
import sys
import time
import pymongo
from pprint import pprint

# Import both BKT engines for testing
from lesson_bkt_engine import (
    run_lesson_bkt_and_get_sequence,
    create_or_get_session,
    process_lesson_question,
    update_session_bkt,
    save_session_to_database,
    get_session_bkt_sequence,
    clear_session
)
from bkt_engine import update_bkt, display_bkt_predictions

# MongoDB connection string
uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

def get_user_bkt_data(user_id):
    """Retrieve user BKT data from the database"""
    try:
        arami = pymongo.MongoClient(uri)["arami"]
        users_col = arami["users"]
        user_doc = users_col.find_one({"user_id": int(user_id)})
        if user_doc and "bkt_data" in user_doc:
            return user_doc["bkt_data"]
        return None
    except Exception as e:
        print(f"Error retrieving user BKT data: {e}")
        return None

def print_bkt_predictions(user_id):
    """Print the BKT predictions for a user"""
    try:
        arami = pymongo.MongoClient(uri)["arami"]
        users_col = arami["users"]
        user_doc = users_col.find_one({"user_id": int(user_id)})
        if user_doc and "bkt_data" in user_doc and "predictions" in user_doc["bkt_data"]:
            predictions = user_doc["bkt_data"]["predictions"]
            print(f"\nBKT Predictions for User {user_id}:")
            print("-" * 60)
            print(f"{'Vocabulary':<20} | {'Mastery':<8} | {'Confidence':<10} | {'Reviewed'}")
            print("-" * 60)
            
            for vocab, data in sorted(predictions.items()):
                mastery = data.get("p_mastery", 0.5)
                confidence = data.get("confidence", 0.0)
                reviewed = "Yes" if data.get("reviewed", False) else "No"
                print(f"{vocab:<20} | {mastery:<8.3f} | {confidence:<10.3f} | {reviewed}")
            
            print("-" * 60)
        else:
            print(f"No BKT predictions found for user {user_id}")
    except Exception as e:
        print(f"Error printing predictions: {e}")

def test_old_bkt_engine(user_id):
    """Test the old BKT engine"""
    print("\n==== Testing Original BKT Engine ====")
    
    # Create sample questions
    correct_answers = {
        "q1": {"question": "What is 'hello' in Spanish?", "answer": "hola", "vocabulary": "hola"},
        "q2": {"question": "What is 'goodbye' in Spanish?", "answer": "adiós", "vocabulary": "adiós"}
    }
    
    incorrect_answers = {
        "q3": {"question": "What is 'thank you' in Spanish?", "answer": "gracias", "vocabulary": "gracias"}
    }
    
    # Get BKT data before update
    print("\nBKT data BEFORE update:")
    before_data = get_user_bkt_data(user_id)
    if before_data and "predictions" in before_data:
        print(f"Found {len(before_data['predictions'])} predictions before update")
    else:
        print("No existing predictions found")
    
    # Run BKT update
    bkt_sequence = update_bkt(user_id, correct_answers, incorrect_answers)
    
    print(f"\nGenerated BKT sequence with {len(bkt_sequence)} values")
    
    # Get BKT data after update
    print("\nBKT data AFTER update:")
    after_data = get_user_bkt_data(user_id)
    if after_data and "predictions" in after_data:
        print(f"Found {len(after_data['predictions'])} predictions after update")
    else:
        print("No predictions found after update")

    # Display BKT predictions
    display_bkt_predictions(user_id)

def test_lesson_bkt_engine(user_id):
    """Test the new lesson BKT engine"""
    print("\n==== Testing New Lesson BKT Engine ====")
    
    # Create sample questions
    correct_answers = {
        "q1": {"question": "What is 'cat' in Spanish?", "answer": "gato", "vocabulary": "gato"},
        "q2": {"question": "What is 'dog' in Spanish?", "answer": "perro", "vocabulary": "perro"}
    }
    
    incorrect_answers = {
        "q3": {"question": "What is 'bird' in Spanish?", "answer": "pájaro", "vocabulary": "pájaro"}
    }
    
    # Get BKT data before update
    print("\nBKT data BEFORE update:")
    before_data = get_user_bkt_data(user_id)
    if before_data and "predictions" in before_data:
        print(f"Found {len(before_data['predictions'])} predictions before update")
        # Print a few examples
        vocab_sample = list(before_data["predictions"].keys())[:3]
        for v in vocab_sample:
            print(f"  - {v}: mastery = {before_data['predictions'][v].get('p_mastery', 0.5):.3f}")
    else:
        print("No existing predictions found")
    
    # Test individual session management functions
    session = create_or_get_session(user_id, session_id="test_session")
    
    for key, question in correct_answers.items():
        process_lesson_question(user_id, key, question, True, session_id="test_session")
    
    for key, question in incorrect_answers.items():
        process_lesson_question(user_id, key, question, False, session_id="test_session")
    
    update_session_bkt(user_id, session_id="test_session")
    save_session_to_database(user_id, session_id="test_session")
    
    # Get BKT sequence
    bkt_sequence = get_session_bkt_sequence(user_id, session_id="test_session")
    clear_session(user_id, session_id="test_session")
    
    # Now test the integrated function
    print("\nTesting integrated run_lesson_bkt_and_get_sequence function...")
    integrated_sequence = run_lesson_bkt_and_get_sequence(
        user_id, correct_answers, incorrect_answers, impact_scale=1.0)
    
    print(f"Generated BKT sequence with {len(integrated_sequence)} values")
    print(f"Non-default values: {sum(1 for x in integrated_sequence if x != 0.5)}/{len(integrated_sequence)}")
    
    # Get BKT data after update
    print("\nBKT data AFTER update:")
    after_data = get_user_bkt_data(user_id)
    if after_data and "predictions" in after_data:
        print(f"Found {len(after_data['predictions'])} predictions after update")
        # Check if new vocabulary was added
        new_vocab = set(after_data["predictions"].keys()) - set(before_data["predictions"].keys() if before_data and "predictions" in before_data else [])
        print(f"New vocabulary added: {', '.join(sorted(new_vocab)) if new_vocab else 'None'}")
        
        # Check if session history was recorded
        if "session_history" in after_data:
            print(f"Session history entries: {len(after_data['session_history'])}")
            if after_data["session_history"]:
                last_session = after_data["session_history"][-1]
                print(f"Latest session: {last_session['correct_count']} correct, {last_session['incorrect_count']} incorrect")
    else:
        print("No predictions found after update")
    
    # Display predictions
    print_bkt_predictions(user_id)

def check_data_merging(user_id):
    """Verify that data is merged, not overwritten"""
    print("\n==== Checking Data Merging ====")
    
    # Get current data
    before_data = get_user_bkt_data(user_id)
    if not before_data or "predictions" not in before_data:
        print("No existing predictions found, cannot test merging")
        return
    
    existing_count = len(before_data["predictions"])
    print(f"Found {existing_count} existing predictions")
    
    # Create unique new vocabulary for this test
    test_vocab = f"test_vocab_{int(time.time())}"
    
    # Create sample questions with the unique vocabulary
    correct_answers = {
        "q1": {"question": f"What is '{test_vocab}'?", "answer": "test", "vocabulary": test_vocab}
    }
    
    incorrect_answers = {}
    
    # Run lesson BKT engine
    print(f"Running lesson BKT engine with new vocabulary '{test_vocab}'...")
    run_lesson_bkt_and_get_sequence(user_id, correct_answers, incorrect_answers)
    
    # Check if data was merged
    after_data = get_user_bkt_data(user_id)
    if not after_data or "predictions" not in after_data:
        print("No predictions found after update, merging failed")
        return
    
    after_count = len(after_data["predictions"])
    
    # Check if the new vocabulary was added
    new_vocab_found = test_vocab in after_data["predictions"]
    
    # Verify other vocabulary still exists
    existing_vocab = list(before_data["predictions"].keys())[:5]  # Get a few examples
    still_exist = all(v in after_data["predictions"] for v in existing_vocab)
    
    print("\nMerging Test Results:")
    print(f"- Before count: {existing_count}")
    print(f"- After count: {after_count}")
    print(f"- New vocabulary '{test_vocab}' added: {new_vocab_found}")
    print(f"- Existing vocabulary preserved: {still_exist}")
    
    if new_vocab_found and still_exist and after_count >= existing_count:
        print("\n✅ SUCCESS: Data was properly merged, not overwritten!")
    else:
        print("\n❌ FAILURE: Data merging test failed!")

def test_difficulty_transfer(user_id):
    """Test if difficulty transfers between vocabulary items"""
    print("\n==== Testing Difficulty Transfer ====")
    
    # Create a new session
    session_id = f"difficulty_test_{int(time.time())}"
    session = create_or_get_session(user_id, session_id=session_id)
    
    # Add correct and incorrect answers to see difficulty adjustments
    test_vocab_1 = f"diff_test_1_{int(time.time())}"
    test_vocab_2 = f"diff_test_2_{int(time.time())}"
    
    # Create questions
    q1 = {"question": f"What is '{test_vocab_1}'?", "answer": "test1", "vocabulary": test_vocab_1}
    q2 = {"question": f"What is '{test_vocab_2}'?", "answer": "test2", "vocabulary": test_vocab_2}
    
    # First add multiple correct answers to decrease difficulty
    print(f"Adding correct answers for '{test_vocab_1}'...")
    for i in range(3):
        process_lesson_question(user_id, f"q{i+1}", q1, True, session_id=session_id)
    
    # Then get the difficulty factor
    update_session_bkt(user_id, session_id=session_id)
    diff_1 = session.get_difficulty_factor(test_vocab_1)
    print(f"Difficulty factor for '{test_vocab_1}' after correct answers: {diff_1:.2f}")
    
    # Now add incorrect answers for the second vocabulary
    print(f"Adding incorrect answers for '{test_vocab_2}'...")
    for i in range(2):
        process_lesson_question(user_id, f"q{i+4}", q2, False, session_id=session_id)
    
    # Update BKT and get difficulty
    update_session_bkt(user_id, session_id=session_id)
    diff_2 = session.get_difficulty_factor(test_vocab_2)
    print(f"Difficulty factor for '{test_vocab_2}' after incorrect answers: {diff_2:.2f}")
    
    # Save to database and clean up
    save_session_to_database(user_id, session_id=session_id)
    clear_session(user_id, session_id=session_id)
    
    print("\nDifficulty Transfer Results:")
    print(f"- '{test_vocab_1}' difficulty factor: {diff_1:.2f} (expected < 1.0 after correct answers)")
    print(f"- '{test_vocab_2}' difficulty factor: {diff_2:.2f} (expected > 1.0 after incorrect answers)")
    
    if diff_1 < 1.0 and diff_2 > 1.0:
        print("\n✅ SUCCESS: Difficulty factors adjust as expected!")
    else:
        print("\n❌ FAILURE: Difficulty adjustment test failed!")

def test_bkt_sequence_for_lstm(user_id):
    """Test generating BKT sequence for LSTM input"""
    print("\n==== Testing BKT Sequence for LSTM ====")
    
    # Create sample questions
    vocab_list = ["manzana", "naranja", "plátano", "uva", "fresa"]
    correct_answers = {}
    incorrect_answers = {}
    
    # Add some correct and incorrect answers
    for i, vocab in enumerate(vocab_list):
        if i % 2 == 0:
            correct_answers[f"q{i+1}"] = {
                "question": f"What is '{vocab}' in English?", 
                "answer": "fruit", 
                "vocabulary": vocab
            }
        else:
            incorrect_answers[f"q{i+1}"] = {
                "question": f"What is '{vocab}' in English?", 
                "answer": "fruit", 
                "vocabulary": vocab
            }
    
    # Get sequence before update
    before_data = get_user_bkt_data(user_id)
    
    # Run the integrated function
    print("Generating BKT sequence for LSTM...")
    bkt_sequence = run_lesson_bkt_and_get_sequence(
        user_id, correct_answers, incorrect_answers)
    
    print(f"Generated BKT sequence with {len(bkt_sequence)} values")
    print(f"Sample sequence values: {bkt_sequence[:10]}")
    
    # Check for non-default values
    non_default = sum(1 for x in bkt_sequence if abs(x - 0.5) > 0.01)
    print(f"Non-default values in sequence: {non_default}/{len(bkt_sequence)}")
    
    if non_default > 0:
        print("\n✅ SUCCESS: BKT sequence has valid values for LSTM!")
    else:
        print("\n❌ WARNING: BKT sequence contains only default values!")

def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python test_bkt_integration.py <user_id>")
        sys.exit(1)
    
    user_id = int(sys.argv[1])
    print(f"Testing BKT integration for user {user_id}")
    
    # Print initial state
    print("\nInitial BKT state:")
    print_bkt_predictions(user_id)
    
    # Run all tests
    test_old_bkt_engine(user_id)
    test_lesson_bkt_engine(user_id)
    check_data_merging(user_id)
    test_difficulty_transfer(user_id)
    test_bkt_sequence_for_lstm(user_id)
    
    print("\n==== Testing Completed ====")
    print("You should review the results above to verify that:")
    print("1. BKT data is merged (not overwritten) in the database")
    print("2. Difficulty transfer between vocabulary items works")
    print("3. In-session BKT sequence is correctly merged with database data")
    print("4. Daily review logic remains unchanged and functional")
    print("5. The system generates valid BKT sequences for LSTM input")

if __name__ == "__main__":
    main()
