-- REPLYNT Supabase Database Schema Setup Script
-- Run this in the SQL Editor of your Supabase project to create the necessary tables, indexes, and realtime publications.

-- 1. Create Emails Table
CREATE TABLE IF NOT EXISTS public.emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id VARCHAR(255) UNIQUE NOT NULL,
    sender VARCHAR(255) NOT NULL,
    subject VARCHAR(512) NOT NULL,
    body TEXT NOT NULL,
    priority VARCHAR(10) DEFAULT 'P3', -- P1, P2, P3
    intent VARCHAR(100),
    risk_score NUMERIC(5, 4) DEFAULT 0.0000,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index for querying email by email_id
CREATE INDEX IF NOT EXISTS idx_emails_email_id ON public.emails(email_id);
CREATE INDEX IF NOT EXISTS idx_emails_priority ON public.emails(priority);

-- 2. Create Commitments Table
CREATE TABLE IF NOT EXISTS public.commitments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id VARCHAR(255) NOT NULL REFERENCES public.emails(email_id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    raw_text TEXT,
    who VARCHAR(255) DEFAULT 'me',
    deadline TIMESTAMP WITH TIME ZONE,
    pattern_type VARCHAR(50),
    confidence NUMERIC(5, 4) DEFAULT 1.0000,
    status VARCHAR(50) DEFAULT 'pending', -- pending, done, snoozed, dismissed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index for searching commitments by email and status
CREATE INDEX IF NOT EXISTS idx_commitments_email_id ON public.commitments(email_id);
CREATE INDEX IF NOT EXISTS idx_commitments_status ON public.commitments(status);

-- 3. Create Alerts Table
CREATE TABLE IF NOT EXISTS public.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id VARCHAR(255) NOT NULL REFERENCES public.emails(email_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alerts_email_id ON public.alerts(email_id);
CREATE INDEX IF NOT EXISTS idx_alerts_is_read ON public.alerts(is_read);

-- 4. Create Draft Replies Table
CREATE TABLE IF NOT EXISTS public.draft_replies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id VARCHAR(255) NOT NULL REFERENCES public.emails(email_id) ON DELETE CASCADE,
    subject VARCHAR(512),
    draft_body TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_draft_replies_email_id ON public.draft_replies(email_id);

-- 5. Enable Realtime for all tables
-- This allows the Next.js frontend to receive instant updates when n8n inserts data.
ALTER PUBLICATION supabase_realtime ADD TABLE public.emails;
ALTER PUBLICATION supabase_realtime ADD TABLE public.commitments;
ALTER PUBLICATION supabase_realtime ADD TABLE public.alerts;
ALTER PUBLICATION supabase_realtime ADD TABLE public.draft_replies;
