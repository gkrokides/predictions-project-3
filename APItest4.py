import requests
import json
from predictions_project.settings import production


# get list of fixtures by date for league
league = 253 #cyprus division 1
season = 13045
market_id = 1

http1 = 'https://soccer.sportmonks.com/api/v2.0/fixtures/between/'
start_date = '2018-08-01' #YYYY-MM-DD
end_date = '2019-04-01' #YYYY-MM-DD
# idConcat = str(season)
http2 = '?api_token='
if production.sm_API == '':
    from predictions_project.settings import local
    api_token = local.sm_API
else:
    api_token = production.sm_API
http3 = '&include=round,stage,odds&leagues='
http4 = str(league)

requestString = http1+start_date+'/'+end_date+http2+api_token+http3+http4

response = requests.get(requestString)
smData= response.json()
dataJson = json.dumps(smData, sort_keys=True, indent=4)
fixtures_for_date = json.loads(dataJson)

f = fixtures_for_date['data']

final_list = []
fixtures_with_no_odds = []

for i in range(0, len(f)-1):
    if f[i]['season_id'] == season:
        allOdds = f[i]['odds']['data']
        oddslist = [x for x in allOdds if x['id'] == market_id]
        if len(oddslist) < 1:
            # if there are no available odds for that match the fields will be empty
            finalData = {'1': '', 'X': '', '2': ''}
        else:
            odds1x2 = [x for x in oddslist[0]['bookmaker']['data']]
            finalData = {k['label']:k['value'] for k in odds1x2[0]['odds']['data']}    
        
        final_list.append({
            'fixture_id': f[i]['id'],
            'season': f[i]['season_id'],
            'hometeam': f[i]['localteam_id'],
            'awayteam': f[i]['visitorteam_id'],
            'home_goals': f[i]['scores']['localteam_score'],
            'away_goals': f[i]['scores']['visitorteam_score'],
            'ht_score': f[i]['scores']['ht_score'],
            'ft_score': f[i]['scores']['ft_score'],
            'match_status': f[i]['time']['status'],
            'match_date': f[i]['time']['starting_at']['date'],
            'match_time': f[i]['time']['starting_at']['time'],
            'gameweek': f[i]['round']['data']['name'],
            'stage': f[i]['stage']['data']['type'],
            'odds_1': finalData['1'],
            'odds_x': finalData['X'],
            'odds_2': finalData['2']
            })

print final_list


