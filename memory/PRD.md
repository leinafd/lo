# Impulse AI - Product Requirements Document

## Architecture
- Frontend: React + Tailwind + Shadcn UI (port 3000)
- Backend: FastAPI (port 8001)
- Database: MongoDB
- AI Chat: Claude Sonnet (claude-4-sonnet-20250514) via emergentintegrations
- Image Gen: Gemini Nano Banana (gemini-3-pro-image-preview) via emergentintegrations
- Video Gen: Mocked Seedance 2.0 (placeholder)
- Payments: Stripe via emergentintegrations
- Storage: Emergent Object Storage

## Updated Pricing (April 2026)
- Free: $0/mo | 20 msgs/day, 2 imgs/day, 1 vid/day first 7 days only, 5s max, standard, watermarked
- Reasoning Pro: $19/mo | Unlimited chat, 10 imgs/day, 20 credits/mo, 10s max, SD+HD, no watermark
- Creative Pro: $39/mo | Unlimited chat+imgs, 50 credits/mo, 15s max, HD, no watermark
- Admin: All limits bypassed

## Credit System
- 1-5s = 1 credit, 6-10s = 2 credits, 11-15s = 3 credits, HD = 2x
- Top-ups: 50/$5, 120/$10, 300/$20 (both pro tiers)

## Implemented Features
### Phase 1: Tier Limits & Credits
- [x] Comprehensive tier config with daily limits
- [x] Duration-based video credit system
- [x] Credit top-up store (3 packs via Stripe)
- [x] Admin dashboard (users, feedback, revenue)

### Phase 2: AI Integrations
- [x] Claude Sonnet for chat (with conversation history)
- [x] Nano Banana Pro for image generation
- [x] Object storage for generated images
- [x] File serving with auth

### Phase 3: Video, Avatars, Onboarding, Analytics
- [x] Video tab with mocked Seedance 2.0 (duration slider, quality picker, progress bar)
- [x] Free user video trial (7 days then locked with upgrade prompt)
- [x] Credit deduction on video generation for pro users
- [x] Avatar system (face + body photo, per-tier limits: 1/2/5)
- [x] "Get To Know You" onboarding modal on first login
- [x] User memory system (persists for pro, clears for free)
- [x] Usage analytics (generation history, credit consumption, image gallery)
- [x] Sidebar navigation (Videos, Avatars, Stats)

## Prioritized Backlog
### P0 (Phase 4 - Next)
- Document creation/editing with rich text editor
- Export to PDF and DOCX
- Cross-chat memory injection into Claude system prompt

### P1
- Real Seedance 2.0 integration (when API key provided)
- Chat message streaming
- Start/end frame upload for video generation

### P2
- Team collaboration
- API access for Pro users
- Subscription management (cancel/change)
