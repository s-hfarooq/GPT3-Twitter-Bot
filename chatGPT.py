import json
import tweepy
import time
import random
from datetime import datetime, timedelta
import langid
from revChatGPT.revChatGPT import Chatbot

woeid = 2490383 # 2490383 = Seattle
quoteTweetPercent = 0.2

apiKeys = json.load(open("api_keys.json"))

client = tweepy.Client(
    consumer_key=apiKeys["consumer_key"], consumer_secret=apiKeys["consumer_secret"],
    access_token=apiKeys["access_token"], access_token_secret=apiKeys["access_token_secret"]
)

chatbotConfig = {
    "email": apiKeys["email"],
    "password": apiKeys["password"]
}

chatbot = Chatbot(chatbotConfig, conversation_id=None)

auth = tweepy.OAuthHandler(apiKeys["consumer_key"], apiKeys["consumer_secret"])
auth.set_access_token(apiKeys["access_token"], apiKeys["access_token_secret"])
auth.secure = True
api = tweepy.API(auth)

while(True):
    # Get tweet based on most popular trend in specific location
    rj_trends = api.get_place_trends(id=woeid)
    trends = []
    for trend in rj_trends[0]['trends']: 
        if trend['tweet_volume'] is not None and trend['tweet_volume'] > 10000: 
            trends.append((trend['name'], trend['tweet_volume']))
    trends.sort(key=lambda x:-x[1])
    searchWord = trends[0][0]

    startTime = datetime.today() - timedelta(days=1)
    endTime = datetime.today() - timedelta(seconds=90)

    # Determine if we should quote tweet or reply
    isQuoteTweet = True
    if random.uniform(0, 1) < quoteTweetPercent:
        isQuoteTweet = False
    
    # Sometimes search doesn't always work properly so needs to be in a try/except
    try:
        tweetData = client.search_recent_tweets(query=searchWord, user_auth=True, start_time=startTime, end_time=endTime)
    except:
        print("Error on fetching tweets... restarting")
        continue

    # Sometimes tweetData is empty so need to search again
    try:
        while(tweetData is None):
            tweetData = client.search_recent_tweets(query=searchWord, user_auth=True, start_time=startTime, end_time=endTime)
        
        tweetText = "The following Tweet was posted today: \"" + tweetData.data[0].text + "\". Write a response to the Tweet. Do not give any other information. Ensure the response is under 280 characters."
    except TypeError:
        print("Type error on tweetdata... restarting")
        continue

    if langid.classify(tweetText)[0] != "en":
        print("tweet not english, trying again")
        continue

    origTweetUrl = f"https://twitter.com/user/status/{tweetData.data[0].id}"
    print("Search term:", searchWord)
    print("Tweet responding to:", tweetText)
    print("Link:", origTweetUrl)

    # Run openai completion on tweet
    print("starting")
    print(tweetData.data[0].text)
    out = chatbot.get_chat_response(tweetText)['message']
    print("done")
    print("out:", out)

    # Ensure tweet isn't over max len (start thread instead of regen?)
    while(len(out) > 280 or len(out) < 1):
        out = chatbot.get_chat_response(tweetData.data[0].text)['message']

    # Send tweet
    try:
        client.like(tweetData.data[0].id)
        if isQuoteTweet:
            api.update_status(
                status=out,
                attachment_url=origTweetUrl
            )
        else:
            response = client.create_tweet(
                text=out,
                in_reply_to_tweet_id=tweetData.data[0].id
            )
        
            print(f"gpt3 response: https://twitter.com/user/status/{response.data['id']}")
    except:
        print("error on sending tweet... restarting")
        continue

    # Sleep for random amount of time (5-25 minutes)
    sleepTime = random.randint(60 * 5, 60 * 25)
    nextTime = datetime.today() + timedelta(seconds=sleepTime)
    nextTime = nextTime.strftime("%Y-%m-%d %H:%M:%S")
    nextTime = datetime.strptime(nextTime, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %I:%M:%S %p")
    print(f"Sleeping for {sleepTime} seconds (Next tweet at {nextTime})...\n\n\n")
    time.sleep(sleepTime)
