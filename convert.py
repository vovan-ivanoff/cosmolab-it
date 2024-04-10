import json
result = {}
with open("TDQuestion.json", 'r', encoding='UTF-8') as f:
    temp = json.load(f)
result["questions"] = []
for q in temp['content']:
    vopros = q['text']
    otvety = []
    for i,k in enumerate(q['choices']):
        otvety.append(k['text'])
        if "correct" in k:
            correct = i

    result["questions"].append({"question":vopros, "answers":otvety, "correct":correct, "time":30})
with open("test.json", 'w', encoding='UTF-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)