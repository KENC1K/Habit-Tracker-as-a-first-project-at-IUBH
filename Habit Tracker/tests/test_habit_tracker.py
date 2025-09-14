import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
from datetime import datetime, timedelta
from main import Habit
from database import Database
from analytics import (
    recent_completions_fp,
    longest_streak_for_habit_fp,
    recent_completions_summary,
    habit_longest_streak
)


@pytest.fixture
def fresh_db(tmp_path):

    """Create a fresh database for each test."""

    db_path = tmp_path / "test_habits.db"
    db = Database(str(db_path))
    db.reset_empty() 
    return db


@pytest.fixture
def habit(fresh_db):

    """Add a test habit to the fresh database."""

    habit_id = fresh_db.add_habit("New Habit", "daily", 1)
    habit = Habit("New Habit", "daily", 1, db_instance=fresh_db, habit_id=habit_id)
    return habit


def test_add_habit(fresh_db):

    """Test that a new habit can be added to the database."""

    habit_id = fresh_db.add_habit("New Habit", "daily", 1)
    habit = Habit("New Habit", "daily", 1, db_instance=fresh_db, habit_id=habit_id)
    habits = fresh_db.load_habits()
    assert any(h['name'] == "New Habit" for h in habits)


def test_mark_performed(fresh_db):

    """Test marking a habit as completed stores a completion."""

    habit_id = fresh_db.add_habit("Daily Habit", "daily", 1)
    habit = Habit("Daily Habit", "daily", 1, db_instance=fresh_db, habit_id=habit_id)
    habit.performed()
    completions = fresh_db.load_completions(habit.id)
    assert len(completions) == 1


def test_current_streak(fresh_db):

    """Test that the current streak is calculated correctly."""

    habit_id = fresh_db.add_habit("Streak Habit", "daily", 1)
    habit = Habit("Streak Habit", "daily", 1, db_instance=fresh_db, habit_id=habit_id)
    now = datetime.now()
    for i in range(3):
        fresh_db.add_completion(habit.id, now - timedelta(days=i))
    streak = habit.calculate_current_streak()
    assert streak == 3


def test_longest_streak_for_habit(fresh_db):

    """Test that the longest streak is calculated correctly for a habit."""

    habit_id = fresh_db.add_habit("Longest Habit", "daily", 1)
    habit = Habit("Longest Habit", "daily", 1, db_instance=fresh_db, habit_id=habit_id)
    now = datetime.now()
    for i in range(5):
        fresh_db.add_completion(habit.id, now - timedelta(days=i))
    longest = habit.calculate_longest_streak()
    assert longest == 5


def test_recent_completions_fp(fresh_db):

    """Test that recent completions are returned in correct order."""

    habit_id = fresh_db.add_habit("Recent Habit", "daily", 1)
    habit = Habit("Recent Habit", "daily", 1, db_instance=fresh_db, habit_id=habit_id)
    now = datetime.now()
    dates = [now - timedelta(days=i) for i in range(4)]
    for d in dates:
        fresh_db.add_completion(habit.id, d)
    recent = recent_completions_fp(fresh_db.load_completions(habit.id))
    assert recent == sorted(dates, reverse=True)


def test_habit_longest_streak_analytics(fresh_db):
    
    """Test longest streak retrieval from analytics function."""

    habit_id = fresh_db.add_habit("Analytics Habit", "daily", 1)
    now = datetime.now()
    for i in range(3):
        fresh_db.add_completion(habit_id, now - timedelta(days=i))
    assert habit_longest_streak(habit_id, db_instance=fresh_db) == 3


def test_can_mark_performed(fresh_db):

    """Test that can_mark_performed enforces periodicity correctly."""

    habit_id = fresh_db.add_habit("Check Habit", "daily", 2)
    habit = Habit("Check Habit", "daily", 2, db_instance=fresh_db, habit_id=habit_id)
    assert habit.can_mark_performed() is True
    habit.performed()
    assert habit.can_mark_performed() is True
    habit.performed()
    assert habit.can_mark_performed() is False


def test_delete_habit(fresh_db):

    """Test that a habit can be deleted from the database."""

    habit_id = fresh_db.add_habit("Delete Habit", "daily", 1)
    habit = Habit("Delete Habit", "daily", 1, db_instance=fresh_db, habit_id=habit_id)
    fresh_db.delete_habit(habit.id)
    habits = fresh_db.load_habits()
    assert not any(h['id'] == habit.id for h in habits)


def test_period_summary(fresh_db):

    """Test daily period summary shows completed and missed habits."""

    habit1_id = fresh_db.add_habit("Daily1", "daily", 1)
    habit2_id = fresh_db.add_habit("Daily2", "daily", 2)
    habit1 = Habit("Daily1", "daily", 1, db_instance=fresh_db, habit_id=habit1_id)
    habit2 = Habit("Daily2", "daily", 2, db_instance=fresh_db, habit_id=habit2_id)
    habit1.performed() 
    summary = fresh_db.period_summary("daily")
    assert summary['completed'] == 1

    assert summary['missed'] >= 1
