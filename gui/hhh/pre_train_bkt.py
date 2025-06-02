import pandas as pd
import json
import os
import random
import pickle
import math
import sys
from pyBKT.models import Model
from tqdm import tqdm
import numpy as np
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning, module='pyBKT.fit.EM_fit')

# Import modules directly from qbank.py
from qbank import module_1, module_2, module_3, module_4, module_5

def preprocess_training_data(df):
    """Clean and preprocess data to avoid fitting errors"""
    print("Preprocessing synthetic data...")
    
    # 1. Remove any rows with NaN values
    initial_count = len(df)
    df = df.dropna()
    if len(df) < initial_count:
        print(f"Removed {initial_count - len(df)} rows with missing values")
    
    # 2. Ensure minimum number of examples per skill
    min_examples = 3
    skill_counts = df['skill_name'].value_counts()
    skills_to_keep = skill_counts[skill_counts >= min_examples].index
    
    filtered_df = df[df['skill_name'].isin(skills_to_keep)]
    if len(filtered_df) < len(df):
        print(f"Removed {len(df) - len(filtered_df)} rows with insufficient examples per skill")
        df = filtered_df
    
    # 3. Ensure guess and slip values are valid (not too close to 0 or 1)
    df['guess'] = df['guess'].clip(0.05, 0.95)
    df['slip'] = df['slip'].clip(0.05, 0.95)
    
    # 4. Add small random noise to avoid exact duplicates
    for col in ['guess', 'slip', 'prior']:
        if col in df.columns:
            df[col] = df[col] + np.random.normal(0, 0.001, size=len(df))
            df[col] = df[col].clip(0.01, 0.99)  # Keep within valid range
            
    print(f"Preprocessed data: {len(df)} rows for {df['skill_name'].nunique()} skills")
    return df

def extract_vocabulary_from_qbank():
    """Extract vocabulary items with metadata from qbank modules"""
    vocabulary_items = {}
    
    # Process all modules
    all_modules = [module_1, module_2, module_3, module_4, module_5]
    
    # Create progress bar for module processing
    module_pbar = tqdm(enumerate(all_modules, 1), total=len(all_modules),
                      desc="Processing modules", ncols=100)
    
    for module_idx, module in module_pbar:
        module_pbar.set_description(f"Processing module {module_idx}")
        
        # Process each lesson in the module
        lesson_count = len(module)
        lesson_pbar = tqdm(module.items(), total=lesson_count, leave=False,
                          desc=f"Module {module_idx} lessons", ncols=100)
        
        for lesson_name, questions in lesson_pbar:
            lesson_idx = int(lesson_name.split()[-1])
            lesson_pbar.set_description(f"Lesson {lesson_idx}")
            
            # Process each question in the lesson
            for question in questions:
                vocab = question.get('vocabulary', '').lower()
                if not vocab or vocab in vocabulary_items:
                    continue
                    
                # Store metadata for this vocabulary item
                vocabulary_items[vocab] = {
                    'module': module_idx,
                    'lesson': lesson_idx,
                    'difficulty': question.get('difficulty', 1),
                    'english': question.get('english_translation', ''),
                    'type': question.get('type', '')
                }
    
    print(f"Extracted {len(vocabulary_items)} unique vocabulary items from qbank")
    return vocabulary_items

def create_synthetic_data_from_qbank():
    """Create synthetic training data based on vocabulary from qbank"""
    vocab_metadata = extract_vocabulary_from_qbank()
    synthetic_data = []
    
    print("Generating synthetic learning data...")
    
    # Create progress bar for vocabulary processing
    vocab_pbar = tqdm(vocab_metadata.items(), total=len(vocab_metadata),
                     desc="Generating data", ncols=100)
    
    for vocab, metadata in vocab_pbar:
        vocab_pbar.set_description(f"Processing '{vocab}'")
        
        # Calculate base parameters based on metadata
        module = metadata['module']
        lesson = metadata['lesson']
        difficulty = metadata.get('difficulty', 1)
        
        # If no explicit difficulty, calculate based on module and lesson
        if difficulty is None:
            difficulty = (module - 1) * 0.3 + (lesson - 1) * 0.1
        else:
            # Normalize difficulty to 0-1 scale
            difficulty = min(1.0, difficulty / 5.0)
        
        # Create synthetic learning curve
        correct_prob = 1.0 - (difficulty * 0.5)  # Harder items have lower probability
        
        # Generate attempts with a learning curve
        attempts = 10  # Number of synthetic attempts per vocab
        for i in range(attempts):
            # Learning curve: probability increases as student "learns"
            learning_curve = min(1.0, correct_prob + (i * 0.08))
            
            # Determine correct/incorrect with this probability
            is_correct = 1 if random.random() < learning_curve else 0
            
            # More strategic patterns based on difficulty
            if i < 2 and difficulty > 0.7:  # Hard words start with wrong answers
                is_correct = 0
            if i > 7 and difficulty < 0.4:  # Easy words end with correct answers
                is_correct = 1
            
            # Set guess/slip parameters based on difficulty
            guess = 0.2 + (difficulty * 0.1)  # Harder words have higher guess
            slip = 0.1 + (difficulty * 0.05)  # Harder words have higher slip
            
            # Create the data point
            synthetic_data.append({
                "user_id": "synthetic",
                "skill_name": vocab,
                "correct": is_correct,
                "guess": guess,
                "slip": slip,
                "prior": 0.5
            })
    
    print(f"Generated {len(synthetic_data)} synthetic training data points")
    return synthetic_data

def create_base_bkt_model():
    """Create a pre-trained BKT model based on qbank vocabulary"""
    try:
        import time
        import numpy as np
        from datetime import datetime, timedelta
        
        # Generate synthetic data from qbank
        synthetic_data = create_synthetic_data_from_qbank()
        
        # Create DataFrame with progress bar
        print("Creating training DataFrame...")
        df = pd.DataFrame(synthetic_data)
        
        # Preprocess the data
        df = preprocess_training_data(df)
        
        # Create and fit the BKT model
        print("Training BKT model with synthetic data...")
        base_model = Model()
        
        # Record start time for estimation
        start_time = time.time()
        
        # Create a progress indicator with time estimation
        total_steps = 20  # Simulated steps for visualization
        print("Fitting model:")
        
        # Display initial progress
        print("0% complete | Estimated time: calculating...")
        
        # Perform the actual model fitting (only happens once)
        base_model.fit(data=df)
        
        # Calculate actual training time
        training_time = time.time() - start_time
        
        # Show completed progress with total time
        print(f"100% complete | Total time: {training_time:.1f} seconds")
        
        # Save the model
        print("Saving model and data files...")
        with open("bkt_base_model.pkl", "wb") as f:
            pickle.dump(base_model, f)
        print("Base model saved to 'bkt_base_model.pkl'")
        
        # Save the synthetic data for reference
        df.to_csv("bkt_synthetic_data.csv", index=False)
        print("Synthetic data saved to 'bkt_synthetic_data.csv'")
        
        # Test with a few predictions
        print("\nSample predictions from the pre-trained model:")
        unique_vocabs = df['skill_name'].unique()
        test_vocabs = random.sample(list(unique_vocabs), min(5, len(unique_vocabs)))
        
        # Add time estimation to prediction testing
        pred_start_time = time.time()
        total_tests = len(test_vocabs)
        
        for i, vocab in enumerate(test_vocabs):
            # Calculate prediction progress and time estimation
            progress_pct = (i / total_tests) * 100
            elapsed = time.time() - pred_start_time
            if i > 0:
                estimated_total = elapsed / i * total_tests
                remaining = estimated_total - elapsed
                eta = datetime.now() + timedelta(seconds=remaining)
                time_str = f"ETA: {eta.strftime('%H:%M:%S')}"
            else:
                time_str = "Calculating ETA..."
                
            # Display progress
            print(f"\rTesting: {progress_pct:.1f}% | {time_str}", end="")
            
            # Make prediction
            test_data = df[df['skill_name'] == vocab].iloc[-1:].copy()
            prediction = base_model.predict(test_data)
            mastery = float(prediction.iloc[-1].get('state_predictions', 0.5))
        
        # Final output
        print("\nPrediction results:")
        for i, vocab in enumerate(test_vocabs):
            test_data = df[df['skill_name'] == vocab].iloc[-1:].copy()
            prediction = base_model.predict(test_data)
            mastery = float(prediction.iloc[-1].get('state_predictions', 0.5))
            print(f"  - '{vocab}': mastery = {mastery:.2f}")
        
        return base_model
        
    except Exception as e:
        print(f"Error during model training: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("=== BKT Base Model Pre-Training ===")
    print("Using vocabulary directly from qbank.py")
    
    try:
        model = create_base_bkt_model()
        if model:
            print("\nPre-training successful! The base model is ready for use.")
            print("This model contains all vocabulary items from your curriculum.")
        else:
            print("\nPre-training failed. See error messages above.")
    except Exception as e:
        print(f"Error running pre-training script: {str(e)}")
        import traceback
        traceback.print_exc()