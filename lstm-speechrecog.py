import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Embedding
import numpy as np
import speech_recognition as sr

# Sample dataset (replace with your actual dataset)
# X_train should be sequences of integers representing words
# y_train should be the corresponding labels
X_train = np.random.randint(1000, size=(100, 10))  # 100 samples, each of length 10
y_train = np.random.randint(2, size=(100, 1))  # Binary labels

# Define the LSTM model
model = Sequential()
model.add(Embedding(input_dim=1000, output_dim=64, input_length=10))
model.add(LSTM(128))
model.add(Dense(1, activation='sigmoid'))

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Train the model
model.fit(X_train, y_train, epochs=10, batch_size=32)

# Function to recognize speech and predict using the trained model
def recognize_and_predict():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something:")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"Recognized text: {text}")
            # Convert text to sequence of integers (this is a placeholder, replace with actual preprocessing)
            sequence = np.random.randint(1000, size=(1, 10))
            prediction = model.predict(sequence)
            print(f"Prediction: {prediction}")
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

# Example usage
recognize_and_predict()