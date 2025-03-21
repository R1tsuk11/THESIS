import numpy as np
import pandas as pd
from pyBKT.models import Model
from pymongo import MongoClient

def main():
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['arami']
    collection = db['users']

    # Fetch user data from MongoDB
    user_data_cursor = collection.find({'user_id': 7})  # Fetch data for user_id 7 for debugging
    userData = pd.DataFrame(list(user_data_cursor))

    # Print the columns of the userData DataFrame
    print("Columns in userData:", userData.columns)

    # Print the first few rows of the userData DataFrame to inspect the data
    print("First few rows of userData:")
    print(userData.head())

    # Ensure the required fields are present
    if 'questions_correct' not in userData.columns:
        raise ValueError("The MongoDB data does not contain the required 'questions_correct' field.")

    # Extract questions_answers data from questions_correct
    bkt_data = []
    for user_id, user_row in userData.iterrows():
        if 'questions_correct' in user_row and isinstance(user_row['questions_correct'], dict):
            for question, answer in user_row['questions_correct'].items():
                skill_name = question  # Use question as skill name
                correct = True  # Since it's questions_correct, we assume the answer is correct
                bkt_data.append({
                    'user_id': user_row['user_id'],
                    'skill_name': skill_name,
                    'correct': correct
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

if __name__ == '__main__':
    main()