import os
import json
import numpy as np
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.preprocessing.sequence import pad_sequences

MODEL_PATH = "lstm_proficiency_model.h5"
MIN_SEQUENCE_LENGTH = 3

def build_lstm_model(input_shape):
    model = Sequential()
    model.add(LSTM(64, input_shape=input_shape, return_sequences=False))
    model.add(Dense(1, activation='sigmoid'))  # Output: proficiency (0-1)
    model.compile(optimizer='adam', loss='mse')
    return model

def train_lstm_model(sequences, labels, epochs=10):
    # sequences: list of lists (BKT data per user)
    # labels: list of proficiency scores (0-1)
    maxlen = max(len(seq) for seq in sequences)
    X = pad_sequences(sequences, maxlen=maxlen, dtype='float32')
    y = np.array(labels)
    model = build_lstm_model((X.shape[1], 1))
    X = np.expand_dims(X, -1)
    model.fit(X, y, epochs=epochs)
    model.save(MODEL_PATH)
    return model

def predict_proficiency(bkt_sequence):
    """
    bkt_sequence: list of floats (e.g., skill mastery probabilities or 0/1 correct/incorrect)
    Returns: predicted proficiency (float 0-1)
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("LSTM model not trained yet.")
    model = load_model(MODEL_PATH)
    X = pad_sequences([bkt_sequence], maxlen=model.input_shape[1], dtype='float32')
    X = np.expand_dims(X, -1)
    pred = model.predict(X)
    return float(pred[0][0])

def overall_proficiency(bkt_sequence, completion_percentage):
    if len(bkt_sequence) < MIN_SEQUENCE_LENGTH:
        return None  # Not enough data to predict
    proficiency = predict_proficiency(bkt_sequence)
    # Optionally adjust by completion
    adjusted_proficiency = proficiency * completion_percentage
    return adjusted_proficiency


