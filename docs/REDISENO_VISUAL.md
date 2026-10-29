# Dulce Mar — rediseño visual

## Dirección

Una herramienta de trabajo para una pastelería: clara, tranquila y con una
identidad ligada al nombre Dulce Mar. Se conserva Streamlit y sus controles nativos.
El diseño usa papel claro, verdes marinos y tipografía editorial en los títulos;
los importes mantienen cifras tabulares y suficiente espacio para leerlos.

| Uso | Color |
| --- | --- |
| Fondo | `#F7FAF9` |
| Navegación y superficies suaves | `#E9F3F0` |
| Texto | `#183C42` |
| Acciones | `#176B65` |
| Acento secundario | `#F0D99A` |
| Texto secundario | `#576F72` |

Georgia se usa en la marca y títulos; Aptos/Segoe UI/Arial en controles e importes.
No se agregan bibliotecas, imágenes remotas, servicios ni fuentes de terceros.

## Cambios

- Bienvenida en dos columnas, marca propia y acceso con Google destacado.
- Navegación breve, destino activo visible y acciones secundarias debajo del menú.
- Venta con formulario a la izquierda y resumen con guardado a la derecha.
- Historial plegable con las mismas operaciones y paginación anteriores.
- Resultado operativo destacado en el dashboard; evolución, productos y detalle
  se organizan en pestañas. Los gráficos comparten colores, ejes y formato.
- Catálogo más ancho, importes numéricos ordenables y tablas con altura ajustada.
- Formularios y pestañas consistentes en insumos, gastos, mermas y calculadora.
- Fechas en día/mes/año e importes principales con separadores argentinos.
- Distribución móvil de indicadores en dos columnas, foco de teclado visible y
  respeto por la preferencia de movimiento reducido.

## Conservación de comportamiento

Se mantienen el acceso con Google, la lista de cuentas autorizadas, los nombres
internos de navegación, las validaciones de guardado y los cálculos financieros.
Las filas de ventas conservan los mismos campos y valores; CSV y filtros mantienen
su fuente de datos. La reorganización no ejecuta SQL ni modifica la base de datos.
La tabla de precios ahora conserva números para que su ordenamiento sea correcto.
Los textos dinámicos del historial se escapan antes de mostrarlos como HTML.

## Verificación

Probado con Streamlit 1.63.0 y Python 3.14:

- Suite existente: 18 pruebas correctas.
- Ocho pantallas privadas, ingreso y tres páginas de demostración sin errores.
- Venta ficticia con cantidad dos: precio sugerido actualizado y guardado con
  monto, costo y margen exactos.
- Dashboard: pestañas, filtro de fechas y CSV verificados.
- Vista de 390 × 844: sin desplazamiento horizontal ni importes cortados.
- Revisión de código independiente: no se encontraron cambios en cálculos,
  autenticación ni contenido de las escrituras.

La vista previa usa únicamente datos ficticios y un cliente simulado sin acceso
a la red. No usa los secretos ni la base de producción. No certifica por sí sola
una integración completa de Supabase con escrituras productivas.

## Entrega

Preparado en `audit/dulce-mar-integridad`, sin publicación ni cambios en main.
La aplicación pública conserva su versión actual. La publicación de esta nueva
versión requiere revisión y aprobación explícita del usuario, según lo acordado.
