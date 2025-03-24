import numpy as np
import pandas as pd
import re
from pyBKT.models import Model
from pymongo import MongoClient

# Minimum number of attempts before BKT considers the skill mastery
MIN_QUESTIONS = 1  

def extract_vocab_word(question_text, user_data):
    """Finds the correct vocabulary word by matching the question with the module's question data."""
    
    # If the question is stored as a dictionary (it should be a string), attempt retrieval
    if isinstance(question_text, dict):
        return question_text.get('vocabulary', 'unknown')

    # Search for the correct vocabulary in the user's stored modules
    for module in user_data.get('modules', []):
        for level in module.get('levels', []):
            for question_data in level.get('questions_answers', []):
                if question_data.get('question') == question_text:
                    return question_data.get('vocabulary', 'unknown')  # Retrieve correct vocabulary

    # Fallback: Extract last word using regex if no match is found
    words = re.findall(r'\b[a-zA-Z]+\b', question_text)
    return words[-1] if words else 'unknown'

def main():
    # Connect to MongoDB
    client = MongoClient('mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/?tls=true&tlsInsecure=true')
    db = client['arami']
    collection = db['users']

    # Fetch user data from MongoDB (debugging with user_id 8)
    user_data_cursor = collection.find({'user_id': 8})  
    userData = pd.DataFrame(list(user_data_cursor))

    # Print data structure for debugging
    print("Columns in userData:", userData.columns)
    print("First few rows of userData:\n", userData.head())

    # Ensure required fields exist
    if 'questions_correct' not in userData.columns or 'questions_wrong' not in userData.columns:
        raise ValueError("The MongoDB data does not contain 'questions_correct' or 'questions_wrong' fields.")

    # Process BKT Data
    bkt_data = []
    for _, user_row in userData.iterrows():
        vocab_correct = {}
        vocab_wrong = {}

        # Process questions_correct
        if isinstance(user_row['questions_correct'], dict):
            print(f"Processing questions_correct for user_id: {user_row['user_id']}")
            for question, answer in user_row['questions_correct'].items():
                vocab_word = extract_vocab_word(question, user_row)
                print(f"Extracted vocabulary (correct): {vocab_word}")
                if vocab_word and vocab_word != 'unknown':  
                    vocab_correct[vocab_word] = vocab_correct.get(vocab_word, 0) + 1

        # Process questions_wrong
        if isinstance(user_row['questions_wrong'], dict):
            print(f"Processing questions_wrong for user_id: {user_row['user_id']}")
            for question, answer in user_row['questions_wrong'].items():
                vocab_word = extract_vocab_word(question, user_row)
                print(f"Extracted vocabulary (wrong): {vocab_word}")
                if vocab_word and vocab_word != 'unknown':  
                    vocab_wrong[vocab_word] = vocab_wrong.get(vocab_word, 0) + 1

        # Print vocab counts before filtering
        print("Vocab correct counts:", vocab_correct)
        print("Vocab wrong counts:", vocab_wrong)

        # Prepare BKT data per vocabulary word
        for vocab_word in set(vocab_correct.keys()).union(vocab_wrong.keys()):
            correct = vocab_correct.get(vocab_word, 0)
            wrong = vocab_wrong.get(vocab_word, 0)
            total = correct + wrong

            # Reduce minimum attempts for testing
            if total >= MIN_QUESTIONS:
                proficiency = correct / total  
                for _ in range(total):  
                    bkt_data.append({
                        'user_id': user_row['user_id'],
                        'skill_name': vocab_word,
                        'correct': 1 if correct > wrong else 0,
                        'guess': 0.25,  # Default guess parameter
                        'slip': 0.1    # Default slip parameter
                    })

    # Convert to DataFrame
    bkt_data = pd.DataFrame(bkt_data)

    # Handle empty dataset case
    if bkt_data.empty:
        raise ValueError("The prepared BKT data is empty. Please check the data preparation steps.")

    print("BKT Data:\n", bkt_data)

    # Ensure required columns exist
    required_columns = {'user_id', 'skill_name', 'correct', 'guess', 'slip'}
    if not required_columns.issubset(bkt_data.columns):
        raise ValueError("The BKT data is missing required columns. Expected: {}".format(required_columns))

    # Fit BKT Model normally
    model = Model()
    model.fit(data=bkt_data)  # NO multigs=True

    # Set different guess/slip values per skill
    skill_params = {
        "Kamusta ka?": {"p_guess": 0.2, "p_slip": 0.1},
        "gihapon": {"p_guess": 0.25, "p_slip": 0.1},
        "Maupay nga aga": {"p_guess": 0.15, "p_slip": 0.05},
        "Pakadto": {"p_guess": 0.3, "p_slip": 0.1},
    }

    # Update skill parameters after fitting
    for skill, params in skill_params.items():
        if skill in model.params():
            model.params()[skill]['p_guess'] = params['p_guess']
            model.params()[skill]['p_slip'] = params['p_slip']

    # Predict user proficiency
    predictions = model.predict(data=bkt_data)

    print("Predictions:")
    print(predictions)
    print("Available columns in predictions:", predictions.columns)

    # Ensure the 'guess' and 'slip' columns exist before using them
    if 'guess' in predictions.columns and 'slip' in predictions.columns:
        predictions['confidence'] = 1 - predictions['guess'] - predictions['slip']
        print("Predictions with Confidence Scores:")
        print(predictions[['user_id', 'skill_name', 'correct_predictions', 'state_predictions', 'confidence']])
    else:
        print("Warning: 'guess' and 'slip' columns are missing from the predictions output.")

if __name__ == '__main__':
    main()
