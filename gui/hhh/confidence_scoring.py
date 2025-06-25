import numpy as np
import json
import os
import matplotlib.pyplot as plt
from scipy.stats import norm
from datetime import datetime
import flet as ft

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("[Confidence] Warning: matplotlib not available, visualization disabled")


class BayesianConfidenceSystem:
    """
    Bayesian fusion system for calculating overall system confidence
    in predicting user proficiency in Waray language learning.
    """
    
    def __init__(self, validation_data_path="validation_data"):
        """
        Initialize the confidence system
        
        Args:
            validation_data_path: Path to store/load validation data
        """
        self.validation_data_path = validation_data_path
        os.makedirs(validation_data_path, exist_ok=True)
        
        # Initialize distribution parameters
        self.distributions = {
            "bkt": {
                "correct": {"mean": 0.75, "std": 0.15},  # Initial estimates
                "incorrect": {"mean": 0.45, "std": 0.20}
            },
            "lstm": {
                "correct": {"mean": 0.70, "std": 0.15},
                "incorrect": {"mean": 0.40, "std": 0.20}
            },
            "supermemo": {
                "correct": {"mean": 0.65, "std": 0.15},
                "incorrect": {"mean": 0.35, "std": 0.20}
            },
            "pronunciation": {
                "correct": {"mean": 0.70, "std": 0.15},
                "incorrect": {"mean": 0.40, "std": 0.20}
            }
        }
        
        # Load validation data if available
        self._load_validation_data()
    
    def _load_validation_data(self):
        """Load existing validation data for modeling with fallback to defaults"""
        self.validation_data = {
            "bkt": {"correct": [], "incorrect": []},
            "lstm": {"correct": [], "incorrect": []},
            "supermemo": {"correct": [], "incorrect": []},
            "pronunciation": {"correct": [], "incorrect": []}
        }
        
        validation_file = os.path.join(self.validation_data_path, "validation_data.json")
        try:
            if os.path.exists(validation_file):
                with open(validation_file, 'r') as f:
                    self.validation_data = json.load(f)
                print(f"[Confidence] Loaded validation data from {validation_file}")
                
                # Check if we have enough data
                has_sufficient_data = False
                for model in self.validation_data:
                    if len(self.validation_data[model]["correct"]) >= 3 and len(self.validation_data[model]["incorrect"]) >= 3:
                        has_sufficient_data = True
                        break
                
                if not has_sufficient_data:
                    print("[Confidence] WARNING: Insufficient validation data, using default distributions")
                    self._init_default_distributions()
                else:
                    # Update distribution parameters based on loaded data
                    self._fit_distributions()
            else:
                print(f"[Confidence] No validation data found, using default distributions")
                self._init_default_distributions()
        except Exception as e:
            print(f"[Confidence] Error loading validation data: {e}. Using defaults.")
            self._init_default_distributions()

    def _init_default_distributions(self):
        """Initialize default reasonable distribution parameters"""
        self.distributions = {
            "bkt": {
                "correct": {"mean": 0.75, "std": 0.15},
                "incorrect": {"mean": 0.35, "std": 0.15}
            },
            "lstm": {
                "correct": {"mean": 0.70, "std": 0.15},
                "incorrect": {"mean": 0.30, "std": 0.15}
            },
            "supermemo": {
                "correct": {"mean": 0.80, "std": 0.15},
                "incorrect": {"mean": 0.40, "std": 0.15}
            },
            "pronunciation": {
                "correct": {"mean": 0.70, "std": 0.15},
                "incorrect": {"mean": 0.30, "std": 0.15}
            }
        }
        print("[Confidence] Initialized default distribution parameters")
    
    def add_validation_point(self, model_name, score, was_correct):
        """
        Add a new validation data point
        
        Args:
            model_name: Name of the model ('bkt', 'lstm', 'supermemo', 'pronunciation')
            score: The model's confidence or score (0-1)
            was_correct: Boolean indicating if the prediction was correct
        """
        if model_name not in self.validation_data:
            print(f"[Confidence] Unknown model: {model_name}")
            return
            
        category = "correct" if was_correct else "incorrect"
        self.validation_data[model_name][category].append(float(score))
        
        # Save updated data
        self._save_validation_data()
        
        # Update distribution parameters
        self._fit_distributions()
    
    def _save_validation_data(self):
        """Save validation data to file"""
        validation_file = os.path.join(self.validation_data_path, "validation_data.json")
        try:
            with open(validation_file, 'w') as f:
                json.dump(self.validation_data, f)
        except Exception as e:
            print(f"[Confidence] Error saving validation data: {e}")
    
    def _fit_distributions(self):
        """Fit Gaussian distributions to validation data with safety limits"""
        for model, data in self.validation_data.items():
            for category in ["correct", "incorrect"]:
                values = data[category]
                if len(values) >= 3:  # Need minimum sample size
                    mean = np.mean(values)
                    std = np.std(values)
                    
                    # Safety limits to prevent distributions that are too narrow
                    std = max(0.10, std)  # Minimum std dev of 0.10
                    
                    # Ensure the distributions are reasonably separated
                    if category == "correct":
                        mean = max(0.55, mean)  # "Correct" mean should be at least 0.55
                    else:
                        mean = min(0.45, mean)  # "Incorrect" mean should be at most 0.45
                    
                    self.distributions[model][category] = {
                        "mean": mean,
                        "std": std
                    }
                    print(f"[Confidence] Updated {model} {category} distribution: mean={mean:.2f}, std={std:.2f}")
                else:
                    # Use default values for insufficient data
                    default_mean = 0.75 if category == "correct" else 0.35
                    default_std = 0.15
                    self.distributions[model][category] = {
                        "mean": default_mean,
                        "std": default_std
                    }
                    print(f"[Confidence] Using default {model} {category} distribution: mean={default_mean:.2f}, std={default_std:.2f}")
    
    def calculate_likelihood(self, model, score, for_correct=True):
        """
        Calculate likelihood of observing this score given model was correct/incorrect
        
        Args:
            model: Model name
            score: Score value (0-1)
            for_correct: If True, calculate P(score|correct), else P(score|incorrect)
        
        Returns:
            Likelihood value
        """
        category = "correct" if for_correct else "incorrect"
        if model not in self.distributions:
            print(f"[Confidence] Unknown model in likelihood calculation: {model}")
            return 0.5
        
        params = self.distributions[model][category]
        mean = params["mean"]
        std = params["std"]
        
        # Calculate likelihood using Gaussian probability density function
        likelihood = norm.pdf(score, loc=mean, scale=std)
        
        # Normalize to 0-1 scale (optional but makes interpretation easier)
        max_likelihood = norm.pdf(mean, loc=mean, scale=std)
        normalized_likelihood = min(1.0, likelihood / max_likelihood)
        
        return normalized_likelihood
    
    def calculate_system_confidence(self, model_scores, prior=0.5):
        """
        Calculate overall system confidence using improved Bayesian fusion
        to prevent extreme posterior values.
        """
        # Use log space for calculations to prevent underflow
        log_likelihood_correct = 0.0
        log_likelihood_incorrect = 0.0
        
        print("[Confidence] Calculating Bayesian fusion with these scores:")
        for model, score in model_scores.items():
            if model in self.distributions:
                # Calculate likelihoods with smoothing
                l_correct = self.calculate_likelihood(model, score, True)
                l_incorrect = self.calculate_likelihood(model, score, False)
                
                # Add smoothing to prevent extreme values
                l_correct = 0.05 + 0.90 * l_correct  # Min 0.05, Max 0.95
                l_incorrect = 0.05 + 0.90 * l_incorrect
                
                # Normalize to ensure they sum to 1.0
                total = l_correct + l_incorrect
                l_correct /= total
                l_incorrect /= total
                
                # Convert to log space
                log_likelihood_correct += np.log(l_correct)
                log_likelihood_incorrect += np.log(l_incorrect)
                
                print(f"  - {model}: score={score:.2f}, l_correct={l_correct:.4f}, l_incorrect={l_incorrect:.4f}")
        
        # Convert back from log space
        likelihood_correct = np.exp(log_likelihood_correct)
        likelihood_incorrect = np.exp(log_likelihood_incorrect)
        
        # Normalize (this prevents extreme values)
        total_likelihood = likelihood_correct + likelihood_incorrect
        likelihood_correct /= total_likelihood
        likelihood_incorrect /= total_likelihood
        
        print(f"[Confidence] Normalized likelihoods - correct: {likelihood_correct:.4f}, incorrect: {likelihood_incorrect:.4f}")
        
        # Apply Bayes' rule
        posterior = (likelihood_correct * prior) / (likelihood_correct * prior + likelihood_incorrect * (1 - prior))
        
        # Safety check - this will rarely be triggered now
        if posterior < 0.05 or posterior > 0.95:
            print(f"[Confidence] Moderating extreme confidence value {posterior:.4f}")
            # Moderate extreme values rather than fallback
            posterior = 0.05 + 0.90 * posterior
            
        print(f"[Confidence] Final posterior: {posterior:.4f}")
        
        # Prepare result
        result = {
            "system_confidence": posterior,
            "timestamp": str(datetime.now())
        }
        
        return result
    
    def visualize_distributions(self, save_path=None):
        """
        Generate visualization of the model distributions
        
        Args:
            save_path: Path to save the visualization, if None just display
        """
        if not HAS_MATPLOTLIB:
            print("[Confidence] Visualization not available - matplotlib not installed")
            return
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Model Score Distributions for Correct vs. Incorrect Predictions')
        
        models = list(self.distributions.keys())
        for i, model in enumerate(models):
            row = i // 2
            col = i % 2
            
            ax = axes[row, col]
            model_data = self.validation_data[model]
            
            # Plot histograms if data exists
            if model_data["correct"]:
                ax.hist(model_data["correct"], alpha=0.5, bins=10, label="Correct Predictions", color="green")
            if model_data["incorrect"]:
                ax.hist(model_data["incorrect"], alpha=0.5, bins=10, label="Incorrect Predictions", color="red")
            
            # Plot distributions
            x = np.linspace(0, 1, 100)
            params_correct = self.distributions[model]["correct"]
            params_incorrect = self.distributions[model]["incorrect"]
            
            # Scaling factor for histogram comparison
            scale_c = max(5, len(model_data["correct"]))
            scale_i = max(5, len(model_data["incorrect"]))
            
            y_correct = norm.pdf(x, params_correct["mean"], params_correct["std"]) * scale_c / 10
            y_incorrect = norm.pdf(x, params_incorrect["mean"], params_incorrect["std"]) * scale_i / 10
            
            ax.plot(x, y_correct, 'g-', linewidth=2)
            ax.plot(x, y_incorrect, 'r-', linewidth=2)
            
            ax.set_title(f"{model.upper()} Model")
            ax.set_xlabel("Score")
            ax.set_ylabel("Frequency")
            ax.legend()
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
            print(f"[Confidence] Saved distribution visualization to {save_path}")
        else:
            plt.show()

def interpret_confidence(confidence_score):
    """
    Get human-readable interpretation of confidence score
    
    Args:
        confidence_score: System confidence (0-1)
    
    Returns:
        interpretation: String description
    """
    if confidence_score >= 0.85:
        return "High confidence - model predictions are likely reliable"
    elif confidence_score >= 0.60:
        return "Moderate confidence - predictions should be reasonably accurate"
    else:
        return "Low confidence - system needs more data for reliable predictions"

def add_validation_example(model_name, score, correct_result):
    """
    Add a validation example for training confidence model
    
    Args:
        model_name: Model name ('bkt', 'lstm', 'supermemo', 'pronunciation')
        score: Model's score
        correct_result: Whether the prediction was correct
    """
    confidence_system = BayesianConfidenceSystem()
    confidence_system.add_validation_point(model_name, score, correct_result)
    print(f"[Confidence] Added validation point for {model_name}: score={score}, correct={correct_result}")

# Example usage:
if __name__ == "__main__":
    # 1. Create system
    confidence_system = BayesianConfidenceSystem()
    
    # 2. Add some sample validation data (you'd get this from real data)
    # Add correct/incorrect examples for each model
    for i in range(10):
        # Correct examples - generally higher scores
        confidence_system.add_validation_point("bkt", 0.7 + 0.2 * np.random.random(), True)
        confidence_system.add_validation_point("lstm", 0.65 + 0.25 * np.random.random(), True)
        confidence_system.add_validation_point("supermemo", 0.6 + 0.3 * np.random.random(), True) 
        confidence_system.add_validation_point("pronunciation", 0.7 + 0.2 * np.random.random(), True)
        
        # Incorrect examples - generally lower scores
        confidence_system.add_validation_point("bkt", 0.2 + 0.4 * np.random.random(), False)
        confidence_system.add_validation_point("lstm", 0.25 + 0.35 * np.random.random(), False)
        confidence_system.add_validation_point("supermemo", 0.2 + 0.3 * np.random.random(), False)
        confidence_system.add_validation_point("pronunciation", 0.3 + 0.3 * np.random.random(), False)
    
    # 3. Visualize the distributions
    confidence_system.visualize_distributions("confidence_distributions.png")
    
    # 4. Calculate system confidence for a new user
    test_scores = {
        "bkt": 0.85,
        "lstm": 0.7,
        "supermemo": 0.65,
        "pronunciation": 0.75
    }
    
    result = confidence_system.calculate_system_confidence(test_scores)
    print(f"\nSystem confidence: {result['system_confidence']:.2f}")
    print(f"Interpretation: {interpret_confidence(result['system_confidence'])}")
    
    # FIXED: Remove the broken model_likelihoods access
    print(f"\nCalculation completed with {len(test_scores)} models")

def get_daily_review_completion_count(user_id):
    """Get the number of completed daily reviews - strict checking"""
    try:
        from mainmenu import connect_to_mongoDB
        usercol = connect_to_mongoDB()
        user = usercol.find_one({"user_id": user_id})
        
        if user:
            # Check review_data first (most reliable)
            review_data = user.get("review_data", {})
            completed_reviews = review_data.get("completed", 0)
            
            if completed_reviews > 0:
                print(f"[SuperMemo] Found {completed_reviews} completed daily reviews")
                return completed_reviews
            
            # Alternative: check review_history but be more strict
            review_history = user.get("review_history", {})
            
            # Count vocabularies that have been reviewed MORE than once (indicating spaced repetition)
            spaced_review_count = 0
            for vocab, data in review_history.items():
                times_reviewed = data.get("times_reviewed", 0)
                last_review = data.get("last_review", None)
                
                # Must have been reviewed multiple times AND have a recent review date
                if times_reviewed >= 2 and last_review:
                    try:
                        from datetime import datetime, timedelta
                        last_review_date = datetime.strptime(last_review, "%Y-%m-%d")
                        # Only count if reviewed in the last 30 days
                        if (datetime.now() - last_review_date).days <= 30:
                            spaced_review_count += 1
                    except:
                        pass  # Skip if date parsing fails
            
            if spaced_review_count > 0:
                print(f"[SuperMemo] Found {spaced_review_count} vocabularies with spaced reviews")
                return spaced_review_count
            
            print(f"[SuperMemo] No meaningful review activity found")
            return 0
                
    except Exception as e:
        print(f"[SuperMemo] Error checking daily review completion: {e}")
    
    return 0

def get_system_confidence(bkt_score, lstm_score, supermemo_score=None, pronunciation_score=None, page=None):
    """Calculate system-wide confidence with proper SuperMemo check"""
    try:
        print(f"[Confidence] Calculating Bayesian fusion with these scores:")
        print(f"  - bkt: score={bkt_score:.2f}")
        print(f"  - lstm: score={lstm_score:.2f}")
        
        # Prepare scores dictionary
        scores = {
            "bkt": min(0.95, max(0.05, float(bkt_score))),
            "lstm": min(0.95, max(0.05, float(lstm_score)))
        }
        
        # Check if SuperMemo data is available by looking for daily review completion
        if supermemo_score is None and page is not None:
            # Try to get SuperMemo data from daily review completion
            try:
                user_id = page.session.get("user_id")
                
                if user_id:
                    daily_review_count = get_daily_review_completion_count(user_id)
                    if daily_review_count > 0:
                        # Calculate a basic SuperMemo score based on completion
                        supermemo_score = min(0.9, 0.5 + (daily_review_count * 0.1))
                        print(f"[Confidence] Calculated SuperMemo score from {daily_review_count} completed reviews: {supermemo_score:.2f}")
                    else:
                        print(f"[Confidence] No daily reviews completed yet")
                
            except Exception as e:
                print(f"[Confidence] Error getting SuperMemo data: {e}")
        
        # Add SuperMemo score if available
        if supermemo_score is not None:
            scores["supermemo"] = min(0.95, max(0.05, float(supermemo_score)))
            print(f"  - supermemo: score={supermemo_score:.2f}")
        else:
            pass
        
        # Add pronunciation score if available
        if pronunciation_score is not None:
            scores["pronunciation"] = min(0.95, max(0.05, float(pronunciation_score)))
            print(f"  - pronunciation: score={pronunciation_score:.2f}")
        
        # Calculate final confidence using Bayesian fusion
        confidence_system = BayesianConfidenceSystem()
        result = confidence_system.calculate_system_confidence(scores)
        final_confidence = result["system_confidence"]
        interpretation = interpret_confidence(final_confidence)
        
        # ENHANCED: Print RAW values with high precision
        print(f"\n{'='*70}")
        print(f"SYSTEM-WIDE CONFIDENCE ASSESSMENT - RAW VALUES")
        print(f"{'='*70}")
        
        # Print included component scores with RAW precision
        for model, score in scores.items():
            print(f"{model.upper()} Confidence:    {score:.8f}")
        
        # Print explicit note if SuperMemo is not included
        if supermemo_score is None:
            pass
        
        # ENHANCED: Show additional raw calculation details
        print(f"Overall System Confidence: {final_confidence:.8f}")
        print(f"Interpretation: {interpretation}")
        
        # ENHANCED: Show raw Bayesian calculation details
        print(f"\nRAW BAYESIAN CALCULATION DETAILS:")
        print(f"  - Input Scores (normalized): {[f'{k}={v:.6f}' for k, v in scores.items()]}")
        print(f"  - Raw Posterior Probability: {final_confidence:.10f}")
        print(f"  - Confidence Level (0-1 scale): {final_confidence:.8f}")
        print(f"  - Confidence Percentage: {final_confidence * 100:.6f}%")
        
        # ENHANCED: Show individual model contributions if available
        if hasattr(result, 'model_contributions') and result.model_contributions:
            print(f"\nINDIVIDUAL MODEL CONTRIBUTIONS:")
            for model, contribution in result.model_contributions.items():
                print(f"  - {model.upper()}: {contribution:.8f}")
        
        print(f"{'='*70}")
        
        return {
            "system_confidence": final_confidence,
            "interpretation": interpretation,
            "components": scores,
            "raw_posterior": final_confidence,
            "confidence_percentage": final_confidence * 100
        }
        
    except Exception as e:
        print(f"[Confidence] Error in system confidence calculation: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "system_confidence": 0.5, 
            "interpretation": "Error in confidence calculation",
            "components": {},
            "raw_posterior": 0.5,
            "confidence_percentage": 50.0
        }