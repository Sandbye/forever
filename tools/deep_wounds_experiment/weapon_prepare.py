import copy, json

db = json.load(open("assets/database/db.json"))
by_id = {item["id"]: item for item in db["items"]}
wanted = [19168, 279259, 2244, 12939, 12940, 19166, 12590, 12783, 14555]
weapons = []
for item_id in wanted + [22384, 12798]:
    if item_id not in by_id: raise ValueError(f"Requested item {item_id} is absent from the pinned Forever database")
    item = by_id[item_id]
    if item.get("weaponType") not in (1, 2, 4, 9) or item.get("handType") not in (1, 2, 3): raise ValueError(f"Invalid one-hand weapon: {item}")
    if item.get("reqLvl", 0) > 60 or item.get("factionRestriction") == 1: raise ValueError(f"Not legal for this Horde level-60 setup: {item_id}")
    if item.get("classAllowlist") and 1 not in item["classAllowlist"]: raise ValueError(f"Warrior cannot use {item_id}")
    scaling = item.get("scalingOptions", {}).get("0", {})
    if not scaling.get("weaponDamageMax") or not item.get("weaponSpeed"): raise ValueError(f"No current base damage for {item_id}")
    weapons.append(dict(id=item_id, name=item["name"], type=item["weaponType"], hand=item["handType"], speed=item["weaponSpeed"], min=scaling["weaponDamageMin"], max=scaling["weaponDamageMax"], ilvl=scaling.get("ilvl"), stats=scaling.get("stats", {}), unique=item.get("unique",False), limitCategory=item.get("limitCategory",0), sources=item.get("sources",[])))
pool = weapons[:-2]
pairs = []
for mh in pool:
    if mh["hand"] not in (1,2): continue
    for oh in pool:
        if oh["hand"] not in (2,3): continue
        if mh["id"] == oh["id"] and mh["unique"]: continue
        if mh["limitCategory"] and mh["limitCategory"] == oh["limitCategory"]: continue
        pairs.append((mh,oh))
pairs.append((weapons[-2], weapons[-1]))
base = json.load(open("experiment-clean-inputs.json"))
templates = [entry for entry in base["cases"] if entry["request"]["encounter"]["duration"] == 180]
cases = []
kind = {9:"sword",2:"dagger",1:"axe",4:"mace"}
for mh, oh in pairs:
    for template in templates:
        entry = copy.deepcopy(template)
        entry["name"] = f'{mh["name"]} + {oh["name"]} | 180s | Hamstring {"ON" if entry["ham"] else "OFF"}'
        entry["pair"] = [mh["id"],oh["id"]]
        entry["category"] = kind[mh["type"]] + "/" + kind[oh["type"]]
        player = entry["request"]["raid"]["parties"][0]["players"][0]
        player["equipment"]["items"][14] = {"id":mh["id"],"enchant":1900}
        player["equipment"]["items"][15] = {"id":oh["id"],"enchant":1900}
        entry["request"]["simOptions"]["iterations"] = 500
        cases.append(entry)
if len(cases) > 200: raise ValueError(f"Too many cases: {len(cases)}")
with open("experiment-weapon-inputs.json","w") as f: json.dump(dict(cases=cases),f)
with open("experiment-weapon-catalog.json","w") as f: json.dump(weapons,f)
print(f"Prepared {len(pairs)} legal weapon pairs and {len(cases)} screening cases, 500 iterations each.")
print("SELECTED_WEAPONS_BEGIN")
print(json.dumps(weapons))
print("SELECTED_WEAPONS_END")
