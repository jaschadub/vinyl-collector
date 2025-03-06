import requests
import argparse
import time
import os
import openai
from dotenv import load_dotenv
from thefuzz import fuzz

# Load environment variables from .env file
load_dotenv()

# Retrieve API credentials and settings from .env
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")
DISCOGS_USERNAME = os.getenv("DISCOGS_USERNAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Default model

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Discogs API Rate Limit Config
DISC_RATE_LIMIT = 60  # Discogs allows 60 requests per minute
REQUEST_DELAY = 1.1   # Slightly over 1 second to avoid hitting the limit

# Get Spotify Access Token
def get_spotify_access_token():
    url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }

    response = requests.post(url, headers=headers, data=data).json()
    return response.get("access_token")

# Get Spotify Playlist Tracks
def get_spotify_tracks(playlist_id, access_token):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching playlist: {response.json().get('error', {}).get('message', 'Unknown error')}")
        return []

    data = response.json()
    tracks = []

    for item in data.get("items", []):
        track = item["track"]
        if track:
            title = track["name"]
            artist = track["artists"][0]["name"]
            tracks.append((title, artist))

    return tracks

# Get existing wantlist to avoid duplicates
def get_existing_wantlist():
    url = f"https://api.discogs.com/users/{DISCOGS_USERNAME}/wants"
    headers = {"Authorization": f"Discogs token={DISCOGS_TOKEN}"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Error retrieving existing wantlist.")
        return set()

    data = response.json()
    existing_wants = {item["id"] for item in data.get("wants", [])}  # Collect existing release IDs
    return existing_wants

# Search for Vinyl Releases on Discogs
def search_discogs(title, artist):
    url = f"https://api.discogs.com/database/search"
    params = {
        "artist": artist,
        "format": "vinyl",
        "type": "release",
        "token": DISCOGS_TOKEN
    }
    
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Error searching Discogs for {title} - {artist}: {response.json().get('message', 'Unknown error')}")
        return None, None, None, None

    data = response.json()
    best_match = None
    highest_score = 0

    for result in data.get("results", []):
        discogs_title = result.get("title", "")
        discogs_artist = " ".join(result.get("artist", []))
        title_score = fuzz.ratio(title.lower(), discogs_title.lower())
        artist_score = fuzz.ratio(artist.lower(), discogs_artist.lower())
        average_score = (title_score + artist_score) / 2

        if average_score > highest_score:
            highest_score = average_score
            best_match = result

    # Set a threshold for what you consider a good match
    if highest_score > 80:  # Adjust the threshold as needed
        return best_match["id"], best_match["title"], best_match.get("year", "Unknown"), best_match.get("label", ["Unknown"])[0]
    else:
        return None, None, None, None

# Use OpenAI's ChatGPT to confirm match
def chatgpt_match(spotify_track, discogs_release, model):
    prompt = f"Do the following Spotify track and Discogs release refer to the same song?\n\nSpotify Track: {spotify_track}\nDiscogs Release: {discogs_release}\n\nAnswer 'yes' or 'no' and provide a brief explanation."
    response = openai.Completion.create(
        engine=model,
        prompt=prompt,
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0
    )
    answer = response.choices[0].text.strip().lower()
    return answer.startswith("yes")

# Prompt user for confirmation
def prompt_user_confirmation(spotify_track, discogs_release):
    print(f"\nSpotify Track: {spotify_track}")
    print(f"Discogs Match: {discogs_release}")
    user_input = input("Do you want to add this release to your wantlist? (yes/no): ").strip().lower()
    return user_input == "yes"

# Add Vinyl to Wantlist (Only if Not a Duplicate)
def add_to_wantlist(release_id, existing_wants):
    if release_id in existing_wants:
        print(f"Skipping {release_id}, already in wantlist.")
        return False

    url = f"https://api.discogs.com/users/{DISCOGS_USERNAME}/wants/{release_id}"
    headers = {"Authorization": f"Discogs token={DISCOGS_TOKEN}"}
    
    response = requests.put(url, headers=headers)

    if response.status_code == 429:  # Too Many Requests
        print("Hit Discogs rate limit
::contentReference[oaicite:0]{index=0}
 
