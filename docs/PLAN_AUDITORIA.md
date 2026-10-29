# Dulce Mar — auditoría y plan de recuperación

Fecha: 2026-10-29. Base revisada: `7de41bd605e8a959d5066c2b8b021ef6080569f6`.
Rama local: `audit/dulce-mar-integridad`.

El rediseño visual posterior está documentado en `docs/REDISENO_VISUAL.md`.
Se preparó y probó con datos ficticios; todavía no está publicado.

La ampliación de cuentas por cobrar, cobrado/pendiente y gráficos semanales está
documentada en `docs/CUENTAS_POR_COBRAR.md`. Cuenta con 47 pruebas correctas y
verificaciones integradas en PostgreSQL local. El usuario aprobó explícitamente la
migración y publicación; las tablas nuevas ya se agregaron sin modificar las filas
de las cinco tablas originales. La publicación de la app está en preparación.
Las ventas históricas se consideran cobradas
por confirmación del usuario, sin modificar sus filas.

## Estado y límites de la evidencia

Se inspeccionaron app.py y requirements.txt. La pantalla pública de producción
muestra el inicio con Google y la demostración. El usuario completó el inicio de
sesión privado. No se insertaron, actualizaron ni borraron datos de negocio.
Se accedió al proyecto correcto de Supabase mediante inicio de sesión del usuario.
Se inspeccionaron las cinco tablas de public, columnas, claves, restricciones,
políticas y privilegios de la API. Las cinco usan id bigint como clave primaria.
Se generó un archivo nativo de toda la base, esquema SQL y roles sin contraseñas,
con manifiesto SHA-256; se conservan fuera del repositorio. Además se exportaron
las tablas y sus metadatos en JSON exacto, evitando redondeos de enteros del navegador.
La aplicación restaurada localmente coincide en todas las filas y valores, columnas,
restricciones, secuencias y políticas RLS. Los esquemas administrados de Supabase
están en el archivo nativo, pero su restauración como plataforma completa no se
certificó. No hay usuarios en Supabase Auth ni buckets/objetos de Storage.
La configuración existente de Streamlit/Google está respaldada en privado; no se
modificó. Se verificó que su clave de servidor permite las lecturas de las cinco
tablas. El usuario completó el ingreso real con Google y se verificaron el modo
privado y la pantalla de registro de venta, sin guardar operaciones.
El 2026-10-29 se retiró de producción la política pública de ventas con aprobación
explícita del usuario, después del respaldo y las pruebas locales. RLS sigue activo.
Se verificó con los roles reales anon y authenticated que no pueden leer ventas;
la clave del servidor sigue leyendo las cinco tablas y todas sus filas/valores
coinciden con el respaldo. La sesión privada sigue abierta sin error de conexión.
La reversión permanece disponible y no se ejecutó. Main y el despliegue no cambiaron.
Esto resuelve la exposición identificada; no constituye certificación completa de seguridad.

## Prioridades

1. P0: respaldo nativo generado y recuperación de la aplicación verificada en
   PostgreSQL local aislado. Configuración de Streamlit preservada, acceso Google
   verificado y corrección puntual de permisos aplicada con aprobación explícita.
2. P0: eliminar escrituras automáticas al iniciar y detener reportes/importación
   cuando fallen lecturas necesarias. Preparado localmente, pendiente de staging.
3. P0: límite de la API confirmado en 1000 filas. Se corrigieron catálogos, dashboard
   y comparación de importaciones con paginación por id y conteo exacto. Verificadas
   contra la API real con consultas SELECT de ids, sin escrituras. No es un snapshot
   transaccional entre peticiones: cierres contables concurrentes necesitarán SQL/RPC.
4. P0 resuelto: ventas tenía una política ALL para public con USING true / WITH CHECK true,
   grants de SELECT/INSERT/UPDATE/DELETE para anon, y está expuesta en Data API.
   Las otras cuatro tablas tienen RLS activo sin políticas. La clave de servidor
   existente lee las cinco. Google en Streamlit no implica una sesión Supabase:
   se retiró únicamente esa política pública, conservando el acceso de servidor.
   El SQL aplicado y su reversión están en proposed_migrations/. En la copia restaurada
   se verificó: anon/authenticated no ven ventas; anon no inserta, modifica ni borra;
   service_role (BYPASSRLS, como en origen) conserva SELECT/INSERT/UPDATE/DELETE.
   Las escrituras de prueba fueron sintéticas y se revirtieron en transacciones.
   También se probó que la propuesta se niega a ejecutar sin habilitación explícita.
   Solo el cambio de retirada se ejecutó en producción tras la aprobación. Las
   pruebas productivas fueron SELECT; las escrituras de prueba se limitaron a staging.
5. P1: importación idempotente y transaccional. La comparación por contenido no
   distingue reintentos concurrentes ni archivos parcialmente importados. El lote
   actual puede quedar parcialmente insertado; preservar operaciones legítimas.
6. P1: caja con medios de pago, saldos, cierres y ajustes trazables; definir requisitos
   con la usuaria. No reinterpretar ventas viejas ni inventar movimientos históricos.
7. P1: validar importes, fechas, rendimientos y costos; mantener aparte las estimaciones
   históricas y los costos guardados al vender. Evaluar numeric/Decimal tras inventario.
8. P2: separar acceso a datos, cálculo financiero y pantallas; mejorar navegación,
   accesibilidad, exportaciones y diagnóstico sin exponer datos ni secretos.

## Cambios locales preparados

- Catálogos vacíos o fallidos detienen la app privada; nunca crean registros de ejemplo.
- La conversión de naranjas queda limitada a demo. Precios y recetas reales se leen
  tal como están guardados; cualquier conversión futura requiere migración explícita.
- Dashboard se detiene si falla ventas, gastos o mermas. Importación se detiene
  si no puede comprobar ventas existentes. Mensajes de estos errores sin detalles internos.
- Lecturas paginadas por id con límite superior fijo y conteos antes/después;
  detectan páginas incompletas, falta de avance y cambios de cantidad de registros.
- Google, lista de acceso y contratos de tablas conservados. La única migración
  productiva fue la retirada de la política pública aprobada; sin cambios de datos.
- Exclusiones Git para secretos y respaldos; pruebas sin red ni datos reales.

## Respaldo: alcance y condiciones de aceptación

1. Confirmar proyecto/ref con el usuario y con la configuración de Streamlit, sin
   copiar valores secretos al chat o a Git. Inventariar todos los esquemas, no solo
   las cinco tablas conocidas; columnas, tipos, defaults, PK/FK, índices, secuencias,
   vistas, funciones, triggers, extensiones, roles/grants y políticas RLS.
2. Capturar conteos exactos por tabla y controles financieros por período sin datos
   individuales en el informe público. Guardar detalle solo en copia privada.
3. Exportar esquema, datos y roles usando un método compatible con la versión de
   Postgres y Supabase. Verificar alcance de auth/storage y objetos administrados.
   Las contraseñas de roles y los objetos de Storage no están cubiertos por un
   respaldo estándar: revisar almacenamiento y descargar sus archivos por separado
   si existen. No considerar CSV de cinco tablas como respaldo completo.
4. Registrar configuración relevante (OAuth Google de Streamlit, redirects,
   versiones, secretos requeridos, Auth de Supabase si se usa, Storage, funciones,
   tareas e integraciones). Preservar secretos en almacenamiento privado protegido,
   fuera del repo, con recuperación comprobada; nunca en documentos públicos.
5. Crear manifiesto con fecha, versión, alcance, tamaños y SHA-256 de los archivos.
   Un hash verifica el archivo, no su restaurabilidad.
6. Restaurar en una base/proyecto aislado sin conexión de escritura a producción.
   Comparar conteos, constraints, RLS, secuencias, agregados e integridad referencial;
   verificar autenticación con Google y rechazo de usuarios no autorizados.
7. Mantener registro de resultado y ubicación privada. Solo marcar respaldo como
   verificado después de restauración y reconciliación satisfactorias.

Referencia: https://supabase.com/docs/guides/platform/backups

## Staging y liberación

Usar una base de pruebas separada y datos sintéticos primero. Nunca configurar
staging con claves de producción. Validar Google con su redirect de staging sin
reemplazar el de producción. Comprobar demo, catálogos, carga de venta, historial,
importación con reintentos, reportes y errores de red/permisos.

No desplegar esta rama mientras sigan pendientes las pruebas integradas de escritura
con Streamlit/Supabase en staging y la aprobación explícita de publicación.
Se dispone de PostgreSQL local en loopback con autenticación propia; no es una
instancia completa de Supabase ni usa claves productivas para escribir.
Presentar cambios y resultados al usuario.
Para migración, merge a main o despliegue productivo: aprobación explícita del
usuario, copia recuperable y plan de reversión comprobado. No revertir mediante
restauración sobre producción sin evaluar las ventas ingresadas desde el respaldo.

## Validación local

`python -m unittest discover -s tests -v`

Pruebas aisladas ejecutan las funciones y bloques reales extraídos del AST con
dobles de base de datos. Cubren catálogos vacíos/fallidos, preservación de valores,
ausencia de conversión privada y bloqueo de reportes/importación tras fallos.
Además, AppTest verifica pantalla de acceso, rechazo de una identidad no autorizada
y las tres páginas de demostración sin inicializar el cliente Supabase.
Resultado: 18 pruebas correctas; compilación Python y revisión de diff correctas.
Además, ocho pantallas privadas se comprobaron con copia de datos y cliente de
red simulado, sin intentos de escritura. Por separado se verificaron lecturas
paginadas contra Supabase y la restauración de la aplicación en PostgreSQL local.
OAuth se simula en AppTest; esas pruebas no certifican Google real.
Se detectaron advertencias de Streamlit por
use_container_width; su actualización queda para la revisión de versiones.
