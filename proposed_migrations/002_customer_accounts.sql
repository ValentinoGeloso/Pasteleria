-- MIGRACIÓN ADITIVA. Aplicada el 29/10/2026 tras respaldo restaurado y aprobación explícita.
-- Requiere respaldo verificado y aprobación explícita: create_customer_accounts.
-- No modifica ventas, productos ni datos históricos. Los cargos a cuenta y sus
-- cobros viven separados: saldar una cuenta nunca duplica una venta existente.
BEGIN;
SET LOCAL lock_timeout = '5s';

DO $guard$
BEGIN
  IF current_setting('dulce_mar.approved_change', true)
       IS DISTINCT FROM 'create_customer_accounts' THEN
    RAISE EXCEPTION 'Cambio no habilitado: requiere aprobación explícita';
  END IF;
  IF to_regclass('public.cuentas_clientes') IS NOT NULL
     OR to_regclass('public.cuentas_cargos') IS NOT NULL
     OR to_regclass('public.cuentas_pagos') IS NOT NULL
     OR to_regclass('public.cuentas_aplicaciones') IS NOT NULL THEN
    RAISE EXCEPTION 'Ya existe parte del esquema de cuentas; revisar antes de continuar';
  END IF;
END
$guard$;

CREATE TABLE public.cuentas_clientes (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nombre text NOT NULL CHECK (nombre=btrim(nombre) AND char_length(nombre) BETWEEN 1 AND 160),
  request_id uuid NOT NULL UNIQUE,
  lock_version bigint NOT NULL DEFAULT 0 CHECK (lock_version>=0),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.cuentas_cargos (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  cliente_id bigint NOT NULL REFERENCES public.cuentas_clientes(id) ON DELETE RESTRICT,
  fecha date NOT NULL,
  producto text NOT NULL CHECK (producto=btrim(producto) AND char_length(producto) BETWEEN 1 AND 240),
  presentacion text NOT NULL CHECK (presentacion=btrim(presentacion) AND char_length(presentacion) BETWEEN 1 AND 240),
  cantidad integer NOT NULL CHECK (cantidad>0),
  precio_unitario numeric(14,2) NOT NULL CHECK (precio_unitario>0 AND precio_unitario<>'NaN'::numeric),
  monto_total numeric(14,2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,
  costo_total numeric(14,2) NOT NULL CHECK (costo_total>=0 AND costo_total<>'NaN'::numeric),
  request_id uuid NOT NULL UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (id,cliente_id)
);
CREATE INDEX cuentas_cargos_cliente_fecha_idx ON public.cuentas_cargos(cliente_id,fecha,id);

CREATE TABLE public.cuentas_pagos (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  cliente_id bigint NOT NULL REFERENCES public.cuentas_clientes(id) ON DELETE RESTRICT,
  fecha date NOT NULL,
  monto numeric(14,2) NOT NULL CHECK (monto>0 AND monto<>'NaN'::numeric),
  nota text NOT NULL DEFAULT '' CHECK (char_length(nota)<=1000),
  cargo_ids bigint[],
  request_id uuid NOT NULL UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (id,cliente_id)
);
CREATE INDEX cuentas_pagos_cliente_fecha_idx ON public.cuentas_pagos(cliente_id,fecha,id);

CREATE TABLE public.cuentas_aplicaciones (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  cliente_id bigint NOT NULL,
  pago_id bigint NOT NULL,
  cargo_id bigint NOT NULL,
  monto numeric(14,2) NOT NULL CHECK (monto>0 AND monto<>'NaN'::numeric),
  UNIQUE (pago_id,cargo_id),
  FOREIGN KEY (pago_id,cliente_id) REFERENCES public.cuentas_pagos(id,cliente_id) ON DELETE RESTRICT,
  FOREIGN KEY (cargo_id,cliente_id) REFERENCES public.cuentas_cargos(id,cliente_id) ON DELETE RESTRICT
);
CREATE INDEX cuentas_aplicaciones_cargo_idx ON public.cuentas_aplicaciones(cargo_id);
CREATE INDEX cuentas_aplicaciones_cliente_idx ON public.cuentas_aplicaciones(cliente_id);

ALTER TABLE public.cuentas_clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cuentas_cargos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cuentas_pagos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cuentas_aplicaciones ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.cuentas_clientes, public.cuentas_cargos,
  public.cuentas_pagos, public.cuentas_aplicaciones FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT, INSERT ON public.cuentas_clientes, public.cuentas_cargos,
  public.cuentas_pagos, public.cuentas_aplicaciones TO service_role;
-- Names and internal locking only; financial records remain append-only.
GRANT UPDATE (nombre, lock_version) ON public.cuentas_clientes TO service_role;
REVOKE ALL ON SEQUENCE public.cuentas_clientes_id_seq, public.cuentas_cargos_id_seq,
  public.cuentas_pagos_id_seq, public.cuentas_aplicaciones_id_seq FROM PUBLIC, anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE public.cuentas_clientes_id_seq, public.cuentas_cargos_id_seq,
  public.cuentas_pagos_id_seq, public.cuentas_aplicaciones_id_seq TO service_role;

CREATE FUNCTION public.crear_cargo_cuenta(
  p_cliente_id bigint, p_fecha date, p_producto text, p_presentacion text,
  p_cantidad integer, p_precio_unitario numeric, p_costo_total numeric, p_request_id uuid
) RETURNS public.cuentas_cargos
LANGUAGE plpgsql SECURITY INVOKER
SET search_path = ''
SET lock_timeout = '5s'
AS $function$
DECLARE
  v_producto text := btrim(p_producto);
  v_presentacion text := btrim(p_presentacion);
  v_existing public.cuentas_cargos%ROWTYPE;
  v_result public.cuentas_cargos%ROWTYPE;
BEGIN
  IF p_fecha IS NULL OR p_request_id IS NULL OR p_cantidad IS NULL OR p_cantidad<=0
     OR p_producto IS NULL OR char_length(v_producto) NOT BETWEEN 1 AND 240
     OR p_presentacion IS NULL OR char_length(v_presentacion) NOT BETWEEN 1 AND 240
     OR p_precio_unitario IS NULL OR p_precio_unitario<=0
     OR p_precio_unitario IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
     OR p_precio_unitario<>pg_catalog.round(p_precio_unitario,2)
     OR p_precio_unitario*p_cantidad>999999999999.99
     OR p_costo_total IS NULL OR p_costo_total<0
     OR p_costo_total>999999999999.99
     OR p_costo_total IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
     OR p_costo_total<>pg_catalog.round(p_costo_total,2) THEN
    RAISE EXCEPTION 'Cargo inválido: revisar producto, cantidad e importes con hasta dos decimales' USING ERRCODE='22023';
  END IF;
  -- Lock first and create a new MVCC row version without changing business values.
  -- This also rejects stale REPEATABLE READ contenders via serialization failure.
  UPDATE public.cuentas_clientes SET lock_version=lock_version+1 WHERE id=p_cliente_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Cliente inexistente o no autorizado' USING ERRCODE='22023';
  END IF;
  SELECT * INTO v_existing FROM public.cuentas_cargos WHERE request_id=p_request_id;
  IF FOUND THEN
    IF v_existing.cliente_id IS DISTINCT FROM p_cliente_id
       OR v_existing.fecha IS DISTINCT FROM p_fecha
       OR v_existing.producto IS DISTINCT FROM v_producto
       OR v_existing.presentacion IS DISTINCT FROM v_presentacion
       OR v_existing.cantidad IS DISTINCT FROM p_cantidad
       OR v_existing.precio_unitario IS DISTINCT FROM p_precio_unitario
       OR v_existing.costo_total IS DISTINCT FROM p_costo_total THEN
      RAISE EXCEPTION 'El identificador de reintento pertenece a otro cargo' USING ERRCODE='22023';
    END IF;
    RETURN v_existing;
  END IF;
  INSERT INTO public.cuentas_cargos
    (cliente_id,fecha,producto,presentacion,cantidad,precio_unitario,costo_total,request_id)
  VALUES (p_cliente_id,p_fecha,v_producto,v_presentacion,p_cantidad,p_precio_unitario,p_costo_total,p_request_id)
  RETURNING * INTO v_result;
  RETURN v_result;
END
$function$;

CREATE FUNCTION public.registrar_pago_cuenta(
  p_cliente_id bigint, p_fecha date, p_monto numeric, p_nota text,
  p_request_id uuid, p_cargo_ids bigint[] DEFAULT NULL
) RETURNS public.cuentas_pagos
LANGUAGE plpgsql SECURITY INVOKER
SET search_path = ''
SET lock_timeout = '5s'
AS $function$
DECLARE
  v_nota text := btrim(COALESCE(p_nota,''));
  v_selected bigint[];
  v_existing public.cuentas_pagos%ROWTYPE;
  v_result public.cuentas_pagos%ROWTYPE;
  v_available numeric;
  v_remaining numeric := p_monto;
  v_amount numeric;
  v_charge record;
BEGIN
  IF p_fecha IS NULL OR p_request_id IS NULL OR p_monto IS NULL OR p_monto<=0
     OR p_monto IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
     OR p_monto<>pg_catalog.round(p_monto,2) OR p_monto>999999999999.99 OR char_length(v_nota)>1000 THEN
    RAISE EXCEPTION 'Pago inválido: usar un importe positivo con hasta dos decimales' USING ERRCODE='22023';
  END IF;
  IF p_cargo_ids IS NOT NULL THEN
    IF pg_catalog.cardinality(p_cargo_ids)=0 OR pg_catalog.array_position(p_cargo_ids,NULL) IS NOT NULL THEN
      RAISE EXCEPTION 'Seleccioná al menos un producto válido para el pago' USING ERRCODE='22023';
    END IF;
    SELECT pg_catalog.array_agg(DISTINCT u.id ORDER BY u.id) INTO v_selected
      FROM pg_catalog.unnest(p_cargo_ids) AS u(id);
  END IF;
  UPDATE public.cuentas_clientes SET lock_version=lock_version+1 WHERE id=p_cliente_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Cliente inexistente o no autorizado' USING ERRCODE='22023';
  END IF;
  SELECT * INTO v_existing FROM public.cuentas_pagos WHERE request_id=p_request_id;
  IF FOUND THEN
    IF v_existing.cliente_id IS DISTINCT FROM p_cliente_id
       OR v_existing.fecha IS DISTINCT FROM p_fecha
       OR v_existing.monto IS DISTINCT FROM p_monto
       OR v_existing.nota IS DISTINCT FROM v_nota
       OR v_existing.cargo_ids IS DISTINCT FROM v_selected THEN
      RAISE EXCEPTION 'El identificador de reintento pertenece a otro pago' USING ERRCODE='22023';
    END IF;
    RETURN v_existing;
  END IF;
  IF v_selected IS NOT NULL THEN
    IF (SELECT count(*) FROM public.cuentas_cargos
        WHERE cliente_id=p_cliente_id AND id=ANY(v_selected)) <> pg_catalog.cardinality(v_selected) THEN
      RAISE EXCEPTION 'Los productos seleccionados no pertenecen a esta cuenta' USING ERRCODE='22023';
    END IF;
    IF EXISTS (SELECT 1 FROM public.cuentas_cargos WHERE id=ANY(v_selected) AND fecha>p_fecha) THEN
      RAISE EXCEPTION 'La fecha del pago no puede ser anterior a los productos seleccionados' USING ERRCODE='22023';
    END IF;
  END IF;
  SELECT COALESCE(sum(s.saldo),0) INTO v_available
  FROM (
    SELECT c.monto_total-COALESCE(sum(a.monto),0) AS saldo
    FROM public.cuentas_cargos c
    LEFT JOIN public.cuentas_aplicaciones a ON a.cargo_id=c.id
    WHERE c.cliente_id=p_cliente_id AND c.fecha<=p_fecha
      AND (v_selected IS NULL OR c.id=ANY(v_selected))
    GROUP BY c.id
  ) s;
  IF p_monto>v_available THEN
    RAISE EXCEPTION 'El pago supera el saldo pendiente de los productos elegidos para esa fecha' USING ERRCODE='22023';
  END IF;
  INSERT INTO public.cuentas_pagos(cliente_id,fecha,monto,nota,cargo_ids,request_id)
  VALUES (p_cliente_id,p_fecha,p_monto,v_nota,v_selected,p_request_id)
  RETURNING * INTO v_result;
  FOR v_charge IN
    SELECT c.id,c.monto_total-COALESCE(sum(a.monto),0) AS saldo
    FROM public.cuentas_cargos c
    LEFT JOIN public.cuentas_aplicaciones a ON a.cargo_id=c.id
    WHERE c.cliente_id=p_cliente_id AND c.fecha<=p_fecha
      AND (v_selected IS NULL OR c.id=ANY(v_selected))
    GROUP BY c.id
    HAVING c.monto_total>COALESCE(sum(a.monto),0)
    ORDER BY c.fecha,c.id
  LOOP
    EXIT WHEN v_remaining=0;
    v_amount := LEAST(v_remaining,v_charge.saldo);
    INSERT INTO public.cuentas_aplicaciones(cliente_id,pago_id,cargo_id,monto)
    VALUES (p_cliente_id,v_result.id,v_charge.id,v_amount);
    v_remaining := v_remaining-v_amount;
  END LOOP;
  IF v_remaining<>0 THEN
    RAISE EXCEPTION 'No se pudo distribuir el pago completo; no se guardó ningún movimiento';
  END IF;
  RETURN v_result;
END
$function$;

REVOKE ALL ON FUNCTION public.crear_cargo_cuenta(bigint,date,text,text,integer,numeric,numeric,uuid)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.crear_cargo_cuenta(bigint,date,text,text,integer,numeric,numeric,uuid)
  TO service_role;
REVOKE ALL ON FUNCTION public.registrar_pago_cuenta(bigint,date,numeric,text,uuid,bigint[])
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.registrar_pago_cuenta(bigint,date,numeric,text,uuid,bigint[])
  TO service_role;

CREATE FUNCTION public.renombrar_cliente_cuenta(
  p_cliente_id bigint, p_nombre text, p_nombre_anterior text
) RETURNS public.cuentas_clientes
LANGUAGE plpgsql SECURITY INVOKER
SET search_path = ''
SET lock_timeout = '5s'
AS $function$
DECLARE
  v_nombre text := btrim(p_nombre);
  v_result public.cuentas_clientes%ROWTYPE;
BEGIN
  IF p_nombre IS NULL OR char_length(v_nombre) NOT BETWEEN 1 AND 160
     OR p_nombre_anterior IS NULL THEN
    RAISE EXCEPTION 'Escribí un nombre de hasta 160 caracteres' USING ERRCODE='22023';
  END IF;
  SELECT * INTO v_result FROM public.cuentas_clientes WHERE id=p_cliente_id FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Cliente inexistente o no autorizado' USING ERRCODE='22023';
  END IF;
  -- A response may be lost after commit. Repeating the same name is harmless.
  IF v_result.nombre=v_nombre THEN
    RETURN v_result;
  END IF;
  IF v_result.nombre IS DISTINCT FROM p_nombre_anterior THEN
    RAISE EXCEPTION 'El nombre cambió. Recargá la cuenta antes de editarlo' USING ERRCODE='22023';
  END IF;
  UPDATE public.cuentas_clientes SET nombre=v_nombre,lock_version=lock_version+1
    WHERE id=p_cliente_id RETURNING * INTO v_result;
  RETURN v_result;
END
$function$;
REVOKE ALL ON FUNCTION public.renombrar_cliente_cuenta(bigint,text,text)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.renombrar_cliente_cuenta(bigint,text,text)
  TO service_role;

-- La API debe descubrir las tablas y funciones nuevas después del commit.
-- https://docs.postgrest.org/en/v14/references/schema_cache.html
NOTIFY pgrst, 'reload schema';
COMMIT;
