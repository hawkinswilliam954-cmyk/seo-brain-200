import json
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "agents" / "registry.json"
agents = json.loads(path.read_text(encoding="utf-8"))
ids = [a["id"] for a in agents]
assert len(agents) == 200, f"Expected 200 roles, got {len(agents)}"
assert len(set(ids)) == 200, "Duplicate agent IDs found"
departments = {a["department"] for a in agents}
assert len(departments) == 10, f"Expected 10 departments, got {len(departments)}"
print(f"OK: {len(agents)} roles across {len(departments)} departments.")
