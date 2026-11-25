-- Run once in the Supabase SQL Editor for the GHOST Cloud Memory table.
create table if not exists public.ghost_memories (
    id uuid primary key,
    owner_id uuid not null references auth.users (id) on delete cascade,
    category text not null default 'general',
    content text not null,
    source_url text,
    confidence double precision not null default 1.0,
    approved boolean not null default true,
    created_at timestamptz not null default now()
);

alter table public.ghost_memories enable row level security;

create policy "GHOST owner can read approved memories"
    on public.ghost_memories for select
    using (auth.uid() = owner_id and approved = true);

create policy "GHOST owner can add own memories"
    on public.ghost_memories for insert
    with check (auth.uid() = owner_id);

create policy "GHOST owner can delete own memories"
    on public.ghost_memories for delete
    using (auth.uid() = owner_id);
