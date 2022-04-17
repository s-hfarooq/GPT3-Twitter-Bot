import json
import openai
import tweepy
import time
from random_word import RandomWords

apiKeys = json.load(open("api_keys.json"))

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

    while(randWord is None):
        randWord = r.get_random_word()

    tweetData = client.search_recent_tweets(query=randWord, user_auth=True)

    while(tweetData is None):
        tweetData = client.search_recent_tweets(query=randWord, user_auth=True)
    
    tweetText = tweetData.data[0].text

    print(tweetText)

    # Run openai completion on tweet
    openai.api_key = apiKeys["openai"]
    out = openai.Completion.create(
        engine="text-davinci-002",
        prompt=tweetText,
        max_tokens=64,
        frequency_penalty=0.5
    )

    # Ensure tweet isn't over max len (start thread instead of regen?)
    while(len(out.choices[0].text) > 280 or len(out.choices[0].text) < 1):
        print("another")
        out = openai.Completion.create(
            engine="text-davinci-002",
            prompt=tweetText,
            max_tokens=64,
            frequency_penalty=0.5
        )

    # Send tweet
    response = client.create_tweet(
        text=out.choices[0].text
    )

    print(f"https://twitter.com/user/status/{response.data['id']}")
    time.sleep(60)

