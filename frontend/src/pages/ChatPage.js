import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "@/contexts/AuthContext";
import ChatSidebar from "@/components/ChatSidebar";
import ChatMessage from "@/components/ChatMessage";
import OnboardingModal from "@/components/OnboardingModal";
import { Button } from "@/components/ui/button";
import { Send, Loader2, Plus, Menu, X, Image } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

export default function ChatPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [generatingImage, setGeneratingImage] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [usage, setUsage] = useState({ daily_message_count: 0, daily_message_limit: 20, role: "free" });
  const [showOnboarding, setShowOnboarding] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchChats = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/api/chat/list`, { withCredentials: true });
      setChats(data);
    } catch { /* ignore */ }
  }, []);

  const fetchUsage = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/api/user/usage`, { withCredentials: true });
      setUsage(data);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    fetchChats();
    fetchUsage();
  }, [fetchChats, fetchUsage]);

  // Show onboarding for first-time users
  useEffect(() => {
    if (user && user.is_first_login) {
      setShowOnboarding(true);
    }
  }, [user]);

  const loadChat = async (chatId) => {
    setActiveChatId(chatId);
    setSidebarOpen(false);
    try {
      const { data } = await axios.get(`${API}/api/chat/${chatId}/messages`, { withCredentials: true });
      setMessages(data);
    } catch { /* ignore */ }
  };

  const startNewChat = () => {
    setActiveChatId(null);
    setMessages([]);
    setSidebarOpen(false);
  };

  const deleteChat = async (chatId) => {
    try {
      await axios.delete(`${API}/api/chat/${chatId}`, { withCredentials: true });
      if (activeChatId === chatId) {
        setActiveChatId(null);
        setMessages([]);
      }
      fetchChats();
    } catch { /* ignore */ }
  };

  const sendMessage = async () => {
    if (!input.trim() || sending) return;
    const content = input.trim();
    setInput("");
    setSending(true);

    // Optimistic user message
    const tempUserMsg = { id: "temp-user", role: "user", content, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const { data } = await axios.post(
        `${API}/api/chat/send`,
        { content, chat_id: activeChatId },
        { withCredentials: true }
      );

      // Replace temp message and add AI response
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== "temp-user");
        return [
          ...filtered,
          { id: data.user_message.id, role: "user", content: data.user_message.content, created_at: new Date().toISOString() },
          { id: data.ai_message.id, role: "assistant", content: data.ai_message.content, created_at: new Date().toISOString() },
        ];
      });

      if (!activeChatId) {
        setActiveChatId(data.chat_id);
      }

      // Update usage
      if (data.daily_message_count !== null && data.daily_message_count !== undefined) {
        setUsage((prev) => ({ ...prev, daily_message_count: data.daily_message_count }));
      }

      fetchChats();
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== "temp-user"));
      const detail = err.response?.data?.detail;
      if (typeof detail === "string" && detail.includes("Daily message limit")) {
        setUsage((prev) => ({ ...prev, daily_message_count: prev.daily_message_limit || 20 }));
      }
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const generateImage = async () => {
    if (!input.trim() || generatingImage) return;
    const prompt = input.trim();
    setInput("");
    setGeneratingImage(true);

    const tempUserMsg = { id: "temp-img", role: "user", content: `Generate image: ${prompt}`, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const { data } = await axios.post(
        `${API}/api/image/generate`,
        { prompt, chat_id: activeChatId },
        { withCredentials: true }
      );

      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== "temp-img");
        return [
          ...filtered,
          { id: `user-img-${Date.now()}`, role: "user", content: `Generate image: ${prompt}`, created_at: new Date().toISOString() },
          { id: `ai-img-${Date.now()}`, role: "assistant", content: data.text || "", image_url: data.image_url, type: "image", created_at: new Date().toISOString() },
        ];
      });

      fetchUsage();
      fetchChats();
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== "temp-img"));
      const detail = err.response?.data?.detail;
      if (typeof detail === "string" && detail.includes("limit")) {
        fetchUsage();
      }
    } finally {
      setGeneratingImage(false);
    }
  };

  const isLimitReached = usage.daily_message_limit !== null && usage.daily_message_limit !== undefined && usage.daily_message_count >= usage.daily_message_limit;

  return (
    <div className="h-screen bg-[#0a0a0a] flex overflow-hidden" data-testid="chat-page">
      {showOnboarding && <OnboardingModal onClose={() => setShowOnboarding(false)} />}
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/60 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <div className={`
        fixed lg:relative z-50 lg:z-auto
        w-[280px] h-full
        transform transition-transform duration-200
        ${sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
      `}>
        <ChatSidebar
          chats={chats}
          activeChatId={activeChatId}
          onSelectChat={loadChat}
          onNewChat={startNewChat}
          onDeleteChat={deleteChat}
          usage={usage}
          onNavigatePricing={() => navigate("/pricing")}
          onNavigateCredits={() => navigate("/credits")}
          onNavigateAdmin={() => navigate("/admin")}
          onNavigateVideos={() => navigate("/videos")}
          onNavigateAvatars={() => navigate("/avatars")}
          onNavigateAnalytics={() => navigate("/analytics")}
          onClose={() => setSidebarOpen(false)}
        />
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <div className="h-14 border-b border-white/[0.06] bg-[#0a0a0a]/80 backdrop-blur-xl flex items-center px-4 gap-3 shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden text-[#a1a1aa] hover:text-white transition-colors"
            data-testid="mobile-menu-button"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400" />
            <span className="text-sm text-[#a1a1aa]">
              {activeChatId ? "Active conversation" : "New conversation"}
            </span>
          </div>
          {usage.role !== "free" && usage.role !== "admin" && (
            <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-[#3b82f6]/10 text-[#3b82f6] border border-[#3b82f6]/20">
              {usage.role === "pro_reasoning" ? "Reasoning Pro" : "Creative Pro"}
            </span>
          )}
          {usage.role === "admin" && (
            <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Admin
            </span>
          )}
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto" data-testid="empty-chat-state">
              <div className="w-14 h-14 rounded-2xl bg-[#3b82f6]/10 border border-[#3b82f6]/20 flex items-center justify-center mb-6">
                <Send className="w-6 h-6 text-[#3b82f6]" />
              </div>
              <h2 className="text-xl font-semibold tracking-tight mb-2" style={{ fontFamily: "'Outfit', sans-serif" }}>
                Start a conversation
              </h2>
              <p className="text-[#52525b] text-sm leading-relaxed">
                Send a message to begin. Impulse AI is powered by Claude for intelligent conversations.
              </p>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-1">
              {messages.map((msg, i) => (
                <ChatMessage key={msg.id || i} message={msg} />
              ))}
              {(sending || generatingImage) && (
                <div className="flex gap-3 py-4 animate-fade-in">
                  <div className="w-7 h-7 rounded-lg bg-[#3b82f6]/10 border border-[#3b82f6]/20 flex items-center justify-center shrink-0 mt-0.5">
                    <Loader2 className="w-3.5 h-3.5 text-[#3b82f6] animate-spin" />
                  </div>
                  <div className="flex items-center gap-1.5 pt-1">
                    <span className="text-xs text-[#52525b]">{generatingImage ? "Generating image..." : "Thinking..."}</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="shrink-0 px-4 pb-4 pt-2">
          {isLimitReached && (
            <div className="max-w-3xl mx-auto mb-3 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-sm flex items-center justify-between" data-testid="limit-reached-banner">
              <span>Daily message limit reached. Upgrade for unlimited.</span>
              <Button
                onClick={() => navigate("/pricing")}
                size="sm"
                className="bg-[#3b82f6] hover:bg-[#2563eb] text-white text-xs h-7 px-3"
                data-testid="upgrade-from-limit-banner"
              >
                Upgrade
              </Button>
            </div>
          )}
          <div className="max-w-3xl mx-auto">
            <div className="bg-[#111111] border border-white/[0.08] rounded-xl p-2 flex items-end gap-2 shadow-2xl">
              <textarea
                ref={textareaRef}
                data-testid="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={isLimitReached ? "Message limit reached..." : "Message Impulse AI..."}
                disabled={isLimitReached || sending || generatingImage}
                rows={1}
                className="flex-1 bg-transparent border-none outline-none resize-none text-[#fafafa] placeholder:text-[#52525b] text-sm py-2 px-2 max-h-32 min-h-[36px]"
                style={{ fontFamily: "'Manrope', sans-serif" }}
              />
              <Button
                data-testid="generate-image-button"
                onClick={generateImage}
                disabled={!input.trim() || sending || generatingImage || isLimitReached}
                size="icon"
                title="Generate image"
                className="w-9 h-9 bg-white/5 hover:bg-white/10 text-[#a1a1aa] hover:text-white border border-white/10 rounded-lg shrink-0 disabled:opacity-30 transition-all duration-200"
              >
                {generatingImage ? <Loader2 className="w-4 h-4 animate-spin" /> : <Image className="w-4 h-4" />}
              </Button>
              <Button
                data-testid="send-message-button"
                onClick={sendMessage}
                disabled={!input.trim() || sending || generatingImage || isLimitReached}
                size="icon"
                className="w-9 h-9 bg-[#3b82f6] hover:bg-[#2563eb] text-white rounded-lg shrink-0 disabled:opacity-30 transition-all duration-200"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
            <p className="text-[10px] text-[#52525b] text-center mt-2">
              Impulse AI is powered by Claude. Image generation by Gemini.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
