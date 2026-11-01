import copy,json

screen = json.load(open("experiment-weapon-screen.json"))
inputs = json.load(open("experiment-weapon-inputs.json"))
metadata = {entry["name"]:entry for entry in inputs["cases"]}
best = {}
for entry in screen["results"]:
    meta = metadata[entry["name"]]
    pair = tuple(meta["pair"])
    score = entry["raw"]["raidMetrics"]["dps"]["avg"]
    if pair not in best or score > best[pair]["score"]: best[pair] = dict(score=score,category=meta["category"],meta=meta)
ranked = sorted(best.items(), key=lambda x:(-x[1]["score"],x[0]))
selected = []
for category in ("sword/sword","sword/dagger","dagger/sword","dagger/dagger"):
    candidate = next((pair for pair, info in ranked if info["category"] == category),None)
    if candidate is not None and candidate not in selected: selected.append(candidate)

reference = (22384,12798)
if reference not in selected: selected.append(reference)
cases = []
for entry in inputs["cases"]:
    if tuple(entry["pair"]) not in selected: continue
    for duration in (60,180):
        item = copy.deepcopy(entry)
        item["name"] = item["name"].replace("180s", f"{duration}s")
        item["request"]["encounter"]["duration"] = duration
        item["request"]["simOptions"]["iterations"] = 3000
        cases.append(item)
with open("experiment-weapon-confirm-inputs.json","w") as f: json.dump(dict(cases=cases),f)
print(f"Confirming {len(selected)} pairs with both fillers and two durations: {len(cases)} cases, 3000 iterations each.")
