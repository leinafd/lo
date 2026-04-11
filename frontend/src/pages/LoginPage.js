import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Zap, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const result = await login(email, password);
    setLoading(false);
    if (result.success) {
      navigate("/chat");
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex">
      {/* Left visual panel */}
      <div className="hidden lg:flex lg:w-[45%] relative overflow-hidden items-center justify-center">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: "url('https://images.pexels.com/photos/36025191/pexels-photo-36025191.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940')" }}
        />
        <div className="absolute inset-0 bg-black/50" />
        <div className="relative z-10 px-12 text-center">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-[#3b82f6] flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="text-2xl font-bold tracking-tight text-white" style={{ fontFamily: "'Outfit', sans-serif" }}>
              Impulse AI
            </span>
          </div>
          <p className="text-white/70 text-lg max-w-sm mx-auto leading-relaxed">
            Your intelligent assistant powered by next-generation reasoning.
          </p>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-10">
            <div className="w-9 h-9 rounded-lg bg-[#3b82f6] flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>
              Impulse AI
            </span>
          </div>

          <h1
            className="text-3xl sm:text-4xl font-bold tracking-tight mb-2"
            style={{ fontFamily: "'Outfit', sans-serif" }}
            data-testid="login-heading"
          >
            Welcome back
          </h1>
          <p className="text-[#a1a1aa] mb-8">Sign in to continue to Impulse AI</p>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm" data-testid="login-error">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-[#a1a1aa] mb-1.5 uppercase tracking-[0.2em]">Email</label>
              <Input
                data-testid="login-email-input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="bg-white/5 border-white/10 h-11 text-white placeholder:text-[#52525b] focus:border-[#3b82f6] focus:ring-1 focus:ring-[#3b82f6]"
              />
            </div>
            <div>
              <label className="block text-sm text-[#a1a1aa] mb-1.5 uppercase tracking-[0.2em]">Password</label>
              <div className="relative">
                <Input
                  data-testid="login-password-input"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  className="bg-white/5 border-white/10 h-11 text-white placeholder:text-[#52525b] focus:border-[#3b82f6] focus:ring-1 focus:ring-[#3b82f6] pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#52525b] hover:text-[#a1a1aa] transition-colors"
                  data-testid="toggle-password-visibility"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <Button
              data-testid="login-submit-button"
              type="submit"
              disabled={loading}
              className="w-full h-11 bg-[#3b82f6] hover:bg-[#2563eb] text-white font-medium transition-all duration-200"
            >
              {loading ? "Signing in..." : "Sign in"}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-[#a1a1aa]">
            Don't have an account?{" "}
            <Link to="/register" className="text-[#3b82f6] hover:text-[#60a5fa] transition-colors" data-testid="go-to-register">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
