import os
import random
import tweepy
import json
import requests
from flask import Flask, jsonify
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from dotenv import load_dotenv
import google.generativeai as genai
from pymongo import MongoClient

# Specify the path to your .env file
load_dotenv("/content/.env")

# API Keys from environment variables
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
ACCESS_KEY = os.getenv('ACCESS_KEY')
ACCESS_SECRET = os.getenv('ACCESS_SECRET')
CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
API_KEY = os.getenv('GEMINI_API_KEY')
PING_API_URL = os.getenv('PING_API_URL')  # Add the PING_API_URL to the .env file

# MongoDB connection
MONGO_URI = "mongodb+srv://angelmardia3:dbangelxtreme@cluster0.psirm.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client['twitterDB']  # Select the database
history_collection = db['historyDB']  # Select the collection

# Flask app initialization
app = Flask(__name__)

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

# Load history from MongoDB
def load_history():
    history = []
    try:
        # Retrieve all documents from history collection
        cursor = history_collection.find()
        for document in cursor:
            history.append(document['response_text'])  # Collect response_text field
    except Exception as e:
        print(f"Error loading history: {e}")
    return history

# Save response to MongoDB
def save_to_history(response_text):
    try:
        # Insert response into the history collection
        history_collection.insert_one({"response_text": response_text})
    except Exception as e:
        print(f"Error saving history: {e}")

# Function to run the scheduled task
def tweet_daily():
    try:
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
        with open('prompts.json') as f:
            prompts = json.load(f)

        # Randomly pick a category and fetch the description
        category = random.choice(list(prompts['prompts'].keys()))
        selected_prompt = prompts['prompts'][category]["description"]

        # Load the conversation history
        history = load_history()
        formatted_history = []
        for message in history:
            formatted_history.append({"role": "model", "content": message})

        # Generate text using Google Generative AI with history (if not empty)
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

        # Start a chat session with properly formatted history
        chat_session = model.start_chat(history=formatted_history if formatted_history else None)
        response = chat_session.send_message({"role": "user", "content": selected_prompt})

        # Print and post the generated text
        tweet_text = response.text
        print(tweet_text)

        # Save the response to MongoDB history
        save_to_history(tweet_text)

        # Create the tweet using the new API
        post_result = newapi.create_tweet(text=tweet_text)

        return jsonify({"status": "success", "tweet": tweet_text})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Function to ping the API to keep service alive
def ping_service():
    try:
        response = requests.get(PING_API_URL)  # Make a GET request to keep the service awake
        if response.status_code == 200:
            print("Service ping successful.")
        else:
            print(f"Service ping failed with status code {response.status_code}")
    except Exception as e:
        print(f"Error pinging service: {e}")

# Flask route to trigger tweet manually
@app.route('/trigger_tweet', methods=['POST'])
def trigger_tweet():
    # Call the tweet_daily function and return a response
    return tweet_daily()

# Flask route to ping the service manually
@app.route('/', methods=['GET'])
def ping_route():
    return "Hello World!!"

# Set up the scheduler
scheduler = BackgroundScheduler()

# Schedule the tweet to run at 1 PM IST every day
scheduler.add_job(tweet_daily, 'cron', hour=13, minute=30, timezone='Asia/Kolkata')

# Schedule the ping service to run every 180 seconds
scheduler.add_job(ping_service, 'interval', seconds=180)

# Start the scheduler
scheduler.start()

# Run the Flask app
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
