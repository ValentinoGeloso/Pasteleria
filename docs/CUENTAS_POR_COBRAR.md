# Dulce Mar — cuentas por cobrar y evolución de ventas

Preparado el 29/10/2026 en `audit/dulce-mar-integridad`. La migración aditiva fue
aprobada explícitamente y aplicada; la publicación de la app está en preparación.
Todas las escrituras de prueba usan datos
sintéticos y PostgreSQL local; no se cargaron operaciones financieras reales.

## Comportamiento

- El aviso extenso de importación queda dentro de «Criterios de importación»,
  cerrado inicialmente. Los controles del archivo siguen activos.
- Evolución diaria, semanal y mensual. La semanal es la vista inicial y agrupa
  de lunes a domingo; los extremos respetan el período elegido sin extrapolar.
- El gráfico de margen porcentual se reemplaza por cantidad vendida. Usa las
  unidades/porciones equivalentes de la receta, indicadas junto al gráfico.
- «Cuentas por cobrar» permite crear una persona, agregar productos entregados
  pendientes, consultar su detalle y registrar pagos parciales o completos.
- La pestaña «Personas» permite crear cuentas sin productos y editar el nombre.
  Se conserva la misma identidad de cuenta, sus productos, pagos y saldos. Si otro
  usuario cambió el nombre mientras se editaba, se exige recargar antes de reemplazarlo.
- Un pago puede cubrir productos concretos o aplicarse a los productos más
  antiguos con saldo. No admite pagar más del saldo ni antes de la entrega.
- Los reintentos conservan un identificador único. Si una respuesta se pierde,
  se bloquea un nuevo movimiento hasta confirmar el anterior.

El usuario confirmó expresamente que todas las ventas existentes están cobradas.
La pantalla anterior pasa a llamarse «Ventas cobradas». Los productos pendientes
se cargan únicamente en la cuenta: no deben cargarse también como venta cobrada.

## Criterio del resumen

| Indicador | Cálculo |
| --- | --- |
| Cobrado | Ventas cobradas del período + pagos de cuentas recibidos en el período |
| Saldo por cobrar | Todos los productos entregados hasta la fecha final menos sus pagos hasta esa fecha |
| Cobrado + pendiente | Cobrado del período + saldo acumulado al cierre; es una proyección, no efectivo disponible |
| Ventas del período | Ventas cobradas + productos a cuenta entregados en ese período |

El cobro de una cuenta no genera otra venta ni vuelve a sumar ingresos al resultado.
El costo del producto a cuenta se conserva al registrarlo. El resultado operativo
incluye lo vendido a cuenta y por eso puede diferir del dinero disponible.
El saldo acumulado puede incluir deudas anteriores al período seleccionado.
Los exportados distinguen venta cobrada y venta a cuenta con referencias diferentes.
Si falta una tabla o falla la lectura, el resumen se detiene; no presenta deuda cero.

## Persistencia propuesta

`proposed_migrations/002_customer_accounts.sql` agrega cuatro tablas independientes:
clientes, cargos, pagos y aplicaciones de pagos. No modifica las tablas existentes
de ventas, productos, insumos, gastos ni mermas. Conserva el acceso actual con Google.
Los importes usan `numeric(14,2)` y Decimal en Python. Las claves foráneas evitan
cruzar pagos entre personas; las funciones guardan cada movimiento en una transacción
y serializan la cuenta para impedir sobrepagos concurrentes.

RLS permanece habilitado. Las tablas y funciones están disponibles solamente para
la clave de servidor existente; no se dan permisos a `anon` ni `authenticated`.
Las funciones son `SECURITY INVOKER` y fijan el search_path. El acceso Google sigue
siendo controlado por Streamlit y su lista de correos autorizados, como hasta ahora.

## Verificación

- 47 pruebas unitarias y de aplicación correctas, incluidas conservación de datos,
  acceso, demo, importación, cuentas, precisión decimal y cálculos del resumen.
- AppTest de nueve pantallas privadas con red bloqueada: alta de persona/producto,
  pago parcial, pago de productos elegidos, cancelación completa de deuda,
  conciliación del resumen y ausencia de duplicados en ventas.
- PostgreSQL local real: migración protegida, permisos/RLS, centavos, reintentos,
  referencias, fechas, sobrepagos y dos pagos concurrentes. También se prueba
  una transacción con snapshot anterior en aislamiento REPEATABLE READ.
- Servicio Python contra esas funciones SQL reales usando `service_role`:
  alta independiente de personas, cambio de nombre, reintentos, cobros parciales
  y cancelación exacta de saldo. El renombrado conserva los registros financieros.
- Las tablas históricas sintéticas conservan su contenido después de la migración.

Límites: no es un proyecto Supabase remoto de staging. Se verificaron por HTTP en
producción la lectura de las cuatro tablas y el rechazo de clientes inexistentes en
las tres funciones, sin insertar datos ficticios. Los flujos válidos de escritura
se probaron en PostgreSQL local. La lectura de las
cuatro tablas se valida y reintenta ante inconsistencias; no usa un único snapshot
global. Google real se verificó previamente en producción; AppTest lo simula.

## Liberación y reversión

Se requiere aprobación explícita antes de agregar las tablas o publicar. Tras ella:

1. Refrescar el respaldo nativo privado, esquema, roles y configuración relevante;
   registrar hashes y verificar recuperación antes de la migración.
2. Confirmar rama/base, tablas y privilegios actuales. Ejecutar el SQL protegido en
   una transacción, con `SET LOCAL dulce_mar.approved_change = 'create_customer_accounts'`
   dentro del BEGIN existente, después de revisar la condición exacta del archivo.
3. Verificar tablas vacías, restricciones, permisos y descubrimiento de RPC por API.
   Comprobar rechazo de argumentos inválidos sin insertar registros ficticios reales.
4. Publicar solo con la aprobación del usuario y verificar Google, lecturas, carga
   de páginas y resumen. La primera operación real debe ser una operación del negocio.

Si falla la migración antes del COMMIT, la transacción revierte completa. Si falla
la versión publicada, volver al commit anterior de la aplicación y conservar las
tablas nuevas con todos sus movimientos. No borrarlas ni restaurar una copia vieja
sobre producción: podría perderse lo ingresado después del respaldo. El código
anterior no muestra las cuentas nuevas; su detalle debe conservarse para recuperación.

No hay secretos ni copias con datos reales en Git o en los entregables públicos.

Se actualizó el respaldo nativo antes de la liberación y se restauró en PostgreSQL
local. Filas/valores, columnas, restricciones, secuencias y políticas RLS coincidieron
con una exportación reciente de producción. La migración 002 se aplicó con aprobación
explícita posterior; las filas de las cinco tablas originales permanecen iguales.
