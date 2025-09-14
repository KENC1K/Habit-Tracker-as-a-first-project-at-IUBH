
# Habit Tracker App

## Overview

A modern Python-based Habit Tracker to efficiently manage daily and weekly habits.
Track completions, monitor progress with current and longest streaks, and analyze habits with automated testing support.

## Requirements

* Python 3.7+
* Libraries: `sqlite3`, `datetime`, `collections`, `typing`, `subprocess`, `questionary`
* `pytest` for running automated tests
* Optional: install all dependencies via `requirements.txt`

## Setup

```bash
git clone https://github.com/KENC1K/Habit-Tracker-as-a-first-project-at-IUBH.git
cd "Habit Tracker"
pip install -r requirements.txt
```

## Running the App

```bash
py main.py
```

Navigate between the main menu, CLI, and analytics. All modules use the shared `habits.db` database.

## Modules

* **main.py** – Entry point to view habits, current streaks, and navigate to CLI or analytics.
* **cli.py** – Interactive interface to add, complete, or delete habits; reset the database.
* **analytics.py** – Provides functions for calculating streaks, completion summaries, and habit insights.
* **database.py** – Handles SQLite database operations, stores habits and completions, and initializes default data.
* **tests/test\_habit\_tracker.py** – Automated tests for habit functionalities using `pytest`.

## Features

* Daily and weekly habit support
* Tracks completions and calculates streaks automatically
* Analytics for habits, including longest streaks and recent completions
* Preloaded with 5 sample habits and 4 weeks of demo data
* Persistent SQLite database (`habits.db`)
* Temporary database for tests to avoid modifying main data

## Usage

* Launch `main.py` to view and manage habits.
* Use `cli.py` for interactive habit management tasks.
* Use `analytics.py` for detailed habit reports.
* Reset database via CLI to restore default habits and fixture data.
* Run all automated tests:

```bash
pytest -v
```

## Project Structure

```
Habit Tracker/
├─ main.py
├─ cli.py
├─ analytics.py
├─ database.py
├─ tests/
│  └─ test_habit_tracker.py
├─ habits.db
├─ README.md
└─ requirements.txt
```

## Notes

* Requires Python 3.7 or higher
* Fully documented modules
* All functionality implemented from scratch without external habit-tracking libraries

