import numpy as np
import pandas as pd
from pyBKT.models import Model
from pymongo import MongoClient

def main():
    # Connect to MongoDB
    client = MongoClient('mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/?tls=true&tlsInsecure=true')
    db = client['arami']
    collection = db['users']

    # Fetch user data from MongoDB
    user_data_cursor = collection.find({'user_id': 8})  # Fetch data for user_id 8 for debugging
    userData = pd.DataFrame(list(user_data_cursor))

    # Print the columns of the userData DataFrame
    print("Columns in userData:", userData.columns)

    # Print the first few rows of the userData DataFrame to inspect the data
    print("First few rows of userData:")
    print(userData.head())

    # Ensure the required fields are present
    if 'questions_correct' not in userData.columns or 'questions_wrong' not in userData.columns:
        raise ValueError("The MongoDB data does not contain the required 'questions_correct' or 'questions_wrong' field.")

    # Extract vocabulary words and group questions by vocabulary
    bkt_data = []
    for user_id, user_row in userData.iterrows():
        vocab_correct = {}
        vocab_wrong = {}

        # Process questions_correct
        if isinstance(user_row['questions_correct'], dict):
            for question, answer in user_row['questions_correct'].items():
                vocab_word = extract_vocab_word(question)  # Function to extract vocabulary word from question
                if vocab_word not in vocab_correct:
                    vocab_correct[vocab_word] = 0
                vocab_correct[vocab_word] += 1

        # Process questions_wrong
        if isinstance(user_row['questions_wrong'], dict):
            for question, answer in user_row['questions_wrong'].items():
                vocab_word = extract_vocab_word(question)  # Function to extract vocabulary word from question
                if vocab_word not in vocab_wrong:
                    vocab_wrong[vocab_word] = 0
                vocab_wrong[vocab_word] += 1

        # Prepare BKT data for each vocabulary word
        for vocab_word in set(vocab_correct.keys()).union(vocab_wrong.keys()):
            correct = vocab_correct.get(vocab_word, 0)
            wrong = vocab_wrong.get(vocab_word, 0)
            total = correct + wrong
            proficiency = correct / total if total > 0 else 0
            bkt_data.append({
                'user_id': user_row['user_id'],
                'skill_name': vocab_word,
                'correct': proficiency
            })

    bkt_data = pd.DataFrame(bkt_data)

    if bkt_data.empty:
        raise ValueError("The prepared BKT data is empty. Please check the data preparation steps.")

    print("BKT Data:")
    print(bkt_data)

    # Ensure the required columns are present
    required_columns = {'user_id', 'skill_name', 'correct'}
    if not required_columns.issubset(bkt_data.columns):
        raise ValueError("The BKT data does not contain the required columns. Expected columns: {}".format(required_columns))

    # Fit the BKT model
    model = Model()
    model.fit(data=bkt_data)

    # Predict user proficiency
    predictions = model.predict(data=bkt_data)

    print("Predictions:")
    print(predictions)

def extract_vocab_word(question):
    # Function to extract vocabulary word from question
    # Assuming question is a string and vocabulary is part of the question text
    # Modify this function based on your actual question format
    if isinstance(question, dict):
        return question.get('vocabulary', '')
    return question

if __name__ == '__main__':
    main()