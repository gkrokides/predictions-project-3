import requests
import json
from predictions_project.settings import production
from predictions_project.smhelpers.emptyIfNone import emptyIfNone

# get fixtures for season in a list of dicts
season = 13045
l = []

http1 = 'https://soccer.sportmonks.com/api/v2.0/seasons/'
idConcat = str(season)
http2 = '?api_token='
if production.sm_API == '':
    from predictions_project.settings import local
    api_token = local.sm_API
else:
    api_token = production.sm_API
http3 = '&include=fixtures,stages,rounds'

requestString = http1+idConcat+http2+api_token+http3
response = requests.get(requestString)
smData= response.json()
dataJson = json.dumps(smData, sort_keys=True, indent=4)
fixtures_for_season = json.loads(dataJson)

# get rounds and stage for season
rounds_for_season = fixtures_for_season['data']['rounds']['data']
stages_for_season = fixtures_for_season['data']['stages']['data']

f = fixtures_for_season['data']['fixtures']['data']

for dictt in f:
    if dictt['weather_report'] != None:
        weatherCode = emptyIfNone(dictt['weather_report']['code']) # CHARFIELD
        weatherType = emptyIfNone(dictt['weather_report']['type']) # CHARFIELD
        weatherIcon = emptyIfNone(dictt['weather_report']['icon']) # TEXTFIELD
    else:
        weatherCode = ''
        weatherType = ''
        weatherIcon = ''

    l.append({
    'fixture_id': dictt['id'],
    'season': dictt['season_id'], # FOREIGN KEY
    'hometeam': dictt['localteam_id'], # FOREIGN KEY
    'awayteam': dictt['visitorteam_id'], # FOREIGN KEY
    'weatherCode': weatherCode,
    'weatherType': weatherType,
    'weatherIcon': weatherIcon,
    'home_formation': emptyIfNone(dictt['formations']['localteam_formation']), # CHARFIELD
    'away_formation': emptyIfNone(dictt['formations']['visitorteam_formation']), # CHARFIELD
    'home_goals': dictt['scores']['localteam_score'], # INTEGERFIElD
    'away_goals': dictt['scores']['visitorteam_score'], # INTEGERFIELD
    'ht_score': emptyIfNone(dictt['scores']['ht_score']), # CHARFIELD
    'ft_score': emptyIfNone(dictt['scores']['ft_score']), # CHARFIELD
    'match_status': emptyIfNone(dictt['time']['status']), # CHARFIELD
    'match_date': dictt['time']['starting_at']['date'], # CONVERT TO DATE
    'match_time': dictt['time']['starting_at']['time'], # NO NEED TO CONVERT TO TIME IF IT IS TEXT
    'gameweek': [gw['name'] for gw in rounds_for_season if gw['id'] == dictt['round_id']][0], # INTEGERFIELD
    'stage': [st['name'] for st in stages_for_season if st['id'] == dictt['stage_id']][0], # CHARFIELD
    })


print l

