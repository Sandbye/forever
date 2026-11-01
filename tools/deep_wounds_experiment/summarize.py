import json, os

def summarize(path):
    data = json.load(open(path))
    rows = []
    for entry in data["results"]:
        raw = entry["raw"]
        n = raw["iterationsDone"]
        duration = raw.get("avgIterationDuration") or raw["firstIterationDuration"]
        metrics = raw["raidMetrics"]
        ham = bleed = overpower = 0
        for action in metrics["parties"][0]["players"][0].get("actions", []):
            spell = action.get("id", {}).get("spellId")
            for target in action.get("targets", []):
                if spell in (7373, 11581): ham += target.get("casts", 0)
                if spell in (12162, 412609, 12850, 12868, 12867): bleed += target.get("damage", 0)
                if spell in (7384, 7887, 11584, 11585): overpower += target.get("casts", 0)
        warnings = []
        def visit(value):
            if isinstance(value, dict):
                if value.get("validation"): warnings.append(value)
                for child in value.values(): visit(child)
            elif isinstance(value, list):
                for child in value: visit(child)
        for party in entry["preflightStats"].get("raidStats", {}).get("parties", []):
            for player in party.get("players", []): visit(player.get("rotationStats", {}))
        rows.append(dict(name=entry["name"], dps=metrics["dps"]["avg"], stdev=metrics["dps"].get("stdev", 0), iterations=n, deepWoundsDps=bleed/n/duration, hamstringPerFight=ham/n, overpowerPerFight=overpower/n, rotationWarnings=warnings))
    return dict(source=data["source"], results=rows)

result = dict(baseline=summarize("experiment-baseline.json"), candidate=summarize("experiment-candidate.json"))
with open("experiment-summary.json", "w") as f: json.dump(result, f, indent=2)
print("EXPERIMENT_SUMMARY_BEGIN")
print(json.dumps(result))
print("EXPERIMENT_SUMMARY_END")
with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
    f.write("# Deep Wounds hand experiment\n\n| Engine | Case | DPS | Deep Wounds DPS | Hamstring / fight |\n|---|---|---:|---:|---:|\n")
    for model in ("baseline", "candidate"):
        for row in result[model]["results"]:
            f.write(f'| {model} | {row["name"]} | {row["dps"]:.2f} | {row["deepWoundsDps"]:.2f} | {row["hamstringPerFight"]:.2f} |\n')
