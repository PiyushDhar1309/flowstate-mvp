import os
import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.spotify_service import SpotifyService
from services.ollama_service import OllamaService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FlowState API", description="AI-assisted music discovery MVP for focus-safe sessions")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for MVP simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateFlowRequest(BaseModel):
    song: str

@app.post("/generate-flow")
async def generate_flow(payload: GenerateFlowRequest):
    if not payload.song.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Song query cannot be empty."
        )
    
    spotify_service = SpotifyService()
    ollama_service = OllamaService()
    
    # 1. Search for the song on Spotify
    logger.info(f"Searching Spotify for: {payload.song}")
    input_song = spotify_service.search_track(payload.song)
    if not input_song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Song '{payload.song}' could not be found on Spotify."
        )
    
    # 2. Find recommended songs with nearby BPM and similar genre
    logger.info(f"Finding recommendations for track ID {input_song['id']} (BPM: {input_song['bpm']})")
    recommendations = spotify_service.get_recommendations(
        seed_track_id=input_song["id"],
        target_bpm=input_song["bpm"],
        seed_genres=input_song["genres"]
    )
    
    # 3. Generate AI explanation using Ollama
    logger.info("Generating AI explanation using Ollama...")
    ai_summary = ollama_service.generate_explanation(input_song, recommendations)
    
    return {
        "input_song": input_song,
        "recommendations": recommendations,
        "ai_summary": ai_summary
    }

if __name__ == "__main__":
    import uvicorn
    # Use PORT env variable if defined (for production deployment like Render/Railway)
    port = int(os.getenv("PORT", 8000))
    # Bind to 0.0.0.0 to receive external connections in cloud platforms
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
