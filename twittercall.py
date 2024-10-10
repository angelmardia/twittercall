import os
import random
import tweepy
import json
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import timezone
from dotenv import load_dotenv
import google.generativeai as genai

# Specify the path to your .env file
load_dotenv("/content/.env")

# API Keys from environment variables
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
ACCESS_KEY = os.getenv('ACCESS_KEY')
ACCESS_SECRET = os.getenv('ACCESS_SECRET')
CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
API_KEY = os.getenv('GEMINI_API_KEY')

# Google Generative AI configuration
genai.configure(api_key=API_KEY)
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 45,
    "response_mime_type": "text/plain",
}

# Timezone for IST
IST = timezone('Asia/Kolkata')

# Function to run the scheduled task
def tweet_daily():
    # Add a timestamp to make each tweet unique
    current_time = datetime.now(IST).strftime("%H:%M:%S")

    # Authenticate to Twitter
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)

    # Twitter API v2.0 client
    newapi = tweepy.Client(
        bearer_token=BEARER_TOKEN,
        access_token=ACCESS_KEY,
        access_token_secret=ACCESS_SECRET,
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
    )

    # Load prompts from the uploaded JSON file
    with open('/content/prompts.json') as f:
        prompts = json.load(f)

    # Randomly pick a category and fetch the description
    category = random.choice(list(prompts['prompts'].keys()))
    selected_prompt = prompts['prompts'][category]["description"]

    # Generate text using Google Generative AI
    model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)
    chat_session = model.start_chat()
    response = chat_session.send_message(selected_prompt)

    # Print and post the generated text
    tweet_text = response.text
    print(tweet_text)

    # Create the tweet using the new API
    post_result = newapi.create_tweet(text=tweet_text)

# Call the function to tweet daily
tweet_daily()

# Set up the scheduler
# scheduler = BlockingScheduler()

# Schedule the job to run at 1 PM IST every day
# scheduler.add_job(tweet_daily, 'cron', hour=12, minute=25, timezone='Asia/Kolkata')

# Start the scheduler
# scheduler.start()