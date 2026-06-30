# FlowState MVP - Focus Music Discovery

FlowState is an AI-assisted music discovery web application designed to curate focus-safe, transition-safe music flows. Starting from a seed track, FlowState extracts its tempo (BPM) and genres, retrieves recommendations, filters them for low-energy and tempo continuity, and generates an AI summary explaining the flow using a local LLM.

---

## Repository Structure

```
├── backend/            # FastAPI Python application
│   ├── main.py         # Main entry point & API routes
│   ├── services/       # Spotify & Ollama integration services
│   └── requirements.txt
├── frontend/           # Next.js 16 Web application
│   ├── app/            # App router components
│   └── package.json
└── .gitignore          # Root Git ignore rules
```

---

## Features

- **Tempo & Genre Continuation**: Searches tracks and recommendations to match target BPM ranges (+/- 8 BPM) and genres for low-disruption background listening.
- **Ollama AI Flow Supervision**: Utilizes a local `llama3.2` model to explain the flow transitions and focus benefits dynamically.
- **Robust API Fallbacks**: Automatically intercepts Spotify API restrictions (e.g. 403 Forbidden Premium requirement) and falls back to a high-quality local focus track list to keep the app working seamlessly.
- **Responsive Dashboard**: Dark-mode glassmorphic interface with interactive loaders, real-time logging, and transition visualizers.

---

## Getting Started

### 1. Setup Environment Variables

Create a `.env` file in the root directory (or in the `backend/` directory):

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
```

### 2. Run the Backend (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .\.venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server:
   ```bash
   python main.py
   ```
   *The backend will run on `http://localhost:8000`.*

### 3. Run the Frontend (Next.js)

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   *Open [http://localhost:3000](http://localhost:3000) in your browser.*

---

## Deployment (Vercel)

The Next.js frontend is configured to use environment variables for api resolution:
- Set `NEXT_PUBLIC_API_URL` on Vercel to point to your hosted backend (e.g., hosted on Render or Railway).
- If left unset, it will default to querying the local server running on `http://127.0.0.1:8000` on the client side.
