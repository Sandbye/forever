import json,os

def summarize(path):
    data=json.load(open(path))
    rows=[]
    for entry in data["results"]:
        raw=entry["raw"]
        n=raw["iterationsDone"]
        duration=raw.get("avgIterationDuration") or raw["firstIterationDuration"]
        player=raw["raidMetrics"]["parties"][0]["players"][0]
        ham=bleed=overpower=0
        for action in player.get("actions",[]):
            spell=action.get("id",{}).get("spellId")
            for target in action.get("targets",[]):
                if spell in (7373,11581): ham+=target.get("casts",0)
                if spell in (12162,412609,12850,12868,12867): bleed+=target.get("damage",0)
                if spell in (7384,7887,11584,11585): overpower+=target.get("casts",0)
        warnings=[]
        def visit(value):
            if isinstance(value,dict):
                if value.get("validation") and value.get("logLevel") in ("Warning","Error"): warnings.append(value)
                for child in value.values(): visit(child)
            elif isinstance(value,list):
                for child in value: visit(child)
        visit(entry["preflightStats"])
        if warnings: raise ValueError(f"Rotation warnings for {entry['name']}: {warnings}")
        items=entry["request"]["raid"]["parties"][0]["players"][0]["equipment"]["items"]
        rows.append(dict(name=entry["name"],pair=[items[14]["id"],items[15]["id"]],ham=entry["ham"],duration=entry["request"]["encounter"]["duration"],dps=raw["raidMetrics"]["dps"]["avg"],stdev=raw["raidMetrics"]["dps"].get("stdev",0),iterations=n,deepWoundsDps=bleed/n/duration,hamstringPerFight=ham/n,overpowerPerFight=overpower/n,rotationWarnings=warnings))
    return dict(source=data["source"],results=rows)
result=dict(screen=summarize("experiment-weapon-screen.json"),confirmation=summarize("experiment-weapon-confirm.json"),weapons=json.load(open("experiment-weapon-catalog.json")))
with open("experiment-weapon-summary.json","w") as f: json.dump(result,f,indent=2)
print("WEAPON_RESULTS_BEGIN")
print(json.dumps(dict(confirmation=result["confirmation"],weapons=result["weapons"],screenCases=len(result["screen"]["results"]))))
print("WEAPON_RESULTS_END")
with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as f:
    f.write("# Weapon comparison\n\n| Pair / case | DPS | Bleed DPS | Hamstrings |\n|---|---:|---:|---:|\n")
    for row in sorted(result["confirmation"]["results"],key=lambda r:(r["duration"],-r["dps"])):
        f.write(f'| {row["name"]} | {row["dps"]:.2f} | {row["deepWoundsDps"]:.2f} | {row["hamstringPerFight"]:.2f} |\n')
