class User:
    def __init__(self, user_id, first_time=True):
        self.user_id = user_id
        self.first_time = first_time
        self.proficiency = 0
        self.word_library = []
        self.questions_wrong = {}
        self.questions_correct = {}
        self.achievements = Achievements()

    def signup(self):
        print("Signing up new user...")
        self.first_time = False

    def login(self):
        print("Logging in existing user...")

    def analyze_proficiency(self, total_questions):
        return (self.proficiency / total_questions) * 100

    def record_answer(self, question, answer, correct):
        if correct:
            self.proficiency += 1
            self.questions_correct[question] = answer
            self.word_library.append(answer)
        else:
            self.questions_wrong[question] = answer


class Achievements:
    def __init__(self):
        self.achievements = {
            "First Level Completed": False,
            "First Module Completed": False,
            "All Modules Completed": False,
            "All Levels Completed": False,
            "All Chapter Tests Passed": False,
            "All Achievements Unlocked": False
        }

    def unlock_achievement(self, achievement):
        self.achievements[achievement] = True
        print(f"Achievement Unlocked: {achievement}")

    def display_achievements(self):
        for achievement, unlocked in self.achievements.items():
            print(f"{achievement}: {'Unlocked' if unlocked else 'Locked'}")


class Level:
    def __init__(self, questions_answers):
        self.questions_answers = questions_answers
        self.completed = False
        self.pass_threshold = 70


class ChapterTest:
    def __init__(self, questions_answers):
        self.questions_answers = questions_answers
        self.completed = False
        self.pass_threshold = 80


class Module:
    def __init__(self, name):
        self.name = name
        self.completed = False
        self.levels = self.create_levels()
        self.chapter_test = self.create_chapter_test()

    def create_levels(self):
        return [
            Level({"Q1": "A1", "Q2": "A2"}),
            Level({"Q3": "A3", "Q4": "A4"})
        ]
    
    def create_chapter_test(self):
        return ChapterTest({"Q1": "A1", "Q2": "A2", "Q3": "A3", "Q4": "A4"})

    def run_review(self, user):
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

    def run_levels_list(self, user):
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
                            user.achievements.unlock_achievement("All Chapter Tests Passed")
                            if all(level.completed for level in self.levels) and self.chapter_test.completed:
                                self.completed = True
                                print("Module complete!")
                                user.achievements.unlock_achievement("First Module Completed")
                                if all(module.completed for module in user.modules):
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

    def run_level(self, level, user):
        user.proficiency = 0
        for question, correct_answer in level.questions_answers.items():
            print(f"Question: {question}")
            answer = input()
            user.record_answer(question, answer, answer == correct_answer)
        return

    def run_chapter_test(self, user):
        user.proficiency = 0
        print(f"Chapter Test for {self.name}")
        for question, correct_answer in self.chapter_test.questions_answers.items():
            print(f"Question: {question}")
            answer = input()
            user.record_answer(question, answer, answer == correct_answer)


class LearningApp:
    def __init__(self):
        self.user = User(user_id=1)
        self.modules = self.create_modules()

    def create_modules(self):
        return [
            Module("Basics"),
            Module("Greetings"),
        ]

    def start(self):
        if self.user.first_time:
            self.user.signup()
        else:
            self.user.login()
        self.main_menu()

    def main_menu(self):
        while True:
            choice = input("Choose: (1) Start (2) Profile (3) Achievements (4) About (5) Settings (0) Exit: ")
            if choice == "1":
                self.run_modules()
            elif choice == "2":
                self.profile()
            elif choice == "3":
                self.achievements()
            elif choice == "4":
                print("About Us: This is a Waray Learning App.")
            elif choice == "5":
                print("Settings: Coming soon...")
            elif choice == "0":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Try again.")

    def profile(self):
        print("Profile")
        print(f"User ID: {self.user.user_id}")
        print(f"Proficiency: {self.user.proficiency}")
        print(f"Word Library: {self.user.word_library}")
    
    def achievements(self):
        print("Achievements")
        self.user.achievements.display_achievements()

    def run_modules(self):
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


if __name__ == "__main__":
    app = LearningApp()
    app.start()
