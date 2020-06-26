import api_request as api

# Switch statement for queue type
def switch(queue):
    switcher = {
        'norms': "400",
        'ranked': "420",
        'both' : "400,420"
    }
    return switcher.get(queue, "error")

print("Enter your summoner id: ")
summonerId = input()

print("How many games are you requesting (in multiples of 50)?")
game_num = int(input())

queueCode = "error"
print("norms, ranked, or both?")
while queueCode == "error":
    queueCode = switch(input())
    if queueCode == "error":
        print("Invalid input. Please type 'norms', 'ranked', or 'both'.")
    else:
        print("Input accepted.")

print("Starting - note that the process can take a considerable amount of time depending on the request")

# second parameter is an int indicating the number of games to request in multiples of 100
api.displayWinrates(api.getSummonerId(summonerId),queueCode, game_num)