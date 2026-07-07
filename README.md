# Sistema de Control de Calidad — App web (demo)

App de control de calidad con interfaz web moderna que corre LOCAL en tu
computadora (NO usa internet, NO sube datos a ningún lado). Login, evaluación en
dos fases según el consultor, historial de lotes, reportes PDF y exportación a Excel.

## Cómo abrir

Doble clic en **Abrir_App.bat**. Se abre una ventana negra (el servidor; no la
cierres mientras usas la app) y la app aparece sola en tu navegador.
Login: usuario **admin**, contraseña **1234**.

## Requisitos (una sola vez)

```
py -m pip install openpyxl reportlab
```

## Lógica de evaluación (según el consultor)

Recibe el **archivo JSON** que sale directo del equipo. Por cada canal (10 ópticos
+ 4 eléctricos, uno por frecuencia) calcula media, desviación estándar y rango, y evalúa en DOS FASES:

- **Fase 1 — Desviación (primero):** la desviación debe estar dentro del rango
  [mín, máx] del consultor, Y no puede ser mayor que el mejor (menor) histórico
  registrado para ese canal. Si falla, se detiene y alerta.
- **Fase 2 — Promedio (si pasó la fase 1):** el promedio debe estar dentro del
  rango [mín, máx] del consultor.

Si falla cualquier fase, el sistema marca **NO PASÓ** y recomienda repetir la prueba.
El desechable pasa solo si todos sus canales pasan ambas fases.

## Las 4 secciones

1. **Procesar corrida** — seleccionas los JSON de la corrida, eliges el perfil de
   estándar, lote y operador, evalúas. Ves cada pieza con resultado por prueba y
   alerta de repetición si falla. Clic en una pieza para ver el detalle por canal
   (media, desviación, rango, rangos del estándar y mejor histórico).
2. **Estándar de calidad** — defines por canal: rango de desviación (mín/máx) y
   rango de media (mín/máx) que da el consultor. Lo guardas como perfil reutilizable.
3. **Dashboard** — visión global: aprobación por lote en el tiempo y canales que
   más fallan.
4. **Historial de lotes** — todos los lotes evaluados, con buscador. Clic en
   cualquiera para ver su detalle y gráficas, aunque sea de hace meses.

## Reportes y exportación

- **Reporte PDF** individual por pieza o del lote completo (con logo, firmas,
  resultado por prueba y fases).
- **Exportar a Excel**: genera un .xlsx con el resumen y el detalle por canal, en
  la carpeta `Reportes_QC` de tu usuario, listo para subir a Drive.

## Almacenamiento

Todo en `qc_datos.db` (un archivo local). El historial persiste. El diseño separa
los datos del resto, de modo que escalar a la nube solo requiere cambiar esa capa.

## Pendientes

- Confirmar con el consultor el detalle fino de "variabilidad no mayor a las
  anteriores" (hoy se compara contra el mejor/menor histórico de cada canal).
- Personalizar nombre de empresa y logo en `reporte.py`.
- Escalamiento futuro: nube (acceso multiusuario) + validación IQ/OQ/PQ.
