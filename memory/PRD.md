# Impulse AI - Product Requirements Document

## Problem Statement
Full-stack SaaS AI chat platform with tiered subscriptions, credit system, AI chat (Claude), image generation (Nano Banana), and planned video/document/avatar features.

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn UI (port 3000)
- **Backend**: FastAPI (port 8001)
- **Database**: MongoDB
- **AI Chat**: Claude Sonnet (claude-4-sonnet-20250514) via emergentintegrations
- **Image Gen**: Gemini Nano Banana (gemini-3-pro-image-preview) via emergentintegrations
- **Payments**: Stripe via emergentintegrations
- **Storage**: Emergent Object Storage for generated images
- **Auth**: JWT + bcrypt with httpOnly cookies

## Tiers
- Free: 20 msgs/day, 2 images/day, 1 video/day (5s, watermarked)
- Reasoning Pro ($12/mo): Unlimited chat, 10 images/day, 3 videos/day (10s, SD+HD)
- Creative Pro ($24/mo): Unlimited all, 100 monthly video credits, credit top-ups
- Admin: All limits bypassed, admin dashboard

## What's Been Implemented (April 12, 2026)
### Phase 1: Tier Limits, Credit System, Credit Top-Up Store
- [x] Comprehensive TIER_LIMITS config for all tiers
- [x] Daily message/image/video limits with per-tier enforcement
- [x] Video credit system (duration-based: 1-5s=1cr, 6-10s=2cr, 11-15s=3cr, HD=2x)
- [x] Credit top-up store (Starter 50/$5, Standard 120/$10, Power 300/$20)
- [x] Admin role with all limits bypassed
- [x] Admin dashboard (users, feedback, revenue stats)
- [x] Updated pricing page with accurate feature lists

### Phase 2: Claude Chat + Nano Banana Image Generation
- [x] Claude Sonnet integration for chat (with conversation history)
- [x] Nano Banana Pro image generation via Gemini API
- [x] Object storage for generated images
- [x] Image display in chat messages
- [x] Image generation button in chat input
- [x] Graceful fallback for API budget errors
- [x] File serving endpoint with auth

## Prioritized Backlog
### P0 (Phase 3 - Next)
- Video tab with mocked Seedance 2.0
- Avatar system (upload face/body photos)
- "Get To Know You" onboarding modal

### P1 (Phase 4)
- Document creation/editing with rich text editor
- Export to PDF and DOCX
- Cross-chat memory system

### P2 (Future)
- Real Seedance 2.0 integration
- Chat streaming
- Team collaboration
- API access for Pro users
