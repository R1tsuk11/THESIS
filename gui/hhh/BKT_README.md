# BKT Engine Refactoring and Testing

This README provides an overview of the changes made to the BKT (Bayesian Knowledge Tracing) engine for lesson/chapter test sessions in the language learning application.

## Problem Statement

The original implementation had several issues:
1. BKT data was being overwritten in the database instead of merged, causing loss of previous session data.
2. Difficulty transfer between vocabulary items was not working as intended.
3. In-session BKT sequence was not correctly merged with database data.

## Solution

A new dedicated lesson/chapter test BKT engine (`lesson_bkt_engine.py`) has been created that:
- Tracks session answers and difficulty factors
- Merges session and database predictions
- Updates and saves merged predictions to the database
- Provides a session-specific BKT sequence for LSTM input

The `run_bkt_and_lstm` function in `levels.py` has been updated to:
- Use the new lesson BKT engine for lessons/chapter tests
- Preserve the original BKT engine for daily reviews
- Display BKT predictions after updates
- Handle BKT sequence caching and fallback robustly

## Testing the Changes

Two test scripts have been provided:

### 1. Test BKT Integration

This script tests the core BKT functionality:

```bash
python test_bkt_integration.py <user_id>
```

This will run tests to verify:
- BKT data is merged (not overwritten) in the database
- Difficulty transfer between vocabulary items works
- In-session BKT sequence is correctly merged with database data
- The system generates valid BKT sequences for LSTM input

### 2. Test Integration with Workflow

This script tests the integration with the main workflow:

```bash
python test_integration.py <user_id>
```

This will test:
- The lesson workflow using the new lesson BKT engine
- The daily review workflow using the original BKT engine
- That both workflows generate valid proficiency predictions

## Implementation Details

### New Files:
- `lesson_bkt_engine.py`: A dedicated BKT engine for lesson/chapter test sessions

### Modified Files:
- `levels.py`: Updated `run_bkt_and_lstm` function to use different engines based on the test type

### Key Components:

1. `LessonSession` class in `lesson_bkt_engine.py`:
   - Tracks correct and incorrect answers within a session
   - Manages session-specific difficulty factors
   - Handles merging of session and database BKT predictions
   - Provides methods for BKT sequence generation

2. Session Management in `lesson_bkt_engine.py`:
   - Functions to create/get sessions, process questions, update BKT, and save to database
   - Thread-safe design with locking mechanisms
   - Comprehensive error handling and logging

3. Integration in `run_bkt_and_lstm`:
   - Uses `is_daily_review` parameter to determine which BKT engine to use
   - Includes fallback mechanisms if the new engine fails
   - Ensures that BKT predictions are displayed after updates

## Expected Outcomes

After these changes:
1. BKT data is properly merged in the database
2. Difficulty factors are transferred between vocabulary items
3. In-session BKT sequence is correctly merged with database data
4. Daily review logic remains unchanged and functional
5. The new lesson/chapter test BKT engine is used in the main workflow
6. The system provides improved proficiency predictions

## Next Steps

After testing:
1. Monitor the system for any edge cases or regressions
2. Collect user feedback on proficiency predictions
3. Consider further optimizations based on performance metrics
