"""
Test the integration of the lesson BKT engine with the main workflow
"""

import json
import os
import sys
from types import SimpleNamespace
import time

# Local imports
from lesson_bkt_engine import run_lesson_bkt_and_get_sequence
from levels import run_bkt_and_lstm

class MockPage:
    def __init__(self):
        self.session = {}
    
    def update(self):
        pass

class Session:
    def __init__(self):
        self.data = {}
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def set(self, key, value):
        self.data[key] = value
        print(f"[Session] Set {key} = {value}")

def create_test_data():
    """Create test data for the integration test"""
    # Create mock correct and incorrect answers
    correct_answers = {
        "q1": {"question": "What is 'apple' in Spanish?", "answer": "manzana", "vocabulary": "manzana"},
        "q2": {"question": "What is 'dog' in Spanish?", "answer": "perro", "vocabulary": "perro"}
    }
    
    incorrect_answers = {
        "q3": {"question": "What is 'cat' in Spanish?", "answer": "gato", "vocabulary": "gato"}
    }
    
    return correct_answers, incorrect_answers

def test_lesson_workflow(user_id):
    """Test the lesson workflow with run_bkt_and_lstm"""
    print("\n==== Testing Lesson Workflow ====")
    
    # Create mock page and session
    page = MockPage()
    page.session = Session()
    page.session.data["user_id"] = user_id
    
    # Set completion percentage
    completion = 50  # 50% completion
    
    # Create test data
    correct_answers, incorrect_answers = create_test_data()
    
    print(f"Testing run_bkt_and_lstm for user {user_id} with lesson mode (is_daily_review=False)")
    start_time = time.time()
    run_bkt_and_lstm(page, completion, user_id, correct_answers, incorrect_answers, is_daily_review=False)
    end_time = time.time()
    
    print(f"Lesson workflow completed in {end_time - start_time:.2f} seconds")
    
    # Print final session values
    print("\nFinal session values:")
    for key in ["proficiency", "lstm_raw_confidence", "proficiency_confidence", "system_confidence"]:
        print(f"- {key}: {page.session.get(key)}")
    
    # Return success if we have a proficiency value
    return page.session.get("proficiency") is not None

def test_daily_review_workflow(user_id):
    """Test the daily review workflow with run_bkt_and_lstm"""
    print("\n==== Testing Daily Review Workflow ====")
    
    # Create mock page and session
    page = MockPage()
    page.session = Session()
    page.session.data["user_id"] = user_id
    
    # Set completion percentage
    completion = 50  # 50% completion
    
    # Create test data
    correct_answers, incorrect_answers = create_test_data()
    
    # Set daily review questions
    page.session.set("daily_review_questions", [
        {"question": "What is 'apple' in Spanish?", "answer": "manzana", "vocabulary": "manzana", "type": "vocab"},
        {"question": "What is 'dog' in Spanish?", "answer": "perro", "vocabulary": "perro", "type": "vocab"},
    ])
    
    print(f"Testing run_bkt_and_lstm for user {user_id} with daily review mode (is_daily_review=True)")
    start_time = time.time()
    run_bkt_and_lstm(page, completion, user_id, correct_answers, incorrect_answers, is_daily_review=True)
    end_time = time.time()
    
    print(f"Daily review workflow completed in {end_time - start_time:.2f} seconds")
    
    # Print final session values
    print("\nFinal session values:")
    for key in ["proficiency", "lstm_raw_confidence", "proficiency_confidence", "system_confidence"]:
        print(f"- {key}: {page.session.get(key)}")
    
    # Return success if we have a proficiency value
    return page.session.get("proficiency") is not None

def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python test_integration.py <user_id>")
        sys.exit(1)
    
    user_id = int(sys.argv[1])
    print(f"Testing integration for user {user_id}")
    
    # Test lesson workflow
    lesson_success = test_lesson_workflow(user_id)
    
    # Test daily review workflow
    daily_review_success = test_daily_review_workflow(user_id)
    
    # Print summary
    print("\n==== Test Summary ====")
    print(f"Lesson workflow test: {'✅ SUCCESS' if lesson_success else '❌ FAILED'}")
    print(f"Daily review workflow test: {'✅ SUCCESS' if daily_review_success else '❌ FAILED'}")
    
    if lesson_success and daily_review_success:
        print("\nAll tests passed! The system is ready for production use.")
    else:
        print("\nSome tests failed. Please review the logs above.")

if __name__ == "__main__":
    main()
