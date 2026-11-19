import json
from collections import Counter

with open("data/papers.json", "r", encoding="utf-8") as f:
    data = json.load(f)

papers = data["papers"]
# 'papers' is a dictionary of records; handle either dict values or a list.
records = papers.values() if isinstance(papers, dict) else papers

counts = Counter()
missing = 0
for rec in records:
    year = rec.get("year") if isinstance(rec, dict) else None
    if year is None:
        missing += 1
    else:
        counts[str(year)] += 1

print("Papers per year:")
for year in sorted(counts):
    print(f"{year}: {counts[year]}")
print(f"Total with year: {sum(counts.values())}")
if missing:
    print(f"Records without a year field: {missing}")
