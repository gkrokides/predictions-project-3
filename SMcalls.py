from __future__ import unicode_literals
from predictions.models import CountrySM, LeagueSM, SeasonSM, TeamSM, FixtureSM, Game
from predictions_project.smhelpers.emptyIfNone import emptyIfNone
import datetime
from datetime import timedelta, datetime
import requests
import json


# API call to get data for selected league (by Id) from sportmonks and convert it to dict


def SMcall_LeagueById(leagueId):
    import requests
    import json
    from predictions_project.settings import production

    http1 = 'https://soccer.sportmonks.com/api/v2.0/leagues/'
    leagueID = str(leagueId)
    http2 = '?api_token='
    if production.sm_API == '':
        from predictions_project.settings import local
        api_token = local.sm_API
    else:
        api_token = production.sm_API
    http3 = '&include=country,season'

    requestString = http1 + leagueID + http2 + api_token + http3

    response = requests.get(requestString)

    smleague = response.json()
    leaguesJson = json.dumps(smleague, sort_keys=True, indent=4)
    leaguesDict = json.loads(leaguesJson)
    smleague_data = {}

    countryObj = CountrySM.objects.get(pk=leaguesDict['data']['country_id'])

    # populate the dict to be used to update the smLeague database table
    smleague_data['league_id'] = leaguesDict['data']['id']
    smleague_data['name'] = leaguesDict['data']['name']
    smleague_data['country'] = countryObj
    smleague_data['is_cup'] = leaguesDict['data']['is_cup']
    smleague_data['live_standings'] = leaguesDict['data']['live_standings']
    smleague_data['topscorer_goals'] = leaguesDict['data']['coverage']['topscorer_goals']
    smleague_data['topscorer_assists'] = leaguesDict['data']['coverage']['topscorer_assists']
    smleague_data['topscorer_cards'] = leaguesDict['data']['coverage']['topscorer_cards']

    return smleague_data

# API call to get data for selected Country (by Id) from sportmonks and convert it to dict


def SMcall_CountryById(Id):
    import requests
    import json
    from predictions_project.settings import production

    http1 = 'https://soccer.sportmonks.com/api/v2.0/countries/'
    idConcat = str(Id)
    http2 = '?api_token='
    if production.sm_API == '':
        from predictions_project.settings import local
        api_token = local.sm_API
    else:
        api_token = production.sm_API

    requestString = http1 + idConcat + http2 + api_token

    response = requests.get(requestString)

    smResponse = response.json()
    smJson = json.dumps(smResponse, sort_keys=True, indent=4)
    smDict = json.loads(smJson)
    db_data = {}

    # populate the dict to be used to update the smCountry database table
    db_data['country_id'] = smDict['data']['id']
    db_data['name'] = smDict['data']['name']
    try:
        db_data['continent'] = smDict['data']['extra']['continent']
    except TypeError as er:
        db_data['continent'] = ''
        print 'Warning: ' + smDict['data']['name'] + ' is missing the continent.'

    try:
        db_data['fifa_code'] = smDict['data']['extra']['fifa']
    except TypeError as er:
        db_data['fifa_code'] = ''
        print 'Warning: ' + smDict['data']['name'] + ' is missing the fifa_code.'

    try:
        db_data['iso_code'] = smDict['data']['extra']['iso']
    except TypeError as er:
        db_data['iso_code'] = ''
        print 'Warning: ' + smDict['data']['name'] + ' is missing the iso_code.'

    try:
        db_data['flag'] = smDict['data']['extra']['flag']
    except TypeError as er:
        db_data['flag'] = ''
        print 'Warning: ' + smDict['data']['name'] + ' is missing the flag.'

    return db_data

# API call to get data for selected Season (by Id) from sportmonks and convert it to dict


def SMcall_SeasonById(Id):
    import requests
    import json
    from predictions_project.settings import production

    http1 = 'https://soccer.sportmonks.com/api/v2.0/seasons/'
    idConcat = str(Id)
    http2 = '?api_token='
    if production.sm_API == '':
        from predictions_project.settings import local
        api_token = local.sm_API
    else:
        api_token = production.sm_API

    requestString = http1 + idConcat + http2 + api_token

    response = requests.get(requestString)

    smResponse = response.json()
    smJson = json.dumps(smResponse, sort_keys=True, indent=4)
    smDict = json.loads(smJson)
    db_data = {}

    leagueObj = LeagueSM.objects.get(pk=smDict['data']['league_id'])

    # populate the dict to be used to update the smSeason database table
    db_data['season_id'] = smDict['data']['id']
    db_data['name'] = smDict['data']['name']
    db_data['league'] = leagueObj

    return db_data

# API call to get data for selected Team (by Id) from sportmonks and convert it to dict


def SMcall_TeamById(Id):
    import requests
    import json
    from predictions_project.settings import production

    http1 = 'https://soccer.sportmonks.com/api/v2.0/teams/'
    idConcat = str(Id)
    http2 = '?api_token='
    if production.sm_API == '':
        from predictions_project.settings import local
        api_token = local.sm_API
    else:
        api_token = production.sm_API
    http3 = '&include=venue'

    requestString = http1 + idConcat + http2 + api_token + http3

    response = requests.get(requestString)

    smResponse = response.json()
    smJson = json.dumps(smResponse, sort_keys=True, indent=4)
    smDict = json.loads(smJson)
    db_data = {}

    countryObj = CountrySM.objects.get(pk=smDict['data']['country_id'])

    # populate the dict to be used to update the smTeam database table
    db_data['team_id'] = smDict['data']['id']
    db_data['name'] = smDict['data']['name']
    db_data['short_code'] = smDict['data']['short_code']
    db_data['country'] = countryObj
    db_data['founded'] = smDict['data']['founded']
    db_data['logo_path'] = smDict['data']['logo_path']

    return db_data

# API call to get data for selected Fixture (by Id) from sportmonks and convert it to dict


def SMcall_FixtureById(Id):
    import requests
    import json
    from predictions_project.settings import production

    http1 = 'https://soccer.sportmonks.com/api/v2.0/fixtures/'
    idConcat = str(Id)
    http2 = '?api_token='
    if production.sm_API == '':
        from predictions_project.settings import local
        api_token = local.sm_API
    else:
        api_token = production.sm_API
    http3 = '&include=round,stage,flatOdds,venue,localCoach,visitorCoach'

    requestString = http1 + idConcat + http2 + api_token + http3

    response = requests.get(requestString)

    smResponse = response.json()
    smJson = json.dumps(smResponse, sort_keys=True, indent=4)
    smDict = json.loads(smJson)
    db_data = {}

    # populate the dict to be used to update the smFixture database table
    db_data['fixture_id'] = smDict['data']['id']
    db_data['season'] = smDict['data']['season_id']  # FOREIGN KEY
    db_data['hometeam'] = smDict['data']['localteam_id']  # FOREIGN KEY
    db_data['awayteam'] = smDict['data']['visitorteam_id']  # FOREIGN KEY
    if smDict['data']['weather_report'] != None:
        db_data['weather_code'] = emptyIfNone(smDict['data']['weather_report']['code'])  # CHARFIELD
        db_data['weather_type'] = emptyIfNone(smDict['data']['weather_report']['type'])  # CHARFIELD
        db_data['weather_icon'] = emptyIfNone(smDict['data']['weather_report']['icon'])  # TEXTFIELD
    else:
        db_data['weather_code'] = ''
        db_data['weather_type'] = ''
        db_data['weather_icon'] = ''
    db_data['attendance'] = emptyIfNone(smDict['data']['attendance'])  # INTEGERFIELD
    db_data['pitch_status'] = emptyIfNone(smDict['data']['pitch'])  # CHARFIELD
    db_data['home_formation'] = emptyIfNone(smDict['data']['formations']['localteam_formation'])  # CHARFIELD
    db_data['away_formation'] = emptyIfNone(smDict['data']['formations']['visitorteam_formation'])  # CHARFIELD
    db_data['home_goals'] = smDict['data']['scores']['localteam_score']  # INTEGERFIElD
    db_data['away_goals'] = smDict['data']['scores']['visitorteam_score']  # INTEGERFIELD
    db_data['ht_score'] = emptyIfNone(smDict['data']['scores']['ht_score'])  # CHARFIELD
    db_data['ft_score'] = emptyIfNone(smDict['data']['scores']['ft_score'])  # CHARFIELD
    db_data['match_status'] = emptyIfNone(smDict['data']['time']['status'])  # CHARFIELD
    db_data['match_date'] = smDict['data']['time']['starting_at']['date']  # CONVERT TO DATE
    db_data['match_time'] = smDict['data']['time']['starting_at']['time']  # NO NEED TO CONVERT TO TIME IF IT IS TEXT
    db_data['gameweek'] = smDict['data']['round']['data']['name']  # INTEGERFIELD
    db_data['stage'] = smDict['data']['stage']['data']['name']  # CHARFIELD
    db_data['venue_name'] = emptyIfNone(smDict['data']['venue']['data']['name'])  # CHARFIELD
    db_data['venue_surface'] = emptyIfNone(smDict['data']['venue']['data']['surface'])  # CHARFIELD
    db_data['venue_city'] = emptyIfNone(smDict['data']['venue']['data']['city'])  # CHARFIELD
    db_data['venue_capacity'] = smDict['data']['venue']['data']['capacity']  # LONG INTEGERFIELD
    db_data['venue_image'] = emptyIfNone(smDict['data']['venue']['data']['image_path'])  # TEXTFIELD

    if 'localCoach' in smDict['data']:
        db_data['home_coach'] = emptyIfNone(smDict['data']['localCoach']['data']['fullname'])  # CHARFIELD
        db_data['home_coach_nationality'] = emptyIfNone(smDict['data']['localCoach']['data']['nationality'])  # CHARFIELD
        db_data['home_coach_image'] = emptyIfNone(smDict['data']['localCoach']['data']['image_path'])  # TEXTFIELD
    else:
        db_data['home_coach'] = ''
        db_data['home_coach_nationality'] = ''
        db_data['home_coach_image'] = ''

    if 'visitorCoach' in smDict['data']:
        db_data['away_coach'] = emptyIfNone(smDict['data']['visitorCoach']['data']['fullname'])  # CHARFIELD
        db_data['away_coach_nationality'] = emptyIfNone(smDict['data']['visitorCoach']['data']['nationality'])  # CHARFIELD
        db_data['away_coach_image'] = emptyIfNone(smDict['data']['visitorCoach']['data']['image_path'])  # TEXTFIELD
    else:
        db_data['away_coach'] = ''
        db_data['away_coach_nationality'] = ''
        db_data['away_coach_image'] = ''

    return db_data

# API call to get fixtures json for selected season from sportmonks and convert it to dict


def SMcall_LeagueFixturesByDaterange(league, season, start_date, end_date):
    import requests
    import json
    from predictions_project.settings import production
    # league = 253 #cyprus division 1
    # season = 13045
    market_id = 1
    selected_season = SeasonSM.objects.get(pk=season)

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

    f = fixtures_for_date['data']

    final_list = []

    for i in range(0, len(f)):
        if f[i]['season_id'] == season:
            match_date_str = f[i]['time']['starting_at']['date']
            match_date = datetime.strptime(match_date_str, '%Y-%m-%d')
            match_time_str = f[i]['time']['starting_at']['time']
            match_time = datetime.strptime(match_time_str, '%H:%M:%S')
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

# Same as above but it can handle pagination


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
    timezone = "&tz=Europe/Athens"

    requestString = http1 + start_date + '/' + end_date + http2 + api_token + http3 + http4 + timezone
    response = requests.get(requestString)
    smData = response.json()
    dataJson = json.dumps(smData, sort_keys=True, indent=4)
    fixtures_for_date = json.loads(dataJson)
    total_pages = fixtures_for_date['meta']['pagination']['total_pages']

    for j in range(1, total_pages + 1):
        http5 = "&page=" + str(j)
        requestString = http1 + start_date + '/' + end_date + http2 + api_token + http3 + http4 + http5 + timezone

        response = requests.get(requestString)
        smData = response.json()
        dataJson = json.dumps(smData, sort_keys=True, indent=4)
        fixtures_for_date = json.loads(dataJson)

        f = fixtures_for_date['data']

        for i in range(0, len(f)):
            if f[i]['season_id'] == season:
                match_date_str = f[i]['time']['starting_at']['date']
                match_date = datetime.strptime(match_date_str, '%Y-%m-%d')
                match_time_str = f[i]['time']['starting_at']['time']
                match_time = datetime.strptime(match_time_str, '%H:%M:%S')
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


# API call to get data for all countries (in your plan) from sportmonks and convert it to dict


def SMcall_allCountries():
    import requests
    import json
    from predictions_project.settings import production

    http1 = 'https://soccer.sportmonks.com/api/v2.0/countries?api_token='
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
    final_list = []

    for i in range(0, len(smDict['data'])):
        try:
            continent = smDict['data'][i]['extra']['continent']
        except TypeError as er:
            continent = ''
            print 'Warning: ' + smDict['data'][i]['name'] + ' is missing the continent.'

        try:
            fifa = smDict['data'][i]['extra']['fifa']
        except TypeError as er:
            fifa = ''
            print 'Warning: ' + smDict['data'][i]['name'] + ' is missing the fifa_code.'

        try:
            iso = smDict['data'][i]['extra']['iso']
        except TypeError as er:
            iso = ''
            print 'Warning: ' + smDict['data'][i]['name'] + ' is missing the iso_code.'

        try:
            flag = smDict['data'][i]['extra']['flag']
        except TypeError as er:
            flag = ''
            print 'Warning: ' + smDict['data'][i]['name'] + ' is missing the flag.'

        final_list.append({
            'country_id': smDict['data'][i]['id'],
            'name': smDict['data'][i]['name'],
            'continent': continent,
            'fifa_code': fifa,
            'iso_code': iso,
            'flag': flag
        })

    return final_list

# API call to get the teams for the selected season from sportmonks and convert it to dict


def SMcall_teamsBySeason(seasonId):
    import requests
    import json
    from predictions_project.settings import production

    # create the http address that will get me the data
    http1 = 'https://soccer.sportmonks.com/api/v2.0/teams/season/'
    http2 = str(seasonId)
    http3 = '?api_token='
    if production.sm_API == '':
        from predictions_project.settings import local
        api_token = local.sm_API
    else:
        api_token = production.sm_API
    requestString = http1 + http2 + http3 + api_token

    # get the data from the http address, convert them to json and then to dict
    response = requests.get(requestString)
    smResponse = response.json()
    smJson = json.dumps(smResponse, sort_keys=True, indent=4)
    smDict = json.loads(smJson)

    final_list = []
    # populate the list of dicts to be used to update the smCountry database table
    for i in range(0, len(smDict['data'])):
        countryObj = CountrySM.objects.get(pk=smDict['data'][i]['country_id'])

        # convert none values to empty strings so the db does not raise errors
        if smDict['data'][i]['short_code'] == None:
            short_code = ''
            print 'Warning: ' + smDict['data'][i]['name'] + ' missing short_code'
        else:
            short_code = smDict['data'][i]['short_code']

        if smDict['data'][i]['logo_path'] == None:
            logo_path = ''
            print 'Warning: ' + smDict['data'][i]['name'] + ' missing logo_path'
        else:
            logo_path = smDict['data'][i]['logo_path']

        # populate the dict
        try:
            final_list.append({
                'team_id': smDict['data'][i]['id'],
                'name': smDict['data'][i]['name'],
                'short_code': short_code,
                'country': countryObj,
                'founded': smDict['data'][i]['founded'],
                'logo_path': logo_path
            })
        except TypeError as er:
            print 'Serious Warning: ' + smDict['data'][i]['name'] + ' is missing one or more vital values and has been excluded.'

    return final_list


# this is used only for updating the LeagueSMforLive table. DO NOT use for updating the LeagueSM
def SMcall_allLeagues():
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

    return final_list
# def SMcall_livescore(request):
#     today = datetime.today()
#     threshold = datetime.now() + timedelta(days=2)
#     upcoming_predictions = Game.objects.select_related('season').filter(date__gte=today, date__lte=threshold, game_status='OK').exclude(homegoals__gte=0).order_by('date', 'fixture_sm__match_time')
#     leagues = [l.fixture_sm.season.league.league_id for l in upcoming_predictions]
#     final_data = []
#     from predictions_project.settings import production
#     MAX_RETRIES = 5
#     if production.sm_API == '':
#         from predictions_project.settings import local
#         api_token = local.sm_API
#     else:
#         api_token = production.sm_API

#     # timezone = "&tz=Europe/Athens"
#     url = "https://soccer.sportmonks.com/api/v2.0/livescores"
#     params = (
#         ('api_token', api_token),
#         ('include', 'localTeam,visitorTeam,tvstations'),
#         ('tz', 'Europe/Athens'),
#     )

#     if request.method == "GET":
#         attempt_num = 0  # keep track of how many times we've retried
#         while attempt_num < MAX_RETRIES:
#             r = requests.get(url, params=params, timeout=10)
#             # print r.url
#             if r.status_code == 200:
#                 data = r.json()
#                 dataJson = json.dumps(data, sort_keys=True, indent=4)
#                 dataDict = json.loads(dataJson)
#                 for d in dataDict['data']:
#                     if d['league_id'] in leagues:
#                         currentMatch_id = int(d['id'])
#                         minute = ''
#                         score = '-'
#                         gameObj = Game.objects.get(fixture_sm__fixture_id=currentMatch_id)
#                         tm = gameObj.fixture_sm.match_time
#                         tm_formatted = tm.strftime("%H:%M")
#                         if d['time']['minute'] != None:
#                             minute = str(d['time']['minute']) + "'"
#                             score = str(d['scores']['localteam_score']) + " - " + str(d['scores']['visitorteam_score'])

#                         final_data.append(
#                             {
#                                 'cntr': gameObj.season.league.country_code,
#                                 'lg': gameObj.season.league.short_name,
#                                 'gmwk': gameObj.gameweek,
#                                 'home': gameObj.hometeam.name,
#                                 'vs': '-',
#                                 'away': gameObj.awayteam.name,
#                                 'date': gameObj.date,
#                                 'time': tm_formatted,
#                                 'bp': gameObj.prediction_elohist,
#                                 'mp': gameObj.prediction_elol6,
#                                 'yp': gameObj.prediction_gsrs,
#                                 'pk': gameObj.pk,
#                                 'score': score,
#                                 'minute': minute,
#                                 'status': d['time']['status']
#                             }
#                         )
#                 # final_data_json = json.dumps(final_data)
#                 return final_data
#             else:
#                 attempt_num += 1
#                 errormsg = "Request failed"
#                 # You can probably use a logger to log the error here
#                 time.sleep(5)  # Wait for 5 seconds before re-trying
#         return errormsg
#     else:
#         errormsg = "Method not allowed"
#         return errormsg
