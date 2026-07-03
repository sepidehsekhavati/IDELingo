-- =====================================================================
-- IDELingo — Supabase schema for Leaderboard / Community sync
-- Run this once in Supabase Dashboard → SQL Editor → New query
-- =====================================================================

-- 1) Table that only holds PUBLIC leaderboard fields (never passwords,
--    never vocabulary/phrases — those stay local on the phone)
create table if not exists public.leaderboard_profiles (
    username text primary key,
    sync_token text not null,
    avatar text default '😊',
    level int default 1,
    xp_total int default 0,
    current_streak int default 0,
    today_words int default 0,
    today_date date default current_date,
    updated_at timestamptz default now()
);

-- 2) Lock the table down completely. No one (not even with the anon key)
--    can read/write this table directly. Access ONLY through the
--    functions below, which validate the sync_token first.
alter table public.leaderboard_profiles enable row level security;
revoke all on public.leaderboard_profiles from anon, authenticated;

-- 3) Create/update a profile. Called on register, login, avatar change,
--    and whenever daily progress changes.
create or replace function public.upsert_leaderboard_profile(
    p_username text,
    p_sync_token text,
    p_avatar text,
    p_level int,
    p_xp int,
    p_streak int,
    p_today_words int
) returns void
language plpgsql
security definer
set search_path = public
as $$
declare
    existing_token text;
begin
    select sync_token into existing_token
    from leaderboard_profiles where username = p_username;

    if existing_token is not null and existing_token <> p_sync_token then
        raise exception 'invalid sync token';
    end if;

    insert into leaderboard_profiles
        (username, sync_token, avatar, level, xp_total, current_streak, today_words, today_date, updated_at)
    values
        (p_username, p_sync_token, p_avatar, p_level, p_xp, p_streak, p_today_words, current_date, now())
    on conflict (username) do update set
        avatar = excluded.avatar,
        level = excluded.level,
        xp_total = excluded.xp_total,
        current_streak = excluded.current_streak,
        today_words = case when leaderboard_profiles.today_date = current_date
                            then excluded.today_words else excluded.today_words end,
        today_date = current_date,
        updated_at = now();
end;
$$;

-- 4) Remove a profile (used when the user disables "public profile"
--    or deletes their account).
create or replace function public.remove_leaderboard_profile(
    p_username text,
    p_sync_token text
) returns void
language plpgsql
security definer
set search_path = public
as $$
begin
    delete from leaderboard_profiles
    where username = p_username and sync_token = p_sync_token;
end;
$$;

-- 5) Read the top of the leaderboard (today's words, tie-broken by level).
create or replace function public.get_leaderboard(p_limit int default 50)
returns table (username text, avatar text, level int, today_words int)
language sql
security definer
set search_path = public
as $$
    select username, avatar, level,
           case when today_date = current_date then today_words else 0 end as today_words
    from leaderboard_profiles
    order by today_words desc, level desc
    limit p_limit;
$$;

-- 6) Search public profiles by username (for the "Community" tab).
create or replace function public.search_leaderboard_profiles(
    p_query text,
    p_exclude_username text
) returns table (username text, avatar text, level int, xp_total int)
language sql
security definer
set search_path = public
as $$
    select username, avatar, level, xp_total
    from leaderboard_profiles
    where username ilike '%' || p_query || '%'
      and username <> p_exclude_username
    limit 20;
$$;

-- 7) Fetch a single public profile by username (for "View Profile").
create or replace function public.get_leaderboard_profile(p_username text)
returns table (username text, avatar text, level int, current_streak int, today_words int)
language sql
security definer
set search_path = public
as $$
    select username, avatar, level, current_streak,
           case when today_date = current_date then today_words else 0 end as today_words
    from leaderboard_profiles
    where username = p_username;
$$;

-- 8) Allow the anon (public) API key to call these functions only.
--    The table itself stays locked (step 2).
grant execute on function public.upsert_leaderboard_profile to anon;
grant execute on function public.remove_leaderboard_profile to anon;
grant execute on function public.get_leaderboard to anon;
grant execute on function public.search_leaderboard_profiles to anon;
grant execute on function public.get_leaderboard_profile to anon;
