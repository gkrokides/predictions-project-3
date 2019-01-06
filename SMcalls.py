from __future__ import unicode_literals
from predictions.models import CountrySM, LeagueSM, SeasonSM, TeamSM, FixtureSM

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

    requestString = http1+leagueID+http2+api_token+http3

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

    requestString = http1+idConcat+http2+api_token

    response = requests.get(requestString)

    smResponse = response.json()
    smJson = json.dumps(smResponse, sort_keys=True, indent=4)
    smDict = json.loads(smJson)
    db_data = {}

    # populate the dict to be used to update the smCountry database table
    db_data['country_id'] = smDict['data']['id']
    db_data['name'] = smDict['data']['name']
    db_data['continent'] = smDict['data']['extra']['continent']
    db_data['fifa_code'] = smDict['data']['extra']['fifa']
    db_data['iso_code'] = smDict['data']['extra']['iso']
    db_data['flag'] = smDict['data']['extra']['flag']

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

    requestString = http1+idConcat+http2+api_token

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

    requestString = http1+idConcat+http2+api_token+http3

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

    requestString = http1+idConcat+http2+api_token+http3

    response = requests.get(requestString)

    smResponse = response.json()
    smJson = json.dumps(smResponse, sort_keys=True, indent=4)
    smDict = json.loads(smJson)
    db_data = {}

    # populate the dict to be used to update the smFixture database table
    db_data['fixture_id'] = smDict['data']['id']
    db_data['season'] = smDict['data']['season_id']
    db_data['hometeam'] = smDict['data']['localteam_id']
    db_data['awayteam'] = smDict['data']['visitorteam_id']
    db_data['weather_code'] = smDict['data']['weather_report']['code']
    db_data['weather_type'] = smDict['data']['weather_report']['type']
    db_data['weather_icon'] = smDict['data']['weather_report']['icon']
    db_data['attendance'] = smDict['data']['attendance']
    db_data['pitch_status'] = smDict['data']['pitch']
    db_data['home_formation'] = smDict['data']['formations']['localteam_formation']
    db_data['away_formation'] = smDict['data']['formations']['visitorteam_formation']
    db_data['home_goals'] = smDict['data']['scores']['localteam_score']
    db_data['away_goals'] = smDict['data']['scores']['visitorteam_score']
    db_data['ht_score'] = smDict['data']['scores']['ht_score']
    db_data['ft_score'] = smDict['data']['scores']['ft_score']
    db_data['match_status'] = smDict['data']['time']['status']
    db_data['match_date'] = smDict['data']['time']['starting_at']['date']
    db_data['match_time'] = smDict['data']['time']['starting_at']['time']
    db_data['gameweek'] = smDict['data']['round']['data']['name']
    db_data['stage'] = smDict['data']['stage']['data']['name']
    db_data['venue_name'] = smDict['data']['venue']['data']['name']
    db_data['venue_surface'] = smDict['data']['venue']['data']['surface']
    db_data['venue_city'] = smDict['data']['venue']['data']['city']
    db_data['venue_capacity'] = smDict['data']['venue']['data']['capacity']
    db_data['venue_image'] = smDict['data']['venue']['data']['image_path']
    db_data['odds_1'] = smDict['data']['flatOdds']['data'][0]['odds'][0]['value']
    db_data['odds_x'] = smDict['data']['flatOdds']['data'][0]['odds'][1]['value']
    db_data['odds_2'] = smDict['data']['flatOdds']['data'][0]['odds'][2]['value']
    db_data['home_coach'] = smDict['data']['localCoach']['data']['fullname']
    db_data['home_coach_nationality'] = smDict['data']['localCoach']['data']['nationality']
    db_data['home_coach_image'] = smDict['data']['localCoach']['data']['image_path']
    db_data['away_coach'] = smDict['data']['visitorCoach']['data']['fullname']
    db_data['away_coach_nationality'] = smDict['data']['visitorCoach']['data']['nationality']
    db_data['away_coach_image'] = smDict['data']['visitorCoach']['data']['image_path']

    return db_data

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

    requestString = http1+api_token

    response = requests.get(requestString)

    smResponse = response.json()
    smJson = json.dumps(smResponse, sort_keys=True, indent=4)
    smDict = json.loads(smJson)
    final_list = []

    # populate the list of dicts to be used to update the smCountry database table
    for i in range(0, len(smDict['data'])):
        try:
            final_list.append({
                'country_id': smDict['data'][i]['id'],
                'name': smDict['data'][i]['name'],
                'continent': smDict['data'][i]['extra']['continent'],
                'fifa_code': smDict['data'][i]['extra']['fifa'],
                'iso_code': smDict['data'][i]['extra']['iso'],
                'flag': smDict['data'][i]['extra']['flag']
                })
        except TypeError as er:
            print 'Warning:' + smDict['data'][i]['name'] + ' is missing one or more values and has been excluded.'  

    return final_list

# API call to get the teams for the selected season from sportmonks and convert it to dict
def SMcall_teamsBySeason(seasonId):
    import requests
    import json
    from predictions_project.settings import production

    http1 = 'https://soccer.sportmonks.com/api/v2.0/teams/season/'
    http2 = str(seasonId)
    http3 = '?api_token='
    if production.sm_API == '':
        from predictions_project.settings import local
        api_token = local.sm_API
    else:
        api_token = production.sm_API

    requestString = http1 + http2 + http3 + api_token

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
        else:
            short_code = smDict['data'][i]['short_code']

        if smDict['data'][i]['logo_path'] == None:
            logo_path = ''
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
            print 'Warning:' + smDict['data'][i]['name'] + ' is missing one or more values and has been excluded.'  

    return final_list

