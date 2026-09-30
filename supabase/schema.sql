-- Run once in the Supabase SQL editor. Public reads use the publishable key;
-- writes are handled by the public-dictionaries Edge Function.
create table if not exists public.public_dictionaries (
  id text primary key check (id ~ '^[a-f0-9]{64}$'),
  name text not null check (char_length(trim(name)) between 1 and 60),
  mapping jsonb not null check (jsonb_typeof(mapping) = 'object' and octet_length(mapping::text) <= 262144),
  created_at timestamptz not null default now(),
  active boolean not null default true
);
alter table public.public_dictionaries enable row level security;
revoke all on public.public_dictionaries from anon, authenticated;
grant select on public.public_dictionaries to anon, authenticated;
grant select, insert, update on public.public_dictionaries to service_role;
drop policy if exists "Public dictionaries are readable" on public.public_dictionaries;
create policy "Public dictionaries are readable"
on public.public_dictionaries for select to anon, authenticated
using (active);
create index if not exists public_dictionaries_recent on public.public_dictionaries (created_at desc) where active;
-- To hide a problematic dictionary, set active=false in the dashboard.
-- Identical contents cannot be uploaded twice, including after being hidden.

-- Validate every insert and bound anonymous publication volume across app sessions.
create or replace function public.validate_public_dictionary()
returns trigger language plpgsql set search_path = public, pg_temp as $$
declare item record; entry_count integer;
begin
  perform pg_advisory_xact_lock(827451);
  select count(*) into entry_count from jsonb_each(new.mapping);
  if entry_count not between 1 and 500 then
    raise exception 'Dictionary must contain 1-500 entries';
  end if;
  for item in select key, value from jsonb_each(new.mapping) loop
    if char_length(trim(item.key)) not between 1 and 64
       or jsonb_typeof(item.value) <> 'string'
       or char_length(trim(item.value #>> '{}')) not between 1 and 256 then
      raise exception 'Invalid dictionary entry';
    end if;
  end loop;
  if (select count(*) from public.public_dictionaries where created_at > now() - interval '1 minute') >= 10 then
    raise exception 'Publication rate limit reached';
  end if;
  return new;
end;
$$;
revoke all on function public.validate_public_dictionary() from public, anon, authenticated;
drop trigger if exists validate_public_dictionary on public.public_dictionaries;
create trigger validate_public_dictionary before insert or update on public.public_dictionaries
for each row execute function public.validate_public_dictionary();

-- Merge an uploaded JSON object into an existing dictionary in one transaction.
-- Existing entries with the same source term are replaced by the new upload.
create or replace function public.merge_public_dictionary(target_id text, additions jsonb)
returns setof public.public_dictionaries
language plpgsql
set search_path = public, pg_temp
as $$
begin
  return query
  update public.public_dictionaries
  set mapping = mapping || additions,
      created_at = now()
  where id = target_id and active
  returning *;
end;
$$;
revoke all on function public.merge_public_dictionary(text, jsonb) from public, anon, authenticated;
grant execute on function public.merge_public_dictionary(text, jsonb) to service_role;
