import json

db = json.load(open("assets/database/db.json"))
rows = []
for item in db["items"]:
    if item.get("weaponType") not in (1, 2, 4, 9): continue
    if item.get("handType") not in (1, 2, 3): continue
    if item.get("reqLvl", 0) > 60 or item.get("factionRestriction") == 1: continue
    if item.get("classAllowlist") and 1 not in item["classAllowlist"]: continue
    scaling = item.get("scalingOptions", {}).get("0", {})
    speed = item.get("weaponSpeed", 0)
    if not speed: continue
    damage = (scaling.get("weaponDamageMin", 0) + scaling.get("weaponDamageMax", 0)) / 2
    sources = item.get("sources", [])
    raid = any(s.get("drop", {}).get("difficulty") == 2 for s in sources)
    rows.append(dict(id=item["id"], name=item["name"], type=item["weaponType"], hand=item["handType"], speed=speed, avg=damage, dps=damage/speed, ilvl=scaling.get("ilvl"), reqLvl=item.get("reqLvl"), unique=item.get("unique",False), sources=sources, raid=raid, stats=scaling.get("stats", {}), effects=item.get("itemEffects", []), phase=item.get("phase")))
chosen = []
for kind in (9, 2, 1, 4):
    for raid in (False, True):
        subset = sorted([r for r in rows if r["type"] == kind and r["raid"] == raid], key=lambda r: (-r["dps"],r["id"]))
        chosen.extend(subset[:8 if not raid else 3])
print("WEAPON_CATALOG_BEGIN")
print(json.dumps(chosen))
print("WEAPON_CATALOG_END")
with open("experiment-weapons.json", "w") as f: json.dump(chosen, f, indent=2)
