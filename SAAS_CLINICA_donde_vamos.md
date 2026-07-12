# SaaS Clínica — Dónde vamos (nota de avance)

_Última actualización: 2026-07-12_

App web de control de calidad para dispositivo médico. Se abre con **Abrir_App.bat**.
Tras cualquier cambio: **reiniciar el servidor** (cerrar ventana negra + volver a abrir el .bat) y **Ctrl+F5** en el navegador.

## Ya está hecho y probado
1. Cálculos de media/desviación/rango correctos (el error estaba en la hoja manual: usaba `AVEDEV` en vez de `PROMEDIO`).
2. Canales ópticos con nombres reales: `415, 445, 480, 515, 555, 590, 630, 680, CLEAR, >700`.
3. Evaluación basada SOLO en los límites del perfil (se quitó la comparación con el histórico).
4. Veredicto seguro: PASÓ / NO PASÓ / INCOMPLETO (+ RECHAZADO si el archivo no es del formato).
5. Vista de lote grande: mapa de cuadros clicables + ventana de detalle + tabla "requieren atención".
6. Al guardar un perfil, la app bloquea rangos invertidos (mínimo mayor que máximo).
7. Se rechazan archivos fuera de formato (deben traer 10 ópticos + 4 eléctricos).
8. Dashboard mejorado: además de las gráficas, ahora hay una lista de **lotes clicables** (color por % de aprobación) que abren el mapa de piezas y el detalle.
9. **Corregir pruebas mal hechas**: se puede **eliminar un lote completo** (botón rojo en el detalle) y **eliminar una pieza suelta** (botón rojo en la ventana de detalle de la pieza). Al borrar una pieza, los % del lote se recalculan solos. Ambos con confirmación.
10. **Dashboard reorganizado en 3 capas** (una por cada persona que lo usa):
    - **Resumen** (para el jefe): KPIs separando Pasaron / No pasaron / Incompletos / Rechazados (ya no se mezclan los rechazados como si fueran fallas) + % de aprobación global.
    - **🔔 Alertas — desechables a repetir** (para el operador): tabla clara de qué pieza no pasó, en qué lote, dónde falló y "↻ Repetir en el siguiente desechable". Clic en una fila abre su detalle.
    - **Análisis** (para el ingeniero): la gráfica ahora tiene un **selector de alcance**: Todo / Por día / Por lote / Un desechable. La línea tiene escala 0–100% y línea de **meta 95%**. "Un desechable" muestra la media de cada canal dentro de su **banda de límite** [mín–máx] (verde dentro, rojo fuera). Debajo sigue el **Pareto** de canales que más fallan.

11. **Cálculos validados contra la hoja manual con datos reales** (2026-07-07):
    los 14 canales (10 ópticos + 4 eléctricos, n=60 por frecuencia) de una
    corrida real (SN 13, 2026-03-19) coinciden con `calculos_manuales.xlsx`
    en media, desviación y rango (diferencia < 0.01), leyendo tanto el JSON
    como el Excel del equipo. Quedó como **test automatizado** en `tests/`
    (`py -m unittest discover -s tests -v`).
12. **Limpieza del repositorio** (2026-07-07): `.gitignore` (la base
    `qc_datos.db` y `__pycache__` ya no se versionan — respalda la base
    aparte), `requirements.txt`, `Abrir_App.bat` versionado, app Tkinter
    vieja movida a `legacy/`, y correcciones: ruta absoluta de la base de
    datos, veredicto RECHAZADO ahora sale en PDF y Excel, botones "Reporte de
    esta pieza" y "Eliminar lote" reparados, documentación alineada con el
    comportamiento real (la comparación histórica está desactivada hasta que
    el consultor la defina).

13. **Los Excel exportados se guardan directo en tu Drive** (2026-07-09):
    nueva sección **Ajustes** donde eliges una carpeta destino; la app detecta
    los Drives instalados (OneDrive, Google Drive para escritorio, Dropbox) y
    propone una subcarpeta `Reportes_QC` dentro. Cada "Excel de verificación"
    exportado se guarda directamente en esa carpeta y el programa del Drive lo
    sube solo a la nube (la app sigue 100% local, sin internet). Si la carpeta
    no está disponible al exportar —o no configuraste ninguna— el Excel sale
    en la carpeta local `Reportes_QC`, como siempre, y el aviso dice el
    motivo. Con tests en `tests/test_drive.py`.

14. **Rediseño de los reportes PDF y del Excel de verificación** (2026-07-12):
    - **PDF (pieza y lote)**: formato de documento controlado — pie de página en
      todas las hojas con folio, fecha de generación y "Página X de Y"; franja
      con el criterio de dos fases bajo el encabezado; trazabilidad en cajas
      etiquetadas; veredicto con glifo (✓/✗/!); la tabla de detalle ahora separa
      **Fase 1 (desviación)** y **Fase 2 (promedio)** con sus límites, resalta en
      rojo el valor que provocó la falla y agrega una barra **"Posición"** que
      muestra dónde cae cada valor dentro de la zona permitida. La portada del
      lote trae tarjetas KPI, barra de distribución con leyenda y columna de
      canales con falla; firmas con nombre, rol y fecha.
    - **Excel**: el Resumen agrega gráfica de dona con la distribución del lote,
      el criterio de aceptación y configuración de impresión. La hoja
      **Verificación de cálculos** ahora es un respaldo de auditoría real: por
      canal muestra los límites de cada fase, el resultado de cada fase
      (✓ Dentro / ✗ Fuera / — No evaluada) y una columna **"Comprobación Excel"**
      con una fórmula viva que recalcula el veredicto dentro del propio Excel
      (independiente de la app, con formato condicional): si no coincide con
      "Estado (app)", algo anda mal. Impresión en horizontal con encabezados
      repetidos en cada página.

15. **Identidad Hera Diagnostics + reportes sobrios + PDF al Drive** (2026-07-12):
    - **Marca**: la interfaz, los PDF y el Excel usan ahora la paleta morada de
      Hera Diagnostics (tokens centralizados: 6 valores en `reporte.py`, 5 en
      `exportar.py` y las variables CSS de `web/index.html` — ajustar ahí si el
      manual de marca da otros códigos). El nombre "Hera Diagnostics" aparece en
      login, barra lateral, encabezados de PDF y subtítulos del Excel.
    - **Reportes más sobrios**: se quitaron las notas explicativas largas y se
      acortaron los textos del encabezado y del veredicto.
    - **Sin solapamiento**: formato numérico compacto (los valores ≥1000 pierden
      decimales y usan separador de miles) para que los canales ópticos en
      decenas de miles quepan en su columna; columnas reequilibradas y formato
      de miles también en el Excel.
    - **PDF al Drive**: los reportes PDF (pieza y lote) ahora se guardan en la
      misma carpeta del Drive configurada en Ajustes, igual que el Excel (con el
      mismo aviso si la carpeta no está disponible).

## Pendiente (de mi lado)
- Crear un **perfil de límites real y completo** (10 ópticos + 4 eléctricos) con los valores del área de calidad.
- Correr una prueba real completa desde la interfaz (subir los JSON con un perfil real).

## Idea a futuro (opcional)
- Barra de progreso al procesar muchos archivos (aunque con JSON es casi instantáneo).
