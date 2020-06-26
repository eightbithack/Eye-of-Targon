import requests
import time
import json

# Development key changes every 24 hours, access it by logging in to the Riot Developer Portal with your League of Legends account
# Paste your API key here:
api_key = "RGAPI-157bd38b-7fd6-4397-afec-f307f922eb51"

# request headers
headers = {
    "Origin": "https://developer.riotgames.com",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Riot-Token": api_key,
    "Accept-Language": "en-us",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Safari/605.1.15"
}

# get latest version
version = requests.get('https://ddragon.leagueoflegends.com/api/versions.json').json()[0]

# convert key to champion name
datadragon = requests.get('http://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json'.format(version)).json()
champions = {}
for champion in datadragon["data"]:
    key = int(datadragon["data"][champion]["key"])
    champions[key] = champion

def championId_to_name(id: int):
    return champions[id]

# Given a list of wins and losses, calculate the winrate as a percentage
def winrate(winloss: list):
    return winloss[0] / (winloss[0] + winloss[1]) * 100

# Each player has an encrypted account ID that is used to get match history and other data
def getSummonerId(summonerName: str):
    summonerNameUrl = 'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/' + summonerName
    response = requests.get(summonerNameUrl, headers = headers).json()
    #print (response)
    return response['accountId']

# List of past matches from the player in a certain queue
# Queue codes:
# 400 - 5v5 Draft Pick
# 420 - 5v5 Ranked Solo
# 430 - 5v5 Blind Pick
# 440 - 5v5 Ranked Flex
# 450 - 5v5 ARAM
def getMatchList(summonerId: str, queue: int, index: int):
    params1 = '?queue=400&queue=420&season=13&endIndex={}'.format(index*50)
    minIndex = index - 1
    params2 = '&beginIndex={}'.format(minIndex*100)
    params = params1 + params2
    summonerMatchlistUrl = 'https://na1.api.riotgames.com/lol/match/v4/matchlists/by-account/' + summonerId + params
    return requests.get(summonerMatchlistUrl, headers = headers).json()

# Given matchlist, print the overall winrate and the list of champions played, their winrates, and number of games played
# Also returns the champion names and their respective winrates as two lists
def displayWinrates(summonerId: str, queue: int, index: int):
    win_loss = [0,0]
    champion_winrates = {}
    matchNum = 4
    while index > 0:
        matchList = getMatchList(summonerId, queue, index)
        # print(matchList)
        index = index - 1
        start = time.perf_counter()

        # Parse through matchlist
        # Per-request delays and longer operation pauses to accommidate for the 1 per second 200 per minute Riot API constraints
        for match in matchList['matches']:
            time.sleep(1)
            if matchNum % 30 == 0:
                stop = time.perf_counter()
                i = 60
                print (f"after {stop - start:0.4f}, refreshing api throttle timer for {i}...")   
                while i != 0: 
                    # print (i)
                    time.sleep (1)
                    i = i - 1
                print ("refresh complete, resuming requests...")
                start = time.perf_counter()
            champion = championId_to_name(match['champion'])
            gameId = match['gameId']
            role = match['role']
            lane = match['lane']
            # if (role == "DUO_SUPPORT" or (role == "DUO" and lane == "NONE")):
            matchNum = matchNum + 1
            # Access match data
            matchUrl = 'https://na1.api.riotgames.com/lol/match/v4/matches/{}'.format(gameId)
            matchInfo = requests.get(matchUrl, headers = headers).json()
            # print ("request - match")
            #print (matchInfo)
            # Find participant ID
            participantId = 0
            for player in matchInfo['participantIdentities']:
                if player['player']['summonerName'] == summonerId:
                    participantId = player['participantId']
            
            # Use participant ID to determine which team player is on
            if participantId <= 5:
                participantId = 0
            else:
                participantId = 1
            
            # Increments win/loss counters for overall and per champion
            if matchInfo['teams'][participantId]['win'] == 'Win':
                win_loss[0] += 1
                #print(champion, role, lane, gameId, "WIN", matchNum, '\n')
                if champion in champion_winrates:
                    champion_winrates[champion][0] += 1
                else:
                    champion_winrates[champion] = [1,0,0]
            else:
                win_loss[1] += 1
                print(champion, role, lane, gameId, "LOSE", matchNum, '\n')
                if champion in champion_winrates:
                    champion_winrates[champion][1] += 1
                else:
                    champion_winrates[champion] = [0,1,0]
            champion_winrates[champion][2] += 1


    # Sort champions in descending order of games 
    champion_winrates = dict(sorted(champion_winrates.items(), reverse=True, key=lambda x: x[1][2]))
    champion_list = []
    champion_winrates_list = []

    # Overall wins and losses
    print(win_loss[0], 'wins', win_loss[1], 'losses')

    # Overall winrate to two decimal places
    print('%.2f'%(winrate(win_loss)) + "%")
    for champion in champion_winrates:
        # Prints champion winrates and checks for plural games
        percentage = '%.2f'%(winrate(champion_winrates[champion]))
        games = champion_winrates[champion][2]

        champion_list.append(champion)
        champion_winrates_list.append(float(percentage))

        if games > 3:
            print(champion, percentage + '%', games, 'games')

    with open('data.txt', 'w') as outfile:
        json.dump(champion_winrates, outfile)
