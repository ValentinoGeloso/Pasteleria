-- REVERSIÓN PROPUESTA. Restaura el acceso público anterior (inseguro).
-- No ejecutar salvo decisión explícita de recuperación del usuario.
BEGIN;
SET LOCAL lock_timeout = '5s';
DO $guard$
BEGIN
  IF current_setting('dulce_mar.approved_change', true)
       IS DISTINCT FROM 'restore_previous_sales_policy' THEN
    RAISE EXCEPTION 'Reversión no habilitada: requiere aprobación explícita';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='ventas') THEN
    RAISE EXCEPTION 'Las políticas cambiaron; revisar antes de revertir';
  END IF;
END
$guard$;
CREATE POLICY "Permitir todo a la app" ON public.ventas
  AS PERMISSIVE FOR ALL TO public USING (true) WITH CHECK (true);
COMMIT;
