# !pip install python-dotenv


import requests
import json
import os
import random
import tweepy
from datetime import datetime

BEARER_TOKEN= os.getenv('BEARER_TOKEN')
ACCESS_KEY= os.getenv('ACCESS_KEY')
ACCESS_SECRET= os.getenv('ACCESS_SECRET')
CONSUMER_KEY= os.getenv('CONSUMER_KEY')
CONSUMER_SECRET= os.getenv('CONSUMER_SECRET')

# Replace 'YOUR_API_KEY' with your actual API key
API_KEY = os.getenv('GEMINI_API_KEY')

# Add a timestamp to make each tweet unique
current_time = datetime.now().strftime("%H:%M:%S")

# Authenticate to Twitter
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)

# Twitter API v2.0 client
newapi = tweepy.Client(
    bearer_token= BEARER_TOKEN,
    access_token= ACCESS_KEY,
    access_token_secret= ACCESS_SECRET,
    consumer_key= CONSUMER_KEY,
    consumer_secret= CONSUMER_SECRET,
)

# Load prompts from the uploaded JSON file
with open('/content/prompts.json') as f:
    prompts = json.load(f)



url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}'

# Randomly pick a category and fetch the description
category = random.choice(list(prompts['prompts'].keys()))
selected_prompt = prompts['prompts'][category]["description"]

# Payload data to send
payload = {
    "contents": [
        {
            "parts": [
                {"text": selected_prompt}
            ]
        }
    ]
}

# Headers for the request
headers = {
    'Content-Type': 'application/json'
}

# Send the POST request
response = requests.post(url, headers=headers, data=json.dumps(payload))

# Check if the request was successful
if response.status_code == 200:
    data = response.json()

    # Extract and print the text from parts
    for candidate in data.get("candidates", []):
        parts = candidate.get("content", {}).get("parts", [])
        for part in parts:
            tweet_text = part.get("text", "")

            # Limit the tweet text to 200 characters
            tweet_text = tweet_text[:200]

            print(tweet_text)

            # Create the tweet using the new API
            post_result = newapi.create_tweet(text=tweet_text)
else:
    print(f"Request failed with status code {response.status_code}: {response.text}")
