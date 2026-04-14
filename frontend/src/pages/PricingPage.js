import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import axios from "axios";
import { Check, Zap, Brain, Palette, ArrowLeft } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

const plans = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    period: "/month",
    description: "Get started with basic AI capabilities",
    features: [
      "20 messages per day",
      "2 images per day",
      "1 video per day (first 7 days only)",
      "5s max, standard quality, watermarked",
      "Chat history",
    ],
    cta: "Current plan",
    icon: Zap,
    featured: false,
  },
  {
    id: "pro_reasoning",
    name: "Reasoning Pro",
    price: "$19",
    period: "/month",
    description: "Advanced reasoning with video credits",
    features: [
      "Unlimited messages",
      "10 images per day",
      "20 video credits per month",
      "Up to 10s, standard + HD",
      "No watermark",
      "Credit top-up store",
    ],
    cta: "Subscribe",
    icon: Brain,
    featured: false,
  },
  {
    id: "pro_creative",
    name: "Creative Pro",
    price: "$39",
    period: "/month",
    description: "Full creative suite, unlimited generation",
    features: [
      "Unlimited messages",
      "Unlimited images",
      "50 video credits per month",
      "Up to 15s, HD quality",
      "No watermark",
      "Credit top-up store",
      "Priority support",
    ],
    cta: "Subscribe",
    icon: Palette,
    featured: true,
  },
];

export default function PricingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleSubscribe = async (planId) => {
    if (planId === "free") return;
    if (!user) {
      navigate("/login");
      return;
    }
    try {
      const originUrl = window.location.origin;
      const { data } = await axios.post(
        `${API}/api/checkout/create`,
        { plan: planId, origin_url: originUrl },
        { withCredentials: true }
      );
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      console.error("Checkout error:", err);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] relative" data-testid="pricing-page">
      {/* Subtle background */}
      <div
        className="fixed inset-0 opacity-[0.08] pointer-events-none"
        style={{
          backgroundImage: "url('https://images.unsplash.com/photo-1692125440608-4364afbf849b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwyfHxkYXJrJTIwbW9kZSUyMGFic3RyYWN0JTIwZ2VvbWV0cnklMjBibHVlfGVufDB8fHx8MTc3NTkwNjI0MXww&ixlib=rb-4.1.0&q=85')",
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />

      <div className="relative z-10">
        {/* Nav */}
        <nav className="border-b border-white/[0.06] bg-[#0a0a0a]/80 backdrop-blur-xl">
          <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
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
            {user && (
              <span className="text-xs text-[#52525b]">{user.email}</span>
            )}
          </div>
        </nav>

        {/* Header */}
        <div className="text-center py-16 px-6">
          <p className="text-xs text-[#3b82f6] uppercase tracking-[0.2em] mb-4 font-medium">Pricing</p>
          <h1
            className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-4"
            style={{ fontFamily: "'Outfit', sans-serif" }}
            data-testid="pricing-heading"
          >
            Choose your plan
          </h1>
          <p className="text-[#a1a1aa] text-base sm:text-lg max-w-md mx-auto">
            Upgrade for unlimited messages and access to advanced AI models.
          </p>
        </div>

        {/* Plans grid */}
        <div className="max-w-5xl mx-auto px-6 pb-24 grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan) => {
            const Icon = plan.icon;
            const isCurrentPlan = user?.role === plan.id || (user?.role === "free" && plan.id === "free");
            return (
              <div
                key={plan.id}
                className={`rounded-xl border p-6 flex flex-col transition-all duration-300 ${
                  plan.featured
                    ? "bg-[#111111] border-[#3b82f6]/40 shadow-[0_0_30px_rgba(59,130,246,0.12)] animate-pulse-glow"
                    : "bg-[#111111] border-white/[0.08] hover:border-white/[0.15]"
                }`}
                data-testid={`pricing-card-${plan.id}`}
              >
                {plan.featured && (
                  <span className="text-[10px] uppercase tracking-[0.2em] text-[#3b82f6] font-medium mb-4">
                    Most popular
                  </span>
                )}
                <div className="flex items-center gap-3 mb-4">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    plan.featured ? "bg-[#3b82f6]/10 border border-[#3b82f6]/20" : "bg-white/5"
                  }`}>
                    <Icon className={`w-5 h-5 ${plan.featured ? "text-[#3b82f6]" : "text-[#a1a1aa]"}`} />
                  </div>
                  <h3 className="text-lg font-semibold" style={{ fontFamily: "'Outfit', sans-serif" }}>
                    {plan.name}
                  </h3>
                </div>

                <div className="mb-4">
                  <span className="text-4xl font-bold tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>
                    {plan.price}
                  </span>
                  <span className="text-[#52525b] text-sm">{plan.period}</span>
                </div>

                <p className="text-sm text-[#a1a1aa] mb-6">{plan.description}</p>

                <ul className="space-y-3 mb-8 flex-1">
                  {plan.features.map((f, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm">
                      <Check className={`w-4 h-4 shrink-0 mt-0.5 ${plan.featured ? "text-[#3b82f6]" : "text-emerald-400"}`} />
                      <span className="text-[#e4e4e7]">{f}</span>
                    </li>
                  ))}
                </ul>

                <Button
                  onClick={() => handleSubscribe(plan.id)}
                  disabled={isCurrentPlan}
                  className={`w-full h-11 font-medium transition-all duration-200 ${
                    plan.featured
                      ? "bg-[#3b82f6] hover:bg-[#2563eb] text-white"
                      : isCurrentPlan
                        ? "bg-white/5 text-[#52525b] cursor-default"
                        : "bg-white/5 hover:bg-white/10 text-white border border-white/10"
                  }`}
                  data-testid={`subscribe-${plan.id}`}
                >
                  {isCurrentPlan ? "Current plan" : plan.cta}
                </Button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
