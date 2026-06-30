"use client";

import React, { useState, useEffect } from "react";

interface Track {
  id: string;
  title: string;
  artist: string;
  bpm: number;
  genres: string[];
  album_image?: string;
  bpm_diff?: number;
}

interface FlowResponse {
  input_song: Track;
  recommendations: Track[];
  ai_summary: string;
}

const STAGES = [
  "Searching Spotify...",
  "Extracting BPM...",
  "Finding similar tracks...",
  "Building focus-safe flow...",
  "Generating AI explanation..."
];

export default function FlowStatePage() {
  const [songQuery, setSongQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentStage, setCurrentStage] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FlowResponse | null>(null);

  // Handle stage transition animations during loading
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (loading) {
      interval = setInterval(() => {
        setCurrentStage((prev) => {
          if (prev < STAGES.length - 1) {
            return prev + 1;
          }
          return prev;
        });
      }, 700);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!songQuery.trim()) return;

    setLoading(true);
    setCurrentStage(0);
    setError(null);
    setResult(null);

    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/generate-flow`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ song: songQuery }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to generate focus flow.");
      }

      const data: FlowResponse = await response.json();
      
      // Let the loader finish showing the final stages nicely
      setTimeout(() => {
        setResult(data);
        setLoading(false);
      }, 800);

    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0b0e] text-[#f4f4f6] flex flex-col justify-between py-12 px-6 sm:px-12 font-sans selection:bg-[#1db954] selection:text-black">
      
      {/* Top Header */}
      <header className="max-w-2xl mx-auto w-full text-center mb-10">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-[#e2e2e9] to-[#1db954] bg-clip-text text-transparent">
          FlowState
        </h1>
        <p className="mt-2 text-sm sm:text-base text-zinc-400 font-medium tracking-wide">
          AI-assisted focus-safe music discovery
        </p>
      </header>

      {/* Main Form Box */}
      <main className="flex-1 flex flex-col items-center justify-start w-full max-w-4xl mx-auto">
        <div className="w-full max-w-xl bg-[#121216] border border-[#232329] rounded-2xl p-6 sm:p-8 shadow-2xl transition-all duration-300">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="song-input" className="sr-only">Starting Song</label>
              <input
                id="song-input"
                type="text"
                value={songQuery}
                onChange={(e) => setSongQuery(e.target.value)}
                placeholder="Enter a song you focus with..."
                className="w-full px-5 py-4 bg-[#1a1a22] border border-[#2d2d37] rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-[#1db954] focus:border-transparent transition-all font-medium"
                disabled={loading}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !songQuery.trim()}
              className="w-full py-4 px-6 bg-[#1db954] text-black font-semibold rounded-xl hover:bg-[#1ed760] active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg shadow-[#1db954]/20"
            >
              {loading ? "Aligning Focus States..." : "Generate Focus Flow"}
            </button>
          </form>
        </div>

        {/* Live Loading Logs */}
        {loading && (
          <div className="w-full max-w-xl mt-8 bg-[#121216] border border-[#232329] rounded-2xl p-6 shadow-xl space-y-3.5 transition-all duration-300">
            <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-1">
              Active Pipeline Logs
            </h3>
            {STAGES.map((stage, idx) => {
              const isDone = idx < currentStage;
              const isCurrent = idx === currentStage;
              const isPending = idx > currentStage;

              return (
                <div key={idx} className="flex items-center space-x-3 text-sm transition-opacity duration-300">
                  {isDone && (
                    <span className="text-[#1db954] flex items-center justify-center font-bold">
                      ✓
                    </span>
                  )}
                  {isCurrent && (
                    <div className="w-3 h-3 border-2 border-[#1db954] border-t-transparent rounded-full animate-spin" />
                  )}
                  {isPending && (
                    <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
                  )}
                  <span className={`font-mono ${isCurrent ? "text-white font-medium" : isDone ? "text-zinc-400" : "text-zinc-600"}`}>
                    {stage}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="w-full max-w-xl mt-6 p-4 bg-red-950/40 border border-red-800/60 rounded-xl text-red-200 text-sm font-medium">
            ⚠️ {error}
          </div>
        )}

        {/* Results view */}
        {result && (
          <div className="w-full mt-10 space-y-10 animate-fade-in">
            
            {/* Input Song Detail Header */}
            <div className="bg-[#121216]/60 border border-[#232329] rounded-2xl p-5 flex flex-col sm:flex-row items-center sm:space-x-5 space-y-4 sm:space-y-0">
              {result.input_song.album_image && (
                <img
                  src={result.input_song.album_image}
                  alt={result.input_song.title}
                  className="w-20 h-20 rounded-xl object-cover shadow-md border border-white/5"
                />
              )}
              <div className="text-center sm:text-left flex-1 min-w-0">
                <span className="inline-block text-[10px] font-bold text-[#1db954] uppercase tracking-wider bg-[#1db954]/10 px-2 py-0.5 rounded-full mb-1">
                  Seed Focus Track
                </span>
                <h2 className="text-xl font-bold truncate text-white">
                  {result.input_song.title}
                </h2>
                <p className="text-zinc-400 text-sm font-medium">
                  {result.input_song.artist}
                </p>
                <div className="flex flex-wrap justify-center sm:justify-start gap-1.5 mt-2">
                  {result.input_song.genres.map((g, i) => (
                    <span key={i} className="text-[11px] bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded-md">
                      {g}
                    </span>
                  ))}
                </div>
              </div>
              <div className="text-center sm:text-right bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-2 min-w-[100px]">
                <div className="text-2xl font-black text-[#1db954] leading-none">
                  {Math.round(result.input_song.bpm)}
                </div>
                <div className="text-[9px] uppercase tracking-wider text-zinc-500 font-bold mt-1">
                  Base BPM
                </div>
              </div>
            </div>

            {/* Recommendations Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-zinc-200 flex items-center">
                <span className="w-1.5 h-5 bg-[#1db954] rounded-full mr-2.5"></span>
                Focus Flow Recommendations
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.recommendations.map((track) => (
                  <div
                    key={track.id}
                    className="group bg-[#121216] border border-[#232329] hover:border-[#383842] rounded-xl p-4 flex items-center space-x-4 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg shadow-black/40"
                  >
                    {track.album_image && (
                      <img
                        src={track.album_image}
                        alt={track.title}
                        className="w-16 h-16 rounded-lg object-cover flex-shrink-0"
                      />
                    )}
                    <div className="min-w-0 flex-1">
                      <h4 className="font-bold text-sm text-white truncate group-hover:text-[#1db954] transition-colors">
                        {track.title}
                      </h4>
                      <p className="text-zinc-400 text-xs truncate">
                        {track.artist}
                      </p>
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {track.genres.slice(0, 2).map((g, i) => (
                          <span key={i} className="text-[9px] bg-zinc-800/80 text-zinc-400 px-1.5 py-0.5 rounded">
                            {g}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="text-right flex-shrink-0 pl-2">
                      <div className="text-base font-bold text-zinc-200 leading-none">
                        {Math.round(track.bpm)}
                      </div>
                      <div className="text-[8px] uppercase tracking-wider text-zinc-500 mt-1">
                        BPM
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Explanation Summary */}
            <div className="bg-[#121216] border border-[#2d2d38]/60 rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-[#1db954] to-emerald-500" />
              <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-2 flex items-center">
                💡 FlowState AI Summary
              </h3>
              <p className="text-zinc-200 leading-relaxed text-sm sm:text-base font-medium italic">
                "{result.ai_summary}"
              </p>
            </div>

          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="max-w-2xl mx-auto w-full text-center mt-12 pt-6 border-t border-[#1a1a20]">
        <p className="text-xs text-zinc-500">
          FlowState MVP • Powered by Spotify Web API & Ollama LLM
        </p>
      </footer>

    </div>
  );
}
