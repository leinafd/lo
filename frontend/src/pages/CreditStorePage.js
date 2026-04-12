import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import axios from "axios";
import { ArrowLeft, Zap, Coins, Sparkles, Rocket, Flame } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

const packIcons = { starter: Sparkles, standard: Rocket, power: Flame };

export default function CreditStorePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [packs, setPacks] = useState([]);
  const [currentCredits, setCurrentCredits] = useState(0);
  const [loading, setLoading] = useState(null);

  useEffect(() => {
    const fetchPacks = async () => {
      try {
        const { data } = await axios.get(`${API}/api/credits/packs`, { withCredentials: true });
        setPacks(data.packs);
        setCurrentCredits(data.current_credits);
      } catch { /* ignore */ }
    };
    fetchPacks();
  }, []);

  const handlePurchase = async (packId) => {
    setLoading(packId);
    try {
      const originUrl = window.location.origin;
      const { data } = await axios.post(
        `${API}/api/credits/purchase`,
        { pack_id: packId, origin_url: originUrl },
        { withCredentials: true }
      );
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      console.error("Purchase error:", err);
    } finally {
      setLoading(null);
    }
  };

  const isAllowed = user?.role === "pro_creative" || user?.role === "admin";

  return (
    <div className="min-h-screen bg-[#0a0a0a]" data-testid="credit-store-page">
      {/* Nav */}
      <nav className="border-b border-white/[0.06] bg-[#0a0a0a]/80 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <button onClick={() => navigate("/chat")} className="text-[#a1a1aa] hover:text-white transition-colors mr-2" data-testid="back-to-chat">
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div className="w-8 h-8 rounded-lg bg-[#3b82f6] flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-semibold tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>
              Impulse AI
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Coins className="w-4 h-4 text-[#3b82f6]" />
            <span className="text-sm text-[#fafafa] font-medium" data-testid="current-credit-balance">{currentCredits} credits</span>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <p className="text-xs text-[#3b82f6] uppercase tracking-[0.2em] mb-4 font-medium">Credit Store</p>
          <h1
            className="text-4xl sm:text-5xl font-bold tracking-tight mb-4"
            style={{ fontFamily: "'Outfit', sans-serif" }}
            data-testid="credit-store-heading"
          >
            Video Credits
          </h1>
          <p className="text-[#a1a1aa] text-base max-w-md mx-auto">
            Purchase additional video credits for your Creative Pro account.
          </p>
        </div>

        {!isAllowed ? (
          <div className="text-center p-8 rounded-xl bg-[#111111] border border-white/[0.08]" data-testid="credits-locked">
            <Coins className="w-10 h-10 text-[#52525b] mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2" style={{ fontFamily: "'Outfit', sans-serif" }}>
              Creative Pro Required
            </h3>
            <p className="text-sm text-[#a1a1aa] mb-6">
              Credit top-ups are only available for Creative Pro subscribers.
            </p>
            <Button
              onClick={() => navigate("/pricing")}
              className="bg-[#3b82f6] hover:bg-[#2563eb] text-white h-10 px-6"
              data-testid="upgrade-to-creative"
            >
              Upgrade to Creative Pro
            </Button>
          </div>
        ) : (
          <>
            {/* Credit calculator info */}
            <div className="mb-8 p-4 rounded-xl bg-[#111111] border border-white/[0.08]">
              <h3 className="text-sm font-semibold mb-3 text-[#fafafa]" style={{ fontFamily: "'Outfit', sans-serif" }}>
                Credit Usage
              </h3>
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-white/5 text-center">
                  <p className="text-lg font-bold text-[#fafafa]">1</p>
                  <p className="text-[10px] text-[#a1a1aa] uppercase tracking-wider">1-5 sec</p>
                </div>
                <div className="p-3 rounded-lg bg-white/5 text-center">
                  <p className="text-lg font-bold text-[#fafafa]">2</p>
                  <p className="text-[10px] text-[#a1a1aa] uppercase tracking-wider">6-10 sec</p>
                </div>
                <div className="p-3 rounded-lg bg-white/5 text-center">
                  <p className="text-lg font-bold text-[#fafafa]">3</p>
                  <p className="text-[10px] text-[#a1a1aa] uppercase tracking-wider">11-15 sec</p>
                </div>
              </div>
              <p className="text-xs text-[#52525b] mt-2 text-center">HD quality doubles the credit cost</p>
            </div>

            {/* Pack cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {packs.map((pack) => {
                const Icon = packIcons[pack.id] || Coins;
                const perCredit = (pack.amount / pack.credits).toFixed(2);
                const isBestValue = pack.id === "power";
                return (
                  <div
                    key={pack.id}
                    className={`rounded-xl border p-6 flex flex-col transition-all duration-300 ${
                      isBestValue
                        ? "bg-[#111111] border-[#3b82f6]/40 shadow-[0_0_30px_rgba(59,130,246,0.12)]"
                        : "bg-[#111111] border-white/[0.08] hover:border-white/[0.15]"
                    }`}
                    data-testid={`credit-pack-${pack.id}`}
                  >
                    {isBestValue && (
                      <span className="text-[10px] uppercase tracking-[0.2em] text-[#3b82f6] font-medium mb-3">Best value</span>
                    )}
                    <div className="flex items-center gap-3 mb-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                        isBestValue ? "bg-[#3b82f6]/10 border border-[#3b82f6]/20" : "bg-white/5"
                      }`}>
                        <Icon className={`w-5 h-5 ${isBestValue ? "text-[#3b82f6]" : "text-[#a1a1aa]"}`} />
                      </div>
                      <h3 className="text-lg font-semibold" style={{ fontFamily: "'Outfit', sans-serif" }}>
                        {pack.name}
                      </h3>
                    </div>

                    <div className="mb-2">
                      <span className="text-4xl font-bold tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>
                        ${pack.amount}
                      </span>
                    </div>
                    <p className="text-2xl font-semibold text-[#3b82f6] mb-1">{pack.credits} credits</p>
                    <p className="text-xs text-[#52525b] mb-6">${perCredit} per credit</p>

                    <Button
                      onClick={() => handlePurchase(pack.id)}
                      disabled={loading === pack.id}
                      className={`w-full h-11 font-medium transition-all duration-200 mt-auto ${
                        isBestValue
                          ? "bg-[#3b82f6] hover:bg-[#2563eb] text-white"
                          : "bg-white/5 hover:bg-white/10 text-white border border-white/10"
                      }`}
                      data-testid={`buy-pack-${pack.id}`}
                    >
                      {loading === pack.id ? "Processing..." : "Purchase"}
                    </Button>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
