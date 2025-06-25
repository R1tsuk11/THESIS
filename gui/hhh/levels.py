from datetime import datetime
import time
import traceback
import flet as ft
import json
import os
from bkt_engine import update_bkt, get_all_p_masteries, get_vocabulary_from_question
from lstm_engine import display_lstm_predictions_table
from lstm_helper import get_lstm_proficiency
from confidence_scoring import get_daily_review_completion_count, get_system_confidence
from supermemo_engine import get_user_proficiency
import pymongo
import threading
import subprocess
from achievements_manager import check_and_unlock_achievements

uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

def create_lesson_blueprint(lesson_questions, lesson_id):
    """Create a lesson blueprint instead of pre-selecting specific questions - FIXED for Pronunciation"""
    
    # Group questions by vocabulary and type
    vocab_structure = {}
    
    for q in lesson_questions:
        vocab = q.get('vocabulary', '').lower()
        q_type = q.get('type', '')
        
        if vocab not in vocab_structure:
            vocab_structure[vocab] = {
                'lesson': [],
                'practice': {},
                'pronunciation': []
            }
        
        if q_type == 'Lesson':
            vocab_structure[vocab]['lesson'].append(q)
        elif q_type == 'Pronunciation':
            vocab_structure[vocab]['pronunciation'].append(q)
        else:
            # Group practice questions by type
            if q_type not in vocab_structure[vocab]['practice']:
                vocab_structure[vocab]['practice'][q_type] = []
            vocab_structure[vocab]['practice'][q_type].append(q)
    
    # Create the blueprint - defines WHAT should appear, not WHICH questions
    lesson_blueprint = {
        'lesson_id': lesson_id,
        'vocabulary_order': [],  # Order of vocabularies
        'question_structure': {},  # What types of questions for each vocab
        'available_questions': lesson_questions,  # All available questions for selection
        'total_estimated_questions': 0
    }
    
    # Define the question structure for each vocabulary
    for vocab, data in vocab_structure.items():
        if data['lesson']:  # Only include vocabularies that have lesson questions
            lesson_blueprint['vocabulary_order'].append(vocab)
            
            # CRITICAL FIX: Include Pronunciation in practice_types if available
            practice_types = list(data['practice'].keys())
            
            # ENHANCED: Add Pronunciation to practice_types if available
            if data['pronunciation']:  # If pronunciation questions exist
                # Add Pronunciation to the front of the list (prioritize it)
                practice_types.insert(0, 'Pronunciation')
                print(f"[BLUEPRINT] ✅ Added Pronunciation to practice_types for '{vocab}'")
            
            # ENHANCED: Adjust practice count if Pronunciation is available
            base_practice_count = 3
            if data['pronunciation']:
                # If we have pronunciation, we want it PLUS 2 other practice questions
                # This ensures pronunciation is always included
                practice_count = base_practice_count  # Keep total at 3, but guarantee pronunciation is one of them
            else:
                practice_count = base_practice_count
            
            # Define structure: 1 Lesson + practice questions
            structure = {
                'lesson': 1,  # Always 1 lesson question
                'practice_count': practice_count,  # Practice questions total
                'practice_types': practice_types,  # FIXED: Now includes Pronunciation
                'has_pronunciation': len(data['pronunciation']) > 0,
                'min_pronunciation': 1 if data['pronunciation'] else 0,  # At least 1 pronunciation if available
                'mandatory_pronunciation': len(data['pronunciation']) > 0  # NEW: Flag for mandatory inclusion
            }
            
            lesson_blueprint['question_structure'][vocab] = structure
            lesson_blueprint['total_estimated_questions'] += 4  # 1 lesson + 3 practice
            
            # ENHANCED DEBUG: Show what practice types are available
            print(f"[BLUEPRINT] {vocab}:")
            print(f"  - Practice types: {practice_types}")
            print(f"  - Has pronunciation: {structure['has_pronunciation']}")
            print(f"  - Practice questions available: {sum(len(questions) for questions in data['practice'].values())}")
            print(f"  - Pronunciation questions available: {len(data['pronunciation'])}")
    
    print(f"[BLUEPRINT] Created lesson blueprint with {len(lesson_blueprint['vocabulary_order'])} vocabularies")
    print(f"[BLUEPRINT] Estimated total questions: {lesson_blueprint['total_estimated_questions']}")
    print(f"[BLUEPRINT] Vocabulary order: {lesson_blueprint['vocabulary_order']}")
    
    return lesson_blueprint

def get_questions_for_lesson(page):
    """Create a lesson blueprint for the correct module and lesson."""
    try:
        # Get module data
        selected_module_levels, selected_module_desc, selected_module_name, user_id = get_module_data(page)
        lesson_id = page.session.get("lesson_id")
        module_id = page.session.get("module_id")  # <-- Ensure this is set in session

        if not lesson_id or not module_id:
            print("No lesson ID or module ID found in session")
            return None

        # Import qbank to get ALL questions for this lesson
        import qbank
        lesson_key = f"Lesson {lesson_id}"

        # Dynamically select the correct module
        module_attr = f"module_{module_id}"
        if hasattr(qbank, module_attr):
            module = getattr(qbank, module_attr)
            if lesson_key in module:
                all_lesson_questions = module[lesson_key]
                lesson_blueprint = create_lesson_blueprint(all_lesson_questions, lesson_id)
            else:
                print(f"[LEVELS] Lesson {lesson_key} not found in {module_attr}")
                return None
        else:
            print(f"[LEVELS] Module {module_attr} not found in qbank")
            return None

        # Store blueprint in session instead of specific questions
        from types import SimpleNamespace
        level_data = SimpleNamespace()
        level_data.lesson_id = lesson_id
        level_data.module_name = selected_module_name
        level_data.lesson_blueprint = lesson_blueprint  # Store blueprint
        level_data.questions_answers = []  # Empty - will be populated by lesson.py

        page.session.set("level_data", level_data)
        print(f"[LEVELS] Created lesson blueprint for {lesson_key}")

        return lesson_blueprint

    except Exception as e:
        print(f"[LEVELS] Error creating lesson blueprint: {e}")
        return None

def run_bkt_and_lstm(page, completion, user_id, correct_answers, incorrect_answers, is_daily_review=False):
    """Run BKT and LSTM models to update proficiency."""
    try:
        # Import the lesson BKT engine at the top of the function
        try:
            from lesson_bkt_engine import (
                process_lesson_question, 
                save_session_to_database,
                get_session_bkt_sequence,
                reset_session
            )
            lesson_engine_available = True
        except ImportError as e:
            print(f"[BKT] Warning: Lesson BKT engine not available: {e}")
            lesson_engine_available = False

        # FIXED: Initialize historical_mastery_values early
        historical_mastery_values = []
        try:
            arami = pymongo.MongoClient(uri)["arami"]
            user = arami["users"].find_one({"user_id": int(user_id)})
            if user and "mastery_history" in user:
                historical_mastery_values = user["mastery_history"]
        except Exception as e:
            print(f"[BKT] Error getting historical mastery: {e}")
            historical_mastery_values = []

        # CRITICAL CHANGE: Branch based on session type
        if is_daily_review:
            # For daily reviews, use the original BKT engine (preserve existing functionality)
            print("[BKT] Processing daily review session with ORIGINAL BKT engine")
            
            # Use the existing update_bkt function for daily reviews
            review_scale_factor = 1.5
            current_bkt_sequence = update_bkt(user_id, correct_answers, incorrect_answers, 
                                      impact_scale=review_scale_factor, 
                                      is_daily_review=True)
        else:
            # For lessons and chapter tests, use the new lesson BKT engine
            print("[BKT] Processing lesson/chapter test session with NEW LESSON BKT engine")
            
            if lesson_engine_available:
                # Process each correct answer with the lesson BKT engine
                for question_id, question in correct_answers.items():
                    vocab = get_vocabulary_from_question(question)
                    if vocab:
                        difficulty = getattr(question, 'difficulty', 1)
                        print(f"[LessonBKT] Processing correct answer for '{vocab}' with difficulty {difficulty}")
                        process_lesson_question(user_id, question_id, question, True)
                        
                # Process each incorrect answer with the lesson BKT engine
                for question_id, question in incorrect_answers.items():
                    vocab = get_vocabulary_from_question(question)
                    if vocab:
                        difficulty = getattr(question, 'difficulty', 1)
                        print(f"[LessonBKT] Processing incorrect answer for '{vocab}' with difficulty {difficulty}")
                        process_lesson_question(user_id, question_id, question, False)
                
                # FIXED: Get the BKT sequence from the lesson session
                current_bkt_sequence = get_session_bkt_sequence(user_id)
                print(f"[LessonBKT] Generated sequence with {len(current_bkt_sequence)} values: {current_bkt_sequence}")
                # If we got an empty or default sequence, build it from session data
                if not current_bkt_sequence or current_bkt_sequence == [0.5, 0.55, 0.6, 0.65, 0.7]:
                    print("[LessonBKT] Building sequence from lesson session data...")
                    try:
                        from lesson_bkt_engine import create_or_get_session
                        session = create_or_get_session(user_id)
                        if session and session.session_predictions:
                            # Get actual mastery values from the session
                            masteries = []
                            for vocab, prediction in session.session_predictions.items():
                                mastery = prediction.get('p_mastery', 0.5)
                                masteries.append(mastery)
                                print(f"[LessonBKT] Adding '{vocab}' mastery: {mastery:.3f}")
                            
                            if masteries:
                                current_bkt_sequence = masteries
                                print(f"[LessonBKT] Built sequence from session data: {current_bkt_sequence}")
                    except Exception as e:
                        print(f"[LessonBKT] Error building sequence from session: {e}")
                
                # Save the lesson session to database (preserving data, not overwriting)
                save_result = save_session_to_database(user_id)
                print(f"[LessonBKT] Session save result: {save_result}")
                
            else:
                # Fallback to original BKT engine if lesson engine is not available
                print("[BKT] Falling back to original BKT engine for lesson/test")
                current_bkt_sequence = update_bkt(user_id, correct_answers, incorrect_answers, 
                                          impact_scale=1.0, 
                                          is_daily_review=False)
        
        # Validate BKT sequence before proceeding
        if not current_bkt_sequence or len(current_bkt_sequence) == 0:
            print("[BKT] WARNING: No current BKT sequence available, falling back to database values")
            current_bkt_sequence = get_all_p_masteries(user_id)
            
        # Ensure we have a valid sequence for LSTM
        if not current_bkt_sequence:
            print("[BKT] ERROR: Could not generate any BKT sequence, using default values")
            current_bkt_sequence = [0.5, 0.55, 0.6, 0.65, 0.7]  # Default sequence to prevent LSTM failure

        # CRITICAL: Always use the merged BKT sequence for LSTM input
        try:
            from bkt_engine import ensure_bkt_data_loaded
            current_bkt_sequence = ensure_bkt_data_loaded(user_id, force_db_refresh=True)
            print(f"[BKT] Final sequence for LSTM (merged): {current_bkt_sequence}")
        except Exception as e:
            print(f"[BKT] Error loading merged BKT sequence: {e}")

        # NEW: Display BKT predictions table BEFORE running LSTM
        try:
            print("\n" + "="*70)
            print("BKT PREDICTIONS TABLE (Before LSTM Processing)")
            print("="*70)
            
            if not is_daily_review and lesson_engine_available:
                # Process with lesson BKT engine
                for question_id, question in correct_answers.items():
                    vocab = get_vocabulary_from_question(question)
                    if vocab:
                        process_lesson_question(user_id, question_id, question, True)
                        
                for question_id, question in incorrect_answers.items():
                    vocab = get_vocabulary_from_question(question)
                    if vocab:
                        process_lesson_question(user_id, question_id, question, False)
                
                # CRITICAL: Save lesson data to database BEFORE getting sequence
                save_result = save_session_to_database(user_id)
                print(f"[LessonBKT] Session save result: {save_result}")
                
                # CRITICAL: Ensure main BKT engine has the latest data
                try:
                    from bkt_engine import ensure_bkt_data_loaded
                    current_bkt_sequence = ensure_bkt_data_loaded(user_id, force_db_refresh=True)
                    print(f"[BKT] Refreshed sequence from database: {len(current_bkt_sequence)} values")
                except Exception as e:
                    print(f"[BKT] Error refreshing from database: {e}")
                    current_bkt_sequence = get_session_bkt_sequence(user_id)
                
                # Validate sequence quality
                if len(current_bkt_sequence) < 5:
                    print("[LessonBKT] Warning: Sequence too short, enhancing...")
                    # Build from session data more carefully
                    try:
                        from lesson_bkt_engine import create_or_get_session
                        session = create_or_get_session(user_id)
                        if session and session.session_predictions:
                            # Get all vocabulary masteries including database values
                            enhanced_sequence = []
                            
                            # Add session vocabulary first (most recent learning)
                            for vocab, pred in session.session_predictions.items():
                                mastery = pred.get('p_mastery', 0.5)
                                enhanced_sequence.append(mastery)
                                print(f"[LessonBKT] Added '{vocab}' mastery: {mastery:.3f} to sequence")
                            
                            if len(enhanced_sequence) >= 5:
                                current_bkt_sequence = enhanced_sequence
                                print(f"[LessonBKT] Enhanced sequence: {current_bkt_sequence}")
                            
                    except Exception as e:
                        print(f"[LessonBKT] Error enhancing sequence: {e}")
                
                # Final validation
                if not current_bkt_sequence or len(current_bkt_sequence) < 3:
                    print("[LessonBKT] Using fallback sequence")
                    current_bkt_sequence = [0.3, 0.4, 0.55, 0.65, 0.75]  # Progressive learning sequence
                # Use the new lesson BKT display function
                from lesson_bkt_engine import display_lesson_bkt_predictions, get_lesson_bkt_summary
                
                # Show summary first
                summary = get_lesson_bkt_summary(user_id)
                print(f"[LessonBKT] Session Summary: {summary}")
                
                # Show detailed table
                vocab_count = display_lesson_bkt_predictions(user_id)
                print(f"[LessonBKT] Displayed {vocab_count} vocabulary predictions from lesson session")
                
            else:
                # For daily reviews, use the original BKT display function
                from bkt_engine import display_bkt_predictions
                vocab_count = display_bkt_predictions(user_id)
                print(f"[BKT] Displayed {vocab_count} vocabulary predictions from daily review")
            
            print("="*70)
            print("Now running LSTM with BKT sequence...")
            print("="*70 + "\n")
        except Exception as e:
            print(f"[BKT] Error displaying predictions table: {e}")
        
        # Get historical sequences for LSTM context
        historical_mastery_values = []
        try:
            arami = pymongo.MongoClient(uri)["arami"]
            user = arami["users"].find_one({"user_id": int(user_id)})
            if user and "bkt_data" in user and "historical_mastery_sequences" in user["bkt_data"]:
                historical_mastery_values = user["bkt_data"]["historical_mastery_sequences"]
                print(f"[DEBUG] Found {len(historical_mastery_values)} historical mastery sequences")
        except Exception as e:
            print(f"[DEBUG] Error retrieving historical BKT data: {str(e)}")
        
        # Cache the current BKT sequence for consistency
        try:
            cache_key = f"bkt_sequence_{user_id}"
            with open(cache_key, 'w') as f:
                json.dump(current_bkt_sequence, f)
            print(f"[BKT] Cached sequence to {cache_key}")
        except Exception as e:
            print(f"[BKT] Error caching sequence: {e}")
            
            # Prepare input for LSTM model
        with open("temp_lstm_input.json", "w") as f:
            json.dump({
                "bkt_sequence": current_bkt_sequence,
                "historical_sequences": historical_mastery_values if not is_daily_review else [],
                "completion_percentage": completion,
                "sequence_metadata": {
                    "source": "lesson_session" if not is_daily_review else "daily_review",
                    "vocab_count": len(current_bkt_sequence),
                    "user_id": user_id
                }
            }, f)
            
        print(f"[LSTM] Input prepared with sequence length: {len(current_bkt_sequence)}")
            
        print(f"[LSTM] Input prepared with sequence length: {len(current_bkt_sequence)}")
        
        # Run the LSTM model to get proficiency
        result = get_lstm_proficiency(current_bkt_sequence, completion, user_id)
        proficiency = result.get("proficiency", 0)
        lstm_confidence = result.get("confidence", 0)
        method = result.get("method", "none")
        
        # CRITICAL FIX: Save LSTM proficiency to database immediately
        try:
            arami = pymongo.MongoClient(uri)["arami"]
            users_col = arami["users"]
            
            # Update user document with LSTM proficiency
            update_result = users_col.update_one(
                {"user_id": int(user_id)},
                {"$set": {
                    "lstm_proficiency": proficiency,
                    "lstm_confidence": lstm_confidence,
                    "lstm_last_updated": int(time.time())
                }}
            )
            print(f"[LSTM] Saved proficiency {proficiency:.4f} to database: matched={update_result.matched_count}, modified={update_result.modified_count}")
            
        except Exception as e:
            print(f"[LSTM] Error saving proficiency to database: {e}")
        
        # Store in session for immediate use
        page.session.set("lstm_proficiency", proficiency)
        page.session.set("lstm_confidence", lstm_confidence)
        page.session.set("method", method)
        
        print(f"[LSTM] Proficiency: {proficiency:.4f}, Confidence: {lstm_confidence:.2f}, Method: {method}")
        
        # Display the LSTM predictions in a formatted table
        try:
            # FIXED: Import and use the display function
            from lstm_engine import display_lstm_predictions_table
            lstm_display_result = display_lstm_predictions_table(current_bkt_sequence, user_id)
            page.session.set("lstm_display_result", lstm_display_result)
            print(f"[LSTM] Generated predictions table: {lstm_display_result}")
        except ImportError as e:
            print(f"[LSTM] Could not import display function: {e}")
            # Try alternative display
            try:
                print(f"[LSTM] BKT Sequence Display:")
                for i, mastery in enumerate(current_bkt_sequence):
                    print(f"[LSTM]   Vocab {i+1}: {mastery:.3f}")
            except Exception as e2:
                print(f"[LSTM] Error displaying sequence: {e2}")
        except Exception as e:
            print(f"[LSTM] Error displaying predictions table: {e}")
        
        # Calculate BKT confidence score

        from bkt_engine import calculate_bkt_confidence, get_custom_bkt
        try:
            custom_bkt = get_custom_bkt(user_id)
            vocab_list = custom_bkt.get_vocabulary_in_order() if custom_bkt else []
            bkt_confidences = []
            if vocab_list:
                for vocab in vocab_list:
                    params = custom_bkt.vocab_parameters.get(vocab, {})
                    mastery = params.get("p_mastery", 0.5)
                    guess = params.get("guess", 0.25)
                    slip = params.get("slip", 0.1)
                    conf = calculate_bkt_confidence(mastery, guess, slip, vocab=vocab, params=params)
                    bkt_confidences.append(conf)
                    print(f"[BKT] Calculated confidence for {vocab}: {conf:.4f}")
                bkt_score = sum(bkt_confidences) / len(bkt_confidences)
            else:
                # Fallback: calculate from current_bkt_sequence if available
                if current_bkt_sequence:
                    avg_mastery = sum(current_bkt_sequence) / len(current_bkt_sequence)
                    # Use default guess/slip for fallback
                    conf = calculate_bkt_confidence(avg_mastery, 0.25, 0.1)
                    bkt_score = conf
                    print(f"[BKT] Fallback confidence from sequence: {conf:.4f}")
                else:
                    bkt_score = 0.5
            print(f"[BKT] Average BKT confidence score: {bkt_score:.3f}")
        except Exception as e:
            print(f"[BKT] Error calculating BKT confidence: {e}")
            bkt_score = 0.5

        try:
            print(f"[BKT] Average mastery score: {bkt_score:.3f}")
            
            # Get value from the table generation (which has the 0.76 value)
            lstm_score = lstm_display_result
            print(f"[LSTM] Using LSTM model confidence: {lstm_score}")
            
            # Get SuperMemo data if available
            try:
                from supermemo_engine import get_average_efactor, get_completion_rate
                
                # CRITICAL: Only get SuperMemo score if user has actually completed reviews
                avg_efactor = get_average_efactor(user_id)
                if avg_efactor is not None:
                    supermemo_score = avg_efactor / 2.5  # Normalize to 0-1 range
                    print(f"[SuperMemo] Using efactor-based score: {supermemo_score:.3f}")
                else:
                    # Check daily review completion as alternative
                    daily_review_count = get_daily_review_completion_count(user_id)
                    if daily_review_count > 0:
                        supermemo_score = min(0.9, 0.5 + (daily_review_count * 0.1))
                        print(f"[SuperMemo] Using daily review count-based score: {supermemo_score:.3f}")
                    else:
                        supermemo_score = None
                        print(f"[SuperMemo] No SuperMemo data available - user hasn't completed any reviews")
                        
            except Exception as e:
                print(f"[SuperMemo] Error getting SuperMemo data: {e}")
                supermemo_score = None
            
            # Calculate overall system confidence - LET IT HANDLE ALL PRINTING
            confidence_result = get_system_confidence(bkt_score, lstm_score, supermemo_score, page=page)
            system_confidence = confidence_result["system_confidence"]
            confidence_interpretation = confidence_result["interpretation"]
            
            # Store in session
            page.session.set("system_confidence", system_confidence)
            page.session.set("confidence_interpretation", confidence_interpretation)
            
        except Exception as e:
            print(f"[Confidence] Error calculating system confidence: {e}")
            import traceback
            traceback.print_exc()

        # Record confidence validation if available
        if page.session.get("proficiency_confidence") is not None and correct_answers and incorrect_answers:
            record_confidence_validation(page, correct_answers, incorrect_answers)
        
        # Return the LSTM result
        return result
        
    except Exception as e:
        print(f"[BKT] Error in run_bkt_and_lstm: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"proficiency": 0, "confidence": 0, "method": "error", "error": str(e)}

def compute_completion(page):
    """Calculate user completion percentage with proper session storage"""
    try:
        user_id = page.session.get("user_id")
        if not user_id:
            return 0
        
        # Get modules from session
        modules = page.session.get("modules")
        if not modules:
            print("[Progress] No modules found in session")
            return 0
        
        total_lessons = 0
        completed_lessons = 0
        
        for module in modules:
            levels = getattr(module, 'levels', [])
            total_lessons += len(levels)
            
            for level in levels:
                if getattr(level, 'completed', False):
                    completed_lessons += 1
        
        if total_lessons == 0:
            completion_percentage = 0
        else:
            completion_percentage = (completed_lessons / total_lessons) * 100
        
        print(f"[Progress] Calculated: {completed_lessons}/{total_lessons} = {completion_percentage:.1f}%")
        
        # CRITICAL: Store in session for logout
        page.session.set("completion_percentage", completion_percentage)
        
        # FIXED: Save completion percentage to database WITHOUT triggering logout
        try:
            import pymongo
            arami = pymongo.MongoClient("mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/")["arami"]
            users_col = arami["users"]
            
            # Direct database update without using save_user method
            update_result = users_col.update_one(
                {"user_id": int(user_id)},
                {"$set": {"completion_percentage": completion_percentage}}
            )
            
            if update_result.modified_count > 0:
                print(f"[Progress] ✅ Updated completion percentage in database: {completion_percentage:.1f}%")
            else:
                print(f"[Progress] ⚠️ Database update failed or no change needed")
                
        except Exception as e:
            print(f"[Progress] Error updating completion percentage in database: {e}")
        
        return completion_percentage
        
    except Exception as e:
        print(f"[Progress] Error calculating completion: {e}")
        return 0

def merge_answer_data(existing, new):
    """Merge dictionaries while preserving key structure and merging nested values."""
    for k, v in new.items():
        if k in existing and isinstance(existing[k], dict) and isinstance(v, dict):
            existing[k].update(v)  # Shallow merge
        else:
            existing[k] = v  # Add or replace
    return existing

def get_module_data(page):
    """Get module data from session."""
    # Get module_id and modules from session
    module_id = page.session.get("module_id")
    modules = page.session.get("modules")
    user_id = page.session.get("user_id")

    # Debug logging
    print(f"[DEBUG] Getting module data: module_id={module_id}, user_id={user_id}")
    print(f"[DEBUG] Found {len(modules) if modules else 0} modules in session")

    # Check if we have all required data
    if not module_id or not modules or not user_id:
        print("[ERROR] Missing required session data for module processing")
        print(f"  - module_id: {module_id}")
        print(f"  - modules: {'Present' if modules else 'Missing'}")
        print(f"  - user_id: {user_id}")
        
        # Try to load from temp file if available
        try:
            with open("temp_modules.json", "r") as f:
                from mainmenu import Module
                modules = [Module(m) for m in json.load(f)]
                print(f"[DEBUG] Loaded {len(modules)} modules from temp file")
                
                # Re-set the session data
                page.session.set("modules", modules)
                
                # If module_id is missing but we loaded modules, use the first one
                if not module_id and modules:
                    module_id = modules[0].id
                    page.session.set("module_id", module_id)
                    print(f"[DEBUG] Using first module ID: {module_id}")
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            print(f"[ERROR] Failed to load modules from temp file: {str(e)}")
            # Return safe defaults to prevent unpacking error
            return [], "Module not found", "Module not found", user_id

    # Find the selected module
    selected_module = None
    for module in modules:
        if getattr(module, "id", None) == module_id:
            selected_module = module
            break
    
    # If module not found, return safe defaults
    if not selected_module:
        print(f"[ERROR] Module with ID {module_id} not found")
        return [], "Module not found", "Module not found", user_id
    
    # Return module data
    return (
        getattr(selected_module, "levels", []), 
        getattr(selected_module, "desc", "No description available"), 
        getattr(selected_module, "waray_name", "Untitled Module"), 
        user_id
    )

def get_chapter_test_status(user_id, module_id):
    """Get the most current chapter test status from database"""
    if not user_id or not module_id:
        return False, False, 0
        
    try:
        import pymongo
        arami = pymongo.MongoClient("mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/")["arami"]
        users_col = arami["users"]
        
        user_doc = users_col.find_one({"user_id": int(user_id)})
        if user_doc:
            for module in user_doc.get("modules", []):
                if module.get("id") == int(module_id):
                    chapter_test_data = module.get("chapter_test", {})
                    completed = chapter_test_data.get("completed", False)
                    grade_percentage = chapter_test_data.get("grade_percentage", 0)
                    return completed, grade_percentage >= 70, grade_percentage
                    
    except Exception as e:
        print(f"[CHAPTER TEST] Error checking status: {e}")
    
    return False, False, 0

def refresh_chapter_test_status(page):
    """Refresh chapter test status from database and update UI"""
    user_id = page.session.get("user_id")
    module_id = page.session.get("module_id")
    
    if not user_id or not module_id:
        return
        
    try:
        import pymongo
        arami = pymongo.MongoClient("mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/")["arami"]
        users_col = arami["users"]
        
        user_doc = users_col.find_one({"user_id": int(user_id)})
        if user_doc:
            # FIXED: Properly handle session modules
            try:
                modules = page.session.get("modules")
                if modules is None:
                    modules = []
            except Exception as e:
                print(f"[REFRESH] Error getting modules from session: {e}")
                modules = []
            
            for db_module in user_doc.get("modules", []):
                if db_module.get("id") == int(module_id):
                    # Find corresponding session module and update it
                    for session_module in modules:
                        if hasattr(session_module, 'id') and str(session_module.id) == str(module_id):
                            if hasattr(session_module, 'chapter_test'):
                                # Update chapter test data from database
                                db_ct = db_module.get("chapter_test", {})
                                session_module.chapter_test.completed = db_ct.get("completed", False)
                                session_module.chapter_test.grade_percentage = db_ct.get("grade_percentage", 0)
                                
                                print(f"[REFRESH] Updated chapter test status: completed={session_module.chapter_test.completed}, grade={session_module.chapter_test.grade_percentage}")
                            break
                    break
            
            # FIXED: Properly set the modules back to session
            try:
                page.session.set("modules", modules)
            except Exception as e:
                print(f"[REFRESH] Error setting modules to session: {e}")
            
    except Exception as e:
        print(f"[REFRESH] Error refreshing chapter test status: {e}")
        import traceback
        traceback.print_exc()

def get_chapter_test(page):
    modules = page.session.get("modules")
    module_id = page.session.get("module_id")

    if not modules:
        try:
            with open("temp_modules.json", "r") as f:
                modules = json.load(f)
        except FileNotFoundError:
            print("Temp module cache not found.")
            return None

    if not module_id:
        print("Module ID not found in session.")
        return None

    for module in modules:
        if str(module.id) == str(module_id):
            return module.chapter_test  # <-- now it's safe!

    print(f"No matching module with ID {module_id} found.")
    return None

def get_updated_data(page):
    updated_data = page.session.get("updated_data")
    if not updated_data:
        return None

    grade_percentage, formatted_time, total_response_time, correct_answers, incorrect_answers, updated_questions = updated_data
    return {
        "grade": grade_percentage,
        "time": formatted_time,
        "correct": correct_answers,
        "incorrect": incorrect_answers,
        "questions": updated_questions,
        "total_response_time": total_response_time,
    }

def clear_temp_module_cache():
    if os.path.exists("temp_modules.json"):
        os.remove("temp_modules.json")

def record_confidence_validation(page, correct_answers, incorrect_answers):
    """Record validation data for improving the confidence prediction model"""
    try:
        from confidence_scoring import add_validation_example
        
        # Get model outputs (predictions before the test/lesson)
        bkt_score = page.session.get("bkt_average")
        lstm_confidence = page.session.get("proficiency_confidence")
        
        if bkt_score is None or lstm_confidence is None:
            print("[Confidence] Missing prediction data for validation")
            return
            
        # Calculate actual performance score
        total_questions = len(correct_answers) + len(incorrect_answers)
        if total_questions == 0:
            return
            
        actual_score = len(correct_answers) / total_questions
        
        # Was the prediction correct? (did high confidence match high performance?)
        # A prediction is considered "correct" if:
        # - High confidence (>0.7) → high score (>70%)
        # - Low confidence (<0.5) → low score (<60%)
        
        threshold = 0.7  # Performance threshold
        was_correct_bkt = (bkt_score >= 0.7 and actual_score >= threshold) or \
                          (bkt_score < 0.5 and actual_score < 0.6)
                          
        was_correct_lstm = (lstm_confidence >= 0.7 and actual_score >= threshold) or \
                           (lstm_confidence < 0.5 and actual_score < 0.6)
        
        # Add validation data points
        add_validation_example("bkt", bkt_score, was_correct_bkt)
        add_validation_example("lstm", lstm_confidence, was_correct_lstm)
        
        print(f"[Confidence] Added validation points - BKT: {bkt_score:.2f} (correct: {was_correct_bkt}), " +
              f"LSTM: {lstm_confidence:.2f} (correct: {was_correct_lstm})")
        
    except Exception as e:
        print(f"[Confidence] Error recording validation: {e}")

def levels_page(page: ft.Page, image_urls: list):
    """Levels selection page"""
    try:
        # Try to get module data
        selected_module_levels, selected_module_desc, selected_module_name, user_id = get_module_data(page)
        
    except Exception as e:
        # If failed, try to recover
        print(f"[ERROR] Failed to get module data: {str(e)}")
        
        # Show friendly error message
        error_view = ft.View(
            "/levels",
            [
                ft.Container(
                    content=ft.Column([
                        ft.Text("Session data couldn't be loaded.", size=20, text_align=ft.TextAlign.CENTER),
                        ft.Text("Returning to main menu...", size=16, text_align=ft.TextAlign.CENTER),
                        ft.ElevatedButton("Main Menu", on_click=lambda _: page.go("/main-menu"))
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    expand=True
                )
            ],
            bgcolor="#FFFFFF"
        )
        
        page.views.append(error_view)
        page.update()
        
        # Schedule return to main menu
        import asyncio
        async def delayed_navigate():
            await asyncio.sleep(2)
            page.go("/main-menu")
            
        asyncio.create_task(delayed_navigate())
        return
    
    page.title = f"Arami - \"{selected_module_name}\" Levels"
    page.bgcolor = "#FFFFFF"
    page.padding = 0
    level_rows = []
    row = []
    refresh_chapter_test_status(page)

    def cache_library_to_temp(library):
        """Cache the user's vocabulary library to a temporary file"""
        with open("temp_library.json", "w") as f:
            json.dump(library, f)
        print(f"[DEBUG] Cached library with {len(library)} vocabulary items to temp file")

    updated = get_updated_data(page)

    if updated and updated["questions"]:
        # Get any question to extract identifying info (safe if list isn't empty)
        first_question = updated["questions"][0]
        
        # SAFETY FIX: Ensure the question has required attributes
        if not hasattr(first_question, 'lesson_id'):
            print("[LEVELS] WARNING: First question missing lesson_id, trying to get from session")
            first_question.lesson_id = page.session.get("lesson_id", 1)
            
        if not hasattr(first_question, 'module_name'):
            print("[LEVELS] WARNING: First question missing module_name, trying to get from session")
            level_data = page.session.get("level_data")
            if level_data and hasattr(level_data, 'module_name'):
                first_question.module_name = level_data.module_name
            else:
                first_question.module_name = "Module 1"  # Fallback
        
        completion_time = updated["total_response_time"]
        grade_percentage = updated["grade"]

        # FIXED: Find and update the correct level
        completed_level = None
        for level in selected_module_levels:
            if level.lesson_id == first_question.lesson_id and level.module_name == first_question.module_name:
                level.questions_answers = updated["questions"]
                level.completed = updated["grade"] >= level.pass_threshold
                level.completion_time = completion_time
                level.grade_percentage = grade_percentage
                completed_level = level  # Store reference to the completed level
                break

        # FIXED: Only try database update if we found and completed a level
        if completed_level and completed_level.completed:
            try:
                # Save the completed level to the database immediately
                arami = pymongo.MongoClient(uri)["arami"]
                users_col = arami["users"]
                
                print(f"[LEVELS] Attempting to update lesson {completed_level.lesson_id} for user {user_id}")
                print(f"[LEVELS] Grade: {grade_percentage}%, Time: {completion_time}s")
                
                # Check if lesson was already marked complete by lesson.py
                user_doc = users_col.find_one({"user_id": int(user_id)})
                if user_doc:
                    for module in user_doc.get("modules", []):
                        if module.get("id") == int(page.session.get("module_id")):
                            for level in module.get("levels", []):
                                if level.get("lesson_id") == completed_level.lesson_id:
                                    current_status = level.get("completed", False)
                                    print(f"[LEVELS] Current database status for lesson {completed_level.lesson_id}: {current_status}")
                                    
                                    if current_status:
                                        print(f"[LEVELS] ✅ Lesson {completed_level.lesson_id} already marked complete in database")
                                        return  # Exit early, no need to update again
                
                # If we reach here, the lesson wasn't marked complete, so update it
                print(f"[LEVELS] Lesson not yet marked complete, updating database...")
                
                # Rest of your existing database update code...
                update_query = {
                    "user_id": int(user_id),
                    "modules.id": int(page.session.get("module_id"))
                }
                
                update_operation = {
                    "$set": {
                        "modules.$[module].levels.$[level].completed": True,
                        "modules.$[module].levels.$[level].completion_time": completion_time,
                        "modules.$[module].levels.$[level].grade_percentage": grade_percentage,
                        "modules.$[module].levels.$[level].last_completed": datetime.datetime.utcnow().isoformat()
                    }
                }
                
                array_filters = [
                    {"module.id": int(page.session.get("module_id"))},
                    {"level.lesson_id": completed_level.lesson_id}
                ]
                
                update_result = users_col.update_one(
                    update_query,
                    update_operation,
                    array_filters=array_filters
                )
                
                print(f"[LEVELS] Database update result:")
                print(f"  - Matched: {update_result.matched_count}")
                print(f"  - Modified: {update_result.modified_count}")
                
                if update_result.modified_count > 0:
                    print(f"[LEVELS] ✅ Successfully updated lesson {completed_level.lesson_id} completion")
                else:
                    print(f"[LEVELS] ⚠️ No documents modified - lesson may already be complete")
                    
            except Exception as e:
                print(f"[LEVELS] ❌ Failed to update level completion: {str(e)}")
                import traceback
                traceback.print_exc()

        # FALLBACK: Still try to check achievements with the session data
        try:
            check_and_unlock_achievements(user_id, page)
            from mainmenu import sync_user_progress
            sync_user_progress(page, user_id)
        except Exception as e2:
            print(f"[ERROR] Failed fallback operations: {str(e2)}")

    completion = compute_completion(page)

    if completion:
        print("DEBUG (levels.py) Completion:", completion)
    else:
        print("DEBUG (levels.py) Completion is None")

    if os.path.exists("temp_chaptertest_data.json"):
        with open("temp_chaptertest_data.json", "r") as f:
            chaptertest_data = json.load(f)
        # Call BKT update just for chapter test data

        correct_answers = page.session.get("correct_answers")
        incorrect_answers = page.session.get("incorrect_answers")

        if correct_answers and incorrect_answers:
            # Merge with existing data
            correct_answers = merge_answer_data(correct_answers, chaptertest_data.get("questions_correct", {}))
            incorrect_answers = merge_answer_data(incorrect_answers, chaptertest_data.get("questions_incorrect", {}))
        else:
            # Connect to MongoDB
            arami = pymongo.MongoClient(uri)["arami"]
            usercol = arami["users"]
            # Retrieve questions_correct and questions_incorrect from MongoDB
            user_data = usercol.find_one({"user_id": user_id})
            if not user_data:
                print(f"User with ID {user_id} not found in MongoDB.")
                return
            questions_correct = user_data.get("questions_correct", {})
            questions_incorrect = user_data.get("questions_incorrect", {})
            # Merge with existing data
            correct_answers = merge_answer_data(questions_correct, chaptertest_data.get("questions_correct", {}))
            incorrect_answers = merge_answer_data(questions_incorrect, chaptertest_data.get("questions_incorrect", {}))
        
        threading.Thread(target=run_bkt_and_lstm, args=(page, completion, user_id, correct_answers, incorrect_answers)).start()

    elif updated:
        # Load previous session data (initialize if none)
        correct_answers = page.session.get("correct_answers")
        incorrect_answers = page.session.get("incorrect_answers")
        if correct_answers:
            correct_answers = merge_answer_data(correct_answers, updated["correct"])
        else:
            correct_answers = updated["correct"]
            page.session.set("correct_answers", correct_answers)   

        if incorrect_answers:
            incorrect_answers = merge_answer_data(incorrect_answers, updated["incorrect"])
        else:
            incorrect_answers = updated["incorrect"]
            page.session.set("incorrect_answers", incorrect_answers)

        completion_time = updated["total_response_time"]
        grade_percentage = updated["grade"]

        page.session.set("correct_answers", correct_answers)
        page.session.set("incorrect_answers", incorrect_answers)

        user_id = page.session.get("user_id")
        user_library = page.session.get("user_library")
        if user_library is None:
            user_library = []
            # Also set it in the session so it's available for future use
            page.session.set("user_library", user_library)
            # Cache the empty library
            cache_library_to_temp(user_library)
            print("[DEBUG] Initialized empty user library")

        if updated and updated["questions"]:
            # Collect new vocabulary words
            new_vocabs = []
            for question in updated["questions"]:
                if hasattr(question, "vocabulary") and question.vocabulary:
                    vocab = question.vocabulary
                    # Check if vocabulary already exists in library
                    if vocab not in user_library and vocab not in new_vocabs:
                        new_vocabs.append(vocab)
            
            # Add new vocabulary words to the library
            if new_vocabs:
                print(f"[DEBUG] Adding {len(new_vocabs)} new vocabulary words to library")
                user_library.extend(new_vocabs)
                page.session.set("user_library", user_library)
                cache_library_to_temp(user_library)

        threading.Thread(target=run_bkt_and_lstm, args=(page, completion, user_id, correct_answers, incorrect_answers)).start()

    def go_back(e):
        """Navigate back to the main menu"""
        selected_module_levels = page.session.get("module_levels")
        modules = page.session.get("modules")
        module_id = page.session.get("module_id")
 
        if modules and selected_module_levels and module_id:
            for module in modules:
                if str(module.id) == str(module_id):
                    # Update levels in the matched module
                    updated_levels = []
                    for lvl in selected_module_levels:
                        if getattr(lvl, "type", "") != "chaptertest":  # skip chaptertest
                            updated_levels.append(lvl)
                    module.levels = updated_levels
                    break

            # Save updated modules back to the user
            user = page.session.get("user")
            if user:
                user.modules = modules
                page.session.set("user", user)
            else:
                print("User not found in session. Cannot save updated modules.")

        clear_temp_module_cache()
        page.go("/main-menu")

    def level_select(e, level_num):
        level_index = int(level_num) - 1
        level_data = selected_module_levels[level_index]

        # Prerequisite and completion checks...
        prerequisite_levels = selected_module_levels[:level_index]
        all_prerequisites_completed = all(level.completed for level in prerequisite_levels)

        if not all_prerequisites_completed:
            page.open(ft.SnackBar(ft.Text("You must complete previous levels first."), bgcolor="#FF0000"))
            page.update()
            return

        # Prevent re-entering a finished level
        if level_data.completed:
            page.open(ft.SnackBar(ft.Text("Level already completed!"), bgcolor="#FF0000"))
            page.update()
            return

        # Fetch current proficiency
        user_id = page.session.get("user_id")
        proficiency = page.session.get("lstm_proficiency")
        if proficiency is None:
            proficiency = get_user_proficiency(user_id)
        print(f"[DEBUG] User proficiency: {proficiency}")

        # CHANGED: Use blueprint instead of pre-selecting questions
        page.session.set("lesson_id", level_data.lesson_id)
        page.session.set("lesson_name", f"Level {level_num}")
        
        # Create lesson blueprint instead of selecting specific questions
        blueprint = get_questions_for_lesson(page)
        
        if blueprint:
            print(f"[LEVELS] Created blueprint for level {level_num} with {len(blueprint['vocabulary_order'])} vocabularies")
            print(f"[LEVELS] Vocabularies: {blueprint['vocabulary_order']}")
            page.go("/lesson")
        else:
            print(f"[LEVELS] Failed to create blueprint for level {level_num}")
            page.open(ft.SnackBar(ft.Text("Could not load lesson. Please try again."), bgcolor="#FF0000"))
            page.update()

    def chapter_test_select(page):
        # Check if all levels are completed first
        all_levels_completed = all(level.completed for level in selected_module_levels)
        
        if not all_levels_completed:
            page.open(ft.SnackBar(ft.Text("You must complete all levels first."), bgcolor="#FF0000"))
            page.update()
            return
        
        # Get chapter test data
        ct_level = get_chapter_test(page)
        if not ct_level:
            page.open(ft.SnackBar(ft.Text("Chapter test data not found."), bgcolor="#FF0000"))
            page.update()
            return
        
        # ENHANCED: Check completion status from multiple sources
        user_id = page.session.get("user_id")
        module_id = page.session.get("module_id")
        
        # Check database for the most up-to-date completion status
        chapter_test_completed = False
        chapter_test_passed = False
        grade_percentage = 0
        
        if user_id and module_id:
            try:
                import pymongo
                arami = pymongo.MongoClient("mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/")["arami"]
                users_col = arami["users"]
                
                user_doc = users_col.find_one({"user_id": int(user_id)})
                if user_doc:
                    for module in user_doc.get("modules", []):
                        if module.get("id") == int(module_id):
                            chapter_test_data = module.get("chapter_test", {})
                            chapter_test_completed = chapter_test_data.get("completed", False)
                            grade_percentage = chapter_test_data.get("grade_percentage", 0)
                            pass_threshold = getattr(ct_level, 'pass_threshold', 70)
                            chapter_test_passed = grade_percentage >= pass_threshold
                            break
                            
                print(f"[CHAPTER TEST] Database check - Completed: {chapter_test_completed}, Grade: {grade_percentage}%, Passed: {chapter_test_passed}")
                
            except Exception as e:
                print(f"[CHAPTER TEST] Error checking database: {e}")
                # Fallback to session data
                chapter_test_completed = hasattr(ct_level, 'completed') and ct_level.completed
                if hasattr(ct_level, 'grade_percentage') and hasattr(ct_level, 'pass_threshold'):
                    chapter_test_passed = ct_level.grade_percentage >= ct_level.pass_threshold
                else:
                    chapter_test_passed = False
        
        # CRITICAL: Block access if chapter test is completed and passed
        if chapter_test_completed and chapter_test_passed:
            page.open(ft.SnackBar(
                ft.Text(f"Chapter Test already completed with {grade_percentage:.1f}%! Check next module."), 
                bgcolor="#4CAF50"
            ))
            page.update()
            return
        
        # Allow retake if failed
        if chapter_test_completed and not chapter_test_passed:
            page.open(ft.SnackBar(
                ft.Text(f"Retaking Chapter Test (Previous: {grade_percentage:.1f}%)"), 
                bgcolor="#FF9800"
            ))
            page.update()
            # Continue to allow retake
        
        # Proceed to the chapter test
        page.session.set("ct_data", ct_level)
        page.go("/chaptertest")

    def create_level_button(level_number, is_available=True):
        # Use dark gray for unavailable levels, blue for available ones
        color = "#4285F4" if is_available else "#666666"
        
        return ft.Container(
            content=ft.Text(
                str(level_number),
                color="#FFFFFF",
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=color,
            width=60,
            height=60,
            border_radius=10,
            alignment=ft.alignment.center,
            data=level_number,
            # Always keep the click handler, but handle availability inside level_select
            on_click=lambda e, level=level_number: level_select(e, level)  # Fixed lambda capture
    )

    # Get current user and module info
    user_id = page.session.get("user_id")
    module_id = page.session.get("module_id")
    
    # Get chapter test status from database
    ct_completed, ct_passed, ct_grade = get_chapter_test_status(user_id, module_id)
    
    # Check if all levels are completed
    all_levels_completed = all(level.completed for level in selected_module_levels)
    
    # Determine chapter test button appearance and behavior
    if ct_completed and ct_passed:
        # Completed and passed - green with checkmark
        chapter_test_color = "#4CAF50"
        chapter_test_icon = ft.Icons.CHECK_CIRCLE
        chapter_test_tooltip = f"Completed ({ct_grade:.1f}%)"
    elif ct_completed and not ct_passed:
        # Completed but failed - orange with retry
        chapter_test_color = "#FF9800"
        chapter_test_icon = ft.Icons.REFRESH
        chapter_test_tooltip = f"Failed ({ct_grade:.1f}%) - Click to retry"
    elif all_levels_completed:
        # Ready to take - blue
        chapter_test_color = "#4285F4"
        chapter_test_icon = ft.Icons.GRADING
        chapter_test_tooltip = "Ready to take Chapter Test"
    else:
        # Locked - gray
        chapter_test_color = "#666666"
        chapter_test_icon = ft.Icons.LOCK
        chapter_test_tooltip = "Complete all levels first"

    chapter_test_button = ft.Container(
        content=ft.Icon(
            name=chapter_test_icon,  
            color="#FFFFFF",
            size=28,
        ),
        bgcolor=chapter_test_color,
        width=60,
        height=60,
        border_radius=10,
        alignment=ft.alignment.center,
        data="chaptertest",
        tooltip=chapter_test_tooltip,
        on_click=lambda e: chapter_test_select(page)
    )

        # Process level buttons
    level_count = 0
    for index, level in enumerate(selected_module_levels, start=1):
        # Check if all prerequisites for this level are completed
        prerequisite_levels = selected_module_levels[:index-1]
        all_prerequisites_completed = all(level.completed for level in prerequisite_levels)
        
        # Create button with appropriate color based on availability
        level_button = create_level_button(index, all_prerequisites_completed)

        row.append(level_button)
        level_count += 1

        # Add chapter test button next to level 5
        if index == 5:
            row.append(chapter_test_button)
            
        # When we have 3 buttons, or it's the last button, add the row
        if len(row) == 3 or index == len(selected_module_levels):
            level_rows.append(
                ft.Row(
                    row,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10
                )
            )
            row = []  # reset for the next row

    # If we didn't add the chapter test button yet (in case there are fewer than 5 levels)
    if level_count < 5 and not any(chapter_test_button in r.controls for r in level_rows):
        if row:  # If there's an incomplete row
            row.append(chapter_test_button)
            level_rows.append(
                ft.Row(
                    row,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10
                )
            )
        else:  # Start a new row for the chapter test button
            level_rows.append(
                ft.Row(
                    [chapter_test_button],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10
                )
            )

    user_id = page.session.get("user_id")
    if user_id:
        check_and_unlock_achievements(user_id, page)

    # Header with gradient background and title
    header = ft.Container(
        content=ft.Stack([
            ft.Container(
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["#0066FF", "#9370DB"],
                ),
                height=170,
            ),
            ft.Container(
                bgcolor="#4285F4",
                padding=ft.padding.symmetric(vertical=1, horizontal=16),
                margin=ft.margin.only(top=150),
                width=300,
                height=75,
            ),
            ft.Container(
                content=ft.Text(
                    selected_module_name,
                    size=26,
                    color="#FFFFFF",
                    weight=ft.FontWeight.W_900,
                    text_align=ft.TextAlign.LEFT,
                ),
                bgcolor="#4285F4",
                border_radius=30,
                padding=ft.padding.symmetric(vertical=1, horizontal=16),
                margin=ft.margin.only(top=150),
                width=350,
                height=75,
                alignment=ft.alignment.center_left,
            ),
            
            # Button in top-right
            ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color="#FFFFFF",
                    icon_size=24,
                    on_click=lambda _: page.go("/main-menu")
                    ),
                alignment=ft.alignment.top_left,
                padding=10,  # Space from the edges
            )
        ]),
        height=230,
    )

    explanation = ft.Container(
        content=ft.Text(
            selected_module_desc,
            color="#000000",
            size=14,
            text_align=ft.TextAlign.CENTER,
        ),
        margin=ft.margin.only(top=10,bottom=15,left=10, right=10),
        alignment=ft.alignment.center,
    )

    level_grid = ft.Container(
        content=ft.Column(
            level_rows,
            spacing=10, 
        alignment=ft.MainAxisAlignment.CENTER),
        margin=ft.margin.only(top=10),
    )

    bottom_nav = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.MENU_BOOK_OUTLINED,
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=lambda _: page.go("/word-library")
                    ),
                    border_radius=20,
                    width=50, 
                    height=50, 
                    alignment=ft.alignment.center, 
                    padding=0, 
                    margin=5,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.HOME_OUTLINED,
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=lambda _: page.go("/main-menu")
                    ),
                    border_radius=20,
                    width=50,
                    height=50,
                    alignment=ft.alignment.center,
                    padding=0,
                    margin=5,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.PERSON_OUTLINED,
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=lambda _: page.go("/achievements")
                    ),
                    border_radius=20,
                    width=50,
                    height=50,
                    alignment=ft.alignment.center,
                    padding=0,
                    margin=5,
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.SETTINGS_OUTLINED,  
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=lambda _: page.go("/settings")
                    ),
                    border_radius=20,
                    width=50,
                    height=50,
                    alignment=ft.alignment.center,
                    padding=0,
                    margin=5,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            vertical_alignment=ft.CrossAxisAlignment.CENTER, 
            height=60,  
        ),
        border_radius=25,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#30b4fc", "#2980b9"],
        ),
        height=70,  
        padding=ft.padding.symmetric(horizontal=15, vertical=5),
        margin=ft.margin.only(bottom=10, left=10, right=10),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, "#000000"),
            offset=ft.Offset(0, 0),
        ),
        alignment=ft.alignment.center,
    )

    content = ft.Column(
        [
            header,
            explanation,
            level_grid,
            ft.Container(expand=True),
            bottom_nav,
        ],
        spacing=0,
        expand=True,
    )

    page.views.append(ft.View(
        "/levels",
        controls=[content],
        bgcolor="#FFFFFF",
        padding=0
    ))
    page.update()
