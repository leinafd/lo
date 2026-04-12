import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Plus, MessageSquare, Trash2, Zap, LogOut, Crown, X, Image, Video, Coins, Shield } from "lucide-react";

export default function ChatSidebar({ chats, activeChatId, onSelectChat, onNewChat, onDeleteChat, usage, onNavigatePricing, onNavigateCredits, onNavigateAdmin, onClose }) {
  const { user, logout } = useAuth();
  const role = usage.role || "free";
  const isFree = role === "free";
  const isAdmin = role === "admin";

  const msgLimit = usage.daily_message_limit;
  const msgCount = usage.daily_message_count || 0;
  const msgPercent = msgLimit ? Math.min((msgCount / msgLimit) * 100, 100) : 0;

  const imgLimit = usage.daily_image_limit;
  const imgCount = usage.daily_image_count || 0;
  const vidLimit = usage.daily_video_limit;
  const vidCount = usage.daily_video_count || 0;

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
      <div className="p-3 space-y-2 shrink-0 border-t border-white/[0.06]">
        {isFree ? (
          <div className="p-3 rounded-xl bg-white/5 border border-white/[0.08] space-y-3" data-testid="usage-counter">
            {/* Messages */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-[#a1a1aa] uppercase tracking-[0.15em] flex items-center gap-1">
                  <MessageSquare className="w-3 h-3" /> Messages
                </span>
                <span className="text-[10px] text-[#fafafa] font-medium">{msgCount}/{msgLimit}</span>
              </div>
              <Progress value={msgPercent} className="h-1 bg-white/10" data-testid="msg-progress" />
            </div>
            {/* Images */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-[#a1a1aa] uppercase tracking-[0.15em] flex items-center gap-1">
                  <Image className="w-3 h-3" /> Images
                </span>
                <span className="text-[10px] text-[#fafafa] font-medium">{imgCount}/{imgLimit}</span>
              </div>
              <Progress value={imgLimit ? (imgCount / imgLimit) * 100 : 0} className="h-1 bg-white/10" />
            </div>
            {/* Videos */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-[#a1a1aa] uppercase tracking-[0.15em] flex items-center gap-1">
                  <Video className="w-3 h-3" /> Videos
                </span>
                <span className="text-[10px] text-[#fafafa] font-medium">{vidCount}/{vidLimit}</span>
              </div>
              <Progress value={vidLimit ? (vidCount / vidLimit) * 100 : 0} className="h-1 bg-white/10" />
            </div>
            <Button
              onClick={onNavigatePricing}
              size="sm"
              className="w-full h-7 bg-[#3b82f6] hover:bg-[#2563eb] text-white text-xs"
              data-testid="upgrade-button"
            >
              <Crown className="w-3 h-3 mr-1.5" />
              Upgrade to Pro
            </Button>
          </div>
        ) : isAdmin ? (
          <div className="space-y-2">
            <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20" data-testid="admin-badge">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-amber-400" />
                <span className="text-sm font-medium text-[#fafafa]">Admin</span>
              </div>
              <p className="text-xs text-[#a1a1aa] mt-1">All limits bypassed</p>
            </div>
            <Button
              onClick={onNavigateAdmin}
              size="sm"
              variant="outline"
              className="w-full h-7 bg-white/5 border-white/10 hover:bg-white/10 text-white text-xs"
              data-testid="admin-dashboard-button"
            >
              <Shield className="w-3 h-3 mr-1.5" />
              Dashboard
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="p-3 rounded-xl bg-[#3b82f6]/5 border border-[#3b82f6]/20" data-testid="pro-badge">
              <div className="flex items-center gap-2">
                <Crown className="w-4 h-4 text-[#3b82f6]" />
                <span className="text-sm font-medium text-[#fafafa]">
                  {role === "pro_reasoning" ? "Reasoning Pro" : "Creative Pro"}
                </span>
              </div>
              <p className="text-xs text-[#a1a1aa] mt-1">Unlimited messages</p>
              {/* Show daily limits for Reasoning Pro */}
              {role === "pro_reasoning" && (
                <div className="mt-2 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-[#a1a1aa] flex items-center gap-1"><Image className="w-3 h-3" /> Images</span>
                    <span className="text-[10px] text-[#fafafa]">{imgCount}/{imgLimit}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-[#a1a1aa] flex items-center gap-1"><Video className="w-3 h-3" /> Videos</span>
                    <span className="text-[10px] text-[#fafafa]">{vidCount}/{vidLimit}</span>
                  </div>
                </div>
              )}
              {/* Show credits for Creative Pro */}
              {role === "pro_creative" && (
                <div className="mt-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-[#a1a1aa] flex items-center gap-1"><Coins className="w-3 h-3" /> Video Credits</span>
                    <span className="text-[10px] text-[#fafafa] font-medium">{usage.video_credits || 0}</span>
                  </div>
                  <Button
                    onClick={onNavigateCredits}
                    size="sm"
                    variant="outline"
                    className="w-full mt-2 h-6 bg-white/5 border-white/10 hover:bg-white/10 text-white text-[10px]"
                    data-testid="buy-credits-button"
                  >
                    <Coins className="w-3 h-3 mr-1" />
                    Buy Credits
                  </Button>
                </div>
              )}
            </div>
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
