import os
import sys
import time
import json
import random
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Load environment variables from .env file
load_dotenv()

class RateLimiter:
    """Simple rate limiter to avoid hitting API rate limits"""
    def __init__(self, calls_per_minute):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.last_call_time = 0
    
    def wait(self):
        """Wait if necessary to respect the rate limit"""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            # Add some jitter to avoid patterns
            sleep_time += random.uniform(0, self.min_interval * 0.1)
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()

def authenticate_spotify():
    """
    Authenticate with Spotify API using OAuth.
    You'll need to create an app at https://developer.spotify.com/dashboard
    """
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    
    if not all([client_id, client_secret, redirect_uri]):
        raise ValueError(
            "Missing Spotify API credentials. Please check your .env file includes "
            "SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, and SPOTIFY_REDIRECT_URI"
        )
    
    scope = "playlist-read-private playlist-read-collaborative"
    
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope
    ))
    
    return spotify

def authenticate_youtube():
    """
    Authenticate with YouTube API using OAuth.
    You'll need to create credentials.json from Google Cloud Console.
    """
    # The file token.json stores the user's access and refresh tokens
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_info(json.load(open('token.json')))
    
    # If there are no valid credentials available, prompt the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Check if credentials.json exists
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "credentials.json not found. Please download OAuth 2.0 Client ID from "
                    "Google Cloud Console -> APIs & Services -> Credentials"
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                ['https://www.googleapis.com/auth/youtube']
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    # Build the YouTube API client
    youtube = build('youtube', 'v3', credentials=creds)
    
    return youtube

def get_spotify_playlist(spotify, playlist_id, spotify_limiter=None):
    """
    Get all tracks from a Spotify playlist
    """
    # Initialize rate limiter if not provided
    if spotify_limiter is None:
        spotify_limiter = RateLimiter(100)  # 100 requests per minute
    
    try:
        spotify_limiter.wait()
        results = spotify.playlist(playlist_id)
        playlist_name = results['name']
        playlist_description = results.get('description', '')
        
        print(f"Playlist: {playlist_name} by {results['owner']['display_name']}")
        
        tracks = []
        items = results['tracks']['items']
        
        # Handle pagination for playlists with >100 tracks
        while results['tracks']['next']:
            spotify_limiter.wait()
            results['tracks'] = spotify.next(results['tracks'])
            items.extend(results['tracks']['items'])
        
        for item in items:
            track = item['track']
            if track:  # Some items may be None if track was removed
                artist_names = ", ".join([artist['name'] for artist in track['artists']])
                track_name = track['name']
                album_name = track['album']['name']
                
                tracks.append({
                    'artist': artist_names,
                    'title': track_name,
                    'album': album_name,
                    'search_query': f"{artist_names} - {track_name}"
                })
        
        return {
            'name': playlist_name,
            'description': playlist_description,
            'tracks': tracks
        }
        
    except Exception as e:
        print(f"Error getting Spotify playlist: {e}")
        sys.exit(1)

def search_youtube_videos(youtube, tracks, youtube_limiter=None):
    """
    Search for each track on YouTube and get the video IDs
    """
    # Initialize rate limiter if not provided
    if youtube_limiter is None:
        youtube_limiter = RateLimiter(60)  # YouTube API limit is 100 units per day, each search costs 100 units
    
    video_ids = []
    not_found = []
    
    for i, track in enumerate(tracks):
        search_query = track['search_query']
        print(f"Searching {i+1}/{len(tracks)}: {search_query}")
        
        try:
            youtube_limiter.wait()
            
            # Search for the track on YouTube
            search_response = youtube.search().list(
                q=search_query,
                part='id,snippet',
                maxResults=1,
                type='video'
            ).execute()
            
            # Check if we got any results
            if search_response['items']:
                video_id = search_response['items'][0]['id']['videoId']
                video_title = search_response['items'][0]['snippet']['title']
                
                video_ids.append(video_id)
                print(f"✅ Found: {video_title} (ID: {video_id})")
            else:
                print(f"❌ No results found for: {search_query}")
                not_found.append(track)
                
        except HttpError as e:
            print(f"YouTube API error: {e}")
            if "quota" in str(e).lower():
                print("You have exceeded your YouTube API quota. Try again tomorrow.")
                break
            not_found.append(track)
        except Exception as e:
            print(f"Error searching for {search_query}: {e}")
            not_found.append(track)
    
    return video_ids, not_found

def create_youtube_playlist(youtube, playlist_info, video_ids, youtube_limiter=None):
    """
    Create a YouTube playlist and add videos to it
    """
    if not video_ids:
        print("No videos found to add to playlist")
        return None
    
    # Initialize rate limiter if not provided
    if youtube_limiter is None:
        youtube_limiter = RateLimiter(60)
    
    try:
        # Create a new private playlist
        youtube_limiter.wait()
        
        playlist_name = f"Spotify: {playlist_info['name']}"
        playlist_description = f"Converted from Spotify playlist: {playlist_info['name']}\n\n{playlist_info['description']}"
        
        playlist_response = youtube.playlists().insert(
            part='snippet,status',
            body={
                'snippet': {
                    'title': playlist_name,
                    'description': playlist_description
                },
                'status': {
                    'privacyStatus': 'private'
                }
            }
        ).execute()
        
        playlist_id = playlist_response['id']
        print(f"Created YouTube playlist: {playlist_name} (ID: {playlist_id})")
        
        # Add videos to the playlist
        videos_added = 0
        
        for video_id in video_ids:
            try:
                youtube_limiter.wait()
                
                youtube.playlistItems().insert(
                    part='snippet',
                    body={
                        'snippet': {
                            'playlistId': playlist_id,
                            'resourceId': {
                                'kind': 'youtube#video',
                                'videoId': video_id
                            }
                        }
                    }
                ).execute()
                
                videos_added += 1
                print(f"Added video {videos_added}/{len(video_ids)} to playlist")
                
            except HttpError as e:
                print(f"Error adding video {video_id} to playlist: {e}")
                if "quota" in str(e).lower():
                    print("You have exceeded your YouTube API quota. Try again tomorrow.")
                    break
        
        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        return {
            'id': playlist_id,
            'url': playlist_url,
            'videos_added': videos_added
        }
        
    except HttpError as e:
        print(f"YouTube API error: {e}")
        return None
    except Exception as e:
        print(f"Error creating YouTube playlist: {e}")
        return None

def main():
    try:
        # Get playlist ID from command line
        if len(sys.argv) < 2:
            print("Usage: python spotify_to_youtube.py <spotify_playlist_id> [max_tracks]")
            print("Example: python spotify_to_youtube.py spotify:playlist:37i9dQZEVXcJZyENOWUFo7 50")
            sys.exit(1)
        
        playlist_id = sys.argv[1]
        max_tracks = int(sys.argv[2]) if len(sys.argv) > 2 else None
        
        # Set up rate limiters
        spotify_limiter = RateLimiter(100)  # 100 requests per minute for Spotify
        youtube_limiter = RateLimiter(60)   # YouTube API has strict quotas
        
        # Authenticate with both services
        print("Authenticating with Spotify...")
        spotify = authenticate_spotify()
        
        print("Authenticating with YouTube...")
        youtube = authenticate_youtube()
        
        # Get tracks from Spotify playlist
        print(f"Getting tracks from Spotify playlist: {playlist_id}")
        playlist_info = get_spotify_playlist(spotify, playlist_id, spotify_limiter)
        tracks = playlist_info['tracks']
        
        print(f"Found {len(tracks)} tracks in playlist")
        
        # Limit the number of tracks if specified
        if max_tracks and max_tracks < len(tracks):
            print(f"Limiting to {max_tracks} tracks as requested")
            tracks = tracks[:max_tracks]
        
        # Search for YouTube videos
        print("Searching for tracks on YouTube...")
        video_ids, not_found = search_youtube_videos(youtube, tracks, youtube_limiter)
        
        print(f"Found {len(video_ids)} videos on YouTube")
        print(f"Could not find {len(not_found)} tracks")
        
        # Create YouTube playlist and add videos
        print("Creating YouTube playlist...")
        result = create_youtube_playlist(youtube, playlist_info, video_ids, youtube_limiter)
        
        if result:
            print("\n--- SUMMARY ---")
            print(f"Spotify playlist: {playlist_info['name']}")
            print(f"Tracks processed: {len(tracks)}")
            print(f"Videos found and added to YouTube: {result['videos_added']}")
            print(f"Could not find {len(not_found)} tracks")
            print(f"\nYouTube playlist URL: {result['url']}")
            
            if not_found:
                print("\nTracks not found on YouTube:")
                for track in not_found:
                    print(f"- {track['search_query']}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
