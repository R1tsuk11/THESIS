import numpy as np
import pandas as pd
from pyBKT.models import Model

def main():
    userData = pd.DataFrame({
        'user_id': [10, 11, 12],
        'skill_id': ['word', 'phrases', 'speaking'],
        'attempt': [1, 2, 1],
        'correct': [0, 1, 1],
        'timestamp': ['2024-02-07 10:00', 
                      '2024-02-07 10:05', 
                      '2024-02-07 10:10']
    })

    
    userData['timestamp'] = pd.to_datetime(userData['timestamp'])
    userData = userData.sort_values(by=['user_id', 'timestamp'])

   
    userData['skill_id'] = userData['skill_id'].astype('category')

    
    skill_mapping = dict(enumerate(userData['skill_id'].cat.categories))
    print("Skill Mapping:", skill_mapping)

  
    bkt_data = pd.DataFrame({
        'user_id': userData['user_id'].values,  
        'skill_name': userData['skill_id'].values,
        'correct': userData['correct'].values
    })

    # Check if bkt_data is empty
    if bkt_data.empty:
        raise ValueError("The prepared BKT data is empty. Please check the data preparation steps.")

    # Print bkt_data for debugging to check
    print("BKT Data:")
    print(bkt_data)

    # Checks data has correct columns
    required_columns = {'user_id', 'skill_name', 'correct'}
    if not required_columns.issubset(bkt_data.columns):
        raise ValueError("The BKT data does not contain the required columns. Expected columns: {}".format(required_columns))

    # Initialize and fit/train the BKT model
    model = Model()
    model.fit(data=bkt_data)

    # Predict probabilities (printed in order to check if pyBkt is working)
    predictions = model.predict(data=bkt_data)

    print("Predictions:")
    print(predictions)

if __name__ == '__main__':
    main()
