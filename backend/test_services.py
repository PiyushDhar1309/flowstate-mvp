import os
import sys
from dotenv import load_dotenv

# Load env from root or backend
load_dotenv()
load_dotenv("../.env")

from services.spotify_service import SpotifyService
from services.ollama_service import OllamaService

def test_spotify():
    print("=== Testing Spotify Service ===")
    spotify = SpotifyService()
    print("Spotify Client ID:", spotify.client_id)
    
    # 1. Authenticate
    auth_success = spotify._authenticate()
    print("Authentication Success:", auth_success)
    if not auth_success:
        print("Spotify auth failed. Please verify SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env")
        return False
    
    # Let's inspect the actual search request manually to get exact error message
    import requests
    url = f"{spotify.base_url}/search"
    headers = spotify._get_headers()
    params = {
        "q": "Rain",
        "type": "track",
        "limit": 1
    }
    resp = requests.get(url, headers=headers, params=params)
    print("Search Status Code:", resp.status_code)
    print("Search Response Headers:", resp.headers)
    print("Search Response Content:", resp.text)
        
    # 2. Search track
    search_query = "Rain"
    print(f"Searching track: '{search_query}'")
    track = spotify.search_track(search_query)
    print("Track result:", track)
    if not track:
        print("Failed to find track or fetch details.")
        return False
        
    # 3. Recommendations
    print("Fetching recommendations...")
    recs = spotify.get_recommendations(
        seed_track_id=track["id"],
        target_bpm=track["bpm"],
        seed_genres=track["genres"]
    )
    print(f"Found {len(recs)} recommendations:")
    for r in recs:
        print(f"- {r['title']} by {r['artist']} (BPM: {r['bpm']}, BPM Diff: {r['bpm_diff']:.1f}, Genre Match: {r['genre_match']})")
        
    return track, recs

def test_ollama(track, recs):
    print("\n=== Testing Ollama Service ===")
    ollama = OllamaService()
    print("Ollama Base URL:", ollama.base_url)
    print("Ollama Model:", ollama.model)
    
    summary = ollama.generate_explanation(track, recs)
    print("Generated AI Summary:")
    print(summary)

if __name__ == "__main__":
    res = test_spotify()
    if res:
        track, recs = res
        test_ollama(track, recs)
    else:
        print("Spotify test failed, skipping Ollama test.")
