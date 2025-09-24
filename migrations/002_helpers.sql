-- =====================================================
-- HELPERS Y FUNCIONES AUXILIARES
-- =====================================================

-- Función para ejecutar SQL dinámico (para el cliente Supabase)
create or replace function execute_sql(
  query text,
  params jsonb default '{}'::jsonb
)
returns jsonb as $$
declare
  result jsonb;
begin
  -- Esta función permite ejecutar SQL dinámico desde el cliente
  -- En producción, deberías restringir qué queries se pueden ejecutar
  execute query into result;
  return result;
exception
  when others then
    return jsonb_build_object('error', sqlerrm);
end;
$$ language plpgsql security definer;

-- Función para obtener estadísticas de uso
create or replace function get_usage_stats(p_household_id uuid)
returns jsonb as $$
declare
  stats jsonb;
begin
  select jsonb_build_object(
    'households', (select count(*) from households where id = p_household_id),
    'categories', (select count(*) from categories where household_id = p_household_id),
    'accounts', (select count(*) from accounts where household_id = p_household_id),
    'transactions', (select count(*) from transactions where household_id = p_household_id),
    'goals', (select count(*) from goals where household_id = p_household_id),
    'obligations', (select count(*) from obligations where household_id = p_household_id),
    'total_balance', (
      select coalesce(sum(balance::numeric), 0)
      from accounts 
      where household_id = p_household_id
    )
  ) into stats;
  
  return stats;
end;
$$ language plpgsql security definer;

-- Función para validar transferencias
create or replace function validate_transfer(
  p_from_account_id uuid,
  p_to_account_id uuid,
  p_amount text
)
returns boolean as $$
begin
  -- Verificar que las cuentas existen y son diferentes
  if p_from_account_id = p_to_account_id then
    return false;
  end if;
  
  -- Verificar que ambas cuentas existen
  if not exists(select 1 from accounts where id = p_from_account_id) then
    return false;
  end if;
  
  if not exists(select 1 from accounts where id = p_to_account_id) then
    return false;
  end if;
  
  -- Verificar que el monto es positivo
  if p_amount::numeric <= 0 then
    return false;
  end if;
  
  return true;
end;
$$ language plpgsql security definer;

-- Función para actualizar balance de cuenta después de transacción
create or replace function update_account_balance()
returns trigger as $$
declare
  account_balance numeric;
  new_balance numeric;
begin
  -- Solo procesar si es una transacción nueva o actualizada
  if tg_op = 'INSERT' or tg_op = 'UPDATE' then
    -- Actualizar balance de cuenta principal
    if new.account_id is not null then
      select balance::numeric into account_balance
      from accounts where id = new.account_id;
      
      if new.kind = 'income' then
        new_balance := account_balance + new.amount::numeric;
      elsif new.kind = 'expense' then
        new_balance := account_balance - new.amount::numeric;
      end if;
      
      update accounts 
      set balance = new_balance::text, updated_at = now()
      where id = new.account_id;
    end if;
    
    -- Actualizar balance de cuenta origen (transferencias)
    if new.from_account_id is not null then
      select balance::numeric into account_balance
      from accounts where id = new.from_account_id;
      
      new_balance := account_balance - new.amount::numeric;
      
      update accounts 
      set balance = new_balance::text, updated_at = now()
      where id = new.from_account_id;
    end if;
    
    -- Actualizar balance de cuenta destino (transferencias)
    if new.to_account_id is not null then
      select balance::numeric into account_balance
      from accounts where id = new.to_account_id;
      
      new_balance := account_balance + new.amount::numeric;
      
      update accounts 
      set balance = new_balance::text, updated_at = now()
      where id = new.to_account_id;
    end if;
  end if;
  
  return new;
end;
$$ language plpgsql;

-- Crear trigger para actualizar balances automáticamente
create trigger trigger_update_account_balance
  after insert or update on transactions
  for each row execute function update_account_balance();

-- Función para limpiar datos de prueba (solo para desarrollo)
create or replace function cleanup_test_data()
returns jsonb as $$
declare
  result jsonb;
begin
  -- Solo ejecutar en entorno de desarrollo
  if current_setting('app.environment', true) != 'development' then
    return jsonb_build_object('error', 'Solo disponible en desarrollo');
  end if;
  
  -- Limpiar datos de prueba
  delete from obligation_payments;
  delete from goal_contributions;
  delete from transactions;
  delete from obligations;
  delete from goals;
  delete from accounts;
  delete from categories;
  delete from household_members;
  delete from households;
  
  select jsonb_build_object(
    'message', 'Datos de prueba eliminados',
    'timestamp', now()
  ) into result;
  
  return result;
end;
$$ language plpgsql security definer;
