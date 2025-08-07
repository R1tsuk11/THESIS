import numpy as np
import pandas as pd
import re
from pyBKT.models import Model
from pymongo import MongoClient

# Minimum number of attempts before BKT considers the skill mastery
MIN_QUESTIONS = 1  

def extract_vocab_word(question_text, user_data):
    """Finds the correct vocabulary word by matching the question with the module's question data."""
    
    if isinstance(question_text, dict):
        return question_text.get('vocabulary', 'unknown')

    for module in user_data.get('modules', []):
        for level in module.get('levels', []):
            for question_data in level.get('questions_answers', []):
                if question_data.get('question') == question_text:
                    return question_data.get('vocabulary', 'unknown')  

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
                    bkt_data.append({
                        'user_id': user_row['user_id'],
                        'skill_name': vocab_word,
                        'correct': 1
                    })

        # Process questions_wrong
        if isinstance(user_row['questions_wrong'], dict):
            print(f"Processing questions_wrong for user_id: {user_row['user_id']}")
            for question, answer in user_row['questions_wrong'].items():
                vocab_word = extract_vocab_word(question, user_row)
                print(f"Extracted vocabulary (wrong): {vocab_word}")
                if vocab_word and vocab_word != 'unknown':  
                    vocab_wrong[vocab_word] = vocab_wrong.get(vocab_word, 0) + 1
                    bkt_data.append({
                        'user_id': user_row['user_id'],
                        'skill_name': vocab_word,
                        'correct': 0
                    })

    # Convert to DataFrame
    bkt_data = pd.DataFrame(bkt_data)

    if bkt_data.empty:
        raise ValueError("The prepared BKT data is empty. Please check the data preparation steps.")

    print("Initial BKT Data:\n", bkt_data)

    # Initialize BKT Model
    model = Model()
    updated_params = {}

    # Process each vocabulary one by one
    for vocab_word in set(bkt_data['skill_name']):
        subset = bkt_data[bkt_data['skill_name'] == vocab_word]

        # Train BKT only on first instance
        model.fit(data=subset.iloc[[0]])  

        # Process each question individually and update parameters
        for index, row in subset.iterrows():
            # Predict per question based on prior knowledge
            prediction = model.predict(data=pd.DataFrame([row]))  

            # Get updated guess/slip parameters for the skill
            learned_params = model.params().get(vocab_word, {})
            updated_guess = learned_params.get('p_guess', 0.25)
            updated_slip = learned_params.get('p_slip', 0.1)

            # Store the updated parameters
            updated_params[vocab_word] = (updated_guess, updated_slip)

            # Apply the updated guess/slip dynamically
            subset.loc[index, 'guess'] = updated_guess
            subset.loc[index, 'slip'] = updated_slip

            # Retrain the model using the latest knowledge for the next question
            model.fit(data=subset.iloc[:index+1])

        # Merge updated subset back into main dataset
        bkt_data.loc[bkt_data['skill_name'] == vocab_word] = subset

    # Predict user proficiency after all updates
    predictions = model.predict(data=bkt_data)

    print("Predictions:")
    print(predictions)

    print("Available columns in predictions:", predictions.columns)

    # Apply updated guess/slip values dynamically
    for skill in updated_params.keys():
        if skill in predictions['skill_name'].values:
            predictions.loc[predictions['skill_name'] == skill, 'guess'] = updated_params[skill][0]
            predictions.loc[predictions['skill_name'] == skill, 'slip'] = updated_params[skill][1]

    # Compute confidence dynamically
    predictions['confidence'] = 1 - predictions['guess'] - predictions['slip']

    print("Predictions with Confidence Scores:")
    print(predictions[['user_id', 'skill_name', 'correct_predictions', 'state_predictions', 'confidence']])

if __name__ == '__main__':
    main()
