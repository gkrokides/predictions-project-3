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

    # response = requests.get("https://soccer.sportmonks.com/api/v2.0/leagues/181?api_token=UtfTQXmWeltdNWnWsL53IbP3t7YDyezdR0fMuVbAl9gk9ErXbJOyxQJAEVGB&include=country,season")
    response = requests.get(requestString)

    smleague = response.json()
    leaguesJson = json.dumps(smleague, sort_keys=True, indent=4)
    leaguesDict = json.loads(leaguesJson)
    smleague_data = {}

    # populate the dict to be used to update the smLeague database table
    smleague_data['league_id'] = leaguesDict['data']['id']
    smleague_data['legacy_id'] = leaguesDict['data']['legacy_id']
    smleague_data['name'] = leaguesDict['data']['name']
    smleague_data['country_id'] = leaguesDict['data']['country_id']
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

    # populate the dict to be used to update the smCountry database table
    db_data['season_id'] = smDict['data']['id']
    db_data['name'] = smDict['data']['name']
    db_data['league'] = smDict['data']['league_id']

    return db_data


