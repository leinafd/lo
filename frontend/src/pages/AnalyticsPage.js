import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "@/contexts/AuthContext";
import { ArrowLeft, Zap, MessageSquare, ImageIcon, Video, Coins, TrendingUp } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

export default function AnalyticsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const { data: d } = await axios.get(`${API}/api/user/analytics`, { withCredentials: true });
        setData(d);
      } catch {
        navigate("/chat");
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [navigate]);

  if (loading) return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
      <div className="w-6 h-6 border-2 border-[#3b82f6] border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (!data) return null;

  const stats = [
    { label: "Messages Sent", value: data.totals.messages, icon: MessageSquare, color: "text-[#3b82f6]", bg: "bg-[#3b82f6]/10" },
    { label: "Images Generated", value: data.totals.images, icon: ImageIcon, color: "text-emerald-400", bg: "bg-emerald-400/10" },
    { label: "Videos Generated", value: data.totals.videos, icon: Video, color: "text-purple-400", bg: "bg-purple-400/10" },
    { label: "Credits Available", value: data.current_credits, icon: Coins, color: "text-amber-400", bg: "bg-amber-400/10" },
    { label: "Credits Spent (30d)", value: data.credits_spent_30d, icon: TrendingUp, color: "text-red-400", bg: "bg-red-400/10" },
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0a]" data-testid="analytics-page">
      <nav className="border-b border-white/[0.06] bg-[#0a0a0a]/80 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center gap-2.5">
          <button onClick={() => navigate("/chat")} className="text-[#a1a1aa] hover:text-white transition-colors mr-2" data-testid="analytics-back">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="w-8 h-8 rounded-lg bg-[#3b82f6] flex items-center justify-center">
            <TrendingUp className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-semibold tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>Usage Analytics</span>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-8">
        <h1 className="text-3xl font-bold tracking-tight mb-8" style={{ fontFamily: "'Outfit', sans-serif" }}>Your Activity</h1>

        {/* Stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-10">
          {stats.map((s, i) => {
            const Icon = s.icon;
            return (
              <div key={i} className="p-4 rounded-xl bg-[#111111] border border-white/[0.08]" data-testid={`analytics-stat-${i}`}>
                <div className={`w-9 h-9 rounded-lg ${s.bg} flex items-center justify-center mb-3`}>
                  <Icon className={`w-4 h-4 ${s.color}`} />
                </div>
                <p className="text-2xl font-bold tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>{s.value}</p>
                <p className="text-[10px] text-[#52525b] uppercase tracking-wider mt-0.5">{s.label}</p>
              </div>
            );
          })}
        </div>

        {/* Recent video activity */}
        {data.recent_videos.length > 0 && (
          <div className="mb-10">
            <h2 className="text-lg font-semibold mb-4" style={{ fontFamily: "'Outfit', sans-serif" }}>Recent Video Activity</h2>
            <div className="p-4 rounded-xl bg-[#111111] border border-white/[0.08]">
              <div className="grid grid-cols-4 gap-2 text-[10px] text-[#52525b] uppercase tracking-wider pb-2 border-b border-white/[0.06]">
                <span>Date</span><span>Duration</span><span>Quality</span><span>Credits</span>
              </div>
              {data.recent_videos.slice(0, 10).map((v, i) => (
                <div key={i} className="grid grid-cols-4 gap-2 py-2 text-xs text-[#a1a1aa] border-b border-white/[0.03] last:border-0">
                  <span>{new Date(v.created_at).toLocaleDateString()}</span>
                  <span>{v.duration}s</span>
                  <span>{v.quality}</span>
                  <span className="text-[#fafafa] font-medium">{v.credits_used}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Image gallery */}
        {data.recent_images.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-4" style={{ fontFamily: "'Outfit', sans-serif" }}>Recent Images</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {data.recent_images.map(img => (
                <div key={img.id} className="aspect-square rounded-xl overflow-hidden bg-[#111111] border border-white/[0.08] group relative" data-testid={`gallery-image-${img.id}`}>
                  <img src={`${API}${img.image_url}`} alt={img.prompt} className="w-full h-full object-cover" crossOrigin="use-credentials" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2">
                    <p className="text-[10px] text-white line-clamp-2">{img.prompt}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {data.recent_images.length === 0 && data.recent_videos.length === 0 && (
          <div className="text-center p-12 rounded-xl bg-[#111111] border border-white/[0.08]">
            <TrendingUp className="w-12 h-12 text-[#52525b] mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2" style={{ fontFamily: "'Outfit', sans-serif" }}>No activity yet</h3>
            <p className="text-sm text-[#a1a1aa]">Start chatting, generating images, and creating videos to see your analytics here.</p>
          </div>
        )}
      </div>
    </div>
  );
}
