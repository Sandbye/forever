import copy,json,re

source=json.load(open("experiment-clean-inputs.json"))
tree=json.load(open("ui/sim/talents/trees/warrior.json"))
preset_text=open("ui/specs/warrior/dps/presets.ts").read()
match=re.search(r"export const FuryTalents[^\n]*talentsString: '([^']+)'",preset_text)
if not match: raise ValueError("Fury preset talent string was not found")
our=source["cases"][0]["request"]["raid"]["parties"][0]["players"][0]["talentsString"]
normal=match.group(1)

def allocation(text):
    sections=text.split("-")
    result={}
    totals=[]
    for ti,branch in enumerate(tree):
        digits=sections[ti] if ti<len(sections) else ""
        if len(digits)>len(branch["talents"]): raise ValueError("Talent string exceeds the tree")
        ranks=[int(digits[i]) if i<len(digits) else 0 for i in range(len(branch["talents"]))]
        for i,talent in enumerate(branch["talents"]):
            rank=ranks[i]
            if rank<0 or rank>talent["maxPoints"]: raise ValueError("Invalid rank for "+talent["fieldName"])
            if rank:
                row=talent["location"]["rowIdx"]
                lower=sum(ranks[j] for j,t in enumerate(branch["talents"]) if t["location"]["rowIdx"]<row)
                if lower<row*5: raise ValueError("Tier not unlocked for "+talent["fieldName"])
                if talent.get("prereqLocation"):
                    prereq=next((j for j,t in enumerate(branch["talents"]) if t["location"]==talent["prereqLocation"]),None)
                    if prereq is None or ranks[prereq]!=branch["talents"][prereq]["maxPoints"]: raise ValueError("Prerequisite not filled for "+talent["fieldName"])
            result[talent["fieldName"]]=rank
        totals.append(sum(ranks))
    if sum(totals)!=51: raise ValueError("Expected 51 points")
    return result,totals

ours,our_totals=allocation(our)
fury,fury_totals=allocation(normal)
metadata=dict(builds=[dict(name="Our bleed hybrid",talents=our,totals=our_totals),dict(name="WoWSims Fury preset",talents=normal,totals=fury_totals)],differences=[dict(talent=k,ours=v,fury=fury[k]) for k,v in ours.items() if v!=fury[k]])
pairs=[(22384,12798),(279259,19168),(279259,12783)]
db=json.load(open("assets/database/db.json"))
names={item["id"]:item["name"] for item in db["items"]}
cases=[]
for mh,oh in pairs:
    if mh not in names or oh not in names: raise ValueError("Missing tested weapon")
    for build in metadata["builds"]:
        for template in source["cases"]:
            entry=copy.deepcopy(template)
            player=entry["request"]["raid"]["parties"][0]["players"][0]
            player["talentsString"]=build["talents"]
            player["equipment"]["items"][14]={"id":mh,"enchant":1900}
            player["equipment"]["items"][15]={"id":oh,"enchant":1900}
            entry["request"]["simOptions"]["iterations"]=5000
            entry["request"]["simOptions"]["randomSeed"]="1793550003"
            duration=entry["request"]["encounter"]["duration"]
            entry["name"]=f'{build["name"]} | {names[mh]} + {names[oh]} | {duration}s | Hamstring {"ON" if entry["ham"] else "OFF"}'
            cases.append(entry)
with open("experiment-build-inputs.json","w") as f: json.dump(dict(cases=cases),f)
with open("experiment-build-metadata.json","w") as f: json.dump(metadata,f,indent=2)
print("BUILD_METADATA_BEGIN")
print(json.dumps(metadata))
print("BUILD_METADATA_END")
print(f"Prepared {len(cases)} cases at 5000 iterations with a fresh shared seed.")
