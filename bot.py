import json
import openai
import tweepy
import time
import random
from random_word import RandomWords
from datetime import datetime, timedelta

apiKeys = json.load(open("api_keys.json"))

openai.api_key = apiKeys["openai"]

client = tweepy.Client(
    consumer_key=apiKeys["consumer_key"], consumer_secret=apiKeys["consumer_secret"],
    access_token=apiKeys["access_token"], access_token_secret=apiKeys["access_token_secret"]
)

# auth = tweepy.OAuthHandler(apiKeys["consumer_key"], apiKeys["consumer_secret"])
# auth.set_access_token(apiKeys["access_token"], apiKeys["access_token_secret"])
# auth.secure = True
# api = tweepy.API(auth)

r = RandomWords()

while(True):
    # Get random tweet
    randWord = r.get_random_word()
    startTime = datetime.today() - timedelta(days=1)

    try:
        while(randWord is None):
            randWord = r.get_random_word()

        tweetData = client.search_recent_tweets(query=randWord, user_auth=True, start_time=startTime)
    except:
        print("Error on fetching tweets... retrying")
        continue

    try:
        while(tweetData is None):
            tweetData = client.search_recent_tweets(query=randWord, user_auth=True, start_time=startTime)
        
        tweetText = "This was posted on Twitter: \"" + tweetData.data[0].text + "\". Produce a response:"
    except TypeError:
        print("Type error on tweetdata... retrying")
        continue

    print("Search term:", randWord)
    print("Tweet responding to:", tweetText)
    print(f"Link: https://twitter.com/user/status/{tweetData.data[0].id}")

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
            max_tokens=64,
            frequency_penalty=0.5
        )

    # Send tweet
    response = client.create_tweet(
        text=out.choices[0].text,
        in_reply_to_tweet_id=tweetData.data[0].id
    )

    print(f"gpt3 response: https://twitter.com/user/status/{response.data['id']}")

    sleepTime = random.randint(60 * 5, 60 * 25)
    print("Sleeping for", sleepTime, "seconds...")
    time.sleep(sleepTime)
