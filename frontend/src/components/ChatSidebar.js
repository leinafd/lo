import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Plus, MessageSquare, Trash2, Zap, LogOut, Crown, X } from "lucide-react";

export default function ChatSidebar({ chats, activeChatId, onSelectChat, onNewChat, onDeleteChat, usage, onNavigatePricing, onClose }) {
  const { user, logout } = useAuth();
  const isFree = usage.role === "free";
  const usagePercent = isFree ? Math.min((usage.daily_message_count / (usage.daily_limit || 10)) * 100, 100) : 0;

  return (
    <div className="h-full bg-[#111111] border-r border-white/[0.06] flex flex-col" data-testid="chat-sidebar">
      {/* Header */}
      <div className="p-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#3b82f6] flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-semibold tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>
            Impulse AI
          </span>
        </div>
        <button
          onClick={onClose}
          className="lg:hidden text-[#52525b] hover:text-white transition-colors"
          data-testid="close-sidebar-button"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* New Chat button */}
      <div className="px-3 mb-2 shrink-0">
        <Button
          onClick={onNewChat}
          variant="outline"
          className="w-full h-9 bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20 text-[#fafafa] text-sm justify-start gap-2 transition-all duration-200"
          data-testid="new-chat-button"
        >
          <Plus className="w-4 h-4" />
          New chat
        </Button>
      </div>

      {/* Chat list */}
      <ScrollArea className="flex-1 px-2">
        <div className="space-y-0.5 py-1">
          {chats.length === 0 ? (
            <p className="text-xs text-[#52525b] px-2 py-4 text-center">No conversations yet</p>
          ) : (
            chats.map((chat) => (
              <div
                key={chat.id}
                className={`group flex items-center gap-2 px-2.5 py-2 rounded-lg cursor-pointer transition-all duration-150 ${
                  activeChatId === chat.id
                    ? "bg-white/10 text-white"
                    : "text-[#a1a1aa] hover:bg-white/5 hover:text-white"
                }`}
                onClick={() => onSelectChat(chat.id)}
                data-testid={`chat-item-${chat.id}`}
              >
                <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                <span className="text-sm truncate flex-1">{chat.title}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); onDeleteChat(chat.id); }}
                  className="opacity-0 group-hover:opacity-100 text-[#52525b] hover:text-red-400 transition-all duration-150 p-0.5"
                  data-testid={`delete-chat-${chat.id}`}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Usage & Plan */}
      <div className="p-3 space-y-3 shrink-0 border-t border-white/[0.06]">
        {isFree ? (
          <div className="p-3 rounded-xl bg-white/5 border border-white/[0.08]" data-testid="usage-counter">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-[#a1a1aa] uppercase tracking-[0.15em]">Daily usage</span>
              <span className="text-xs text-[#fafafa] font-medium">
                {usage.daily_message_count} of {usage.daily_limit || 10}
              </span>
            </div>
            <Progress
              value={usagePercent}
              className="h-1.5 bg-white/10"
              data-testid="usage-progress-bar"
            />
            <Button
              onClick={onNavigatePricing}
              size="sm"
              className="w-full mt-3 h-8 bg-[#3b82f6] hover:bg-[#2563eb] text-white text-xs"
              data-testid="upgrade-button"
            >
              <Crown className="w-3 h-3 mr-1.5" />
              Upgrade to Pro
            </Button>
          </div>
        ) : (
          <div className="p-3 rounded-xl bg-[#3b82f6]/5 border border-[#3b82f6]/20" data-testid="pro-badge">
            <div className="flex items-center gap-2">
              <Crown className="w-4 h-4 text-[#3b82f6]" />
              <span className="text-sm font-medium text-[#fafafa]">
                {usage.role === "pro_reasoning" ? "Reasoning Pro" : "Creative Pro"}
              </span>
            </div>
            <p className="text-xs text-[#a1a1aa] mt-1">Unlimited messages</p>
          </div>
        )}

        {/* User info & logout */}
        <div className="flex items-center gap-2 px-1">
          <div className="w-7 h-7 rounded-full bg-white/10 flex items-center justify-center text-xs text-[#a1a1aa] font-medium">
            {(user?.name || user?.email || "U")[0].toUpperCase()}
          </div>
          <span className="text-xs text-[#a1a1aa] truncate flex-1">{user?.email}</span>
          <button
            onClick={logout}
            className="text-[#52525b] hover:text-red-400 transition-colors p-1"
            data-testid="logout-button"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
