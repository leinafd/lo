# Impulse AI - Product Requirements Document

## Problem Statement
Build a full-stack SaaS app called Impulse AI — a branded AI chat platform with auth, Stripe subscriptions, chat UI with usage limits, and feedback logging. No real AI integration yet.

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn UI (port 3000)
- **Backend**: FastAPI (port 8001)
- **Database**: MongoDB (users, chats, messages, feedback_logs, payment_transactions, login_attempts)
- **Payments**: Stripe via emergentintegrations library
- **Auth**: JWT + bcrypt with httpOnly cookies

## User Personas
1. **Free User**: 10 messages/day, usage counter visible, upgrade prompts
2. **Pro Reasoning User**: Unlimited messages, $12/mo subscription
3. **Pro Creative User**: Unlimited messages, $24/mo subscription

## Core Requirements
- Email/password auth (register, login, logout, token refresh)
- Role-based access (free, pro_reasoning, pro_creative)
- Daily message limit (10/day for free users)
- Chat with placeholder AI responses
- Thumbs up/down feedback logging
- Stripe Checkout for subscription upgrades
- Payment status polling on success page
- Dark theme (#0a0a0a, #3b82f6 accent, Outfit+Manrope fonts)

## What's Been Implemented (April 11, 2026)
- [x] JWT auth with bcrypt password hashing
- [x] Brute force protection (5 attempts → 15 min lockout)
- [x] Admin seeding on startup
- [x] Chat system with placeholder responses
- [x] Daily message limit enforcement
- [x] Feedback logging (thumbs up/down)
- [x] Stripe Checkout session creation and status polling
- [x] Payment webhook handler
- [x] Role upgrade on successful payment
- [x] Split-screen login/register pages
- [x] Chat page with sidebar, history, usage counter
- [x] Pricing page with 3 tier cards
- [x] Payment success page with status polling
- [x] Mobile responsive sidebar

## Prioritized Backlog
### P0 (Critical - Next)
- Integrate real AI API (OpenAI/Claude/etc)
- Add password reset flow
- Email verification on signup

### P1 (Important)
- Chat message streaming
- Chat export functionality
- User settings/profile page
- Subscription management (cancel/change plan)

### P2 (Nice to have)
- Chat search
- Message history pagination
- Dark/light theme toggle
- Team collaboration features
- API access for Pro users

## Next Tasks
1. Integrate AI API (GPT/Claude) for real chat responses
2. Add email verification flow
3. Build user settings page
4. Add subscription management (portal/cancel)
