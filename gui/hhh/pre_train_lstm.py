import os
import sys
import json
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.preprocessing.sequence import pad_sequences

def build_lstm_model(input_shape):
    """Build a simple LSTM model for proficiency prediction"""
    model = Sequential()
    model.add(LSTM(64, input_shape=input_shape, return_sequences=False))
    model.add(Dense(1, activation='sigmoid'))  # Output: proficiency (0-1)
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
    return model

def generate_learning_data(sequence_length=3, num_sequences=50):
    """Generate synthetic data that simulates realistic learning patterns, including high and low mastery"""
    # Create patterns with upward trend + occasional dips
    base_patterns = np.linspace(0.3, 0.8, num_sequences)
    # Add high mastery and low mastery patterns
    high_patterns = np.linspace(0.85, 0.99, num_sequences // 4)
    low_patterns = np.linspace(0.01, 0.2, num_sequences // 4)
    all_patterns = np.concatenate([low_patterns, base_patterns, high_patterns])

    # Add some noise and learning plateaus
    sequences = []
    labels = []

    for i in range(len(all_patterns) - sequence_length):
        seq = all_patterns[i:i+sequence_length] + np.random.normal(0, 0.03, sequence_length)
        seq = np.clip(seq, 0.01, 0.99)
        label = all_patterns[i+sequence_length] + np.random.normal(0, 0.02)
        label = np.clip(label, 0.01, 0.99)
        sequences.append(seq)
        labels.append(label)

    return sequences, labels

def create_base_model(output_dir="lstm_models"):
    """Create the base LSTM model with synthetic data"""
    # Set up directories
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("lstm_history", exist_ok=True)
    os.makedirs("lstm_counters", exist_ok=True)
    
    # Generate synthetic training data
    print("Generating synthetic data for base model...")
    sequences, labels = generate_learning_data()
    
    # Format data for training
    X = np.array(sequences)
    X = np.expand_dims(X, -1)  # Add feature dimension
    y = np.array(labels)
    
    # Create and train model
    print("Training base LSTM model...")
    model = build_lstm_model((X.shape[1], 1))
    history = model.fit(X, y, epochs=15, verbose=1, batch_size=8)
    
    # Save model
    model_path = os.path.join(output_dir, "lstm_proficiency_model.keras")
    model.save(model_path)
    print(f"Base model saved to {model_path}")
    
    # Save loss history to JSON file
    loss_history = {
        "loss": [float(x) for x in history.history['loss']],
        "mae": [float(x) for x in history.history['mae']]
    }
    with open(os.path.join(output_dir, "base_model_loss_history.json"), "w") as f:
        json.dump(loss_history, f, indent=2)
    
    # Save synthetic history data
    history_data = [float(x) for x in np.linspace(0.3, 0.8, 50)]
    with open("lstm_history/temp_prof_history.json", "w") as f:
        json.dump(history_data, f)
    
    # Create counter file
    with open("lstm_counters/lstm_counter.json", "w") as f:
        json.dump({"count": len(history_data)}, f)
    
    print("Base model and history files created successfully.")
    return model_path

def create_user_model(user_id, output_dir="lstm_models"):
    """Create a user-specific model by copying the base model"""
    # Check if base model exists
    base_model_path = os.path.join(output_dir, "lstm_proficiency_model.keras")
    if not os.path.exists(base_model_path):
        print("Base model doesn't exist. Creating it first...")
        create_base_model(output_dir)
    
    # Create user model by copying base model
    user_model_path = os.path.join(output_dir, f"lstm_proficiency_model_{user_id}.keras")
    if os.path.exists(user_model_path):
        print(f"User model already exists at {user_model_path}")
        return user_model_path
        
    # Copy the base model
    import shutil
    shutil.copy(base_model_path, user_model_path)
    print(f"Created user model for {user_id} at {user_model_path}")
    
    # Create initial history file
    history_file = f"lstm_history/temp_prof_history_{user_id}.json"
    if not os.path.exists(history_file):
        with open(history_file, "w") as f:
            # Start with 3 reasonable values
            json.dump([0.3, 0.35, 0.4], f)
        print(f"Created initial history for user {user_id}")
    
    # Create counter file
    counter_file = f"lstm_counters/lstm_counter_{user_id}.json"
    with open(counter_file, "w") as f:
        json.dump({"count": 3}, f)
    
    return user_model_path

if __name__ == "__main__":
    # If user_id provided, create user model
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
        print(f"Creating model for user {user_id}")
        create_user_model(user_id)
    # Otherwise create base model
    else:
        print("Creating base model")
        create_base_model()
    
    print("Done.")