# 🎵 Spotify to Discogs Wantlist Automation

This script automates adding **Spotify playlist tracks** to your **Discogs wantlist** by searching for vinyl releases and adding them automatically.

## 🚀 Features
- ✅ **Retrieves tracks** from a given Spotify playlist.
- ✅ **Searches for vinyl records** on Discogs.
- ✅ **Adds matches to your Discogs wantlist**.
- ✅ **Uses a `.env` file** for secure API key storage.
- ✅ **Handles Spotify authentication** (Client Credentials Flow).
- ✅ **Respects Discogs rate limits** (auto-throttling and retry on 429 errors).

---

## 📜 Requirements

1. **Python 3.7+** installed.
2. Spotify & Discogs API credentials.
3. Required Python packages (`requests`, `python-dotenv`).

---

## 🔧 Setup

### **1️⃣ Get API Credentials**
#### **Spotify API**
- Sign up at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
- Create an app to get:
  - **Client ID**
  - **Client Secret**

#### **Discogs API**
- Sign up at [Discogs Developer Portal](https://www.discogs.com/developers/).
- Generate a **Personal Access Token** under "OAuth & Authentication".

---

### **2️⃣ Install Dependencies**
First, install required Python packages:

```sh
pip install requests python-dotenv
```

---

### **3️⃣ Configure the `.env` File**
Create a file named `.env` in the same directory as the script, and add your credentials:

```ini
# .env file for storing API credentials

# Spotify API Credentials
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Discogs API Credentials
DISCOGS_TOKEN=your_discogs_token
DISCOGS_USERNAME=your_discogs_username
```

**❗ Important:**  
- **DO NOT** commit the `.env` file to Git!  
- Add `.env` to your `.gitignore` to keep it private:

```sh
echo ".env" >> .gitignore
```

---

## 🏃‍♂️ Usage

Run the script with a **Spotify playlist ID**:

```sh
python spotify_to_discogs.py YOUR_SPOTIFY_PLAYLIST_ID
```

**Example:**
```sh
python spotify_to_discogs.py 1GLq1rt6Hs5gJpImyTAZWx
```

### **How to Find Your Playlist ID?**
- Open Spotify and navigate to your playlist.
- Copy the URL (e.g., `https://open.spotify.com/playlist/1GLq1rt6Hs5gJpImyTAZWx`).
- The part after `/playlist/` is the **Playlist ID**.

---

## 📊 How It Works

1. **Fetches the playlist tracks** from Spotify.
2. **Searches for vinyl releases** on Discogs.
3. **Adds matching records** to your Discogs wantlist.
4. **Handles rate limiting**:
   - Adds a small delay between requests.
   - Sleeps if too close to API limits.
   - Retries if Discogs returns a 429 error.

---

## 🛠 Troubleshooting

### **Common Issues & Fixes**
| Issue | Fix |
|------|------|
| `Error fetching playlist` | Check if your Spotify Client ID & Secret are correct. |
| `No tracks found` | Ensure the playlist is **public**. |
| `No vinyl found for track` | The track might not have a vinyl release on Discogs. |
| `Hit Discogs rate limit!` | The script will automatically pause and retry. |

---

## 🔄 Future Improvements
- [ ] Implement fuzzy matching for better track searches on Discogs.
- [ ] Add support for searching multiple formats (CD, cassette, etc.).
- [ ] Store wantlist additions in a local database for tracking.

---

## 📜 License
This project is licensed under the **MIT License**.

---

## 🎧 Happy Collecting!
Got issues? **Open a GitHub issue** or contribute to improve the script! 🚀


