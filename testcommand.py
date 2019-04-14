from __future__ import unicode_literals
from predictions.models import SeasonSM, TeamSM
from predictions_project.smhelpers.emptyIfNone import emptyIfNone
import datetime

# x=SMcall_LeagueFixturesByDaterange_paginated(181,12973,'2018-07-27','2019-07-30')


def SMcall_LeagueFixturesByDaterange_paginated(league, season, start_date, end_date):
    import requests
    import json
    from predictions_project.settings import production
    # league = 253 #cyprus division 1
    # season = 13045
    market_id = 1
    selected_season = SeasonSM.objects.get(pk=season)
    final_list = []

    http1 = 'https://soccer.sportmonks.com/api/v2.0/fixtures/between/'
    # start_date = '2019-03-29' #YYYY-MM-DD
    # end_date = '2019-03-31' #YYYY-MM-DD
    # idConcat = str(season)
    http2 = '?api_token='
    if production.sm_API == '':
        from predictions_project.settings import local
        api_token = local.sm_API
    else:
        api_token = production.sm_API
    http3 = '&include=round,stage,odds&leagues='
    http4 = str(league)

    requestString = http1 + start_date + '/' + end_date + http2 + api_token + http3 + http4

    response = requests.get(requestString)
    smData = response.json()
    dataJson = json.dumps(smData, sort_keys=True, indent=4)
    fixtures_for_date = json.loads(dataJson)
    total_pages = fixtures_for_date['meta']['pagination']['total_pages']

    # f = fixtures_for_date['data']

    # for i in range(0, len(f)):
    #     if f[i]['season_id'] == season:
    #         match_date_str = f[i]['time']['starting_at']['date']
    #         match_date = datetime.datetime.strptime(match_date_str, '%Y-%m-%d')
    #         match_time_str = f[i]['time']['starting_at']['time']
    #         match_time = datetime.datetime.strptime(match_time_str, '%H:%M:%S')
    #         current_hometeam = TeamSM.objects.get(pk=f[i]['localteam_id'])
    #         current_awayteam = TeamSM.objects.get(pk=f[i]['visitorteam_id'])
    #         allOdds = f[i]['odds']['data']
    #         oddslist = [x for x in allOdds if x['id'] == market_id]
    #         if len(oddslist) < 1:
    #             # if there are no available odds for that match the odds fields will be empty
    #             finalData = {'1': None, 'X': None, '2': None}
    #         else:
    #             odds1x2 = [x for x in oddslist[0]['bookmaker']['data']]
    #             finalData = {k['label']: k['value'] for k in odds1x2[0]['odds']['data']}

    #         if '1' in finalData:
    #             odds_1 = finalData['1']
    #         else:
    #             odds_1 = None

    #         if 'X' in finalData:
    #             odds_x = finalData['X']
    #         else:
    #             odds_x = None

    #         if '2' in finalData:
    #             odds_2 = finalData['2']
    #         else:
    #             odds_2 = None

    #         final_list.append({
    #             'fixture_id': f[i]['id'],
    #             'season': selected_season,
    #             'hometeam': current_hometeam,
    #             'awayteam': current_awayteam,
    #             'home_goals': f[i]['scores']['localteam_score'],
    #             'away_goals': f[i]['scores']['visitorteam_score'],
    #             'ht_score': emptyIfNone(f[i]['scores']['ht_score']),
    #             'ft_score': emptyIfNone(f[i]['scores']['ft_score']),
    #             'match_status': emptyIfNone(f[i]['time']['status']),
    #             'match_date': match_date,
    #             'match_time': match_time,
    #             'match_time': f[i]['time']['starting_at']['time'],
    #             'gameweek': f[i]['round']['data']['name'],
    #             'stage': f[i]['stage']['data']['name'],
    #             'odds_1': odds_1,
    #             'odds_x': odds_x,
    #             'odds_2': odds_2
    #         })

    # The part below is ran if the response is paginated i.e it has more than one page
    for j in range(1, total_pages + 1):
        http5 = "?page=" + str(j)
        requestString = http1 + start_date + '/' + end_date + http2 + api_token + http3 + http4 + http5

        response = requests.get(requestString)
        smData = response.json()
        dataJson = json.dumps(smData, sort_keys=True, indent=4)
        fixtures_for_date = json.loads(dataJson)

        f = fixtures_for_date['data']

        for i in range(0, len(f)):
            if f[i]['season_id'] == season:
                match_date_str = f[i]['time']['starting_at']['date']
                match_date = datetime.datetime.strptime(match_date_str, '%Y-%m-%d')
                match_time_str = f[i]['time']['starting_at']['time']
                match_time = datetime.datetime.strptime(match_time_str, '%H:%M:%S')
                current_hometeam = TeamSM.objects.get(pk=f[i]['localteam_id'])
                current_awayteam = TeamSM.objects.get(pk=f[i]['visitorteam_id'])
                allOdds = f[i]['odds']['data']
                oddslist = [x for x in allOdds if x['id'] == market_id]
                if len(oddslist) < 1:
                    # if there are no available odds for that match the odds fields will be empty
                    finalData = {'1': None, 'X': None, '2': None}
                else:
                    odds1x2 = [x for x in oddslist[0]['bookmaker']['data']]
                    finalData = {k['label']: k['value'] for k in odds1x2[0]['odds']['data']}

                if '1' in finalData:
                    odds_1 = finalData['1']
                else:
                    odds_1 = None

                if 'X' in finalData:
                    odds_x = finalData['X']
                else:
                    odds_x = None

                if '2' in finalData:
                    odds_2 = finalData['2']
                else:
                    odds_2 = None

                final_list.append({
                    'fixture_id': f[i]['id'],
                    'season': selected_season,
                    'hometeam': current_hometeam,
                    'awayteam': current_awayteam,
                    'home_goals': f[i]['scores']['localteam_score'],
                    'away_goals': f[i]['scores']['visitorteam_score'],
                    'ht_score': emptyIfNone(f[i]['scores']['ht_score']),
                    'ft_score': emptyIfNone(f[i]['scores']['ft_score']),
                    'match_status': emptyIfNone(f[i]['time']['status']),
                    'match_date': match_date,
                    'match_time': match_time,
                    'match_time': f[i]['time']['starting_at']['time'],
                    'gameweek': f[i]['round']['data']['name'],
                    'stage': f[i]['stage']['data']['name'],
                    'odds_1': odds_1,
                    'odds_x': odds_x,
                    'odds_2': odds_2
                })

    return final_list
