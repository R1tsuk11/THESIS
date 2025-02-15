class User:
    def __init__(self, user_id, first_time=True):
        self.user_id = user_id
        self.first_time = first_time
        self.proficiency = 0
        self.word_library = []

    def signup(self):
        print("Signing up new user...")
        self.first_time = False

    def login(self):
        print("Logging in existing user...")

    def analyze_proficiency(self):
        return self.proficiency

    def record_answer(self, question, correct):
        if correct:
            self.proficiency += 1
        else:
            self.proficiency -= 1


class Level:
    def __init__(self, questions_answers):
        self.questions_answers = questions_answers
        self.completed = False
        self.pass_threshold = 1

class ChapterTest:
    def __init__(self, questions_answers):
        self.questions_answers = questions_answers
        self.completed = False
        self.pass_threshold = 2

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
                        if user.analyze_proficiency() >= self.chapter_test.pass_threshold:
                            self.chapter_test.completed = True
                            print("Chapter Test completed!")
                            if all(level.completed for level in self.levels) and self.chapter_test.completed:
                                self.completed = True
                                print("Module complete!")
                                return
                        else:
                            print("Chapter Test not passed. Review required.")
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
                if user.analyze_proficiency() >= level.pass_threshold:
                    level.completed = True
                    print(f"Level {choice} completed!")
                    continue
                else:
                    print("Review required before proceeding.")
                    continue
            elif level in self.levels and level.completed:
                print("Level already completed.")
                continue
            else:
                print("Invalid input. Try again.")
                continue

    def run_level(self, level, user):
        for question, correct_answer in level.questions_answers.items():
            print(f"Question: {question}")
            answer = input()
            user.record_answer(question, answer == correct_answer)
        return

    def run_chapter_test(self, user):
        print(f"Chapter Test for {self.name}")
        for question, correct_answer in self.chapter_test.questions_answers.items():
            print(f"Question: {question}")
            answer = input()
            user.record_answer(question, answer == correct_answer)

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
            choice = input("Choose: (1) Start (2) About (0) Exit: ")
            if choice == "1":
                self.run_modules()
            elif choice == "2":
                print("About Us: This is a Waray Learning App.")
            elif choice == "0":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Try again.")

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
