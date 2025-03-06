import requests
import argparse
import time
import os
import openai
import re
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

# Function to translate text using OpenAI
def translate_to_english(text):
    """Translate non-Latin text to English using OpenAI API."""
    if re.search(r'[\u3040-\u30FF\u4E00-\u9FFF]', text):  # Detect Japanese/Kanji characters
        prompt = f"Translate this album or artist name to English: {text}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"].strip()
    return text  # Return original if it's already in English

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
    url = "https://api.discogs.com/database/search"
    params = {
        "q": title,
        "artist": artist,
        "format": "vinyl",
        "type": "release",
        "token": DISCOGS_TOKEN
    }

    while True:
        response = requests.get(url, params=params)

        if response.status_code == 429:
            print("⚠️ Hit Discogs rate limit! Sleeping for 60 seconds...")
            time.sleep(60)
            continue  # Retry the request

        if response.status_code != 200:
            print(f"Error searching Discogs for {title} - {artist}: {response.json().get('message', 'Unknown error')}")
            return None, None, None, None

        remaining_requests = int(response.headers.get("X-Discogs-Ratelimit-Remaining", 1))
        if remaining_requests < 5:
            print("⚠️ Approaching Discogs rate limit. Sleeping for 30 seconds...")
            time.sleep(30)

        data = response.json()
        best_match = None
        highest_score = 0

        for result in data.get("results", []):
            discogs_title = result.get("title", "")
            discogs_artist = " ".join(result.get("artist", []))

            # Translate if necessary
            translated_discogs_title = translate_to_english(discogs_title)
            translated_discogs_artist = translate_to_english(discogs_artist)

            # Compare original and translated versions
            title_score = max(
                fuzz.ratio(title.lower(), discogs_title.lower()),
                fuzz.ratio(title.lower(), translated_discogs_title.lower())
            )
            artist_score = max(
                fuzz.ratio(artist.lower(), discogs_artist.lower()),
                fuzz.ratio(artist.lower(), translated_discogs_artist.lower())
            )
            average_score = (title_score + artist_score) / 2

            print(f"DEBUG: Found '{discogs_title}' (translated: '{translated_discogs_title}') by '{discogs_artist}' | Score: {average_score}")

            if average_score > highest_score:
                highest_score = average_score
                best_match = result

        if highest_score > 65 and best_match:
            return best_match["id"], best_match["title"], best_match.get("year", "Unknown"), best_match.get("label", ["Unknown"])[0]
        else:
            return None, None, None, None

# Prompt user for confirmation
def prompt_user_confirmation(spotify_track, discogs_release):
    print(f"\nSpotify Track: {spotify_track}")
    print(f"Discogs Match: {discogs_release}")
    user_input = input("Do you want to add this release to your wantlist? (yes/no): ").strip().lower()
    return user_input == "yes"

# Add Vinyl to Wantlist
def add_to_wantlist(release_id, existing_wants):
    if release_id in existing_wants:
        print(f"Skipping {release_id}, already in wantlist.")
        return False

    url = f"https://api.discogs.com/users/{DISCOGS_USERNAME}/wants/{release_id}"
    headers = {"Authorization": f"Discogs token={DISCOGS_TOKEN}"}

    response = requests.put(url, headers=headers)

    if response.status_code == 429:
        print("⚠️ Hit Discogs rate limit! Sleeping for 60 seconds...")
        time.sleep(60)
        return add_to_wantlist(release_id, existing_wants)

    return response.status_code == 201

# Main function to process CLI arguments
def main():
    parser = argparse.ArgumentParser(description="Add Spotify playlist tracks to Discogs wantlist.")
    parser.add_argument("playlist_id", type=str, help="Spotify playlist ID")
    args = parser.parse_args()

    spotify_access_token = get_spotify_access_token()
    if not spotify_access_token:
        print("Failed to obtain Spotify access token.")
        return

    tracks = get_spotify_tracks(args.playlist_id, spotify_access_token)
    if not tracks:
        print("No tracks found in the playlist or an error occurred.")
        return

    existing_wants = get_existing_wantlist()

    for title, artist in tracks:
        release_id, discogs_title, discogs_year, discogs_label = search_discogs(title, artist)
        time.sleep(REQUEST_DELAY)

        if release_id and prompt_user_confirmation(f"{title} by {artist}", f"{discogs_title} by {discogs_label} ({discogs_year})"):
            add_to_wantlist(release_id, existing_wants)

if __name__ == "__main__":
    main()
