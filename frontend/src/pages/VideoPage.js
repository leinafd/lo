import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ArrowLeft, Zap, Video, Upload, Play, Coins, Lock, Crown } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

function creditCost(duration, quality) {
  let base = duration <= 5 ? 1 : duration <= 10 ? 2 : 3;
  return quality === "hd" ? base * 2 : base;
}

export default function VideoPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [usage, setUsage] = useState({});
  const [prompt, setPrompt] = useState("");
  const [duration, setDuration] = useState(5);
  const [quality, setQuality] = useState("standard");
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [videos, setVideos] = useState([]);
  const [error, setError] = useState("");

  const fetchUsage = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/api/user/usage`, { withCredentials: true });
      setUsage(data);
    } catch {}
  }, []);

  const fetchVideos = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/api/user/videos`, { withCredentials: true });
      setVideos(data);
    } catch {}
  }, []);

  useEffect(() => { fetchUsage(); fetchVideos(); }, [fetchUsage, fetchVideos]);

  const maxDur = usage.max_video_duration || 5;
  const isLocked = usage.video_locked;
  const role = usage.role || "free";
  const cost = usage.uses_credits ? creditCost(duration, quality) : 0;

  const handleGenerate = async () => {
    if (!prompt.trim() || generating) return;
    setError("");
    setGenerating(true);
    setProgress(0);
    setResult(null);

    // Simulate progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) { clearInterval(interval); return 90; }
        return prev + Math.random() * 15;
      });
    }, 400);

    try {
      const { data } = await axios.post(`${API}/api/video/generate`, { prompt: prompt.trim(), duration, quality }, { withCredentials: true });
      clearInterval(interval);
      setProgress(100);
      setTimeout(() => { setResult(data); setGenerating(false); fetchUsage(); fetchVideos(); }, 500);
    } catch (err) {
      clearInterval(interval);
      setProgress(0);
      setGenerating(false);
      setError(err.response?.data?.detail || "Video generation failed.");
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a]" data-testid="video-page">
      <nav className="border-b border-white/[0.06] bg-[#0a0a0a]/80 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center gap-2.5">
          <button onClick={() => navigate("/chat")} className="text-[#a1a1aa] hover:text-white transition-colors mr-2" data-testid="video-back">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="w-8 h-8 rounded-lg bg-[#3b82f6] flex items-center justify-center">
            <Video className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-semibold tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>Videos</span>
          {usage.uses_credits && (
            <div className="ml-auto flex items-center gap-1.5 text-xs text-[#a1a1aa]">
              <Coins className="w-3.5 h-3.5 text-[#3b82f6]" />
              <span className="text-[#fafafa] font-medium">{usage.video_credits || 0}</span> credits
            </div>
          )}
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-8">
        {isLocked ? (
          <div className="text-center p-12 rounded-xl bg-[#111111] border border-white/[0.08]" data-testid="video-locked">
            <Lock className="w-12 h-12 text-[#52525b] mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2" style={{ fontFamily: "'Outfit', sans-serif" }}>Video Trial Expired</h2>
            <p className="text-sm text-[#a1a1aa] mb-6 max-w-sm mx-auto">Your free video trial has ended. Upgrade to Pro to unlock video generation with credits.</p>
            <Button onClick={() => navigate("/pricing")} className="bg-[#3b82f6] hover:bg-[#2563eb] text-white h-10 px-6" data-testid="upgrade-for-video">
              <Crown className="w-4 h-4 mr-2" /> Upgrade to Pro
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {/* Generation Panel */}
            <div className="lg:col-span-3 space-y-5">
              <div className="p-5 rounded-xl bg-[#111111] border border-white/[0.08]">
                <h2 className="text-lg font-semibold mb-4" style={{ fontFamily: "'Outfit', sans-serif" }}>Generate Video</h2>
                <textarea
                  data-testid="video-prompt"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Describe the video you want to create..."
                  rows={3}
                  className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-sm text-[#fafafa] placeholder:text-[#52525b] focus:border-[#3b82f6] focus:ring-1 focus:ring-[#3b82f6] outline-none resize-none"
                />

                {/* Duration Slider */}
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-[#a1a1aa] uppercase tracking-[0.15em]">Duration</span>
                    <span className="text-xs text-[#fafafa] font-medium">{duration}s</span>
                  </div>
                  <Slider
                    data-testid="duration-slider"
                    value={[duration]}
                    onValueChange={([v]) => setDuration(v)}
                    min={1}
                    max={maxDur}
                    step={1}
                    className="w-full"
                  />
                  <div className="flex justify-between mt-1">
                    <span className="text-[10px] text-[#52525b]">1s</span>
                    <span className="text-[10px] text-[#52525b]">{maxDur}s max</span>
                  </div>
                </div>

                {/* Quality */}
                <div className="mt-4">
                  <span className="text-xs text-[#a1a1aa] uppercase tracking-[0.15em] block mb-2">Quality</span>
                  <div className="flex gap-2">
                    {(usage.video_quality || ["standard"]).map(q => (
                      <button
                        key={q}
                        onClick={() => setQuality(q)}
                        className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${quality === q ? "bg-[#3b82f6] text-white" : "bg-white/5 text-[#a1a1aa] border border-white/10 hover:bg-white/10"}`}
                        data-testid={`quality-${q}`}
                      >
                        {q.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Cost display */}
                {usage.uses_credits && (
                  <div className="mt-4 p-3 rounded-lg bg-white/5 flex items-center justify-between">
                    <span className="text-xs text-[#a1a1aa]">Credit cost</span>
                    <span className="text-sm font-bold text-[#3b82f6]">{cost} credit{cost !== 1 ? "s" : ""}</span>
                  </div>
                )}
                {role === "free" && usage.watermark && (
                  <p className="mt-3 text-xs text-amber-400">Free tier: output will have a watermark overlay.</p>
                )}

                {error && <p className="mt-3 text-xs text-red-400" data-testid="video-error">{error}</p>}

                {/* Generate button */}
                <Button
                  onClick={handleGenerate}
                  disabled={!prompt.trim() || generating}
                  className="w-full mt-4 h-11 bg-[#3b82f6] hover:bg-[#2563eb] text-white font-medium"
                  data-testid="generate-video-button"
                >
                  {generating ? "Generating..." : "Generate Video"}
                </Button>

                {/* Progress bar */}
                {generating && (
                  <div className="mt-4" data-testid="video-progress">
                    <Progress value={progress} className="h-2 bg-white/10" />
                    <p className="text-xs text-[#52525b] mt-1 text-center">{Math.round(progress)}% — Processing with Seedance 2.0</p>
                  </div>
                )}
              </div>

              {/* Result */}
              {result && (
                <div className="p-5 rounded-xl bg-[#111111] border border-white/[0.08]" data-testid="video-result">
                  <h3 className="text-sm font-semibold mb-3" style={{ fontFamily: "'Outfit', sans-serif" }}>Generated Video</h3>
                  <div className="relative rounded-lg overflow-hidden bg-black aspect-video">
                    <video src={result.video_url} controls className="w-full h-full object-contain" data-testid="generated-video" />
                    {result.watermark && (
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <span className="text-white/20 text-4xl font-bold rotate-[-20deg] select-none" style={{ fontFamily: "'Outfit', sans-serif" }}>
                          IMPULSE AI
                        </span>
                      </div>
                    )}
                  </div>
                  {result.credits_used > 0 && (
                    <p className="text-xs text-[#52525b] mt-2">{result.credits_used} credit{result.credits_used !== 1 ? "s" : ""} used. Remaining: {result.remaining_credits}</p>
                  )}
                </div>
              )}
            </div>

            {/* History Panel */}
            <div className="lg:col-span-2">
              <div className="p-4 rounded-xl bg-[#111111] border border-white/[0.08] h-full">
                <h3 className="text-sm font-semibold mb-3" style={{ fontFamily: "'Outfit', sans-serif" }}>History</h3>
                <ScrollArea className="h-[500px]">
                  {videos.length === 0 ? (
                    <p className="text-xs text-[#52525b] text-center py-8">No videos generated yet</p>
                  ) : (
                    <div className="space-y-2">
                      {videos.map(v => (
                        <div key={v.id} className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-all cursor-pointer" data-testid={`video-history-${v.id}`}>
                          <div className="flex items-center gap-2 mb-1">
                            <Play className="w-3 h-3 text-[#3b82f6]" />
                            <span className="text-xs text-[#fafafa] truncate flex-1">{v.prompt}</span>
                          </div>
                          <div className="flex gap-2 text-[10px] text-[#52525b]">
                            <span>{v.duration}s</span>
                            <span>{v.quality}</span>
                            {v.credits_used > 0 && <span>{v.credits_used} cr</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
