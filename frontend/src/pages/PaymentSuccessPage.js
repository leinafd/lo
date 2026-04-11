import { useEffect, useState, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { Loader2, CheckCircle2, XCircle, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

const API = process.env.REACT_APP_BACKEND_URL;

export default function PaymentSuccessPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [status, setStatus] = useState("checking"); // checking, success, failed
  const sessionId = searchParams.get("session_id");

  const pollStatus = useCallback(async (attempts = 0) => {
    const maxAttempts = 5;
    if (!sessionId) {
      setStatus("failed");
      return;
    }
    if (attempts >= maxAttempts) {
      setStatus("failed");
      return;
    }
    try {
      const { data } = await axios.get(`${API}/api/checkout/status/${sessionId}`, { withCredentials: true });
      if (data.payment_status === "paid") {
        setStatus("success");
        await refreshUser();
        return;
      }
      if (data.status === "expired") {
        setStatus("failed");
        return;
      }
      // Keep polling
      setTimeout(() => pollStatus(attempts + 1), 2000);
    } catch {
      if (attempts < maxAttempts - 1) {
        setTimeout(() => pollStatus(attempts + 1), 2000);
      } else {
        setStatus("failed");
      }
    }
  }, [sessionId, refreshUser]);

  useEffect(() => {
    pollStatus();
  }, [pollStatus]);

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center px-6" data-testid="payment-success-page">
      <div className="text-center max-w-md">
        {status === "checking" && (
          <div className="animate-fade-in">
            <Loader2 className="w-12 h-12 text-[#3b82f6] animate-spin mx-auto mb-6" />
            <h1 className="text-2xl font-bold tracking-tight mb-2" style={{ fontFamily: "'Outfit', sans-serif" }}>
              Processing payment...
            </h1>
            <p className="text-[#a1a1aa] text-sm">Please wait while we confirm your subscription.</p>
          </div>
        )}

        {status === "success" && (
          <div className="animate-fade-in">
            <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-6">
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
            </div>
            <h1
              className="text-2xl font-bold tracking-tight mb-2"
              style={{ fontFamily: "'Outfit', sans-serif" }}
              data-testid="payment-success-heading"
            >
              Welcome to Pro!
            </h1>
            <p className="text-[#a1a1aa] text-sm mb-8">
              Your subscription is active. Enjoy unlimited messages and advanced AI capabilities.
            </p>
            <Button
              onClick={() => navigate("/chat")}
              className="bg-[#3b82f6] hover:bg-[#2563eb] text-white h-11 px-8"
              data-testid="go-to-chat-button"
            >
              <Zap className="w-4 h-4 mr-2" />
              Start chatting
            </Button>
          </div>
        )}

        {status === "failed" && (
          <div className="animate-fade-in">
            <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-6">
              <XCircle className="w-8 h-8 text-red-400" />
            </div>
            <h1
              className="text-2xl font-bold tracking-tight mb-2"
              style={{ fontFamily: "'Outfit', sans-serif" }}
              data-testid="payment-failed-heading"
            >
              Payment issue
            </h1>
            <p className="text-[#a1a1aa] text-sm mb-8">
              We couldn't confirm your payment. Please try again or contact support.
            </p>
            <div className="flex gap-3 justify-center">
              <Button
                onClick={() => navigate("/pricing")}
                variant="outline"
                className="bg-white/5 border-white/10 hover:bg-white/10 text-white h-11 px-6"
                data-testid="retry-payment-button"
              >
                Try again
              </Button>
              <Button
                onClick={() => navigate("/chat")}
                className="bg-[#3b82f6] hover:bg-[#2563eb] text-white h-11 px-6"
                data-testid="back-to-chat-button"
              >
                Back to chat
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
