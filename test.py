import pymongo
import sys

uri = "mongodb+srv://adam:adam123xd@arami.dmrnv.mongodb.net/"

def connect_to_mongoDB():
    arami = pymongo.MongoClient(uri)
    aramidb = arami["arami"]
    usercol = aramidb["users"]
    return usercol

def test_mongoDB():
    usercol = connect_to_mongoDB()
    if usercol is not None:
        print("Connected to MongoDB")
    else:
        print("Failed to connect to MongoDB")
        sys.exit("Terminating the program due to MongoDB connection failure.")
    

def insert_user(user_id, user_name, proficiency, password, word_library, questions_wrong, questions_correct, achievements):
    usercol = connect_to_mongoDB()
    user = {
        "user_id": user_id,
        "user_name": user_name,
        "proficiency": proficiency,
        "password": password,
        "word_library": word_library,
        "questions_wrong": questions_wrong,
        "questions_correct": questions_correct,
        "achievements": achievements
    }
    if usercol.insert_one(user):
        print("User inserted successfully.")
    else:
        print("Failed to insert user.")
    
    return

def update_user(user_id, user_name, proficiency, password, word_library, questions_wrong, questions_correct, achievements):
    usercol = connect_to_mongoDB()
    user = {
        "user_id": user_id,
        "user_name": user_name,
        "proficiency": proficiency,
        "password": password,
        "word_library": word_library,
        "questions_wrong": questions_wrong,
        "questions_correct": questions_correct,
        "achievements": achievements
    }
    result = usercol.update_one(
        {"user_id": user_id}, 
        {"$set": user}
    )
    return result.modified_count > 0

def delete_user(user_id):
    usercol = connect_to_mongoDB()
    if usercol.delete_one({"user_id": user_id}):
        print("User deleted successfully.")
    else:
        print("Failed to delete user.")
    
    return

def get_next_user_id():
    arami = pymongo.MongoClient(uri)["arami"]
    aramidb = arami["counter"]
    
    # Ensure the initial value is set
    aramidb.update_one(
        {"_id": "user_id"},
        {"$setOnInsert": {"seq": 0}},
        upsert=True
    )
    
    ctr = aramidb.find_one_and_update(
        {"_id": "user_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=pymongo.ReturnDocument.AFTER
    )
    return ctr["seq"]

def find_user(user_name, password):
    """
    Find a user by username and password
    Returns the user document or None if not found
    """
    usercol = connect_to_mongoDB()
    user = usercol.find_one({"user_name": user_name, "password": password})
    if user:
        print("Successful login.")
        return user
    return None

class User: # User class
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.user_name = None
        self.proficiency = 0
        self.password = None
        self.word_library = []
        self.questions_wrong = {}
        self.questions_correct = {}
        self.achievements = Achievements()

    def signup(self): # Sign up a new user
        self.user_id = get_next_user_id()
        print("Signing up new user...")
        self.user_name = input("Enter your username: ")
        self.password = input("Enter your password: ")
        insert_user(self.user_id, self.user_name, self.proficiency, self.password, self.word_library, self.questions_wrong, self.questions_correct, self.achievements.achievements)
        print("User signed up successfully.")
        LearningApp().start()

    def login(self, app=None):  # Add app parameter
        """
        Log in an existing user
        Args:
            app: The LearningApp instance to use
        """
        while True:
            self.user_name = input("Enter your username: ")
            self.password = input("Enter your password: ")
            user = find_user(self.user_name, self.password)
            if user:
                # Update user attributes from database
                self.user_id = user["user_id"]
                self.proficiency = user["proficiency"]
                self.word_library = user["word_library"]
                self.questions_wrong = user["questions_wrong"]
                self.questions_correct = user["questions_correct"]
                self.achievements.achievements = user["achievements"]
                
                # Use the existing app instance
                if app:
                    app.main_menu()
                break
            else:
                print("Invalid credentials. Try again.")

    def analyze_proficiency(self, total_questions): # Analyze user proficiency
        return (self.proficiency / total_questions) * 100

    def record_answer(self, question, answer, correct): # Record user answer
        if correct:
            self.proficiency += 1
            self.questions_correct[question] = answer
            self.word_library.append(answer)
        else:
            self.questions_wrong[question] = answer

    def save(self): # Save user data
        success = update_user(
            self.user_id,
            self.user_name,
            self.proficiency,
            self.password,
            self.word_library,
            self.questions_wrong,
            self.questions_correct,
            self.achievements.achievements
        )
        if success:
            print("User data saved successfully.")
        else:
            print("Failed to save user data.")

class Achievements: # Achievements class
    def __init__(self): # Initialize achievements
        self.achievements = {
            "First Level Completed": False,
            "First Module Completed": False,
            "All Modules Completed": False,
            "All Levels Completed": False,
            "All Chapter Tests Passed": False,
            "All Achievements Unlocked": False
        }

    def unlock_achievement(self, achievement): # Unlock an achievement
        self.achievements[achievement] = True
        print(f"Achievement Unlocked: {achievement}")

    def display_achievements(self): # Display achievements
        for achievement, unlocked in self.achievements.items():
            print(f"{achievement}: {'Unlocked' if unlocked else 'Locked'}")


class Level: # Level class
    def __init__(self, questions_answers):
        self.questions_answers = questions_answers
        self.completed = False
        self.pass_threshold = 70


class ChapterTest: # Chapter Test class
    def __init__(self, questions_answers):
        self.questions_answers = questions_answers
        self.completed = False
        self.pass_threshold = 80


class Module: # Module class
    def __init__(self, name):
        self.name = name
        self.completed = False
        self.levels = self.create_levels()
        self.chapter_test = self.create_chapter_test()

    def create_levels(self): # Create levels
        return [
            Level({"Q1": "A1", "Q2": "A2"}),
            Level({"Q3": "A3", "Q4": "A4"})
        ]
    
    def create_chapter_test(self): # Create chapter test
        return ChapterTest({"Q1": "A1", "Q2": "A2", "Q3": "A3", "Q4": "A4"})

    def run_review(self, user): # Run review level
        print("Reviewing wrong answers...")
        while user.questions_wrong:
            for question, answer in list(user.questions_wrong.items()):
                print(f"Question: {question}")
                print(f"Your answer: {answer}")
                correct_answer = None
                for level in self.levels:
                    if question in level.questions_answers:
                        correct_answer = level.questions_answers[question]
                        break
                if correct_answer is None and question in self.chapter_test.questions_answers:
                    correct_answer = self.chapter_test.questions_answers[question]
                
                if correct_answer is not None:
                    print(f"Correct answer: {correct_answer}")
                    new_answer = input("Enter the correct answer: ")
                    if new_answer == correct_answer:
                        user.record_answer(question, new_answer, True)
                        del user.questions_wrong[question]
                    else:
                        print("Incorrect. Please try again.")
        print("Review completed.")
        if not user.questions_wrong:
            print("No wrong answers to review.")

    def run_levels_list(self, user): # Run levels list
        print("Opening levels...")
        print("Levels List: ")
        while True:
            for level in self.levels:
                if level.completed:
                    print(f"Level {self.levels.index(level) + 1} (Completed)")
                    continue
                num = self.levels.index(level) + 1
                print(f"Level {num}")
            if all(level.completed for level in self.levels):
                print("Chapter Test")
            else:
                print("Chapter Test (Locked)")
            choice = input(f"Choose a level number to start (Enter 0 to go back) (Enter {len(self.levels) + 1} to attempt Chapter Test): ")
            try:
                choice = int(choice)
                if choice == 0:
                    return
                elif choice == len(self.levels) + 1:
                    if all(level.completed for level in self.levels):
                        self.run_chapter_test(user)
                        if user.analyze_proficiency(len(self.chapter_test.questions_answers)) >= self.chapter_test.pass_threshold:
                            self.chapter_test.completed = True
                            print("Chapter Test completed!")
                            if all(level.completed for level in self.levels) and self.chapter_test.completed:
                                self.completed = True
                                print("Module complete!")
                                user.achievements.unlock_achievement("First Module Completed")
                                if all(chapter_test.completed for chapter_test in LearningApp().modules):
                                    user.achievements.unlock_achievement("All Chapter Tests Passed")
                                    if all(module.completed for module in LearningApp().modules):
                                        user.achievements.unlock_achievement("All Modules Completed")
                                        if all(user.achievements.achievements.values()):
                                            user.achievements.unlock_achievement("All Achievements Unlocked")
                                return
                        else:
                            print("Chapter Test not passed. Review required.")
                            self.run_review(user)
                            continue
                    else:
                        print("Chapter Test is locked. Complete all levels first.")
                        continue
                elif choice not in range(1, len(self.levels) + 1):
                    print("Invalid number. Try again.")
                    continue
                else:
                    level = self.levels[choice - 1]
                    if choice > 1 and not self.levels[choice - 2].completed:
                        print("You need to complete the previous level first.")
                        continue
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue

            if level in self.levels and not level.completed:
                self.run_level(level, user)
                proficiency_percentage = user.analyze_proficiency(len(level.questions_answers))
                if proficiency_percentage >= level.pass_threshold:
                    level.completed = True
                    print(f"Level {choice} completed with {proficiency_percentage:.2f}% proficiency!")
                    user.achievements.unlock_achievement("First Level Completed")
                    if all(level.completed for level in self.levels):
                        user.achievements.unlock_achievement("All Levels Completed")
                    continue
                else:
                    print(f"Review required before proceeding. Proficiency: {proficiency_percentage:.2f}%")
                    self.run_review(user)
                    continue
            elif level in self.levels and level.completed:
                print("Level already completed.")
                continue
            else:
                print("Invalid input. Try again.")
                continue

    def run_level(self, level, user): # Run level
        user.proficiency = 0
        for question, correct_answer in level.questions_answers.items():
            print(f"Question: {question}")
            answer = input()
            user.record_answer(question, answer, answer == correct_answer)
        return

    def run_chapter_test(self, user): # Run chapter test
        user.proficiency = 0
        print(f"Chapter Test for {self.name}")
        for question, correct_answer in self.chapter_test.questions_answers.items():
            print(f"Question: {question}")
            answer = input()
            user.record_answer(question, answer, answer == correct_answer)


class LearningApp: # Learning App class
    def __init__(self): # Initialize the learning app
        self.user = User()
        self.modules = self.create_modules()

    def check_users(self): # Check if users exist
        usercol = connect_to_mongoDB()
        user_count = usercol.count_documents({})
        print(f"Found {user_count} users in database")
        return user_count > 0

    def create_modules(self): # Create modules
        return [
            Module("Basics"),
            Module("Greetings"),
        ]

    def start(self): # Start the learning app
        print("Welcome to ARAMI, the Waray Learning App!")
        if self.check_users() is False:
            print("No user found. Please sign up.")
            self.user.signup()
        else:
            while True:
                try:
                    print("(1) Login (2) Signup (0) Exit")
                    choice = input("Choose an option: ")
                    if choice == "1":
                        self.user.login(app=self)  # Pass the current app instance
                        break
                    elif choice == "2":
                        self.user.signup()
                        break
                    elif choice == "0":
                        print("Exiting...")
                        break
                    else:
                        print("Invalid choice. Try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
                    continue

    def main_menu(self): # Main menu
        while True:
            choice = input("Choose: (1) Start (2) Profile (3) Achievements (4) About (5) Acknowledgements (6) Settings (0) Logout: ")
            if choice == "1":
                self.run_modules()
            elif choice == "2":
                self.profile()
            elif choice == "3":
                self.achievements()
            elif choice == "4":
                print("About Us: This is a Waray Learning App.")
            elif choice == "5":
                print("Acknowledgements: Special thanks to...")
            elif choice == "6":
                self.show_settings()
            elif choice == "0":
                self.user.save()
                print("Logging out...")
                self.start()
                break
            else:
                print("Invalid choice. Try again.")

    def profile(self): # Display profile
        print("Profile")
        print(f"User ID: {self.user.user_id}")
        print(f"Proficiency: {self.user.proficiency}")
        print(f"Word Library: {self.user.word_library}")
    
    def achievements(self): # Display achievements
        print("Achievements")
        self.user.achievements.display_achievements()

    def show_settings(self): # Display settings
        while True:
            print("Settings:")
            print("(1) Account Management")
            print("(2) Display Settings")
            print("(3) Sound Settings")

            choice = input("Choose an option: ")
            if choice == "1":
                self.account_management()
                break
            elif choice == "2":
                self.display_settings()
                break
            elif choice == "3":
                self.sound_settings()
                break
            else:
                print("Invalid input. Try again.")

    def account_management(self): # Account management
        while True:
            print("Account Management:")
            print("(1) Change Username")
            print("(2) Change Password")
            print("(3) Delete Account")
            print("(0) Go Back")

            choice = input("Choose an option: ")
            if choice == "1":
                self.change_username()
                break
            elif choice == "2":
                self.change_password()
                break
            elif choice == "3":
                self.delete_account()
                break
            elif choice == "0":
                break
            else:
                print("Invalid input. Try again.")

    def change_username(self): # Change username
        new_username = input("Enter new username: ")
        self.user.user_name = new_username
        self.user.save()
        print("Username changed successfully.")

    def change_password(self): # Change password
        new_password = input("Enter new password: ")
        self.user.password = new_password
        self.user.save()
        print("Password changed successfully.")

    def delete_account(self): # Delete account
        confirm = input("Are you sure you want to delete your account? (yes/no): ")
        if confirm.lower() == "yes":
            delete_user(self.user.user_id)
            print("Account deleted successfully.")
            self.start()
        else:
            print("Account deletion cancelled.")

    def display_settings(self): # Display settings
        print("Coming soon...")

    def sound_settings(self): # Sound settings
        print("Coming soon...")

    def run_modules(self): # Run modules
        print("Opening Modules...")
        print("Modules List: ")
        
        while True:
            for module in self.modules:
                if module.completed:
                    print(f"Module {self.modules.index(module) + 1}: {module.name} (Completed)")
                    continue
                num = self.modules.index(module) + 1
                print(f"Module {num}: {module.name}")

            choice = input("Choose a module number to start (Enter 0 to go back): ")
            try:
                choice = int(choice)
                if choice == 0:
                    break
                elif choice not in range(1, len(self.modules) + 1):
                    print("Invalid number. Try again.")
                    continue
                else:
                    module = self.modules[choice - 1]
                    if choice > 1 and not self.modules[choice - 2].completed:
                        print("You need to complete the previous module first.")
                        continue
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue

            if module in self.modules and not module.completed:
                module.run_levels_list(self.user)
            elif module in self.modules and module.completed:
                print("Module already completed.")
                continue
            else:
                print("Invalid input. Try again.")
                continue


if __name__ == "__main__": # Main function
    test_mongoDB()
    app = LearningApp()
    app.start()
