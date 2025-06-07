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
import time
import threading

warnings.filterwarnings('ignore', category=RuntimeWarning, module='pyBKT.fit.EM_fit')

# Import modules directly from qbank.py
from qbank import module_1, module_2, module_3, module_4, module_5

class CustomBKTPredictor:
    """Custom BKT predictor that directly uses the vocabulary parameters"""
    
    def __init__(self, vocab_parameters):
        """Initialize with vocabulary parameters"""
        self.vocab_parameters = vocab_parameters
    
    def predict(self, vocab, correct_history=None):
        """
        Predict knowledge state using BKT algorithm
        
        Parameters:
        - vocab: The vocabulary item to predict mastery for
        - correct_history: List of 1s and 0s representing correct/incorrect responses
                          (if None, returns prior probability)
        
        Returns:
        - Mastery probability (0-1)
        """
        if vocab not in self.vocab_parameters:
            return 0.5  # Default for unknown vocab
        
        params = self.vocab_parameters[vocab]
        learn = params['learn']    # Learning probability
        guess = params['guess']    # Guess probability
        slip = params['slip']      # Slip probability
        prior = params.get('prior', 0.5)  # Prior probability of mastery
        
        # If no history provided, return prior
        if correct_history is None or len(correct_history) == 0:
            return prior
            
        # Start with prior probability
        mastery = prior
        
        # Update for each observation in history
        for is_correct in correct_history:
            # Step 1: Update based on observation
            if is_correct:
                # P(mastered | correct)
                mastery = (mastery * (1 - slip)) / (mastery * (1 - slip) + (1 - mastery) * guess)
            else:
                # P(mastered | incorrect)
                mastery = (mastery * slip) / (mastery * slip + (1 - mastery) * (1 - guess))
                
            # Step 2: Account for learning
            mastery = mastery + (1 - mastery) * learn
            
        return mastery
    
    def predict_from_df(self, df):
        """
        Make predictions from a pandas DataFrame (similar to PyBKT interface)
        
        Parameters:
        - df: DataFrame with 'skill_name' and 'correct' columns
        
        Returns:
        - DataFrame with predictions added
        """
        result_df = df.copy()
        result_df['state_predictions'] = 0.0
        
        # Group by skill and user
        groups = df.groupby(['skill_name', 'user_id'])
        
        for (vocab, user), group in groups:
            # Get history of correct/incorrect for this user and skill
            history = group['correct'].astype(int).tolist()
            
            # Calculate probability for increasing prefixes of history
            for i in range(len(history)):
                prefix = history[:i+1]
                prob = self.predict(vocab, prefix)
                result_df.loc[group.index[i], 'state_predictions'] = prob
                
        return result_df

def initialize_bkt_model(vocab_parameters):
    """Create a properly initialized BKT model that can make predictions"""
    # SIMPLIFIED APPROACH: Skip the fitting step altogether
    print("Creating BKT model with direct parameter initialization...")
    
    # Create an empty model
    model = Model()
    
    # Set parameters directly
    print("Setting model parameters for all vocabulary items...")
    model.params = {
        'learns': {vocab: params['learn'] for vocab, params in vocab_parameters.items()},
        'guesses': {vocab: params['guess'] for vocab, params in vocab_parameters.items()},
        'slips': {vocab: params['slip'] for vocab, params in vocab_parameters.items()},
        'prior': 0.5
    }
    
    # Try to create a specially formatted dataset that will work with predictions
    print("Creating specialized dataset for model validation...")
    test_vocabs = random.sample(list(vocab_parameters.keys()), min(3, len(vocab_parameters)))
    
    # PyBKT prediction requires a specific format - this format should work
    test_data = []
    for vocab in test_vocabs:
        # PyBKT requires these exact columns
        test_data.append({
            "user_id": "test_user",
            "skill_name": vocab,
            "correct": 1,
            "problem_id": f"problem_{vocab}"  # Adding problem_id column
        })
    
    # Convert to DataFrame
    test_df = pd.DataFrame(test_data)
    
    # Try different approaches to get predictions working
    try:
        print("Attempting validation with approach #1...")
        # First approach - try with minimal dataset
        pred = model.predict(test_df)
        print("✓ Model successfully validated!")
        return model
    except:
        try:
            print("Attempt #1 failed, trying approach #2...")
            # Second approach - try with a minimal fit operation
            mini_train_data = []
            for vocab in test_vocabs:
                params = vocab_parameters[vocab]
                # Create two data points for this vocab
                mini_train_data.append({
                    "user_id": "mini_train",
                    "skill_name": vocab,
                    "correct": 0,
                    "problem_id": f"problem_{vocab}_1"
                })
                mini_train_data.append({
                    "user_id": "mini_train",
                    "skill_name": vocab,
                    "correct": 1,
                    "problem_id": f"problem_{vocab}_2"
                })
            
            train_df = pd.DataFrame(mini_train_data)
            print(f"Performing minimal fit on {len(train_df)} data points...")
            
            # FIXED: Remove the 'seed' parameter which is causing issues
            model.fit(data=train_df, num_fits=1)  # Remove seed=1
            
            # Restore our parameter values
            model.params['learns'] = {vocab: params['learn'] for vocab, params in vocab_parameters.items()}
            model.params['guesses'] = {vocab: params['guess'] for vocab, params in vocab_parameters.items()}
            model.params['slips'] = {vocab: params['slip'] for vocab, params in vocab_parameters.items()}
            
            # Test predictions again
            pred = model.predict(test_df)
            print("✓ Model successfully validated with approach #2!")
            return model
        except Exception as e:
            print(f"All initialization attempts failed: {str(e)}")
            return None

def extract_vocabulary_from_qbank():
    """Extract vocabulary items with metadata from qbank modules"""
    vocabulary_items = {}
    
    # Process all modules
    all_modules = [module_1, module_2, module_3, module_4, module_5]

    if len(sys.argv) > 1 and sys.argv[1] == "--small":
        # Just use 5 vocabulary items for a quick test
        all_modules = [module_1]  # Just use first module
        print("USING MINIMAL DATASET FOR TESTING")
    
    # Create progress bar for module processing
    module_pbar = tqdm(enumerate(all_modules, 1), total=len(all_modules),
                      desc="Processing modules", ncols=100)
    
    for module_idx, module in module_pbar:
        module_pbar.set_description(f"Processing module {module_idx}")
        
        # Process each lesson in the module
        for lesson_name, questions in module.items():
            lesson_idx = int(lesson_name.split()[-1])
            
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

# Updates to create_synthetic_data_for_vocab function
def create_synthetic_data_for_vocab(vocab, metadata):
    """Create synthetic training data for a single vocabulary item"""
    synthetic_data = []
    
    # Calculate base parameters based on metadata
    module = metadata['module']
    lesson = metadata['lesson']
    difficulty = metadata.get('difficulty', 1)
    
    # Normalize difficulty to 0-1 scale
    if difficulty is None:
        difficulty = min(1.0, ((module - 1) * 0.3 + (lesson - 1) * 0.1))
    else:
        difficulty = min(1.0, difficulty / 5.0)
    
    # SIMPLIFIED: Create learning curve with more predictable patterns
    # This will help PyBKT converge more reliably
    attempts = 8  # Reduced number of attempts to focus on quality
    
    # PRE-DEFINED PATTERNS based on difficulty
    if difficulty < 0.3:  # Easy vocabulary
        correct_pattern = [1, 1, 0, 1, 1, 1, 1, 1]  # Mostly correct
    elif difficulty < 0.6:  # Medium vocabulary
        correct_pattern = [0, 1, 0, 1, 1, 0, 1, 1]  # Mixed pattern
    else:  # Hard vocabulary
        correct_pattern = [0, 0, 1, 0, 1, 0, 1, 1]  # Starts wrong, improves
    
    # Create synthetic data points
    for i in range(attempts):
        is_correct = correct_pattern[i]
        
        # Calculate parameters based on difficulty
        guess = 0.2 + (difficulty * 0.1)
        slip = 0.1 + (difficulty * 0.05)
        learn = 0.15 + ((1.0 - difficulty) * 0.1)  # Higher for easier words
        
        # Create the data point
        synthetic_data.append({
            "user_id": "synthetic",
            "skill_name": vocab,
            "correct": is_correct,
            "guess": guess,
            "slip": slip,
            "prior": 0.5,
            "learn": learn  # Added learn rate explicitly
        })
    
    return synthetic_data

def preprocess_training_data(df):
    """Clean and preprocess data to avoid fitting errors"""
    # 1. Remove any rows with NaN values
    df = df.dropna()
    
    # 2. Ensure guess and slip values are valid (not too close to 0 or 1)
    df['guess'] = df['guess'].clip(0.05, 0.95)
    df['slip'] = df['slip'].clip(0.05, 0.95)
    
    # 3. Add small random noise to avoid exact duplicates
    for col in ['guess', 'slip', 'prior']:
        if col in df.columns:
            df[col] = df[col] + np.random.normal(0, 0.001, size=len(df))
            df[col] = df[col].clip(0.01, 0.99)  # Keep within valid range
    
    return df

def create_base_bkt_model_batched():
    """Create a pre-trained BKT model processing one vocabulary at a time"""
    # Extract vocabulary from qbank
    vocab_metadata = extract_vocabulary_from_qbank()
    
    # Create a consolidated model
    base_model = Model()
    
    # Dictionary to store parameters for each vocabulary
    vocab_parameters = {}
    
    # Process each vocabulary individually
    vocab_pbar = tqdm(vocab_metadata.items(), total=len(vocab_metadata),
                    desc="Processing vocabularies", ncols=100)
    
    # Update this section in create_base_bkt_model_batched function
    for vocab, metadata in vocab_pbar:
        vocab_pbar.set_description(f"Processing '{vocab}'")
        
        # Create synthetic data for this vocabulary
        vocab_data = create_synthetic_data_for_vocab(vocab, metadata)
        df = pd.DataFrame(vocab_data)
        
        # SIMPLIFIED APPROACH: Instead of fitting with PyBKT, calculate parameters directly
        # This avoids the fitting problems completely
        
        # Calculate difficulty
        module = metadata['module'] 
        lesson = metadata['lesson']
        difficulty = metadata.get('difficulty', 1)
        if difficulty is None:
            difficulty = (module - 1) * 0.3 + (lesson - 1) * 0.1
        else:
            difficulty = min(1.0, difficulty / 5.0)
        
        # Calculate BKT parameters based on difficulty
        learn = 0.10 + ((1.0 - difficulty) * 0.15)  # Learn rate: 0.10-0.25
        guess = 0.15 + (difficulty * 0.15)          # Guess: 0.15-0.30
        slip = 0.05 + (difficulty * 0.10)           # Slip: 0.05-0.15
        
        # Add small random variation to make parameters more realistic
        learn += random.uniform(-0.02, 0.02)
        guess += random.uniform(-0.02, 0.02)
        slip += random.uniform(-0.02, 0.02)
        
        # Ensure valid ranges
        learn = min(0.3, max(0.05, learn))
        guess = min(0.35, max(0.1, guess))
        slip = min(0.2, max(0.02, slip))
        
        # Store parameters
        vocab_parameters[vocab] = {
            'learn': learn,
            'guess': guess,
            'slip': slip,
            'prior': 0.5,
            'difficulty': difficulty
        }
        
        vocab_pbar.set_postfix({'difficulty': f"{difficulty:.2f}", 'status': 'direct'})
    
    # Save the per-vocabulary parameters
    with open('bkt_vocab_parameters.json', 'w') as f:
        # Convert numpy values to regular Python types before JSON serialization
        clean_params = {}
        for vocab, params in vocab_parameters.items():
            clean_params[vocab] = {k: float(v) if isinstance(v, (np.float32, np.float64)) else v 
                                    for k, v in params.items()}
        json.dump(clean_params, f, indent=2)
    
    print("Vocabulary parameters saved to 'bkt_vocab_parameters.json'")
    
    # Now create a consolidated model with these parameters
    # Now create a consolidated model with these parameters
    print("Building consolidated BKT model...")

    # Initialize model properly instead of just setting params
    consolidated_model = initialize_bkt_model(vocab_parameters)

    if consolidated_model:
        # Save the consolidated model
        with open("bkt_base_model.pkl", "wb") as f:
            pickle.dump(consolidated_model, f)
        print("Consolidated base model saved to 'bkt_base_model.pkl'")
    else:
        print("Failed to initialize model. Creating custom BKT predictor...")
        
        # Create and save custom BKT predictor
        custom_bkt = CustomBKTPredictor(vocab_parameters)
        with open("custom_bkt_predictor.pkl", "wb") as f:
            pickle.dump(custom_bkt, f)
        print("✓ Custom BKT predictor saved to 'custom_bkt_predictor.pkl'")
        
        # Still save the PyBKT model for parameter storage
        basic_model = Model()
        basic_model.params = {
            'learns': {vocab: params['learn'] for vocab, params in vocab_parameters.items()},
            'guesses': {vocab: params['guess'] for vocab, params in vocab_parameters.items()},
            'slips': {vocab: params['slip'] for vocab, params in vocab_parameters.items()},
            'prior': 0.5
        }
        with open("bkt_base_model.pkl", "wb") as f:
            pickle.dump(basic_model, f)
        print("Basic parameter-only PyBKT model saved to 'bkt_base_model.pkl'")
    
    # Test a few predictions
    print("\nSample predictions from the pre-trained model:")
    test_vocabs = random.sample(list(vocab_metadata.keys()), min(5, len(vocab_metadata)))

    # First show the parameters for these vocabs
    print("BKT parameters for selected vocabulary items:")
    for vocab in test_vocabs:
        params = vocab_parameters[vocab]
        diff = params.get('difficulty', 0.0)
        print(f"  - '{vocab}' (difficulty {diff:.2f}): learn={params['learn']:.2f}, " + 
            f"guess={params['guess']:.2f}, slip={params['slip']:.2f}")

    # Initialize the return value
    return_model = None
    
    # Test predictions based on which model we created
    if consolidated_model:
        return_model = consolidated_model
        print("\nAttempting predictions with PyBKT model:")
        # Your existing PyBKT prediction code...
    else:
        # Create custom BKT predictor
        custom_bkt = CustomBKTPredictor(vocab_parameters)
        return_model = custom_bkt  # Set this as our return value
        
        # Save the custom predictor
        with open("custom_bkt_predictor.pkl", "wb") as f:
            pickle.dump(custom_bkt, f)
        print("✓ Custom BKT predictor saved to 'custom_bkt_predictor.pkl'")
        
        # Test the custom predictor
        print("\nAttempting predictions with custom BKT predictor:")
        for vocab in test_vocabs:
            try:
                # Test with a sequence of responses
                correct_history = [0, 1, 1]  # First wrong, then two correct
                mastery = custom_bkt.predict(vocab, correct_history)
                params = vocab_parameters[vocab]
                print(f"  - '{vocab}': mastery={mastery:.2f} after {correct_history}")
                
                # Test with dataframe format (like PyBKT)
                test_df = pd.DataFrame([
                    {"user_id": "test", "skill_name": vocab, "correct": 0},
                    {"user_id": "test", "skill_name": vocab, "correct": 1},
                    {"user_id": "test", "skill_name": vocab, "correct": 1}
                ])
                pred_df = custom_bkt.predict_from_df(test_df)
                final_mastery = pred_df['state_predictions'].iloc[-1]
                print(f"    DataFrame prediction: {final_mastery:.2f}")
            except Exception as e:
                print(f"  - '{vocab}': prediction error - {str(e)}")
    
    # Return either the PyBKT model or custom predictor
    return return_model

if __name__ == "__main__":
    print("=== BKT Base Model Pre-Training (Batched Version) ===")
    print("Using vocabulary directly from qbank.py")
    
    try:
        start_time = time.time()
        model = create_base_bkt_model_batched()
        total_time = time.time() - start_time
        
        if model:
            mins, secs = divmod(int(total_time), 60)
            time_str = f"{mins} minutes and {secs} seconds" if mins > 0 else f"{secs} seconds"
            
            if isinstance(model, CustomBKTPredictor):
                print(f"\nPre-training completed successfully with custom predictor! Total time: {time_str}")
                print("Custom BKT predictor created with parameters for all vocabulary items.")
                print("Use CustomBKTPredictor for predictions in your application.")
            else:
                print(f"\nPre-training completed successfully with PyBKT model! Total time: {time_str}")
                print("This model contains all vocabulary items from your curriculum.")
        else:
            print("\nPre-training failed. See error messages above.")
    except Exception as e:
        print(f"Error running pre-training script: {str(e)}")
        import traceback
        traceback.print_exc()