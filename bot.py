import json
import openai
import tweepy
import time
import random
from datetime import datetime, timedelta

woeid = 2490383 # 2490383 = Seattle
quoteTweetPercent = 0.2

apiKeys = json.load(open("api_keys.json"))

openai.api_key = apiKeys["openai"]

client = tweepy.Client(
    consumer_key=apiKeys["consumer_key"], consumer_secret=apiKeys["consumer_secret"],
    access_token=apiKeys["access_token"], access_token_secret=apiKeys["access_token_secret"]
)

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
        
        if isQuoteTweet:
            tweetText = "This was posted on Twitter: \"" + tweetData.data[0].text + "\". Produce a response:"
        else:
            tweetText = "This was posted on Twitter: \"" + tweetData.data[0].text + "\". Comment a response:"
    except TypeError:
        print("Type error on tweetdata... restarting")
        continue

    origTweetUrl = f"https://twitter.com/user/status/{tweetData.data[0].id}"
    print("Search term:", searchWord)
    print("Tweet responding to:", tweetText)
    print("Link:", origTweetUrl)

    # Run openai completion on tweet
    out = openai.Completion.create(
        engine="text-davinci-002",
        prompt=tweetText,
        max_tokens=60,
        frequency_penalty=0.4
    )

    # Ensure tweet isn't over max len (start thread instead of regen?)
    while(len(out.choices[0].text) > 280 or len(out.choices[0].text) < 1):
        out = openai.Completion.create(
            engine="text-davinci-002",
            prompt=tweetText,
            max_tokens=60,
            frequency_penalty=0.4
        )

    # Send tweet
    try:
        client.like(tweetData.data[0].id)
        if isQuoteTweet:
            api.update_status(
                status=out.choices[0].text,
                attachment_url=origTweetUrl
            )
        else:
            response = client.create_tweet(
                text=out.choices[0].text,
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
