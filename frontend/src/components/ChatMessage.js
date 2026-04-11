import { useState } from "react";
import axios from "axios";
import { useAuth } from "@/contexts/AuthContext";
import { ThumbsUp, ThumbsDown, User, Zap } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

export default function ChatMessage({ message }) {
  const { user } = useAuth();
  const [feedback, setFeedback] = useState(null);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const isUser = message.role === "user";

  const submitFeedback = async (rating) => {
    if (feedbackLoading) return;
    setFeedbackLoading(true);
    try {
      await axios.post(
        `${API}/api/feedback`,
        { message_id: message.id, rating },
        { withCredentials: true }
      );
      setFeedback(rating);
    } catch { /* ignore */ }
    setFeedbackLoading(false);
  };

  return (
    <div className={`flex gap-3 py-4 animate-fade-in ${isUser ? "justify-end" : ""}`} data-testid={`chat-message-${message.role}`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-lg bg-[#3b82f6]/10 border border-[#3b82f6]/20 flex items-center justify-center shrink-0 mt-0.5">
          <Zap className="w-3.5 h-3.5 text-[#3b82f6]" />
        </div>
      )}

      <div className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={
            isUser
              ? "bg-[#3b82f6]/10 border border-[#3b82f6]/20 text-[#fafafa] rounded-2xl rounded-tr-sm px-4 py-3 max-w-[80%]"
              : "text-[#e4e4e7] rounded-2xl rounded-tl-sm px-4 py-3 max-w-[85%]"
          }
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Feedback buttons for AI messages */}
        {!isUser && message.id && message.id !== "temp-user" && (
          <div className="flex items-center gap-1 mt-1.5 ml-1" data-testid={`feedback-actions-${message.id}`}>
            <button
              onClick={() => submitFeedback("up")}
              disabled={feedbackLoading}
              className={`p-1.5 rounded-md transition-all duration-200 ${
                feedback === "up"
                  ? "text-emerald-400 bg-emerald-400/10"
                  : "text-[#52525b] hover:text-[#a1a1aa] hover:bg-white/5"
              }`}
              data-testid={`feedback-up-${message.id}`}
            >
              <ThumbsUp className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => submitFeedback("down")}
              disabled={feedbackLoading}
              className={`p-1.5 rounded-md transition-all duration-200 ${
                feedback === "down"
                  ? "text-red-400 bg-red-400/10"
                  : "text-[#52525b] hover:text-[#a1a1aa] hover:bg-white/5"
              }`}
              data-testid={`feedback-down-${message.id}`}
            >
              <ThumbsDown className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-7 h-7 rounded-lg bg-white/10 flex items-center justify-center shrink-0 mt-0.5">
          <User className="w-3.5 h-3.5 text-[#a1a1aa]" />
        </div>
      )}
    </div>
  );
}
