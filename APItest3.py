import requests
import json
from predictions_project.settings import production

http1 = 'https://soccer.sportmonks.com/api/v2.0/leagues?api_token='
includes = '&include=country'
if production.sm_API == '':
    from predictions_project.settings import local
    api_token = local.sm_API
else:
    api_token = production.sm_API

requestString = http1 + api_token

response = requests.get(requestString)
smResponse = response.json()
smJson = json.dumps(smResponse, sort_keys=True, indent=4)
smDict = json.loads(smJson)
total_pages = smDict['meta']['pagination']['total_pages']
final_list = []

for j in range(1, total_pages + 1):
    page = "&page=" + str(j)
    requestString = http1 + api_token + includes + page

    response = requests.get(requestString)
    smData = response.json()
    dataJson = json.dumps(smData, sort_keys=True, indent=4)
    allLeagues = json.loads(dataJson)

    lgs = allLeagues['data']

for i in range(0, len(lgs)):
    final_list.append({
        'league_id': lgs[i]['id'],
        'name': lgs[i]['name'],
        'country': lgs[i]['country']['data']['name'],
        'logo_path': lgs[i]['logo_path']
    })

print final_list
