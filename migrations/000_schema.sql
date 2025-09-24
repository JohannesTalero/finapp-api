-- =====================================================
-- SCHEMA SQL PARA FINAPP
-- =====================================================

-- Habilitar extensiones necesarias
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- =====================================================
-- TABLAS PRINCIPALES
-- =====================================================

-- Hogares (households)
create table if not exists households (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text,
  owner_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Miembros de hogares
create table if not exists household_members (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references households(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('viewer', 'member', 'admin', 'owner')),
  joined_at timestamptz not null default now(),
  unique (household_id, user_id)
);

-- Categorías
create table if not exists categories (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references households(id) on delete cascade,
  name text not null,
  kind text not null check (kind in ('income', 'expense')),
  description text,
  color text,
  icon text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Cuentas
create table if not exists accounts (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references households(id) on delete cascade,
  name text not null,
  account_type text not null check (account_type in ('checking', 'savings', 'credit_card', 'investment', 'cash', 'other')),
  currency text not null default 'USD',
  balance text not null default '0',
  description text,
  color text,
  icon text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Transacciones
create table if not exists transactions (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references households(id) on delete cascade,
  kind text not null check (kind in ('income', 'expense', 'transfer')),
  amount text not null,
  account_id uuid references accounts(id) on delete set null,
  from_account_id uuid references accounts(id) on delete set null,
  to_account_id uuid references accounts(id) on delete set null,
  category_id uuid references categories(id) on delete set null,
  occurred_at timestamptz not null default now(),
  description text,
  counterparty text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Metas
create table if not exists goals (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references households(id) on delete cascade,
  name text not null,
  target_amount text not null,
  current_amount text not null default '0',
  target_date date,
  description text,
  priority text not null default 'medium' check (priority in ('low', 'medium', 'high')),
  is_recurring boolean not null default false,
  recurrence_pattern text check (recurrence_pattern in ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')),
  status text not null default 'active' check (status in ('active', 'completed', 'cancelled')),
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Aportes a metas
create table if not exists goal_contributions (
  id uuid primary key default gen_random_uuid(),
  goal_id uuid not null references goals(id) on delete cascade,
  transaction_id uuid not null references transactions(id) on delete cascade,
  amount text not null,
  created_at timestamptz not null default now()
);

-- Obligaciones
create table if not exists obligations (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references households(id) on delete cascade,
  name text not null,
  total_amount text not null,
  outstanding_amount text not null,
  due_date date,
  description text,
  priority text not null default 'medium' check (priority in ('low', 'medium', 'high')),
  creditor text,
  is_recurring boolean not null default false,
  recurrence_pattern text check (recurrence_pattern in ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')),
  status text not null default 'active' check (status in ('active', 'completed', 'cancelled')),
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Pagos de obligaciones
create table if not exists obligation_payments (
  id uuid primary key default gen_random_uuid(),
  obligation_id uuid not null references obligations(id) on delete cascade,
  transaction_id uuid not null references transactions(id) on delete cascade,
  amount text not null,
  created_at timestamptz not null default now()
);

-- =====================================================
-- ÍNDICES
-- =====================================================

-- Índices para households
create index if not exists idx_households_owner_id on households(owner_id);
create index if not exists idx_households_created_at on households(created_at desc);

-- Índices para household_members
create index if not exists idx_household_members_household_id on household_members(household_id);
create index if not exists idx_household_members_user_id on household_members(user_id);
create index if not exists idx_household_members_role on household_members(role);

-- Índices para categories
create index if not exists idx_categories_household_id on categories(household_id);
create index if not exists idx_categories_kind on categories(kind);
create index if not exists idx_categories_name on categories(name);

-- Índices para accounts
create index if not exists idx_accounts_household_id on accounts(household_id);
create index if not exists idx_accounts_type on accounts(account_type);
create index if not exists idx_accounts_name on accounts(name);

-- Índices para transactions
create index if not exists idx_transactions_household_id on transactions(household_id);
create index if not exists idx_transactions_kind on transactions(kind);
create index if not exists idx_transactions_account_id on transactions(account_id);
create index if not exists idx_transactions_from_account_id on transactions(from_account_id);
create index if not exists idx_transactions_to_account_id on transactions(to_account_id);
create index if not exists idx_transactions_category_id on transactions(category_id);
create index if not exists idx_transactions_occurred_at on transactions(occurred_at desc);
create index if not exists idx_transactions_occurred_at_id on transactions(occurred_at desc, id desc);

-- Índices para goals
create index if not exists idx_goals_household_id on goals(household_id);
create index if not exists idx_goals_status on goals(status);
create index if not exists idx_goals_is_recurring on goals(is_recurring);
create index if not exists idx_goals_target_date on goals(target_date);
create index if not exists idx_goals_created_at on goals(created_at desc);

-- Índices para goal_contributions
create index if not exists idx_goal_contributions_goal_id on goal_contributions(goal_id);
create index if not exists idx_goal_contributions_transaction_id on goal_contributions(transaction_id);
create index if not exists idx_goal_contributions_created_at on goal_contributions(created_at desc);

-- Índices para obligations
create index if not exists idx_obligations_household_id on obligations(household_id);
create index if not exists idx_obligations_status on obligations(status);
create index if not exists idx_obligations_is_recurring on obligations(is_recurring);
create index if not exists idx_obligations_due_date on obligations(due_date);
create index if not exists idx_obligations_priority on obligations(priority);
create index if not exists idx_obligations_created_at on obligations(created_at desc);

-- Índices para obligation_payments
create index if not exists idx_obligation_payments_obligation_id on obligation_payments(obligation_id);
create index if not exists idx_obligation_payments_transaction_id on obligation_payments(transaction_id);
create index if not exists idx_obligation_payments_created_at on obligation_payments(created_at desc);

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Habilitar RLS en todas las tablas
alter table households enable row level security;
alter table household_members enable row level security;
alter table categories enable row level security;
alter table accounts enable row level security;
alter table transactions enable row level security;
alter table goals enable row level security;
alter table goal_contributions enable row level security;
alter table obligations enable row level security;
alter table obligation_payments enable row level security;

-- Políticas para households
create policy "households_select" on households
for select
using (owner_id = auth.uid());

create policy "households_insert" on households
for insert
with check (owner_id = auth.uid());

create policy "households_update" on households
for update
using (owner_id = auth.uid());

create policy "households_delete" on households
for delete
using (owner_id = auth.uid());

-- Políticas para household_members
create policy "household_members_select" on household_members
for select
using (user_id = auth.uid() or household_id in (
  select id from households where owner_id = auth.uid()
));

create policy "household_members_insert" on household_members
for insert
with check (household_id in (
  select id from households where owner_id = auth.uid()
));

create policy "household_members_update" on household_members
for update
using (household_id in (
  select id from households where owner_id = auth.uid()
));

create policy "household_members_delete" on household_members
for delete
using (household_id in (
  select id from households where owner_id = auth.uid()
));

-- Políticas para categories
create policy "categories_select" on categories
for select
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "categories_insert" on categories
for insert
with check (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "categories_update" on categories
for update
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "categories_delete" on categories
for delete
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

-- Políticas para accounts
create policy "accounts_select" on accounts
for select
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "accounts_insert" on accounts
for insert
with check (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "accounts_update" on accounts
for update
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "accounts_delete" on accounts
for delete
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

-- Políticas para transactions
create policy "transactions_select" on transactions
for select
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "transactions_insert" on transactions
for insert
with check (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "transactions_update" on transactions
for update
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "transactions_delete" on transactions
for delete
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

-- Políticas para goals
create policy "goals_select" on goals
for select
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "goals_insert" on goals
for insert
with check (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "goals_update" on goals
for update
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "goals_delete" on goals
for delete
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

-- Políticas para goal_contributions
create policy "goal_contributions_select" on goal_contributions
for select
using (goal_id in (
  select g.id from goals g
  join household_members hm on g.household_id = hm.household_id
  where hm.user_id = auth.uid()
));

create policy "goal_contributions_insert" on goal_contributions
for insert
with check (goal_id in (
  select g.id from goals g
  join household_members hm on g.household_id = hm.household_id
  where hm.user_id = auth.uid()
));

create policy "goal_contributions_update" on goal_contributions
for update
using (goal_id in (
  select g.id from goals g
  join household_members hm on g.household_id = hm.household_id
  where hm.user_id = auth.uid()
));

create policy "goal_contributions_delete" on goal_contributions
for delete
using (goal_id in (
  select g.id from goals g
  join household_members hm on g.household_id = hm.household_id
  where hm.user_id = auth.uid()
));

-- Políticas para obligations
create policy "obligations_select" on obligations
for select
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "obligations_insert" on obligations
for insert
with check (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "obligations_update" on obligations
for update
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

create policy "obligations_delete" on obligations
for delete
using (household_id in (
  select hm.household_id from household_members hm where hm.user_id = auth.uid()
));

-- Políticas para obligation_payments
create policy "obligation_payments_select" on obligation_payments
for select
using (obligation_id in (
  select o.id from obligations o
  join household_members hm on o.household_id = hm.household_id
  where hm.user_id = auth.uid()
));

create policy "obligation_payments_insert" on obligation_payments
for insert
with check (obligation_id in (
  select o.id from obligations o
  join household_members hm on o.household_id = hm.household_id
  where hm.user_id = auth.uid()
));

create policy "obligation_payments_update" on obligation_payments
for update
using (obligation_id in (
  select o.id from obligations o
  join household_members hm on o.household_id = hm.household_id
  where hm.user_id = auth.uid()
));

create policy "obligation_payments_delete" on obligation_payments
for delete
using (obligation_id in (
  select o.id from obligations o
  join household_members hm on o.household_id = hm.household_id
  where hm.user_id = auth.uid()
));

-- =====================================================
-- VISTAS AUXILIARES
-- =====================================================

-- Vista de balances de cuentas
create or replace view v_account_balances as
select 
  a.id as account_id,
  a.household_id,
  a.name as account_name,
  a.account_type,
  a.currency,
  a.balance,
  a.color,
  a.icon
from accounts a
join household_members hm on a.household_id = hm.household_id
where hm.user_id = auth.uid();

-- Vista de resumen de transacciones por categoría
create or replace view v_category_summary as
select 
  c.id as category_id,
  c.household_id,
  c.name as category_name,
  c.kind,
  count(t.id) as transaction_count,
  sum(t.amount::numeric) as total_amount
from categories c
left join transactions t on c.id = t.category_id
join household_members hm on c.household_id = hm.household_id
where hm.user_id = auth.uid()
group by c.id, c.household_id, c.name, c.kind;

-- =====================================================
-- FUNCIONES AUXILIARES
-- =====================================================

-- Función para obtener cashflow
create or replace function get_cashflow(
  p_household_id uuid,
  p_from_date date,
  p_to_date date,
  p_group_by text default 'month'
)
returns table (
  period text,
  income numeric,
  expense numeric,
  net numeric
) as $$
begin
  return query
  select 
    case p_group_by
      when 'day' then to_char(t.occurred_at::date, 'YYYY-MM-DD')
      when 'week' then to_char(t.occurred_at::date, 'YYYY-"W"WW')
      when 'month' then to_char(t.occurred_at::date, 'YYYY-MM')
      when 'year' then to_char(t.occurred_at::date, 'YYYY')
      else to_char(t.occurred_at::date, 'YYYY-MM')
    end as period,
    coalesce(sum(case when t.kind = 'income' then t.amount::numeric else 0 end), 0) as income,
    coalesce(sum(case when t.kind = 'expense' then t.amount::numeric else 0 end), 0) as expense,
    coalesce(sum(case when t.kind = 'income' then t.amount::numeric else -t.amount::numeric end), 0) as net
  from transactions t
  join household_members hm on t.household_id = hm.household_id
  where hm.user_id = auth.uid()
    and t.household_id = p_household_id
    and t.occurred_at::date >= p_from_date
    and t.occurred_at::date <= p_to_date
  group by period
  order by period;
end;
$$ language plpgsql security definer;

-- Función para obtener top categorías
create or replace function get_top_categories(
  p_household_id uuid,
  p_from_date date,
  p_limit integer default 5
)
returns table (
  category_id uuid,
  category_name text,
  kind text,
  total_amount numeric,
  transaction_count bigint,
  percentage numeric
) as $$
declare
  total_amount numeric;
begin
  -- Calcular total de transacciones en el período
  select coalesce(sum(t.amount::numeric), 0)
  into total_amount
  from transactions t
  join household_members hm on t.household_id = hm.household_id
  where hm.user_id = auth.uid()
    and t.household_id = p_household_id
    and t.occurred_at::date >= p_from_date;
  
  return query
  select 
    c.id as category_id,
    c.name as category_name,
    c.kind,
    coalesce(sum(t.amount::numeric), 0) as total_amount,
    count(t.id) as transaction_count,
    case 
      when total_amount > 0 then (coalesce(sum(t.amount::numeric), 0) / total_amount) * 100
      else 0
    end as percentage
  from categories c
  left join transactions t on c.id = t.category_id
    and t.occurred_at::date >= p_from_date
  join household_members hm on c.household_id = hm.household_id
  where hm.user_id = auth.uid()
    and c.household_id = p_household_id
  group by c.id, c.name, c.kind
  order by total_amount desc
  limit p_limit;
end;
$$ language plpgsql security definer;

-- Función para análisis de categorías
create or replace function get_category_analysis(
  p_household_id uuid,
  p_from_date date,
  p_to_date date,
  p_kind text default null
)
returns table (
  category_id uuid,
  category_name text,
  kind text,
  total_amount numeric,
  transaction_count bigint,
  percentage numeric
) as $$
declare
  total_amount numeric;
begin
  -- Calcular total de transacciones en el período
  select coalesce(sum(t.amount::numeric), 0)
  into total_amount
  from transactions t
  join household_members hm on t.household_id = hm.household_id
  where hm.user_id = auth.uid()
    and t.household_id = p_household_id
    and t.occurred_at::date >= p_from_date
    and t.occurred_at::date <= p_to_date
    and (p_kind is null or t.kind = p_kind);
  
  return query
  select 
    c.id as category_id,
    c.name as category_name,
    c.kind,
    coalesce(sum(t.amount::numeric), 0) as total_amount,
    count(t.id) as transaction_count,
    case 
      when total_amount > 0 then (coalesce(sum(t.amount::numeric), 0) / total_amount) * 100
      else 0
    end as percentage
  from categories c
  left join transactions t on c.id = t.category_id
    and t.occurred_at::date >= p_from_date
    and t.occurred_at::date <= p_to_date
    and (p_kind is null or t.kind = p_kind)
  join household_members hm on c.household_id = hm.household_id
  where hm.user_id = auth.uid()
    and c.household_id = p_household_id
    and (p_kind is null or c.kind = p_kind)
  group by c.id, c.name, c.kind
  order by total_amount desc;
end;
$$ language plpgsql security definer;

-- Función para resumen mensual
create or replace function get_monthly_summary(
  p_household_id uuid,
  p_year integer,
  p_month integer
)
returns table (
  year integer,
  month integer,
  total_income numeric,
  total_expense numeric,
  net_income numeric,
  transaction_count bigint
) as $$
begin
  return query
  select 
    p_year as year,
    p_month as month,
    coalesce(sum(case when t.kind = 'income' then t.amount::numeric else 0 end), 0) as total_income,
    coalesce(sum(case when t.kind = 'expense' then t.amount::numeric else 0 end), 0) as total_expense,
    coalesce(sum(case when t.kind = 'income' then t.amount::numeric else -t.amount::numeric end), 0) as net_income,
    count(t.id) as transaction_count
  from transactions t
  join household_members hm on t.household_id = hm.household_id
  where hm.user_id = auth.uid()
    and t.household_id = p_household_id
    and extract(year from t.occurred_at) = p_year
    and extract(month from t.occurred_at) = p_month;
end;
$$ language plpgsql security definer;
