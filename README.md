# 🎵 Spotify to Discogs Wantlist Automation

This script automates the process of adding tracks from a Spotify playlist to your Discogs wantlist by:

- Retrieving tracks from a specified Spotify playlist.
- Searching for corresponding vinyl records on Discogs.
- Utilizing fuzzy matching techniques to improve search accuracy.
- Integrating OpenAI's ChatGPT API for enhanced matching.
- Prompting the user to confirm matches before adding them to the wantlist.
- Allowing selection of different OpenAI models for the matching process.

## 🚀 Features

- **Spotify Integration**: Fetch tracks from any public Spotify playlist.
- **Discogs Integration**: Search for vinyl releases and manage your wantlist.
- **Fuzzy Matching**: Employs `TheFuzz` library for approximate string matching.
- **AI-Powered Matching**: Leverages OpenAI's ChatGPT API for context-aware matching.
- **User Confirmation**: Prompts users to accept or reject matches before adding to the wantlist.
- **Customizable AI Models**: Choose which OpenAI model to use for matching.

## 📋 Requirements

- **Python 3.7+**: Ensure Python is installed on your system.
- **Spotify API Credentials**: Obtain a Client ID and Client Secret.
- **Discogs API Token**: Generate a personal access token.
- **OpenAI API Key**: Acquire an API key from OpenAI.
- **Python Packages**: Install the following libraries:
  - `requests`
  - `python-dotenv`
  - `openai`
  - `thefuzz`

## 🔧 Setup

### 1️⃣ Obtain API Credentials

**Spotify API**:

- Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
- Log in and create a new application to get your **Client ID** and **Client Secret**.

**Discogs API**:

- Navigate to the [Discogs Developer Portal](https://www.discogs.com/developers/).
- Log in and generate a **Personal Access Token** under the "OAuth & Authentication" section.

**OpenAI API**:

- Go to the [OpenAI Dashboard](https://platform.openai.com/account/api-keys).
- Log in and create a new API key.

### 2️⃣ Install Dependencies

Use `pip` to install the required Python packages:

```bash
pip install requests python-dotenv openai thefuzz
```

### 3️⃣ Configure the `.env` File

Create a `.env` file in the same directory as the script and add your credentials:

```ini
# Spotify API Credentials
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Discogs API Credentials
DISCOGS_TOKEN=your_discogs_token
DISCOGS_USERNAME=your_discogs_username

# OpenAI API Key and Default Model
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo  # Set your preferred default model
```

**Important**: Ensure that your `.env` file is included in `.gitignore` to prevent exposing your credentials.

## 🏃‍♂️ Usage

Run the script with the Spotify playlist ID and specify the OpenAI model (optional):

```bash
python spotify_to_discogs.py YOUR_SPOTIFY_PLAYLIST_ID --model MODEL_NAME
```

**Example**:

```bash
python spotify_to_discogs.py 1GLq1rt6Hs5gJpImyTAZWx --model gpt-3.5-turbo
```

If no model is specified, the script will use the default model set in the `.env` file.

### How to Find Your Playlist ID

- Open Spotify and navigate to your playlist.
- Copy the URL (e.g., `https://open.spotify.com/playlist/1GLq1rt6Hs5gJpImyTAZWx`).
- The part after `/playlist/` is the **Playlist ID**.

## 📊 How It Works

1. **Fetches Playlist Tracks**: Retrieves tracks from the specified Spotify playlist.
2. **Searches Discogs**: Looks for vinyl releases on Discogs using fuzzy matching.
3. **AI-Powered Matching**: Uses OpenAI's ChatGPT API to confirm if the Spotify track and Discogs release refer to the same song.
4. **User Confirmation**: Displays the Spotify track and potential Discogs match, prompting the user to accept or reject the match.
5. **Updates Wantlist**: Adds the confirmed release to your Discogs wantlist, avoiding duplicates.

## 🛠 Troubleshooting

| Issue                              | Solution                                                                 |
|------------------------------------|--------------------------------------------------------------------------|
| Error fetching playlist            | Verify your Spotify Client ID and Secret.                                |
| No tracks found                    | Ensure the playlist is public.                                           |
| No vinyl found for track           | The track might not have a vinyl release on Discogs.                     |
| Skipping {release_id}, already in wantlist | The track is already in your Discogs wantlist.                          |
| Hit Discogs rate limit!            | The script will automatically pause and retry after hitting the rate limit. |

## 🔄 Future Improvements

- Implement more advanced fuzzy matching techniques.
- Add support for searching multiple formats (e.g., CD, cassette).
- Store wantlist additions in a local database for tracking.
- Enhance user interface for better interaction.

## 📜 License

This project is licensed under the **MIT License**.

## 🎧 Happy Collecting!

If you encounter any issues or have suggestions for improvements, feel free to open an issue or contribute to the project. Happy collecting! 
