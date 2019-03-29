import requests
import json
from predictions_project.settings import production

# This function returns a dict of the selected odds for the selected fixture id.

market_id = 1 #enter the market for which you want the odds
fixtureId = 10350335 #enter the fixture id
over = 2.5 # This is taken into consideration ONLY if the market_id is set to 12

# bookies for which we are interested. The function will check if there are available odds
# for the first bookie. If it doesn't find any, it will check for the second bookie. if it
# doesn't find any, it will check to find the first available odds from any bookie.
bet365 = 2 #bookie id
interwetten = 129 #bookie id


http1 = 'https://soccer.sportmonks.com/api/v2.0/fixtures/'
idConcat = str(fixtureId)
http2 = '?api_token='
if production.sm_API == '':
    from predictions_project.settings import local
    api_token = local.sm_API
else:
    api_token = production.sm_API
http3 = '&include=round,stage,odds,venue,localCoach,visitorCoach'    

requestString = http1+idConcat+http2+api_token+http3

response = requests.get(requestString)
smData= response.json()
dataJson = json.dumps(smData, sort_keys=True, indent=4)
fixtureById = json.loads(dataJson)

allOdds = fixtureById['data']['odds']['data']
resultDict = [x for x in allOdds if x['id'] == market_id]
bookmakerIDs = [xs['id'] for xs in resultDict[0]['bookmaker']['data']]
try:
	if bet365 in bookmakerIDs:
		selectedBookmakerData = [x for x in resultDict[0]['bookmaker']['data'] if x['id'] == bet365]
	elif interwetten in bookmakerIDs:
		selectedBookmakerData = [x for x in resultDict[0]['bookmaker']['data'] if x['id'] == interwetten]
	else:		
		selectedBookmakerData = [x for x in resultDict[0]['bookmaker']['data']]
	
	if market_id == 12:
		finalData = {k['label']:k['value'] for k in selectedBookmakerData[0]['odds']['data'] if k['total'] == str(over)}
	else:
		finalData = {k['label']:k['value'] for k in selectedBookmakerData[0]['odds']['data']}	
	
	print finalData
except IndexError as inderr:
	finalData = {}
	print 'The selected market is not available for this match'	


