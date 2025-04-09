import random
import math

class Flashcard:
    def __init__(self, question, answer):
        self.question = question
        self.answer = answer
        self.interval = 1
        self.repetitions = 0
        self.ease_factor = 2.5
        self.due_date = 0

    def update(self, grade):
        if grade >= 3:
            if self.repetitions == 0:
                self.interval = 1
            elif self.repetitions == 1:
                self.interval = 6
            else:
                self.interval = math.ceil(self.interval * self.ease_factor)
            self.repetitions += 1
        else:
            self.repetitions = 0
            self.interval = 1

        self.ease_factor = max(1.3, self.ease_factor + 0.1 - (5 - grade) * 0.08)
        self.due_date += self.interval

    def __str__(self):
        return f"{self.question} - {self.answer} (Due in {self.due_date} days)"

def simulate_supermemo(flashcards, days):
    for day in range(days):
        print(f"Day {day + 1}")
        for card in flashcards:
            if card.due_date <= day:
                print(f"Reviewing: {card}")
                grade = random.randint(1, 5)  # Simulate user grading the flashcard
                card.update(grade)
                print(f"Grade: {grade}, Next review in {card.interval} days\n")

if __name__ == "__main__":
    sample_data = [
        ("Maupay", "Good"),
        ("Aga", "Morning"),
        ("Gihapon", "Also"),
        ("Gab-i", "Night"),
        ("Kulop", "Thunder")
    ]

    flashcards = [Flashcard(question, answer) for question, answer in sample_data]
    simulate_supermemo(flashcards, 30)