import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { ArrowLeft, Zap, Users, ThumbsUp, ThumbsDown, DollarSign, Shield, Crown, Coins } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

export default function AdminDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const { data: d } = await axios.get(`${API}/api/admin/dashboard`, { withCredentials: true });
        setData(d);
      } catch {
        navigate("/chat");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [navigate]);

  if (loading || !data) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-[#3b82f6] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const stats = [
    { label: "Total Users", value: data.users.total, icon: Users, color: "text-[#3b82f6]", bg: "bg-[#3b82f6]/10" },
    { label: "Free Users", value: data.users.free, icon: Users, color: "text-[#a1a1aa]", bg: "bg-white/5" },
    { label: "Reasoning Pro", value: data.users.pro_reasoning, icon: Crown, color: "text-purple-400", bg: "bg-purple-400/10" },
    { label: "Creative Pro", value: data.users.pro_creative, icon: Crown, color: "text-amber-400", bg: "bg-amber-400/10" },
    { label: "Thumbs Up", value: data.feedback.thumbs_up, icon: ThumbsUp, color: "text-emerald-400", bg: "bg-emerald-400/10" },
    { label: "Thumbs Down", value: data.feedback.thumbs_down, icon: ThumbsDown, color: "text-red-400", bg: "bg-red-400/10" },
    { label: "Subscription Revenue", value: `$${data.revenue.subscriptions}`, icon: DollarSign, color: "text-emerald-400", bg: "bg-emerald-400/10" },
    { label: "Credit Revenue", value: `$${data.revenue.credit_purchases}`, icon: Coins, color: "text-[#3b82f6]", bg: "bg-[#3b82f6]/10" },
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0a]" data-testid="admin-dashboard">
      <nav className="border-b border-white/[0.06] bg-[#0a0a0a]/80 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center gap-2.5">
          <button onClick={() => navigate("/chat")} className="text-[#a1a1aa] hover:text-white transition-colors mr-2" data-testid="admin-back-to-chat">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
            <Shield className="w-4 h-4 text-amber-400" />
          </div>
          <span className="text-sm font-semibold tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>
            Admin Dashboard
          </span>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold tracking-tight mb-8" style={{ fontFamily: "'Outfit', sans-serif" }}>
          Overview
        </h1>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat, i) => {
            const Icon = stat.icon;
            return (
              <div key={i} className="p-4 rounded-xl bg-[#111111] border border-white/[0.08]" data-testid={`admin-stat-${i}`}>
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-9 h-9 rounded-lg ${stat.bg} flex items-center justify-center`}>
                    <Icon className={`w-4 h-4 ${stat.color}`} />
                  </div>
                  <span className="text-xs text-[#a1a1aa] uppercase tracking-[0.1em]">{stat.label}</span>
                </div>
                <p className="text-2xl font-bold tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>
                  {stat.value}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
