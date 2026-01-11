import json
from datetime import date, timedelta

BASE_DAILY_LIMIT = 2
DATA_FILE = "Top50Problems.json"

# ---------- Helper functions for date serialization ----------

def serialize_date(d):
    return d.isoformat() if d else None

def deserialize_date(s):
    return date.fromisoformat(s) if s else None


# ---------- Data IO ----------

def load_problems(file_path):
    with open(file_path, "r") as file:
        problems = json.load(file)

    # Convert ISO strings back to date objects
    for p in problems:
        if p.get("next_review"):
            p["next_review"] = deserialize_date(p["next_review"])
        if p.get("last_attempted"):
            p["last_attempted"] = deserialize_date(p["last_attempted"])

    return problems


def save_problems(problems, file_path):
    # Convert dates to strings for JSON
    for p in problems:
        p["next_review"] = serialize_date(p.get("next_review"))
        p["last_attempted"] = serialize_date(p.get("last_attempted"))

    with open(file_path, "w") as file:
        json.dump(problems, file, indent=2)


# ---------- Selection Logic ----------

def get_next_problem(problems, today, used_names, reviews_given=0):
    """
    Select the next problem.
    - Allow at most one review problem per session/day (controlled by reviews_given).
    - If a review has already been given and there are new problems available, prefer a new one.
    - If no new problems exist, allow additional overdue review problems.
    """
    # Overdue reviews (due today or earlier) not yet used
    reviewable = [
        p for p in problems
        if p["status"] == "reviewable"
        and p.get("next_review") is not None
        and p["next_review"] <= today
        and p["name"] not in used_names
    ]
    reviewable.sort(key=lambda p: p["next_review"])

    # New problems not yet used
    new_problems = [
        p for p in problems
        if p["status"] == "new"
        and p["name"] not in used_names
    ]

    # If we haven't had a review yet, prefer a reviewable problem first
    if reviews_given < 1 and reviewable:
        return reviewable[0]

    # Prefer new problems when possible
    if new_problems:
        return new_problems[0]

    # If no new problems exist, fall back to reviewable problems
    if reviewable:
        return reviewable[0]

    return None


# ---------- Update Logic ----------

def update_problem_status(problem, rating, today):
    if rating == "green":
        if problem["status"] == "reviewable":
            problem["status"] = "completed"
            problem["next_review"] = None
        else:  # new
            problem["status"] = "reviewable"
            problem["next_review"] = today + timedelta(days=7)
        problem["confidence"] = "green"

    elif rating == "yellow":
        problem["status"] = "reviewable"
        problem["next_review"] = today + timedelta(days=3)
        problem["confidence"] = "yellow"

    elif rating == "red":
        problem["status"] = "reviewable"
        problem["next_review"] = today + timedelta(days=1)
        problem["confidence"] = "red"

    problem["last_attempted"] = today


# ---------- CLI ----------

def main():
    problems = load_problems(DATA_FILE)
    today = date.today()

    print(f"\n📅 Today: {today}")
    print(f"Starting session (minimum {BASE_DAILY_LIMIT} problems)")

    used_problem_names = set()
    problems_done = 0
    reviews_given = 0

    while True:
        problem = get_next_problem(problems, today, used_problem_names, reviews_given)

        if problem is None:
            print("\n🎉 No more problems available today.")
            break

        label = "new" if problem["status"] == "new" else f"review ({problem['confidence']})"
        print(f"\n🧠 Problem: {problem['name']} [{label}]")

        # If this is an overdue review problem, count it toward the daily review limit
        if problem["status"] == "reviewable" and problem.get("next_review") and problem["next_review"] <= today:
            reviews_given += 1

        # Show existing notes, if any
        if problem.get("notes"):
            print(f"📝 Notes: {problem['notes']}")

        add_notes = input("Add or edit notes? (y/n): ").strip().lower()
        if add_notes == "y":
            notes = input("Enter notes (leave blank to clear): ").strip()
            problem["notes"] = notes

        rating = input("Rate your attempt: [r]ed, [y]ellow, [g]reen → ").strip().lower()

        if rating in {"r", "y", "g"}:
            rating_map = {"r": "red", "y": "yellow", "g": "green"}
            update_problem_status(problem, rating_map[rating], today)
        else:
            print("Invalid input — skipping rating.")
            continue

        used_problem_names.add(problem["name"])
        problems_done += 1

        # Mandatory minimum
        if problems_done < BASE_DAILY_LIMIT:
            continue

        more = input("Do you want another problem? (y/n): ").strip().lower()
        if more != "y":
            break

    save_problems(problems, DATA_FILE)
    print("\n✅ Session saved. See you next time.")


if __name__ == "__main__":
    main()
