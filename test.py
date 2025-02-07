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


class Module:
    def __init__(self, name, questions, chapter_test):
        self.name = name
        self.questions = questions
        self.chapter_test = chapter_test
        self.completed = False


class LearningApp:
    def __init__(self):
        self.user = User(user_id=1)
        self.modules = self.create_modules()
        self.pass_threshold = 1

    def create_modules(self):
        return [
            Module("Basics", ["Q1", "Q2"], ["T1"]),
            Module("Greetings", ["Q3", "Q4"], ["T2"]),
        ]

    def start(self):
        if self.user.first_time:
            self.user.signup()
        else:
            self.user.login()
        self.main_menu()

    def main_menu(self):
        while True:
            choice = input("Choose: (1) Start (2) About (3) Exit: ")
            if choice == "1":
                self.run_modules()
            elif choice == "2":
                print("About Us: This is a Waray Learning App.")
            elif choice == "3":
                print("Exiting...")
                break

    def run_modules(self):
        print("Opening Modules...")
        print("Modules List: ")
        for module in self.modules:
            num = self.modules.index(module) + 1
            print(f"Module {num}: {module.name}")

        while True:
            choice = int(input("Choose a module number to start: "))
            try:
                choice = int(choice)
                if choice not in range(1, len(self.modules) + 1):
                    print("Invalid number. Try again.")
                    continue
                else:
                    module = self.modules[choice - 1]
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue

            if module in self.modules and not module.completed:
                self.run_level(module)
            elif module in self.modules and module.completed:
                print("Module already completed.")
                continue
            else:
                print("Invalid input. Try again.")
                continue
            break
            

    def run_level(self, module):
        for question in module.questions:
            print(f"Question: {question}")
            answer = input()
            self.user.record_answer(question, answer == "correct")
        
        if self.user.analyze_proficiency() >= self.pass_threshold:
            module.completed = True
            print(f"{module.name} completed!")
        else:
            print("Review required before proceeding.")

    def final_exam(self):
        print("Final Exam Starting...")
        for i in range(3):
            answer = input(f"Final Q{i+1}: ")
            self.user.record_answer(f"Final Q{i+1}", answer == "correct")
        
        if self.user.analyze_proficiency() >= self.pass_threshold:
            print("Congratulations! You earned the certificate.")
        else:
            print("Remedial lesson required. Retaking final exam.")
            self.final_exam()


if __name__ == "__main__":
    app = LearningApp()
    app.start()
