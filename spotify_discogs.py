import requests
import argparse
import time

# CONFIGURE YOUR KEYS
SPOTIFY_CLIENT_ID = "your_spotify_client_id"
SPOTIFY_CLIENT_SECRET = "your_spotify_client_secret"
DISCOGS_TOKEN = "your_discogs_token"
DISCOGS_USERNAME = "your_discogs_username"

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


# Search for Vinyl Releases on Discogs
def search_discogs(title, artist):
    url = f"https://api.discogs.com/database/search"
    params = {
        "q": title,
        "artist": artist,
        "format": "vinyl",
        "type": "release",
        "token": DISCOGS_TOKEN
    }
    
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Error searching Discogs for {title} - {artist}: {response.json().get('message', 'Unknown error')}")
        return None

    # Rate Limiting Check
    remaining_requests = int(response.headers.get("X-Discogs-Ratelimit-Remaining", DISC_RATE_LIMIT))
    if remaining_requests < 5:  # If too close to the limit, slow down
        print("Approaching rate limit. Pausing to prevent 429 errors...")
        time.sleep(30)

    data = response.json()
    if data.get("results"):
        return data["results"][0]["id"]  # Return the first matching release ID

    return None


# Add Vinyl to Wantlist
def add_to_wantlist(release_id):
    url = f"https://api.discogs.com/users/{DISCOGS_USERNAME}/wants/{release_id}"
    headers = {"Authorization": f"Discogs token={DISCOGS_TOKEN}"}
    
    response = requests.put(url, headers=headers)

    if response.status_code == 429:  # Too Many Requests
        print("Hit Discogs rate limit! Sleeping for 60 seconds...")
        time.sleep(60)
        return add_to_wantlist(release_id)  # Retry after sleeping

    return response.status_code == 201


# Main function to process CLI arguments
def main():
    parser = argparse.ArgumentParser(description="Add Spotify playlist tracks to Discogs wantlist.")
    parser.add_argument("playlist_id", type=str, help="Spotify playlist ID")
    args = parser.parse_args()

    # Get a new access token for Spotify API
    spotify_access_token = get_spotify_access_token()
    if not spotify_access_token:
        print("Failed to obtain Spotify access token.")
        return

    tracks = get_spotify_tracks(args.playlist_id, spotify_access_token)
    
    if not tracks:
        print("No tracks found in the playlist or an error occurred.")
        return

    for title, artist in tracks:
        release_id = search_discogs(title, artist)
        time.sleep(REQUEST_DELAY)  # Add delay between searches to avoid rate limits
        
        if release_id:
            success = add_to_wantlist(release_id)
            print(f"Added {title} - {artist} to wantlist: {success}")
        else:
            print(f"No vinyl found for {title} - {artist}")

if __name__ == "__main__":
    main()
