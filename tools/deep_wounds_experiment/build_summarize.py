import json,os

data=json.load(open("experiment-build-raw.json"))
rows=[]
for entry in data["results"]:
    raw=entry["raw"]
    n=raw["iterationsDone"]
    duration=raw.get("avgIterationDuration") or raw["firstIterationDuration"]
    player_metrics=raw["raidMetrics"]["parties"][0]["players"][0]
    ham=bleed=overpower=heroic=0
    for action in player_metrics.get("actions",[]):
        spell=action.get("id",{}).get("spellId")
        for target in action.get("targets",[]):
            if spell in (7373,11581): ham+=target.get("casts",0)
            if spell in (12162,412609,12850,12868,12867): bleed+=target.get("damage",0)
            if spell in (7384,7887,11584,11585): overpower+=target.get("casts",0)
            if spell in (11567,25286): heroic+=target.get("casts",0)
    warnings=[]
    def visit(value):
        if isinstance(value,dict):
            if value.get("validation") and value.get("logLevel") in ("Warning","Error"): warnings.append(value)
            for child in value.values(): visit(child)
        elif isinstance(value,list):
            for child in value: visit(child)
    visit(entry["preflightStats"])
    if warnings: raise ValueError(f"Rotation warnings: {warnings}")
    player=entry["request"]["raid"]["parties"][0]["players"][0]
    items=player["equipment"]["items"]
    rows.append(dict(name=entry["name"],build=entry["name"].split(" | ")[0],pair=[items[14]["id"],items[15]["id"]],talents=player["talentsString"],ham=entry["ham"],duration=entry["request"]["encounter"]["duration"],dps=raw["raidMetrics"]["dps"]["avg"],stdev=raw["raidMetrics"]["dps"].get("stdev",0),iterations=n,deepWoundsDps=bleed/n/duration,hamstringPerFight=ham/n,overpowerPerFight=overpower/n,heroicStrikePerFight=heroic/n,rotationWarnings=warnings))
result=dict(source=data["source"],metadata=json.load(open("experiment-build-metadata.json")),results=rows)
with open("experiment-build-summary.json","w") as f: json.dump(result,f,indent=2)
print("BUILD_RESULTS_BEGIN")
print(json.dumps(result))
print("BUILD_RESULTS_END")
with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as f:
    f.write("# Full talent build comparison\n\n| Case | DPS | Bleed DPS | Heroic Strikes |\n|---|---:|---:|---:|\n")
    for row in rows:
        f.write(f'| {row["name"]} | {row["dps"]:.2f} | {row["deepWoundsDps"]:.2f} | {row["heroicStrikePerFight"]:.2f} |\n')
