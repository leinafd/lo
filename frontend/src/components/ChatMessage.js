import { useState } from "react";
import axios from "axios";
import { useAuth } from "@/contexts/AuthContext";
import { ThumbsUp, ThumbsDown, User, Zap, Download } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

export default function ChatMessage({ message }) {
  const { user } = useAuth();
  const [feedback, setFeedback] = useState(null);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);
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

  // Check if message contains an image
  const hasImage = message.image_url || message.type === "image" || (message.image_path && !isUser);
  const imageUrl = message.image_url || (message.image_path ? `${API}${message.image_path.startsWith("/") ? "" : "/api/files/"}${message.image_path}` : null);

  // Parse markdown image from content
  const contentImageMatch = message.content?.match(/!\[.*?\]\((\/api\/files\/[^)]+)\)/);
  const parsedImageUrl = contentImageMatch ? `${API}${contentImageMatch[1]}` : null;
  const displayImageUrl = imageUrl || parsedImageUrl;
  const textContent = message.content?.replace(/!\[.*?\]\([^)]+\)\n*/g, "").trim();

  return (
    <div className={`flex gap-3 py-4 animate-fade-in ${isUser ? "justify-end" : ""}`} data-testid={`chat-message-${message.role}`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-lg bg-[#3b82f6]/10 border border-[#3b82f6]/20 flex items-center justify-center shrink-0 mt-0.5">
          <Zap className="w-3.5 h-3.5 text-[#3b82f6]" />
        </div>
      )}

      <div className={`flex flex-col ${isUser ? "items-end" : "items-start"} max-w-[85%]`}>
        {/* Image display */}
        {displayImageUrl && !isUser && (
          <div className="mb-2 rounded-xl overflow-hidden border border-white/[0.08] relative group">
            {imageLoading && (
              <div className="w-64 h-64 bg-[#111111] animate-pulse flex items-center justify-center">
                <span className="text-xs text-[#52525b]">Loading image...</span>
              </div>
            )}
            <img
              src={displayImageUrl}
              alt="Generated"
              className={`max-w-sm rounded-xl ${imageLoading ? "hidden" : ""}`}
              onLoad={() => setImageLoading(false)}
              onError={() => setImageLoading(false)}
              crossOrigin="use-credentials"
              data-testid="generated-image"
            />
            <a
              href={displayImageUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 text-white opacity-0 group-hover:opacity-100 transition-opacity"
              data-testid="download-image"
            >
              <Download className="w-3.5 h-3.5" />
            </a>
          </div>
        )}

        {/* Text content */}
        {(textContent || (!displayImageUrl && message.content)) && (
          <div
            className={
              isUser
                ? "bg-[#3b82f6]/10 border border-[#3b82f6]/20 text-[#fafafa] rounded-2xl rounded-tr-sm px-4 py-3"
                : "text-[#e4e4e7] rounded-2xl rounded-tl-sm px-4 py-3"
            }
          >
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{textContent || message.content}</p>
          </div>
        )}

        {/* Feedback buttons for AI messages */}
        {!isUser && message.id && !message.id.startsWith("temp-") && (
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
