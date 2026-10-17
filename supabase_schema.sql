-- AgentForge AI task persistence
-- Run this in Supabase SQL Editor before configuring Supabase in Streamlit.
-- This prototype uses a per-session UUID, not user authentication.
-- Do not treat session_id filtering as a substitute for authentication for sensitive data.

create table if not exists public.agentforge_tasks (
    id text primary key,
    session_id text not null,
    title text not null,
    description text not null,
    workflow text not null,
    status text not null,
    result text,
    error text,
    events jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists agentforge_tasks_session_created_idx
on public.agentforge_tasks (session_id, created_at desc);

-- The Streamlit server uses the Supabase key configured in Secrets.
-- For a private or multi-user production app, add authentication and proper RLS policies.
