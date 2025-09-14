import click
import questionary
import subprocess
from main import Habit, db
from datetime import datetime, timedelta
from analytics import (
    recent_completions_summary,
    longest_streak_all,
    period_summary,
    habit_longest_streak
)


def format_recent_completions(completions):

    """Format a list of completions into a summary string."""
    
    if not completions:
        return "0 completions"
    
    completions_sorted = sorted(completions, reverse=True)
    count = len(completions_sorted)
    last = completions_sorted[0].strftime('%Y-%m-%d')

    return f"{count} completions, last: {last}"


@click.group()
def cli():

    """Habit Tracker CLI entry point."""

    pass

@cli.command()
@click.option('--name', prompt='Habit name', help='The name of the habit')
@click.option('--frequency', default='daily', type=click.Choice(['daily', 'weekly']), prompt=True)
@click.option('--periodicity', default=1, type=int, prompt='Times per period')           
def add(name, frequency, periodicity):

    """Add a new habit."""

    existing = next((h for h in db.load_habits() if h['name'] == name), None)
    if existing:
        click.echo(f"Habit '{name}' already exists with ID {existing['id']}.")
        return

    if periodicity < 1:
        click.echo("Periodicity must be at least 1.")
        return

    habit = Habit(name, frequency, periodicity)
    click.echo(f"Habit '{name}' added successfully with ID {habit.id}!")


@cli.command()
def list_habits():

    """List all habits with streaks in a table format."""

    habits = db.load_habits()
    click.echo(f"{'ID':<3} | {'Name':<20} | {'Freq':<6} | {'Periodicity':<11} | {'Current':<7} | {'Longest':<7} | {'Recent completions'}")
    click.echo("-" * 120)

    for h in habits:
        streaks = db.get_streaks(h['id'])
        recent_str = recent_completions_summary(h['id'])
        print(f"{h['id']:<3} | {h['name']:<20} | {h['frequency']:<6} | {h['periodicity']:<11} | "
            f"{streaks['current_streak']:<7} | {streaks['longest_streak']:<7} | {recent_str}")


@cli.command()
@click.option('--habit_id', type=int, prompt='Habit ID to mark as done')
def done(habit_id):

    """Mark a habit as completed."""

    habit_record = next((h for h in db.load_habits() if h['id'] == habit_id), None)   
    if not habit_record:
        click.echo(f"Habit ID {habit_id} does not exist.")
        return

    habit = Habit.from_db(habit_id)
    if habit is None:
        click.echo(f"Habit ID {habit_id} does not exist.")
        return

    if habit.can_mark_performed():
        habit.performed()
        click.echo(f"Habit ID {habit_id} marked as completed!")
    else:
        click.echo(f"Habit '{habit.name}' cannot be marked as completed in this period.")


@cli.command()
@click.option('--habit_id', type=int, prompt='Habit ID to delete')
def delete(habit_id):

    """Delete a habit."""

    db.delete_habit(habit_id)
    click.echo(f"Habit ID {habit_id} deleted successfully!")


@cli.command()
def interactive_menu():

    """Interactive menu for managing habits and viewing analytics."""

    while True:
        print()
        action = questionary.select(
            "=== HABIT TRACKER MENU ===",
            choices=[
                "Add a new habit",
                "List all habits",
                "Mark habit as done",
                "Delete a habit",
                "Show analytics",
                "Reset to default habits",
                "Reset entire database (empty)",
                "Exit"
            ]
        ).ask()

        if action == "Add a new habit":
            name = questionary.text("Habit name:").ask()
            frequency = questionary.select("Frequency:", choices=["daily", "weekly"]).ask()
            periodicity = int(questionary.text("Times per period:").ask())
            habit_id = db.add_habit(name, frequency, periodicity)
            habit = Habit(name, frequency, periodicity, db_instance=db, habit_id=habit_id)
            print(f"Habit '{habit.name}' added with ID {habit.id}")

        elif action == "List all habits":
            habits = db.load_habits()
            print(f"{'ID':<3} | {'Name':<20} | {'Freq':<6} | {'Periodicity':<11} | {'Current':<7} | {'Longest':<7} | {'Recent completions'}")

            for h in habits:
                streaks = db.get_streaks(h['id'])
                recent_str = recent_completions_summary(h['id'])
                print(f"{h['id']:<3} | {h['name']:<20} | {h['frequency']:<6} | {h['periodicity']:<11} | "
                        f"{streaks['current_streak']:<7} | {streaks['longest_streak']:<7} | {recent_str}")

        elif action == "Mark habit as done":
            habit_id = int(questionary.text("Enter habit ID to mark as done:").ask())
            habit = Habit.from_db(habit_id)

            if habit is None:
                print(f"Habit ID {habit_id} not found.")

            elif habit.can_mark_performed():
                habit.performed()
                print(f"Habit '{habit.name}' marked as completed")

            else:
                print(f"Habit '{habit.name}' cannot be marked as completed in this period.")

        elif action == "Delete a habit":
            habit_id = int(questionary.text("Enter habit ID to delete:").ask())
            db.delete_habit(habit_id)
            print(f"Habit {habit_id} deleted.")

        elif action == "Show analytics":
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

                daily_summary = period_summary("daily")
                weekly_summary = period_summary("weekly")
                print(f"📊 Daily Summary: {daily_summary['completed']} completed, {daily_summary['missed']} missed")
                print(f"📊 Weekly Summary: {weekly_summary['completed']} completed, {weekly_summary['missed']} missed\n")

                print("--- Per Habit Analytics ---")
                for h in habits:
                    completions = db.load_completions(h['id'])
                    recent = recent_completions_summary(h['id'])
                    longest = habit_longest_streak(h['id'])
                    print(f"\nHabit: {h['name']}")
                    print(f"   ✅ {recent}")
                    print(f"   🔥 Longest streak: {longest}")

                    if completions:
                        recent_unique = sorted(set(completions), reverse=True)
                        recent_str = ", ".join(c.strftime('%Y-%m-%d') for c in recent_unique[:5])
                        print(f"   🕒 Last completions: {recent_str}")

                    else:
                        print("   🕒 No completions yet.")

                    print("-" * 40)
            print("\nℹ️  Use this table and analytics to understand your habits better.")

        elif action == "Reset to default habits":
                choice = questionary.select(
                    "This will delete ALL habits and completions. What do you want to do?",
                    choices=[
                        "Yes, reset to defaults",
                        "No, cancel",
                        "View default habits"
                    ]
                ).ask()

                if choice == "Yes, reset to defaults":
                    db.reset_to_default() 
                    print("✅ All habits reset to defaults with fixture data for 4 weeks.\n")
                    habits = db.load_habits()
                    print(f"{'ID':<3} | {'Name':<20} | {'Freq':<6} | {'Periodicity':<11} | {'Current':<7} | {'Longest':<7} | {'Recent completions'}")
                    print("-" * 100)

                    for h in habits:
                        streaks = db.get_streaks(h['id'])
                        recent_str = recent_completions_summary(h['id'])
                        print(f"{h['id']:<3} | {h['name']:<20} | {h['frequency']:<6} | {h['periodicity']:<11} | "
                            f"{streaks['current_streak']:<7} | {streaks['longest_streak']:<7} | {recent_str}")

                elif choice == "No, cancel":
                    print("❌ Reset canceled.")

                elif choice == "View default habits":
                    default_habits_data = [
                        {"name": "Drink Water", "frequency": "daily", "periodicity": 3, "current": 28, "longest": 28, "recent": "84 completions, last: 2025-09-07"},
                        {"name": "Stretch", "frequency": "daily", "periodicity": 1, "current": 28, "longest": 28, "recent": "28 completions, last: 2025-09-07"},
                        {"name": "Learn Python", "frequency": "daily", "periodicity": 2, "current": 28, "longest": 28, "recent": "56 completions, last: 2025-09-07"},
                        {"name": "Grocery Shopping", "frequency": "weekly", "periodicity": 2, "current": 4, "longest": 4, "recent": "8 completions, last: 2025-09-01"},
                        {"name": "Clean Room", "frequency": "weekly", "periodicity": 2, "current": 4, "longest": 4, "recent": "8 completions, last: 2025-09-01"},
                    ]

                    print(f"{'ID':<3} | {'Name':<20} | {'Freq':<6} | {'Periodicity':<11} | {'Current':<7} | {'Longest':<7} | {'Recent completions'}")
                    print("-" * 100)

                    for idx, h in enumerate(default_habits_data, start=1):
                        current_streak = h['current']
                        longest_streak = h['longest']
                        recent_str = h['recent']
                        print(f"{idx:<3} | {h['name']:<20} | {h['frequency']:<6} | {h['periodicity']:<11} | "
                            f"{current_streak:<7} | {longest_streak:<7} | {recent_str}")

        elif action == "Reset entire database (empty)":
            confirm = questionary.select(
                "This will delete ALL habits and completions and leave the database empty. Continue?",
                choices=[
                    "Yes",
                    "No"
                ]
            ).ask()

            if confirm == "Yes":
                db.reset_empty()
                print("✅ Database completely emptied.")

            else:
                print("❌ Reset canceled.")

        elif action == "Exit":
            print("\n⚠️  If you choose 'Yes', default habits will be automatically added to the database.\n")
            confirm_exit = questionary.select(
                "Are you sure you want to exit?",
                choices=[
                    "Yes, exit",
                    "No, return to menu"
                ]
            ).ask()

            if confirm_exit == "Yes, exit":
                print("\n✅ Exiting CLI. Goodbye!\n")
                next_action = questionary.select(
                    "What do you want to do next?",
                    choices=[
                        "▶ Run main.py",
                        "🗄 Run database.py",
                        "📊 Run analytics.py",
                        "❌ Full exit"
                    ]
                ).ask()

                if next_action == "▶ Run main.py":
                    subprocess.run(["py", "main.py"])

                elif next_action == "🗄 Run database.py":
                    subprocess.run(["py", "database.py"])

                elif next_action == "📊 Run analytics.py":
                    subprocess.run(["py", "analytics.py"])

                else:
                    print("\n👋 Fully exited. You can restart anytime.\n")

                break  
            else:
                continue



if __name__ == "__main__":
    interactive_menu()