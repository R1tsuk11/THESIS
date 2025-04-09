from bktsim_qbank import sim_bank
import numpy as np
import pandas as pd
from pyBKT.models import Model

def simulate_bkt(student, num_problems, num_simulations):
    # Initialize BKT Model
    bkt = Model()

    # Initialize storage for BKT data
    bkt_data = []

    # Default parameters (now dynamically updated)
    guess = 0.2
    slip = 0.1
    prior = 0.5

    # Simulate BKT over multiple runs
    for _ in range(num_simulations):
        student.reset()
        for i in range(num_problems):
            # Fetch the next question
            question = student.next_question()
            print(f"\nQuestion {i+1}: {question['question']}")

            # Skip lesson-type questions
            if question['correct_answer'] is None:
                print("This is a lesson question. Moving to the next question.")
                continue

            # Get user answer
            answer = student.answer_question(question)
            student.update(answer)

            # Update prior probability dynamically
            prior = student.prior  

            # Adjust guess/slip dynamically based on performance
            if answer == "correct":
                guess = max(0.1, guess * 0.9)  # Reduce guess rate if answering correctly
                slip = max(0.05, slip * 0.9)   # Reduce slip rate if user isn't making mistakes
            else:
                guess = min(0.4, guess * 1.1)  # Increase guess rate if struggling
                slip = min(0.3, slip * 1.1)    # Increase slip rate if making more mistakes

            # Store BKT data per question
            bkt_data.append({
                'user_id': student.user_id,
                'skill_name': "Maupay nga aga",
                'correct': 1 if answer == 'correct' else 0,
                'guess': guess,
                'slip': slip,
                'prior': prior
            })

            # Convert to DataFrame
            bkt_data_df = pd.DataFrame(bkt_data)

            # Fit the BKT model using only past data
            bkt.fit(data=bkt_data_df)

            # Predict proficiency for this specific question
            predictions = bkt.predict(data=bkt_data_df.iloc[-1:])

            # Calculate Confidence Score
            if 'guess' in predictions.columns and 'slip' in predictions.columns:
                predictions['confidence'] = 1 - predictions['guess'].iloc[0] - predictions['slip'].iloc[0]

                print(f"Predictions after question {i+1}:")
                print(predictions[['user_id', 'skill_name', 'correct', 'guess', 'slip', 'correct_predictions', 'state_predictions', 'confidence']])
            else:
                print(f"Predictions after question {i+1}:")
                print(predictions)

    return predictions

# Simulate a student answering questions
class Student:
    def __init__(self, user_id):
        self.user_id = user_id
        self.skills = sim_bank["Level"]
        self.skill_index = 0
        self.prior = 0.5

    def reset(self):
        self.skill_index = 0
        self.prior = 0.5  # Reset learning state

    def next_question(self):
        question = self.skills[self.skill_index]
        self.skill_index = (self.skill_index + 1) % len(self.skills)
        return question

    def answer_question(self, question):
        user_answer = input(f"Answer for '{question['question']}': ").strip().lower()
        correct_answer = question['correct_answer'].strip().lower()
        return 'correct' if user_answer == correct_answer else 'incorrect'

    def update(self, answer):
        if answer == 'correct':
            self.prior = min(1, self.prior + 0.1)
        else:
            self.prior = max(0, self.prior - 0.1)

if __name__ == '__main__':
    student = Student(user_id=1)
    predictions = simulate_bkt(student, num_problems=6, num_simulations=1)
    print("\nFinal Predictions:")
    print(predictions)
