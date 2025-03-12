import os
import requests
import time
from dotenv import load_dotenv
from datetime import datetime

# ==== LOAD ENVIRONMENT VARIABLES ====
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REFRESH_TOKEN = os.getenv('SPOTIFY_REFRESH_TOKEN')

DISCOGS_USER_TOKEN = os.getenv('DISCOGS_TOKEN')
DISCOGS_USERNAME = os.getenv('DISCOGS_USERNAME')
DISCOGS_USER_AGENT = 'NowPlayingDiscogsBot/1.0'

LOG_FILE = 'now_playing_discogs.log'

# ==== LOGGING FUNCTION ====
def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[LOG] {message}")

# ==== SPOTIFY AUTH ====
def get_spotify_access_token():
    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        'Authorization': f'Basic {requests.auth._basic_auth_str(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)}'
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': SPOTIFY_REFRESH_TOKEN
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code != 200:
        error_message = f"Failed to refresh Spotify token: {response.text}"
        log_event(error_message)
        return None
    
    return response.json().get('access_token')

def get_now_playing(access_token):
    url = "https://api.spotify.com/v1/me/player/currently-playing"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 204:
        log_event("Nothing is currently playing.")
        return None
    if response.status_code != 200:
        error_message = f"Error fetching now playing: {response.status_code} {response.text}"
        log_event(error_message)
        return None
    
    data = response.json()
    artist = data['item']['artists'][0]['name']
    track = data['item']['name']
    album = data['item']['album']['name']
    
    log_event(f"Now Playing: {artist} - {track} ({album})")
    
    return {
        'artist': artist,
        'track': track,
        'album': album
    }

# ==== DISCOGS SEARCH ====
def search_discogs(artist, release_title):
    search_url = "https://api.discogs.com/database/search"
    params = {
        'artist': artist,
        'release_title': release_title,
        'format': 'vinyl',
        'token': DISCOGS_USER_TOKEN
    }
    headers = {
        'User-Agent': DISCOGS_USER_AGENT
    }
    
    response = requests.get(search_url, headers=headers, params=params)
    
    if response.status_code != 200:
        error_message = f"Discogs search failed: {response.status_code} {response.text}"
        log_event(error_message)
        return None, None
    
    results = response.json().get('results', [])
    
    if not results:
        log_event("No vinyl releases found on Discogs.")
        return None, None
    
    # Return top 3 results for choice
    log_event(f"Found {len(results)} results on Discogs.")
    
    print("\nTop Discogs Results:")
    for idx, result in enumerate(results[:3], 1):
        print(f"{idx}. {result['title']} | {result.get('year', 'Unknown year')} | {result['uri']}")
    
    choice = input("Choose release to add to wantlist (1-3) or skip (Enter): ").strip()
    
    if choice and choice.isdigit():
        index = int(choice) - 1
        if 0 <= index < len(results[:3]):
            chosen_result = results[index]
            title = chosen_result['title']
            uri = chosen_result['uri']
            log_event(f"Selected release: {title} | https://www.discogs.com{uri}")
            return chosen_result['id'], uri
    
    log_event("No release selected.")
    return None, None

# ==== ADD TO WANTLIST ====
def add_to_wantlist(release_id):
    url = f"https://api.discogs.com/users/{DISCOGS_USERNAME}/wants/{release_id}"
    headers = {
        'Authorization': f'Discogs token={DISCOGS_USER_TOKEN}',
        'User-Agent': DISCOGS_USER_AGENT
    }
    
    response = requests.put(url, headers=headers)
    
    if response.status_code == 201:
        log_event("✅ Successfully added to wantlist!")
    elif response.status_code == 409:
        log_event("⚠️ Already in your wantlist.")
    else:
        error_message = f"❌ Failed to add to wantlist: {response.status_code} {response.text}"
        log_event(error_message)

# ==== MAIN LOOP ====
def main():
    access_token = get_spotify_access_token()
    if not access_token:
        log_event("Failed to get Spotify access token. Exiting...")
        return
    
    now_playing = get_now_playing(access_token)
    
    if now_playing:
        release_id, release_uri = search_discogs(now_playing['artist'], now_playing['album'])
        
        if release_id:
            print(f"🔗 Discogs Link: https://www.discogs.com{release_uri}")
            
            user_input = input("Add to wantlist? (y/n): ").strip().lower()
            if user_input == 'y':
                add_to_wantlist(release_id)
            else:
                log_even
