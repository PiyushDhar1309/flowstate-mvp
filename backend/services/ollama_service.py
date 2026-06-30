import os
import json
import logging
import requests
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        # Fallback to localhost if base URL env var is empty or not set
        base_url = os.getenv("OLLAMA_BASE_URL", "").strip()
        if not base_url:
            base_url = "http://localhost:11434"
        self.base_url = base_url.rstrip("/")
        self.api_key = os.getenv("OLLAMA_API_KEY", "").strip()
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:latest").strip()
        
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    def generate_explanation(self, input_song: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> str:
        """Generate a short AI explanation of why the selected tracks fit together with the input track for focus."""
        url = f"{self.base_url}/api/chat"
        
        recs_text = "\n".join([
            f"- '{rec['title']}' by {rec['artist']} ({rec['bpm']} BPM, Genres: {', '.join(rec['genres'])})"
            for rec in recommendations
        ])
        
        prompt = f"""
You are FlowState AI, a focus-music supervisor.
Explain why the following recommended songs fit together with the starting song '{input_song['title']}' by {input_song['artist']} ({input_song['bpm']} BPM, Genres: {', '.join(input_song['genres'])}) to maintain a focus-safe listening flow.

Recommended tracks:
{recs_text}

Provide a short, smooth, focus-oriented description (2-3 sentences max) explaining how these tracks maintain BPM safety, low-energy transitions, and genre continuity suitable for working or studying.
Keep it encouraging and clean.
"""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant specialized in music and focus flow analysis."},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.3
            }
        }
        
        logger.info(f"Sending prompt to Ollama model '{self.model}' at {url}...")
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.error(f"Error querying Ollama API: {str(e)}")
            # Return a fallback description if the local Ollama instance is not running or accessible
            return (
                f"These tracks were selected to accompany '{input_song['title']}' because they match its "
                f"tempo ({input_song['bpm']} BPM) within a safe transition window and preserve flow continuity, "
                f"ensuring a smooth, focus-friendly background soundscape."
            )
