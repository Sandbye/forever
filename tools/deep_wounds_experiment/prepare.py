import copy, json

source = json.load(open("tools/deep_wounds_experiment/test-fixtures/inputs.json"))
remove_groups = {"Engineering", "CD: Racials", "CD: Trinkets"}
for entry in source["cases"]:
    rotation = entry["request"]["raid"]["parties"][0]["players"][0]["rotation"]
    rotation["groups"] = [g for g in rotation["groups"] if g["name"] not in remove_groups]
    def keep(line):
        action = line.get("action", {})
        if action.get("groupReference", {}).get("groupName") in remove_groups: return False
        spell = action.get("castSpell", {}).get("spellId", {})
        if spell.get("otherId") in ("OtherActionResourcePotion", "OtherActionOffensivePotion"): return False
        if spell.get("spellId") == 12723: return False
        return True
    rotation["priorityList"] = [line for line in rotation["priorityList"] if keep(line)]
    rotation["valueVariables"] = [v for v in rotation["valueVariables"] if v["name"] not in ("Resource Potion: Rage", "Offensive Potion: Rage")]
    for variable in rotation["valueVariables"]:
        if variable["name"] == "Battle Shout: No Raid Buff":
            variable["value"] = {"const": {"val": "true"}}
with open("experiment-clean-inputs.json", "w") as f: json.dump(source, f)
print("Prepared four cases without unavailable racial, item, potion or external-shout references.")
