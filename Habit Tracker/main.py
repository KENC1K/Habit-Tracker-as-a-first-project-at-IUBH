from datetime import datetime, timedelta
from collections import defaultdict
from database import Database
from analytics import longest_streak_for_habit_fp, recent_completions_fp
import subprocess
import questionary


db = Database()


class Habit:

    """
    Represents a habit that can be tracked, completed, and analyzed.
    Stores its name, frequency, periodicity, and interacts with the database.
    """


    @classmethod
    def from_db(cls, habit_id: int, db_instance=None):

        """
        Creates a Habit instance from a database record using its habit_id.
        It searches the database for a habit with the given ID and initializes an object with its attributes (name, frequency, periodicity, creation_date).
        If no matching record is found, it returns None.
        """

        db_inst = db_instance if db_instance else db
        record = next((h for h in db_inst.load_habits() if h['id'] == habit_id), None)
        if not record:
            return None
        obj = cls.__new__(cls)
        obj.name = record['name']
        obj.frequency = record['frequency']
        obj.periodicity = record['periodicity']
        obj.id = habit_id
        obj.creation_date = datetime.fromisoformat(record['creation_date'])
        obj.db = db_inst
        return obj


    def __init__(self, name, frequency, periodicity, db_instance=None, habit_id=None):

        """
        Initializes a new Habit object with provided name, frequency, periodicity, and optionally a habit_id and database instance.
        If no database instance is provided, it creates a default Database() object.
        """

        self.id = habit_id
        self.name = name
        self.frequency = frequency
        self.periodicity = periodicity
        self.db = db_instance if db_instance else Database()


    def performed(self):

        """
        Marks the habit as completed in the database for the current period if allowed.
        It first checks if the habit can be marked as performed using can_mark_performed().
        If allowed, it records a completion in the database and prints a confirmation message.
        """

        if not self.can_mark_performed():
            print(f"Habit '{self.name}' cannot be marked as completed in this period.")
            return
        self.db.add_completion(self.id)
        print(f"Habit '{self.name}' marked as completed in DB.")


    def calculate_current_streak(self):

        """
        Retrieves the current streak of consecutive completions for the habit from the database.
        Returns the value associated with the 'current_streak' key.
        """

        return self.db.get_streaks(self.id)['current_streak']
    
       
    def calculate_longest_streak(self):

        """
        Retrieves the longest streak of consecutive completions for the habit from the database.
        Returns the value associated with the 'longest_streak' key.
        """

        return self.db.get_streaks(self.id)['longest_streak']

    
    def can_mark_performed(self) -> bool:

        """
        Determines whether the habit can be marked as completed for the current period.
        - For daily habits, checks if the habit has been performed fewer times than its `periodicity` today.
        - For weekly habits, checks if the habit has been performed fewer times than its `periodicity` in the current week.
        Returns True if it can be marked, False otherwise.
        """

        completions = self.db.load_completions(self.id)
        now = datetime.now()

        if self.frequency == "daily":
            today_count = sum(1 for c in completions if c.date() == now.date())
            return today_count < self.periodicity

        elif self.frequency == "weekly":
            monday = now - timedelta(days=now.weekday())
            sunday = monday + timedelta(days=6)
            week_count = sum(1 for c in completions if monday.date() <= c.date() <= sunday.date())
            return week_count < self.periodicity

        return False



if __name__ == "__main__":

    """
    Entry point for the Habit Tracker CLI application.

    Functionality:
    1. Greets the user and displays a table of default habits including:
       - ID, Habit Name, Frequency, Periodicity
       - Current streak, Longest streak
       - Recent completions
       
    2. Allows the user to choose where to go next via an interactive menu:
       - ▶ Run CLI: Launch the main habit tracking interface.
       - 🗄 Run database.py: Open database management script.
       - 📊 Run analytics.py: Open analytics script.
       - ❌ Exit: Quit the program.
       
    3. If the user chooses "Run CLI", they can:
       - Use the current database
       - Reset to default habits (resets the database to sample habits)
       - Then launches `cli.py` via subprocess
       
    4. For other options, the corresponding script is run via subprocess.
    
    Notes:
    - The default habits table is for demonstration purposes.
    - Interactive menus are implemented using `questionary`.
    """
    

    print("\n🟢 Welcome to Habit Tracker CLI!\n")
    print("Here’s a sample of default habits to get you started:\n")
    print(f"{'ID':<3} | {'Habit Name':<20} | {'Freq':<6} | {'Periodicity':<11} | "
          f"{'Current':<7} | {'Longest':<7} | {'Recent Completions'}")
    print("-" * 100)

    
    default_habits_data = [
        {"name": "Drink Water", "frequency": "daily", "periodicity": 3},
        {"name": "Stretch", "frequency": "daily", "periodicity": 1},
        {"name": "Learn Python", "frequency": "daily", "periodicity": 2},
        {"name": "Grocery Shopping", "frequency": "weekly", "periodicity": 2},
        {"name": "Clean Room", "frequency": "weekly", "periodicity": 2},
    ]


    now = datetime.now()
    for idx, h in enumerate(default_habits_data, start=1):
        if h['frequency'] == 'daily':
            current = longest = 28
            recent = f"28 completions, last: {now.strftime('%Y-%m-%d')}"
        else:
            current = longest = 4
            recent = f"8 completions, last: {(now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')}"

        print(f"{idx:<3} | {h['name']:<20} | {h['frequency']:<6} | {h['periodicity']:<11} | "
              f"{current:<7} | {longest:<7} | {recent}")

    
    print("\nℹ️  These are default habits for demonstration purposes.")
    print("You can create new habits, track progress, and analyse streaks using the CLI commands.\n")


    move_to = questionary.select(
        "Move to:",
        choices=[
            "▶ Run CLI",
            "🗄 Run database.py",
            "📊 Run analytics.py",
            "❌ Exit"
        ]
    ).ask()


    if move_to == "▶ Run CLI":
        
        choice = questionary.select(
            "Which data would you like to use?",
            choices=[
                "📂 Use current database",
                "🔄 Reset to default habits"
            ]
        ).ask()

        if choice == "🔄 Reset to default habits":
            db = Database()
            db.reset_to_default()   
            print("\n✅ Database has been reset to default habits.\n")

        subprocess.run(["py", "cli.py"])

    elif move_to == "🗄 Run database.py":
        subprocess.run(["py", "database.py"])

    elif move_to == "📊 Run analytics.py":
        subprocess.run(["py", "analytics.py"])

    else:
        print("\n✅ Exiting Habit Tracker. Goodbye!\n")