-- Aplicada manualmente en producción el 2026-10-29 con aprobación explícita.
-- El guard impide repetirla si el estado ya cambió. Ver docs/PLAN_AUDITORIA.md.
-- Usar solo tras verificar respaldo, clave de servidor y acceso con Google.
-- No modifica ventas, columnas, claves, contraseñas ni Google.
BEGIN;
SET LOCAL lock_timeout = '5s';

DO $guard$
BEGIN
  IF current_setting('dulce_mar.approved_change', true)
       IS DISTINCT FROM 'close_public_sales_access' THEN
    RAISE EXCEPTION 'Cambio no habilitado: requiere revisión y aprobación explícita';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='public' AND c.relname='ventas' AND c.relrowsecurity
  ) THEN
    RAISE EXCEPTION 'RLS de ventas no coincide con el estado auditado';
  END IF;
  IF (SELECT count(*) FROM pg_policies WHERE schemaname='public' AND tablename='ventas') <> 1
     OR NOT EXISTS (
       SELECT 1 FROM pg_policies
       WHERE schemaname='public' AND tablename='ventas'
         AND policyname='Permitir todo a la app'
         AND cmd='ALL' AND permissive='PERMISSIVE'
         AND roles=ARRAY['public']::name[] AND qual='true' AND with_check='true'
     ) THEN
    RAISE EXCEPTION 'Políticas distintas a las auditadas; volver a revisar';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='service_role' AND rolbypassrls) THEN
    RAISE EXCEPTION 'El rol de servidor no coincide con el estado auditado';
  END IF;
END
$guard$;

-- Con RLS activo y sin políticas públicas, los clientes anon/authenticated
-- no ven ni modifican filas. La clave secreta del servidor conserva su acceso.
DROP POLICY "Permitir todo a la app" ON public.ventas;
COMMIT;
