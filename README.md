# Sistema de Control de Calidad — App web (demo)

App de control de calidad con interfaz web moderna que corre LOCAL en tu
computadora (NO usa internet, NO sube datos a ningún lado). Login, evaluación en
dos fases según el consultor, historial de lotes, reportes PDF y exportación a Excel.

## Cómo abrir

Doble clic en **Abrir_App.bat**. Se abre una ventana negra (el servidor; no la
cierres mientras usas la app) y la app aparece sola en tu navegador.
Equivalente en consola: `py servidor.py`.
Login: usuario **admin**, contraseña **1234**.

## Requisitos (una sola vez)

```
py -m pip install -r requirements.txt
```

(Solo `openpyxl` y `reportlab`, para reportes y exportación; el servidor web
usa únicamente la librería estándar de Python.)

## Lógica de evaluación (según el consultor)

Recibe el **archivo JSON** que sale directo del equipo (también acepta el Excel
del equipo por compatibilidad). Por canal calcula media, desviación estándar y
rango, y evalúa en DOS FASES contra los límites del perfil:

- **Fase 1 — Desviación (primero):** la desviación debe estar dentro del rango
  [mín, máx] del consultor. Si falla, se detiene y alerta.
- **Fase 2 — Promedio (si pasó la fase 1):** el promedio debe estar dentro del
  rango [mín, máx] del consultor.

Canales: **10 ópticos** (`415, 445, 480, 515, 555, 590, 630, 680, CLEAR, >700`,
20 mediciones cada uno) + **4 eléctricos** (uno por frecuencia: `2000Hz, 3000Hz,
4000Hz, 5000Hz`, agrupando los 3 electrodos = 60 valores cada uno, igual que el
cálculo manual del área de calidad).

Veredictos posibles:

- **PASÓ** — todos los canales dentro de límites en ambas fases.
- **NO PASÓ** — al menos un canal falló; se recomienda repetir la prueba.
- **INCOMPLETO** — ningún canal falló, pero hay canales sin límite definido en
  el perfil: no se puede afirmar que pasó (nunca se aprueba sin comparar).
- **RECHAZADO** — el archivo no tiene el formato del equipo (deben venir
  10 ópticos + 4 eléctricos); no se evalúa.

> **Pendiente (consultor):** la regla "variabilidad no mayor a las anteriores"
> (comparar contra el mejor histórico por canal) está **desactivada** hasta
> tener su definición exacta. Hoy se evalúa únicamente contra los límites del
> perfil. El código conserva el mecanismo para reactivarla cuando se defina.

## Las 5 secciones

1. **Procesar corrida** — seleccionas los JSON de la corrida, eliges el perfil de
   estándar, lote y operador, evalúas. Ves cada pieza con resultado por prueba y
   alerta de repetición si falla. Clic en una pieza para ver el detalle por canal.
2. **Estándar de calidad** — defines por canal: rango de desviación (mín/máx) y
   rango de media (mín/máx) que da el consultor. Lo guardas como perfil reutilizable.
   Los límites **siempre** vienen del consultor; un campo vacío = ese criterio
   no se evalúa (y la pieza sale INCOMPLETO, no aprobada).
3. **Dashboard** — resumen (KPIs), alertas de desechables a repetir, análisis
   (gráfica con selector de alcance + Pareto de canales que más fallan) y lotes
   clicables.
4. **Historial de lotes** — todos los lotes evaluados, con buscador. Clic en
   cualquiera para ver su detalle, corregir (eliminar pieza/lote) o reimprimir.
5. **Ajustes** — carpeta de tu Drive para las copias automáticas de los Excel
   exportados (detecta Google Drive para escritorio, OneDrive y Dropbox).

## Reportes y exportación

- **Reporte PDF** individual por pieza o del lote completo (con logo, firmas,
  resultado por prueba y fases).
- **Exportar a Excel**: genera un .xlsx con el resumen y el respaldo de
  verificación por canal, en la carpeta `Reportes_QC` de tu usuario.
- **Copia automática a tu Drive**: en **Ajustes** eliges una carpeta destino
  (p. ej. dentro de Google Drive para escritorio, OneDrive o Dropbox) y cada
  Excel exportado se copia ahí; el programa del Drive es quien lo sube a la
  nube. La app sigue sin usar internet, y si la copia falla el Excel local ya
  quedó guardado y la app te avisa el motivo.

## Almacenamiento

Todo en `qc_datos.db` (un archivo SQLite local, junto a los .py). El historial
persiste. **No se versiona en git** (está en `.gitignore`): respáldalo aparte.
El diseño separa los datos del resto, de modo que escalar a la nube solo
requiere cambiar esa capa.

## Tests

```
py -m unittest discover -s tests -v
```

- `tests/test_parser.py` — caso de referencia con una **corrida real** del
  equipo (`tests/datos/`): media/desviación/rango de los 14 canales verificados
  contra la hoja de cálculos manuales del área de calidad.
- `tests/test_evaluador.py` — lógica de dos fases, orden de fases, veredictos
  y casos borde (con límites sintéticos de prueba, no del consultor).

## Estructura del repositorio

```
servidor.py      servidor web local (stdlib) + API
parser.py        lee el JSON/Excel del equipo y calcula media/desv/rango
evaluador.py     evaluación en dos fases contra el perfil
db.py            capa de datos SQLite (perfiles, lotes, resultados, usuarios)
reporte.py       reportes PDF (pieza y lote)
exportar.py      Excel de verificación por lote
drive.py         copia de los Excel a la carpeta sincronizada del Drive
piezas.py        número de pieza a partir del nombre del archivo
web/             interfaz (index.html + app.js)
tests/           suite de verificación (unittest, stdlib)
legacy/          código anterior sin mantenimiento (app Tkinter)
```

## Pendientes

- Confirmar con el consultor la definición exacta de "variabilidad no mayor a
  las anteriores" y, con esa definición, reactivar la comparación histórica.
- Crear el perfil de límites real y completo (10 ópticos + 4 eléctricos) con
  los valores del área de calidad. **Ningún límite se inventa.**
- Personalizar nombre de empresa y logo en `reporte.py`.
- Escalamiento futuro: nube (multiusuario) + validación IQ/OQ/PQ. Nota: la
  autenticación actual es solo para uso local; para nube se rehace (sesiones,
  hash de contraseña robusto, autorización por endpoint).
