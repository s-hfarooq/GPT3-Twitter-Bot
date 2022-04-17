import os
import openai

# Pull random tweet
tweet = "This was posted on Twitter: \"i\’m not donating to them ppl bro stop asking me. somebody needa make a donation to ME\" Produce a response:"

# Run openai completion on tweet
openai.api_key =  open("api_key.txt", "r").read()
out = openai.Completion.create(
  engine="text-davinci-002",
  prompt=tweet,
  max_tokens=64,
  frequency_penalty=0.5
)

# Ensure tweet isn't over max len (start thread instead of regen?)
while(len(out.choices[0].text) > 280):
    print("another")
    out = openai.Completion.create(
        engine="text-davinci-002",
        prompt=tweet,
        max_tokens=64,
        frequency_penalty=0.5
    )

print(out.choices[0].text)

# Send tweet