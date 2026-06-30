import os
import logging
import requests
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SpotifyService:
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.access_token = None
        self.base_url = "https://api.spotify.com/v1"

    def _authenticate(self) -> bool:
        """Authenticate with Spotify using client credentials flow."""
        import base64
        url = "https://accounts.spotify.com/api/token"
        
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_str.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")
        
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials"
        }
        try:
            response = requests.post(url, headers=headers, data=data)
            if response.status_code != 200:
                logger.error(f"Spotify token error {response.status_code}: {response.text}")
            response.raise_for_status()
            token_info = response.json()
            self.access_token = token_info.get("access_token")
            logger.info("Successfully authenticated with Spotify.")
            return True
        except Exception as e:
            logger.error(f"Spotify authentication failed: {str(e)}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Helper to get authorization headers, refreshing token if needed."""
        if not self.access_token:
            self._authenticate()
        return {
            "Authorization": f"Bearer {self.access_token}"
        }

    def search_track(self, query: str) -> Optional[Dict[str, Any]]:
        """Search for a track by query and return primary info + artist details."""
        url = f"{self.base_url}/search"
        headers = self._get_headers()
        params = {
            "q": query,
            "type": "track",
            "limit": 1
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            # If token expired, try re-authenticating once
            if response.status_code == 401:
                self._authenticate()
                headers = self._get_headers()
                response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 403:
                logger.warning("Spotify API returned 403 Forbidden. Using fallback mock track search.")
                return self._get_mock_track(query)
                
            response.raise_for_status()
            data = response.json()
            tracks = data.get("tracks", {}).get("items", [])
            if not tracks:
                return None
            
            track = tracks[0]
            artist = track["artists"][0]
            
            # Fetch artist genres since they aren't on the track object
            genres = self.get_artist_genres(artist["id"])
            
            # Fetch audio features (tempo / BPM)
            bpm = self.get_track_bpm(track["id"])
            
            return {
                "id": track["id"],
                "title": track["name"],
                "artist": artist["name"],
                "artist_id": artist["id"],
                "bpm": bpm,
                "genres": genres,
                "album_image": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                "preview_url": track.get("preview_url")
            }
        except Exception as e:
            logger.error(f"Error searching track: {str(e)}")
            logger.warning("Falling back to mock track search.")
            return self._get_mock_track(query)

    def get_track_bpm(self, track_id: str) -> float:
        """Get the tempo (BPM) of a track."""
        url = f"{self.base_url}/audio-features/{track_id}"
        headers = self._get_headers()
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            features = response.json()
            return round(features.get("tempo", 0.0), 1)
        except Exception as e:
            logger.error(f"Error fetching track audio features: {str(e)}")
            return 0.0

    def get_artist_genres(self, artist_id: str) -> List[str]:
        """Get genres associated with an artist."""
        url = f"{self.base_url}/artists/{artist_id}"
        headers = self._get_headers()
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            artist_info = response.json()
            return artist_info.get("genres", [])
        except Exception as e:
            logger.error(f"Error fetching artist info: {str(e)}")
            return []

    def get_batch_artist_genres(self, artist_ids: List[str]) -> Dict[str, List[str]]:
        """Fetch genres for multiple artist IDs in one request."""
        if not artist_ids:
            return {}
        # Spotify allows up to 50 IDs
        unique_ids = list(set(artist_ids))[:50]
        url = f"{self.base_url}/artists"
        headers = self._get_headers()
        params = {"ids": ",".join(unique_ids)}
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return {artist["id"]: artist.get("genres", []) for artist in data.get("artists", []) if artist}
        except Exception as e:
            logger.error(f"Error in batch artist retrieval: {str(e)}")
            return {}

    def get_batch_track_bpms(self, track_ids: List[str]) -> Dict[str, float]:
        """Fetch BPM (tempo) for multiple track IDs in one request."""
        if not track_ids:
            return {}
        unique_ids = list(set(track_ids))[:100]
        url = f"{self.base_url}/audio-features"
        headers = self._get_headers()
        params = {"ids": ",".join(unique_ids)}
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return {feat["id"]: round(feat.get("tempo", 0.0), 1) for feat in data.get("audio_features", []) if feat}
        except Exception as e:
            logger.error(f"Error in batch audio features: {str(e)}")
            return {}

    def get_recommendations(self, seed_track_id: str, target_bpm: float, seed_genres: List[str]) -> List[Dict[str, Any]]:
        """Retrieve recommendations and filter to match BPM range and similar genre."""
        # Check if seed track is a mock track
        if str(seed_track_id).startswith("mock_"):
            logger.info("Using mock recommendations fallback since seed track is a mock track.")
            return self._get_mock_recommendations(target_bpm, seed_genres)
            
        url = f"{self.base_url}/recommendations"
        headers = self._get_headers()
        
        # We specify target BPM but also fetch a bit more tracks (e.g. 30) so we can manually filter and refine.
        params = {
            "seed_tracks": seed_track_id,
            "target_tempo": target_bpm,
            "limit": 30
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 403:
                logger.warning("Spotify API returned 403 Forbidden. Using fallback mock recommendations.")
                return self._get_mock_recommendations(target_bpm, seed_genres)
                
            response.raise_for_status()
            data = response.json()
            tracks = data.get("tracks", [])
            
            if not tracks:
                return []
            
            # Fetch BPMs and Genres in batch
            track_ids = [t["id"] for t in tracks]
            artist_ids = [t["artists"][0]["id"] for t in tracks]
            
            bpms = self.get_batch_track_bpms(track_ids)
            genres_map = self.get_batch_artist_genres(artist_ids)
            
            results = []
            for track in tracks:
                t_id = track["id"]
                art = track["artists"][0]
                art_id = art["id"]
                
                track_bpm = bpms.get(t_id, 0.0)
                track_genres = genres_map.get(art_id, [])
                
                # Check BPM delta (e.g., +/- 8 BPM as preferred)
                bpm_diff = abs(track_bpm - target_bpm)
                
                # Calculate simple genre overlap score
                genre_match = False
                if seed_genres and track_genres:
                    # check if any genre words match or exact match
                    seed_words = set(" ".join(seed_genres).lower().split())
                    track_words = set(" ".join(track_genres).lower().split())
                    if seed_words.intersection(track_words):
                        genre_match = True
                
                results.append({
                    "id": t_id,
                    "title": track["name"],
                    "artist": art["name"],
                    "bpm": track_bpm,
                    "genres": track_genres,
                    "bpm_diff": bpm_diff,
                    "genre_match": genre_match,
                    "album_image": track["album"]["images"][0]["url"] if track["album"]["images"] else None
                })
            
            # Sort: first by genre match (True first), then by BPM diff (smaller first)
            # This ensures genre continuity and BPM closeness.
            results.sort(key=lambda x: (not x["genre_match"], x["bpm_diff"]))
            
            # Return max 6 songs
            return results[:6]
            
        except Exception as e:
            logger.error(f"Error fetching recommendations: {str(e)}")
            logger.warning("Falling back to mock recommendations.")
            return self._get_mock_recommendations(target_bpm, seed_genres)

    def _get_mock_track(self, query: str) -> Dict[str, Any]:
        """Generate or find a mock track for the query."""
        import random
        query_lower = query.lower()
        mock_db = [
            {"title": "Weightless", "artist": "Marconi Union", "bpm": 60.0, "genres": ["ambient", "chillout"]},
            {"title": "Resonance", "artist": "HOME", "bpm": 170.0, "genres": ["synthwave", "chillwave"]},
            {"title": "Intro", "artist": "The xx", "bpm": 120.0, "genres": ["indie pop", "dream pop"]},
            {"title": "Day 3", "artist": "Ta-ku", "bpm": 74.0, "genres": ["lo-fi beat", "chillhop"]},
            {"title": "Gymnopédie No. 1", "artist": "Erik Satie", "bpm": 73.0, "genres": ["classical", "piano"]}
        ]
        # Check for matching query
        for track in mock_db:
            if query_lower in track["title"].lower() or query_lower in track["artist"].lower():
                return {
                    "id": f"mock_{track['title'].lower().replace(' ', '_')}",
                    "title": track["title"],
                    "artist": track["artist"],
                    "artist_id": "mock_artist_id",
                    "bpm": track["bpm"],
                    "genres": track["genres"],
                    "album_image": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b",
                    "preview_url": None
                }
        
        # Default fallback
        return {
            "id": f"mock_{query_lower.replace(' ', '_')}",
            "title": query,
            "artist": "Focus Artist",
            "artist_id": "mock_artist_id",
            "bpm": round(random.uniform(70.0, 110.0), 1),
            "genres": ["lo-fi", "ambient"],
            "album_image": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b",
            "preview_url": None
        }

    def _get_mock_recommendations(self, target_bpm: float, seed_genres: List[str]) -> List[Dict[str, Any]]:
        """Generate high-quality mock recommendations matching target BPM and genre style."""
        mock_db = [
            {"title": "Midnight City", "artist": "M83", "bpm": 105.0, "genres": ["synthpop", "indie pop"]},
            {"title": "Strobe", "artist": "deadmau5", "bpm": 128.0, "genres": ["progressive house", "edm"]},
            {"title": "Day 3", "artist": "Ta-ku", "bpm": 74.0, "genres": ["lo-fi beat", "chillhop"]},
            {"title": "Svefn-g-englar", "artist": "Sigur Rós", "bpm": 72.0, "genres": ["post-rock", "ambient"]},
            {"title": "Clair de Lune", "artist": "Claude Debussy", "bpm": 62.0, "genres": ["classical", "piano"]},
            {"title": "Resonance", "artist": "HOME", "bpm": 170.0, "genres": ["synthwave", "chillwave"]},
            {"title": "Weightless", "artist": "Marconi Union", "bpm": 60.0, "genres": ["ambient", "chillout"]},
            {"title": "Aruarian Dance", "artist": "Nujabes", "bpm": 98.0, "genres": ["lo-fi beat", "hip-hop"]}
        ]
        
        results = []
        for track in mock_db:
            track_bpm = track["bpm"]
            track_genres = track["genres"]
            bpm_diff = abs(track_bpm - target_bpm)
            
            genre_match = False
            if seed_genres and track_genres:
                seed_words = set(" ".join(seed_genres).lower().split())
                track_words = set(" ".join(track_genres).lower().split())
                if seed_words.intersection(track_words):
                    genre_match = True
            
            results.append({
                "id": f"mock_rec_{track['title'].lower().replace(' ', '_')}",
                "title": track["title"],
                "artist": track["artist"],
                "bpm": track_bpm,
                "genres": track_genres,
                "bpm_diff": bpm_diff,
                "genre_match": genre_match,
                "album_image": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b"
            })
            
        results.sort(key=lambda x: (not x["genre_match"], x["bpm_diff"]))
        return results[:6]
