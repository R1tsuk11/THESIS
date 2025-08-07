from bktsim_qbank import sim_bank
import numpy as np
import pandas as pd
from pyBKT.models import Model
import torch
import torch.nn as nn
import torch.optim as optim

# Define LSTM Model for Learning Pattern Recognition
class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        out = self.fc(lstm_out[:, -1, :])  # Take last output for prediction
        return torch.sigmoid(out)  # Ensure output is between 0 and 1

# Initialize LSTM Model
input_size = 3  # Correct, Guess, Slip
hidden_size = 50
output_size = 1  # Predict mastery probability
lstm_model = LSTMModel(input_size, hidden_size, output_size)
optimizer = optim.Adam(lstm_model.parameters(), lr=0.01)
criterion = nn.MSELoss()

def simulate_bkt_lstm(student, num_problems, num_simulations):
    bkt = Model()
    bkt_data = []
    lstm_inputs = []
    guess, slip, prior = 0.2, 0.1, 0.5
    
    for _ in range(num_simulations):
        student.reset()
        lesson_correct = []
        for i in range(num_problems):
            question = student.next_question()
            print(f"\nQuestion {i+1}: {question['question']}")

            if question['correct_answer'] is None:
                print("Lesson question skipped.")
                continue

            answer = student.answer_question(question)
            student.update(answer)
            prior = student.prior
            
            if answer == "correct":
                guess = max(0.05, guess * 0.85)  # Reduce guess rate more aggressively
                slip = max(0.02, slip * 0.85)   # Reduce slip rate if user isn't making mistakes
            else:
                guess = min(0.5, guess * 1.2)  # Increase guess rate faster if struggling
                slip = min(0.4, slip * 1.2)    # Increase slip rate significantly on errors

            # Store BKT data per question
            bkt_data.append({'user_id': student.user_id, 'skill_name': "Maupay nga aga",
                             'correct': 1 if answer == 'correct' else 0, 'guess': guess,
                             'slip': slip, 'prior': prior})
            lstm_inputs.append([1 if answer == 'correct' else 0, guess, slip])
            lesson_correct.append(1 if answer == 'correct' else 0)
            
            # Convert BKT data to DataFrame
            bkt_data_df = pd.DataFrame(bkt_data)
            if not bkt_data_df.empty:
                bkt.fit(data=bkt_data_df)
                predictions = bkt.predict(data=bkt_data_df.iloc[-1:])
                
                if 'guess' in predictions.columns and 'slip' in predictions.columns:
                    predictions['confidence'] = 1 - predictions['guess'].iloc[0] - predictions['slip'].iloc[0]
                    print(f"Predictions after question {i+1}:")
                    print(predictions[['user_id', 'skill_name', 'correct', 'guess', 'slip', 'correct_predictions', 'state_predictions', 'confidence']])

        # LSTM Batch Processing at End of Lesson
        if len(lstm_inputs) > 1:
            lstm_inputs = torch.tensor(lstm_inputs, dtype=torch.float32).unsqueeze(0)
            lstm_target = torch.tensor([sum(lesson_correct) / len(lesson_correct)], dtype=torch.float32).view(-1,1)
            
            optimizer.zero_grad()
            lstm_output = lstm_model(lstm_inputs)
            loss = criterion(lstm_output, lstm_target)
            loss.backward()
            optimizer.step()
            
            # Compute Final Mastery Score using BKT's actual prediction output
            bkt_mastery = predictions['state_predictions'].iloc[-1]  # Get latest BKT prediction
            final_mastery = (bkt_mastery * 0.7) + (lstm_output.item() * 0.3)
            
            print(f"\nBKT Predicted Mastery: {bkt_mastery}")
            print(f"LSTM Predicted Mastery: {lstm_output.item()} (Actual: {lstm_target.item()})")
            print(f"Final Mastery Score: {final_mastery}")

            # Blended confidence score (BKT + LSTM influence)
            bkt_confidence = predictions['confidence'].iloc[0]
            lstm_confidence = lstm_output.item()
            blended_confidence = (bkt_confidence * 0.7) + (lstm_confidence * 0.3)

            print(f"\nBKT Predicted Mastery: {bkt_mastery:.5f}")
            print(f"LSTM Predicted Mastery: {lstm_output.item():.5f} (Actual: {lstm_target.item():.5f})")
            print(f"Final Mastery Score: {final_mastery:.5f}")
            print(f"Blended Confidence Score (BKT + LSTM): {blended_confidence:.5f}")
    
    return predictions

# Student Simulation Class
class Student:
    def __init__(self, user_id):
        self.user_id = user_id
        self.skills = sim_bank["Level"]
        self.skill_index = 0
        self.prior = 0.5

    def reset(self):
        self.skill_index = 0
        self.prior = 0.5

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
            self.prior = min(1, self.prior + 0.15)  # Increase impact on correct
        else:
            self.prior = max(0, self.prior - 0.2)   # Stronger penalty for mistakes

if __name__ == '__main__':
    student = Student(user_id=1)
    predictions = simulate_bkt_lstm(student, num_problems=6, num_simulations=1)
