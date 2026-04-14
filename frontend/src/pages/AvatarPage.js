import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ArrowLeft, Zap, UserCircle, Plus, Trash2, Upload, Crown } from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

export default function AvatarPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [avatars, setAvatars] = useState([]);
  const [limit, setLimit] = useState(1);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [faceFile, setFaceFile] = useState(null);
  const [bodyFile, setBodyFile] = useState(null);
  const [showForm, setShowForm] = useState(false);

  const fetchAvatars = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/api/avatars`, { withCredentials: true });
      setAvatars(data.avatars);
      setLimit(data.limit);
    } catch {}
  }, []);

  useEffect(() => { fetchAvatars(); }, [fetchAvatars]);

  const handleCreate = async () => {
    if (creating) return;
    setCreating(true);
    try {
      const form = new FormData();
      form.append("name", name || `Avatar ${avatars.length + 1}`);
      if (faceFile) form.append("face_photo", faceFile);
      if (bodyFile) form.append("body_photo", bodyFile);
      await axios.post(`${API}/api/avatars`, form, { withCredentials: true, headers: { "Content-Type": "multipart/form-data" } });
      setShowForm(false);
      setName("");
      setFaceFile(null);
      setBodyFile(null);
      fetchAvatars();
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/api/avatars/${id}`, { withCredentials: true });
      fetchAvatars();
    } catch {}
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a]" data-testid="avatar-page">
      <nav className="border-b border-white/[0.06] bg-[#0a0a0a]/80 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto px-6 h-14 flex items-center gap-2.5">
          <button onClick={() => navigate("/chat")} className="text-[#a1a1aa] hover:text-white transition-colors mr-2" data-testid="avatar-back">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="w-8 h-8 rounded-lg bg-[#3b82f6] flex items-center justify-center">
            <UserCircle className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-semibold tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>My Avatars</span>
          <span className="ml-auto text-xs text-[#52525b]">{avatars.length}/{limit} slots</span>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold tracking-tight" style={{ fontFamily: "'Outfit', sans-serif" }}>Avatars</h1>
          {avatars.length < limit && (
            <Button onClick={() => setShowForm(!showForm)} size="sm" className="bg-[#3b82f6] hover:bg-[#2563eb] text-white" data-testid="add-avatar-button">
              <Plus className="w-4 h-4 mr-1" /> New Avatar
            </Button>
          )}
        </div>

        {/* Create form */}
        {showForm && (
          <div className="mb-6 p-5 rounded-xl bg-[#111111] border border-white/[0.08] space-y-4" data-testid="avatar-form">
            <div>
              <label className="block text-xs text-[#a1a1aa] uppercase tracking-[0.15em] mb-1.5">Name</label>
              <input
                data-testid="avatar-name-input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Zara"
                className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-sm text-[#fafafa] placeholder:text-[#52525b] focus:border-[#3b82f6] outline-none"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-[#a1a1aa] uppercase tracking-[0.15em] mb-1.5">Face Photo</label>
                <label className="flex items-center justify-center gap-2 p-4 rounded-lg border border-dashed border-white/10 hover:border-white/20 cursor-pointer transition-colors">
                  <Upload className="w-4 h-4 text-[#52525b]" />
                  <span className="text-xs text-[#52525b]">{faceFile ? faceFile.name : "Upload face"}</span>
                  <input type="file" accept="image/*" className="hidden" onChange={(e) => setFaceFile(e.target.files[0])} data-testid="face-upload" />
                </label>
              </div>
              <div>
                <label className="block text-xs text-[#a1a1aa] uppercase tracking-[0.15em] mb-1.5">Full Body Photo</label>
                <label className="flex items-center justify-center gap-2 p-4 rounded-lg border border-dashed border-white/10 hover:border-white/20 cursor-pointer transition-colors">
                  <Upload className="w-4 h-4 text-[#52525b]" />
                  <span className="text-xs text-[#52525b]">{bodyFile ? bodyFile.name : "Upload body"}</span>
                  <input type="file" accept="image/*" className="hidden" onChange={(e) => setBodyFile(e.target.files[0])} data-testid="body-upload" />
                </label>
              </div>
            </div>
            <Button onClick={handleCreate} disabled={creating} className="w-full h-10 bg-[#3b82f6] hover:bg-[#2563eb] text-white" data-testid="save-avatar-button">
              {creating ? "Saving..." : "Create Avatar"}
            </Button>
          </div>
        )}

        {/* Avatar list */}
        {avatars.length === 0 ? (
          <div className="text-center p-12 rounded-xl bg-[#111111] border border-white/[0.08]">
            <UserCircle className="w-12 h-12 text-[#52525b] mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2" style={{ fontFamily: "'Outfit', sans-serif" }}>No avatars yet</h3>
            <p className="text-sm text-[#a1a1aa]">Create an avatar to use in image and video generation.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {avatars.map(av => (
              <div key={av.id} className="p-4 rounded-xl bg-[#111111] border border-white/[0.08] group" data-testid={`avatar-card-${av.id}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-[#fafafa]">{av.name}</span>
                  <button onClick={() => handleDelete(av.id)} className="text-[#52525b] hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100" data-testid={`delete-avatar-${av.id}`}>
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="aspect-square rounded-lg bg-white/5 flex items-center justify-center overflow-hidden">
                    {av.face_path ? (
                      <img src={`${API}/api/files/${av.face_path}`} alt="Face" className="w-full h-full object-cover" crossOrigin="use-credentials" />
                    ) : (
                      <span className="text-[10px] text-[#52525b]">No face</span>
                    )}
                  </div>
                  <div className="aspect-square rounded-lg bg-white/5 flex items-center justify-center overflow-hidden">
                    {av.body_path ? (
                      <img src={`${API}/api/files/${av.body_path}`} alt="Body" className="w-full h-full object-cover" crossOrigin="use-credentials" />
                    ) : (
                      <span className="text-[10px] text-[#52525b]">No body</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {avatars.length >= limit && (
          <div className="mt-6 p-4 rounded-xl bg-white/5 border border-white/[0.08] text-center">
            <p className="text-xs text-[#a1a1aa] mb-2">Avatar limit reached ({limit})</p>
            <Button onClick={() => navigate("/pricing")} size="sm" className="bg-[#3b82f6] hover:bg-[#2563eb] text-white text-xs" data-testid="upgrade-for-avatars">
              <Crown className="w-3 h-3 mr-1" /> Upgrade for more
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
