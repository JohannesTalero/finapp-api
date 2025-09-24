-- =====================================================
-- TABLA DE IDEMPOTENCIA
-- =====================================================

-- Tabla para manejar idempotencia de requests
create table if not exists idempotency_requests (
  id uuid primary key default gen_random_uuid(),
  key text not null,                -- valor de header Idempotency-Key
  user_id uuid not null,            -- auth.users.id
  household_id uuid not null,
  request_hash text not null,       -- hash del cuerpo del request
  response_status int not null,
  response_body jsonb not null,     -- cuerpo de la respuesta devuelta
  created_at timestamptz not null default now(),
  unique (key, user_id, household_id)
);

-- Habilitar RLS
alter table idempotency_requests enable row level security;

-- Políticas: solo el mismo usuario en el mismo hogar puede ver su registro
create policy "idempotency_select" on idempotency_requests
for select
using ( user_id = auth.uid() );

create policy "idempotency_insert" on idempotency_requests
for insert
with check ( user_id = auth.uid() );

create policy "idempotency_update" on idempotency_requests
for update
using ( user_id = auth.uid() );

create policy "idempotency_delete" on idempotency_requests
for delete
using ( user_id = auth.uid() );

-- Índices para optimizar consultas
create index if not exists idx_idem_user_household on idempotency_requests (user_id, household_id, created_at desc);
create index if not exists idx_idem_key on idempotency_requests (key);
create index if not exists idx_idem_created_at on idempotency_requests (created_at desc);

-- Función para limpiar requests antiguos (opcional)
create or replace function cleanup_old_idempotency_requests(days integer default 30)
returns integer as $$
declare
  deleted_count integer;
begin
  delete from idempotency_requests 
  where created_at < now() - interval '1 day' * days;
  
  get diagnostics deleted_count = row_count;
  return deleted_count;
end;
$$ language plpgsql security definer;
