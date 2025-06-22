"""
BKT Engine Factory - Creates appropriate BKT engines based on context
"""

# Constants for engine types
LESSON_ENGINE = "lesson"
REVIEW_ENGINE = "review"

# Import engine implementations
from .lesson_engine import LessonBKTEngine
# For now, we'll use the same implementation for reviews
# In the future, this could be a specialized ReviewBKTEngine class
ReviewBKTEngine = LessonBKTEngine

def get_bkt_engine(engine_type, user_id):
    """
    Factory function to create the appropriate BKT engine
    
    Args:
        engine_type: The type of engine to create (LESSON_ENGINE or REVIEW_ENGINE)
        user_id: The user ID to associate with the engine
        
    Returns:
        The appropriate BKT engine instance
    """
    if engine_type == LESSON_ENGINE:
        return LessonBKTEngine(user_id)
    elif engine_type == REVIEW_ENGINE:
        return ReviewBKTEngine(user_id)
    else:
        # Default to lesson engine
        print(f"[BKT Factory] Unknown engine type '{engine_type}', defaulting to lesson engine")
        return LessonBKTEngine(user_id)
