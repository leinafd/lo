import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import axios from "axios";
import { Zap, X, Copy, Check } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

const PROMPT_TEXT = `Summarise everything you know about me -- my goals, preferences, communication style, and any projects we've worked on together.`;

export default function OnboardingModal({ onClose }) {
  const { user, refreshUser } = useAuth();
  const [step, setStep] = useState(1);
  const [memoryText, setMemoryText] = useState("");
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const isFree = user?.role === "free";

  const copyPrompt = () => {
    navigator.clipboard.writeText(PROMPT_TEXT);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = async () => {
    if (!memoryText.trim()) { onClose(); return; }
    setSaving(true);
    try {
      await axios.post(`${API}/api/user/memory`, { memory_text: memoryText.trim() }, { withCredentials: true });
      await refreshUser();
    } catch {}
    setSaving(false);
    onClose();
  };

  const handleSkip = async () => {
    try {
      await axios.post(`${API}/api/user/memory`, { memory_text: "" }, { withCredentials: true });
      await refreshUser();
    } catch {}
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4" data-testid="onboarding-modal">
      <div className="w-full max-w-lg bg-[#111111] border border-white/[0.08] rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-white/[0.06] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#3b82f6] flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>
                Let's Set Up Your Impulse
              </h2>
              <p className="text-xs text-[#52525b]">Step {step} of 2</p>
            </div>
          </div>
          <button onClick={handleSkip} className="text-[#52525b] hover:text-white transition-colors" data-testid="onboarding-skip">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">
          {step === 1 ? (
            <div className="space-y-4">
              <p className="text-sm text-[#a1a1aa] leading-relaxed">
                To personalize your experience, paste this prompt into your favorite AI (ChatGPT, Claude, etc.) and copy the response back here.
              </p>
              <div className="p-4 rounded-xl bg-white/5 border border-white/[0.08] relative group">
                <p className="text-sm text-[#e4e4e7] leading-relaxed pr-8">{PROMPT_TEXT}</p>
                <button
                  onClick={copyPrompt}
                  className="absolute top-3 right-3 p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                  data-testid="copy-prompt-button"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-[#52525b]" />}
                </button>
              </div>
              <Button onClick={() => setStep(2)} className="w-full h-10 bg-[#3b82f6] hover:bg-[#2563eb] text-white" data-testid="onboarding-next">
                I've got my summary
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-[#a1a1aa] leading-relaxed">
                Paste your AI-generated summary below. This seeds your personal memory so Impulse can understand you better.
              </p>
              {isFree && (
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-400">
                  Free plan: Memory won't persist across sessions. Upgrade to Pro for persistent memory.
                </div>
              )}
              <textarea
                data-testid="memory-input"
                value={memoryText}
                onChange={(e) => setMemoryText(e.target.value)}
                placeholder="Paste your summary here..."
                rows={6}
                className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-sm text-[#fafafa] placeholder:text-[#52525b] focus:border-[#3b82f6] focus:ring-1 focus:ring-[#3b82f6] outline-none resize-none"
              />
              <div className="flex gap-3">
                <Button onClick={() => setStep(1)} variant="outline" className="flex-1 h-10 bg-white/5 border-white/10 hover:bg-white/10 text-white" data-testid="onboarding-back">
                  Back
                </Button>
                <Button onClick={handleSave} disabled={saving} className="flex-1 h-10 bg-[#3b82f6] hover:bg-[#2563eb] text-white" data-testid="onboarding-save">
                  {saving ? "Saving..." : "Save & Start"}
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
