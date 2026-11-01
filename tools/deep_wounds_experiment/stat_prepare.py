import copy,json

base=json.load(open("experiment-clean-inputs.json"))
templates=[x for x in base["cases"] if x["request"]["encounter"]["duration"]==180]
profiles=[("Baseline",0,0),("+20 Strength",20,0),("+20 Agility",0,20),("20 Strength -> 20 Agility",-20,20),("40 Strength -> 40 Agility",-40,40),("80 Strength -> 80 Agility",-80,80)]
cases=[]
for label,strength,agility in profiles:
    for template in templates:
        entry=copy.deepcopy(template)
        player=entry["request"]["raid"]["parties"][0]["players"][0]
        player["equipment"]["items"][14]={"id":279259,"enchant":1900}
        player["equipment"]["items"][15]={"id":19168,"enchant":1900}
        stats=[0]*39
        stats[0]=strength
        stats[1]=agility
        player["bonusStats"]={"stats":stats}
        entry["request"]["simOptions"]["iterations"]=5000
        entry["request"]["simOptions"]["randomSeed"]="1793550004"
        entry["name"]=f'{label} | Hamstring {"ON" if entry["ham"] else "OFF"}'
        cases.append(entry)
with open("experiment-stat-inputs.json","w") as f: json.dump(dict(cases=cases),f)
print(f"Prepared {len(cases)} hypothetical stat cases, equal weapon/armor gear, 5000 iterations, seed1793550004.")
