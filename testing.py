import json

with open('storage.json') as h:
    data = json.load(h)

sortedSuggestions = []

for mod in data['Suggestions']:
    if mod['CurrentStage'] == 'denied':
        sortedSuggestions.append(mod)

data['Suggestions'] = sortedSuggestions

with open('storage.json', 'w') as f:
    json.dump(data, f, sort_keys=True, indent=4)
