from datetime import datetime, timedelta
from typing import List, Dict
from database import Database
from collections import defaultdict
import questionary
import subprocess


db = Database()

def list_habits(frequency: str = None) -> List[Dict]:

    """Return all habits, optionally filtered by frequency."""

    return db.load_habits(frequency)


def recent_completions(habit_id: int, n: int = 5) -> List[datetime]:
    
    """Return the n most recent unique completion dates for a habit."""

    completions = db.load_completions(habit_id)
    unique_completions = sorted(set(completions), reverse=True)
    return unique_completions[:n]


def recent_completions_fp(completions: List[datetime], n: int = 5) -> List[datetime]:

    """Returns the last n completions."""

    return sorted(completions, reverse=True)[:n]


def recent_completions_summary(habit_id: int) -> str:

    """Return summary of completions count and last completion date."""

    completions = db.load_completions(habit_id)
    if not completions:
        return "0 completions"
    completions.sort(reverse=True)
    return f"{len(completions)} completions, last: {completions[0].strftime('%Y-%m-%d')}"


def longest_streak_for_habit_fp(habit: Dict, completions: List[datetime]) -> int:

    """Calculate the longest streak for a habit."""

    if not completions:
        return 0

    freq = habit['frequency']
    periodicity = habit['periodicity']
    buckets = defaultdict(int)
    for c in completions:
        key = (c.date() if freq == 'daily' else c.date() - timedelta(days=c.weekday()))
        buckets[key] += 1

    valid_periods = sorted(k for k, v in buckets.items() if v >= periodicity)
    if not valid_periods:
        return 0

    streak = 0
    longest = 0
    prev = None
    for period in valid_periods:
        delta = (period - prev).days if prev else None
        expected = 1 if freq == 'daily' else 7

        if prev and delta == expected:
            streak += 1

        else:
            streak = 1

        longest = max(longest, streak)
        prev = period

    return longest


def longest_streak_all():

    """Return the longest streak among all habits."""

    habits = db.load_habits()
    best_streak = 0
    best_habits = []
    for h in habits:
        streak = db.get_streaks(h['id'])['longest_streak']

        if streak > best_streak:
            best_streak = streak
            best_habits = [h['name']]

        elif streak == best_streak:
            best_habits.append(h['name'])
    
    return {"habits": best_habits, "longest_streak": best_streak}


def habit_longest_streak(habit_id: int, db_instance=None) -> int:

    """Return the longest streak for a given habit ID."""

    if db_instance is None:
        db_instance = db

    return db_instance.get_streaks(habit_id)['longest_streak']


def period_summary(period="daily"):

    """Return summary of completions for the given period."""

    return db.period_summary(period)



if __name__ == "__main__":

    """Run analytics overview and interactive menu when executed directly."""

    print("\n📊 Welcome to Habit Analytics!\n")
    print("Here’s an overview of your current habits:\n")
    habits = db.load_habits()
    print(f"{'ID':<3} | {'Habit Name':<20} | {'Freq':<6} | {'Periodicity':<11} | "
          f"{'Current':<7} | {'Longest':<7} | {'Recent Completions'}")
    print("-" * 100)

    if not habits:
        print("⚠️ No habits found in the database.\n")
        print("Tip: You can add habits using the CLI (py cli.py).\n")

    else:
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
            
        print("\n📈 Analytics Summary:\n")
        best = longest_streak_all()
        if best["habits"]:
            habits_str = ", ".join(f"'{h}'" for h in best["habits"])
            print(f"🏆 Longest streak overall: {habits_str} with {best['longest_streak']} periods.")

        today = datetime.now().date()
        completed_today = 0
        for h in habits:
            completions = db.load_completions(h['id'])

            if any(c.date() == today for c in completions):
                completed_today += 1

        total_habits = len(habits)
        print(f"📅 Today’s completions: {completed_today} out of {total_habits} habits.")
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        completed_week = 0

        for h in habits:
            completions = db.load_completions(h['id'])

            if any(monday <= c.date() <= sunday for c in completions):
                completed_week += 1

        print(f"📆 This week’s completions: {completed_week} out of {total_habits} habits.\n")

    print("\nℹ️  Use this table and analytics to understand your habits better.")
    print("You can manage habits interactively using: py cli.py\n")
    move_to = questionary.select(
        "Move to:",
        choices=[
            "🏠 Run main.py",
            "📂 Run database.py",
            "▶ Run cli.py",
            "❌ Exit"
        ]
    ).ask()

    if move_to == "🏠 Run main.py":
        subprocess.run(["py", "main.py"])

    elif move_to == "📂 Run database.py":
        subprocess.run(["py", "database.py"])

    elif move_to == "▶ Run cli.py":
        subprocess.run(["py", "cli.py"])

    else:
        print("\n✅ Exiting Habit Tracker. Goodbye!\n")