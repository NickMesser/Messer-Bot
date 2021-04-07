import requests
import json

header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15'}
responce = requests.get('https://addons-ecs.forgesvc.net/api/v2/addon/search?categoryId=4780&gameId=432&gameVersion=1.16.5&index=0&pageSize=255&searchFilter=toms-storage&sectionId=0&sort=0', headers=header)
data = responce.json()

selectedMod = {}
for x in data:
    if x['slug'] == 'toms-storage-fabric':
        selectedMod = x
        break

print(selectedMod)
