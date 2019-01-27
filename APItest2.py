import requests
import json
from predictions_project.settings import production

# get list of fixtures for season
season = 13045

http1 = 'https://soccer.sportmonks.com/api/v2.0/seasons/'
idConcat = str(season)
http2 = '?api_token='
if production.sm_API == '':
    from predictions_project.settings import local
    api_token = local.sm_API
else:
    api_token = production.sm_API
http3 = '&include=fixtures'

requestString = http1+idConcat+http2+api_token+http3

response = requests.get(requestString)
smData= response.json()
dataJson = json.dumps(smData, sort_keys=True, indent=4)
fixtures_for_season = json.loads(dataJson)

f = fixtures_for_season['data']['fixtures']['data']
# populate a list of all fixture ids with all ids converted to strings so they can be concatenated below
l = [str(g['id']) for g in f]
# concatenate all the strings separated with comma
s = ','.join(l)

# api call to get the fixtures for all ids in variable 's'
http4 = 'https://soccer.sportmonks.com/api/v2.0/fixtures/multi/'
all_fixtures = s
http5 = '?api_token='
if production.sm_API == '':
    from predictions_project.settings import local
    api_token2 = local.sm_API
else:
    api_token2 = production.sm_API
http6 = '&include=round,stage,venue,localCoach,visitorCoach'

requestString = http4+all_fixtures+http5+api_token2+http6

response = requests.get(requestString)
smData= response.json()
dataJson = json.dumps(smData, sort_keys=True, indent=4)
fixtures_for_ids = json.loads(dataJson)

print fixtures_for_ids

