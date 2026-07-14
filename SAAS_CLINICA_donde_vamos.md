# SaaS Clínica — Dónde vamos (nota de avance)

_Última actualización: 2026-07-09_

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

14. **Excel de exportación con formato de documento de liberación** (2026-07-09):
    3 hojas — *Reporte de liberación* (membrete, datos del lote, dictamen
    CONFORME / NO CONFORME / INCOMPLETO, resumen con índice de aprobación,
    criterios y tabla de firmas Elaboró/Revisó/Aprobó), *Resultados por pieza*
    y *Verificación de cálculos* — con membrete corporativo (mismo nombre de
    empresa que el PDF, editable en `reporte.py`) y configuración de impresión.
15. **Corrección del evaluador** (2026-07-09): un canal cuyo estándar tiene
    los 4 campos vacíos ahora cuenta como SIN ESTÁNDAR (antes se daba por
    pasado). Un perfil totalmente vacío ya no puede aprobar piezas ni producir
    un dictamen de lote CONFORME. Con test nuevo en `tests/test_evaluador.py`.

## Pendiente (de mi lado)
- Crear un **perfil de límites real y completo** (10 ópticos + 4 eléctricos) con los valores del área de calidad.
- Correr una prueba real completa desde la interfaz (subir los JSON con un perfil real).

## Idea a futuro (opcional)
- Barra de progreso al procesar muchos archivos (aunque con JSON es casi instantáneo).
