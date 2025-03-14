# YouTube API Setup Instructions

To use the Spotify to YouTube converter, you'll need to set up the YouTube API. This guide walks you through the process.

## 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page and click "New Project"
3. Give your project a name (e.g., "Spotify to YouTube Converter")
4. Click "Create"
5. Make sure your new project is selected in the dropdown

## 2. Enable the YouTube Data API

1. Go to [API Library](https://console.cloud.google.com/apis/library)
2. Search for "YouTube Data API v3"
3. Click on the API and then click "Enable"

## 3. Create OAuth 2.0 Credentials

1. Go to [Credentials](https://console.cloud.google.com/apis/credentials)
2. Click "Create Credentials" and select "OAuth client ID"
3. If prompted to configure the OAuth consent screen:
   - Select "External" (or "Internal" if you have a Google Workspace account)
   - Fill in the required information (App name, user support email, developer contact email)
   - Add the scope: `../auth/youtube` (for managing YouTube account)
   - Add yourself as a test user if you selected "External"
   - Complete the OAuth consent screen setup
4. For application type, select "Desktop app"
5. Give it a name (e.g., "Spotify to YouTube Client")
6. Click "Create"
7. Download the JSON file by clicking the download icon
8. Rename the downloaded file to `credentials.json` and place it in the same directory as the script

## 4. Update your .env file

Make sure your `.env` file includes Spotify credentials:

```
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

## 5. Install Required Libraries

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib spotipy python-dotenv
```

## 6. First Run Authentication

The first time you run the script, it will:

1. Open a browser window asking you to log in to your Google account
2. Ask for permission to access your YouTube account
3. After granting permission, it will create a `token.json` file for future authentication

## Important Notes

- **YouTube API Quota**: The YouTube Data API has a daily quota limit of 10,000 units. Each search operation costs 100 units, so you can search for about 100 tracks per day for free.
- **Recommendations**:
  - Start with smaller playlists (less than 50 tracks) to avoid hitting quota limits
  - If converting large playlists, use the max_tracks parameter to process them in batches
  - Consider applying for a quota increase if you need to convert large playlists frequently
