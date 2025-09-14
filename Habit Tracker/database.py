import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import subprocess
import questionary


class Database:

    """
    Handles all database operations for the Habit Tracker application.
    Provides methods to create tables, add habits and completions, load data,
    calculate streaks, reset database, and generate fixture data for testing.
    """


    def __init__(self, db_path='habits.db'):

        """
        Initializes a Database object, connects to the SQLite database at db_path,
        sets row_factory to access columns by name, creates tables if they don't exist,
        and populates fixture data for demonstration.
        """

        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  
        self.create_tables()
        self.generate_fixture_data()


    def create_tables(self):
        
        """
        Creates the required tables `habits` and `completions` if they do not exist.
        - `habits`: stores id, name, frequency, periodicity, creation_date
        - `completions`: stores habit_id, completion_date, with a foreign key constraint
        Commits changes to the database.
        """

        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            frequency TEXT NOT NULL,
            periodicity INTEGER NOT NULL,
            creation_date TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS completions (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           habit_id INTEGER NOT NULL,
           completion_date TEXT NOT NULL,
           FOREIGN KEY(habit_id) REFERENCES habits(id) ON DELETE CASCADE
        )
        """)

        self.conn.commit()


    def add_habit(self, name: str, frequency: str = 'daily', periodicity: int = 1) -> int:

        """
        Inserts a new habit into the `habits` table with the given name, frequency, and periodicity.
        Returns the auto-generated id of the inserted habit.
        """

        cursor = self.conn.cursor()
        creation_date = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO habits (name, frequency, periodicity, creation_date)
        VALUES (?, ?, ?, ?)
        """, (name, frequency, periodicity, creation_date))
        self.conn.commit()
        return cursor.lastrowid

        
    def add_completion(self, habit_id: int, completion_date: Optional[datetime] = None):

        """
        Records a completion for a given habit_id.
        If completion_date is not provided, defaults to current datetime.
        Inserts into the `completions` table and commits the transaction.
        """

        if completion_date is None:
            completion_date = datetime.now()
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO completions (habit_id, completion_date)
        VALUES (?, ?)
        """, (habit_id, completion_date.isoformat()))
        self.conn.commit()
    

    def load_habits(self, frequency: Optional[str] = None) -> List[Dict]:

        """
        Loads habits from the database.
        If frequency is specified, filters habits by that frequency ('daily' or 'weekly').
        Returns a list of dictionaries representing each habit.
        """

        cursor = self.conn.cursor()
        if frequency:
            cursor.execute("SELECT * FROM habits WHERE frequency = ?", (frequency,))
        else:
            cursor.execute("SELECT * FROM habits")
        rows = cursor.fetchall()
        habits = [dict(row) for row in rows]
        return habits
    

    def load_completions(self, habit_id: int) -> List[datetime]:

        """
        Retrieves all completion dates for a given habit_id as datetime objects.
        Returns a list of completion datetimes.
        """

        cursor = self.conn.cursor()
        cursor.execute("SELECT completion_date FROM completions WHERE habit_id = ?", (habit_id,))
        rows = cursor.fetchall()
        return [datetime.fromisoformat(row['completion_date']) for row in rows]


    def delete_habit(self, habit_id: int):

        """
        Deletes a habit from the `habits` table using its id.
        Also deletes associated completions due to foreign key constraint.
        Commits changes to the database.
        """

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        self.conn.commit()
    

    def reset_to_default(self):

        """
        Clears all habits and completions and resets SQLite autoincrement sequences.
        Then generates fixture/default data for demonstration.
        """
        
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM completions")
        cursor.execute("DELETE FROM habits")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='habits'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='completions'")
        self.conn.commit()
        self.generate_fixture_data()


    def add_predefined_habits(self):

        """
        Adds a predefined set of default habits if they do not already exist in the database.
        Ensures no duplicates are inserted.
        """

        DEFAULT_HABITS = [
            {"name": "Drink Water", "frequency": "daily", "periodicity": 3},
            {"name": "Stretch", "frequency": "daily", "periodicity": 1},
            {"name": "Learn Python", "frequency": "daily", "periodicity": 2},
            {"name": "Grocery Shopping", "frequency": "weekly", "periodicity": 2},
            {"name": "Clean Room", "frequency": "weekly", "periodicity": 2},
        ]

        existing_habits = {h['name'] for h in self.load_habits()}
        for h in DEFAULT_HABITS:
            if h['name'] not in existing_habits:
                self.add_habit(h['name'], h['frequency'], h['periodicity'])


    def get_streaks(self, habit_id: int) -> Dict[str, int]:

        """
        Calculates the current and longest streaks for a given habit.
        - For daily habits: counts consecutive days meeting the periodicity requirement.
        - For weekly habits: counts consecutive weeks meeting the periodicity requirement.
        Returns a dictionary: {"current_streak": int, "longest_streak": int}.
        """
        
        completions = sorted(self.load_completions(habit_id))
        if not completions:
            return {"current_streak": 0, "longest_streak": 0}

        habit = next((h for h in self.load_habits() if h['id'] == habit_id), None)
        if habit is None:
            return {"current_streak": 0, "longest_streak": 0}

        freq = habit['frequency']
        periodicity = habit['periodicity']
        now = datetime.now()
        current_streak = 0
        longest_streak = 0
        
        if freq == "daily":
            days = {}
            for c in completions:
                d = c.date()
                days[d] = days.get(d, 0) + 1

            valid_days = sorted(d for d, count in days.items() if count >= periodicity)

            day = now.date()
            while day in valid_days:
                current_streak += 1
                day -= timedelta(days=1)

            streak = 0
            prev = None
            for d in valid_days:
                if prev and (d - prev).days == 1:
                    streak += 1
                else:
                    streak = 1
                longest_streak = max(longest_streak, streak)
                prev = d

        elif freq == "weekly":
            weeks = {}
            for c in completions:
                monday = c.date() - timedelta(days=c.weekday())
                weeks[monday] = weeks.get(monday, 0) + 1

            valid_weeks = sorted(w for w, count in weeks.items() if count >= periodicity)

            this_week = now.date() - timedelta(days=now.weekday())
            while this_week in valid_weeks:
                current_streak += 1
                this_week -= timedelta(days=7)

            streak = 0
            prev = None
            for w in valid_weeks:
                if prev and (w - prev).days == 7:
                    streak += 1
                else:
                    streak = 1
                longest_streak = max(longest_streak, streak)
                prev = w

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak
        }


    def period_summary(self, period: str = "daily") -> Dict[str,int]:

        """
        Summarizes habits for a given period ('daily' or 'weekly').
        Returns a dictionary with counts of completed and missed habits in that period.
        """
        
        completed = 0
        missed = 0
        habits = self.load_habits()
        now = datetime.now()

        for habit in habits:
            comps = self.load_completions(habit['id'])
            if period == "daily":
                period_start = datetime(now.year, now.month, now.day)
            else:
                period_start = now - timedelta(days=now.weekday())
            count = sum(1 for c in comps if c >= period_start)
            if count >= habit['periodicity']:
                completed += 1
            else:
                missed += 1
        return {"completed": completed, "missed": missed}
    

    def completions_in_current_period(self, habit_id: int) -> int:

        """
        Counts the number of completions a habit has in the current period.
        Period is determined by the habit's frequency (daily or weekly).
        Returns an integer count.
        """

        habit = next((h for h in self.load_habits() if h['id'] == habit_id), None)
        if not habit:
            return 0

        completions = self.load_completions(habit_id)
        now = datetime.now()
        freq = habit['frequency']

        if freq == 'daily':
            period_start = datetime(now.year, now.month, now.day)
            count = sum(1 for c in completions if c >= period_start)

        elif freq == 'weekly':
            period_start = now - timedelta(days=now.weekday())
            count = sum(1 for c in completions if c >= period_start)

        else:
            count = 0

        return count


    def generate_fixture_data(self):

        """
        Generates sample habits and completions for demonstration purposes.
        - Daily habits: 28 days of completions
        - Weekly habits: 4 weeks of completions
        Ensures not to duplicate existing habits.
        """
        
        habits_data = [
            {"name": "Drink Water", "frequency": "daily", "periodicity": 3},
            {"name": "Stretch", "frequency": "daily", "periodicity": 1},
            {"name": "Learn Python", "frequency": "daily", "periodicity": 2},
            {"name": "Grocery Shopping", "frequency": "weekly", "periodicity": 2},
            {"name": "Clean Room", "frequency": "weekly", "periodicity": 2},
        ]

        existing_habits = {h['name'] for h in self.load_habits()}
        for h in habits_data:
            if h['name'] in existing_habits:
                continue  

            habit_id = self.add_habit(h['name'], h['frequency'], h['periodicity'])
            now = datetime.now()

            if h['frequency'] == 'daily':
                for i in range(28):
                    day = now - timedelta(days=i)
                    for _ in range(h['periodicity']):
                        self.add_completion(habit_id, day)

            else:
                for i in range(4):
                    week_start = now - timedelta(days=now.weekday() + 7*i)
                    for _ in range(h['periodicity']):
                        self.add_completion(habit_id, week_start)


    def reset_empty(self):

        """
        Clears all habits and completions and resets SQLite autoincrement sequences.
        Useful for starting with a completely empty database.
        """

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM completions")
        cursor.execute("DELETE FROM habits")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='habits'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='completions'")
        self.conn.commit()



if __name__ == "__main__":

    """
    Entry point for the database demonstration script.

    Functionality:
    1. Initializes the Database and loads all habits.
    2. Prints a table showing each habit's:
       - ID, Name, Frequency, Periodicity
       - Current streak, Longest streak
       - Recent completions
    3. Provides an interactive menu to:
       - Run main.py
       - Run cli.py
       - Run analytics.py
       - Exit
    Uses `questionary` for interactive CLI selections and `subprocess` to run other scripts.
    """

    db = Database()
    habits = db.load_habits()

    print("\nℹ️  This table shows your current habits and streaks.\n")
    print(f"{'ID':<3} | {'Habit Name':<20} | {'Freq':<6} | {'Periodicity':<11} | "
          f"{'Current':<7} | {'Longest':<7} | {'Recent Completions'}")
    print("-" * 100)

    for h in habits:
        habit_id = h['id']
        name = h['name']
        freq = h['frequency']
        period = h['periodicity']
        streaks = db.get_streaks(habit_id)
        current = streaks['current_streak']
        longest = streaks['longest_streak']
        completions = db.load_completions(habit_id)

        if completions:
            last_date = max(completions).strftime('%Y-%m-%d')
            completions_count = len(completions)
            recent_str = f"{completions_count} completions, last: {last_date}"

        else:
            recent_str = "0 completions"

        print(f"{habit_id:<3} | {name:<20} | {freq:<6} | {period:<11} | "
              f"{current:<7} | {longest:<7} | {recent_str}")
        
    move_to = questionary.select(
        "Move to:",
        choices=[
            "🏠 Run main.py",
            "▶ Run cli.py",
            "📊 Run analytics.py",
            "❌ Exit"
        ]
    ).ask()

    if move_to == "🏠 Run main.py":
        subprocess.run(["py", "main.py"])

    elif move_to == "▶ Run cli.py":
        subprocess.run(["py", "cli.py"])

    elif move_to == "📊 Run analytics.py":
        subprocess.run(["py", "analytics.py"])

    else:
        print("\n✅ Exiting Habit Tracker. Goodbye!\n")