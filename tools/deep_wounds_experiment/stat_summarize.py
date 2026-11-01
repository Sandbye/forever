import json,os,math

data=json.load(open("experiment-stat-raw.json"))
rows=[]
for entry in data["results"]:
    raw=entry["raw"]
    n=raw["iterationsDone"]
    duration=raw.get("avgIterationDuration") or raw["firstIterationDuration"]
    player=entry["preflightStats"]["raidStats"]["parties"][0]["players"][0]
    sheet=player["finalStats"]
    stats=sheet["stats"]
    pseudo=sheet.get("pseudoStats",[])
    if len(stats)<39 or len(pseudo)<15: raise ValueError("Incomplete stat sheet")
    bleed=ham=0
    for action in raw["raidMetrics"]["parties"][0]["players"][0].get("actions",[]):
        spell=action.get("id",{}).get("spellId")
        for target in action.get("targets",[]):
            if spell in (12162,412609,12850,12868,12867): bleed+=target.get("damage",0)
            if spell in (7373,11581): ham+=target.get("casts",0)
    warnings=[]
    def visit(value):
        if isinstance(value,dict):
            if value.get("validation") and value.get("logLevel") in ("Warning","Error"): warnings.append(value)
            for child in value.values(): visit(child)
        elif isinstance(value,list):
            for child in value: visit(child)
    visit(entry["preflightStats"])
    if warnings: raise ValueError(str(warnings))
    rows.append(dict(name=entry["name"],profile=entry["name"].split(" | ")[0],ham=entry["ham"],dps=raw["raidMetrics"]["dps"]["avg"],stdev=raw["raidMetrics"]["dps"].get("stdev",0),iterations=n,deepWoundsDps=bleed/n/duration,hamstringPerFight=ham/n,strength=stats[0],agility=stats[1],attackPower=stats[14],armor=stats[27],health=stats[29],meleeCritPercent=pseudo[14],rotationWarnings=warnings))
baseline=next(r for r in rows if r["profile"]=="Baseline" and not r["ham"])
for row in rows:
    row["dpsChange"]=row["dps"]-next(r["dps"] for r in rows if r["profile"]=="Baseline" and r["ham"]==row["ham"])
    if row["profile"]=="+20 Strength":
        if not math.isclose(row["strength"]-baseline["strength"],20,abs_tol=1e-6) or not math.isclose(row["attackPower"]-baseline["attackPower"],40,abs_tol=1e-6): raise ValueError("Strength/AP perturbation did not apply as expected")
    if row["profile"]=="+20 Agility":
        if not math.isclose(row["agility"]-baseline["agility"],20,abs_tol=1e-6) or not math.isclose(row["meleeCritPercent"]-baseline["meleeCritPercent"],1,abs_tol=1e-6): raise ValueError("Agility/crit perturbation did not apply as expected")
result=dict(source=data["source"],mode="hypothetical-strength-agility-budget",results=rows)
with open("experiment-stat-summary.json","w") as f: json.dump(result,f,indent=2)
print("STAT_RESULTS_BEGIN")
print(json.dumps(result))
print("STAT_RESULTS_END")
with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as f:
    f.write("# Strength / Agility sensitivity\n\n| Case | DPS | Change | Bleed DPS | Crit | AP |\n|---|---:|---:|---:|---:|---:|\n")
    for r in rows: f.write(f'| {r["name"]} | {r["dps"]:.2f} | {r["dpsChange"]:+.2f} | {r["deepWoundsDps"]:.2f} | {r["meleeCritPercent"]:.2f}% | {r["attackPower"]:.0f} |\n')
