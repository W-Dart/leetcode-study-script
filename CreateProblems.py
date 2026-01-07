import json

problems = []

with open("Top50Problems.txt", "r") as f:
    for line in f:
        title = line.strip()
        if title == "":
            continue

        problems.append({
            "name": title,
            "status": "new",
            "confidence": None,
            "last_attempted": None,
            "notes": "",
            "next_review": None
        })

with open("Top50Problems.json", "w") as f:
    json.dump(problems, f, indent=2)

print(f"Created Top50Problems.json with {len(problems)} problems")