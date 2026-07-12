"""
exportar.py — Exporta los datos finales de un lote a un archivo Excel (.xlsx)
con formato de reporte profesional: título, bloque de datos del lote con
etiquetas sombreadas, indicadores con color, gráfica de distribución, bandas
de sección y estados coloreados.

Genera dos hojas:
  - Resumen: datos del lote + indicadores + gráfica de dona + una fila por
    pieza agrupada en bandas por veredicto (primero las que requieren atención).
  - Verificación de cálculos: el respaldo de auditoría del cálculo. Por cada
    canal muestra el valor medido, los límites de cada fase, el resultado de
    cada fase y una columna "Comprobación Excel" con una FÓRMULA VIVA que
    recalcula el veredicto dentro del propio Excel (independiente de la app):
    si la fórmula y la columna "Estado (app)" no coinciden, algo anda mal.
"""
from datetime import datetime

from openpyxl import Workbook
from openpyxl.chart import DoughnutChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.series import DataPoint
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.properties import PageSetupProperties

# ---- paleta corporativa Hera Diagnostics (alineada con la interfaz y el PDF) ----
# Colores de marca centralizados: ajustar estos 5 valores basta para retematizar el Excel.
MARINO = '3B1B55'       # morado profundo: título, encabezados fuertes
AZUL = '5E2379'         # morado principal: encabezados de tabla
AZUL_MEDIO = '7B44A3'   # morado medio: grupo Fase 2
AZUL_ETIQUETA = 'EDE3F6'  # fondo de las etiquetas del bloque de datos
ZEBRA = 'F7F3FB'        # fila alterna de las tablas
GRIS_NOTA = '5A6472'

VERDE_BG = 'C6EFCE'; VERDE_TX = '006100'; VERDE_FUERTE = '12A15A'
ROJO_BG = 'FFC7CE'; ROJO_TX = '9C0006'; ROJO_FUERTE = 'D03B3B'
AMBAR_BG = 'FFF2CC'; AMBAR_TX = '9C6500'; AMBAR_FUERTE = 'E9A23B'
GRIS_BG = 'EDEDED'; GRIS_TX = '3A3A3A'; GRIS_FUERTE = '5A6472'

# bandas de sección por veredicto (fondo fuerte + texto blanco)
BANDAS = {
    'NO PASO':    (ROJO_FUERTE, 'NO PASARON — repetir la prueba'),
    'INCOMPLETO': (AMBAR_FUERTE, 'SIN ESTÁNDAR — completar el perfil'),
    'RECHAZADO':  (GRIS_FUERTE, 'RECHAZADOS — archivo inválido'),
    'PASO':       (VERDE_FUERTE, 'PASARON'),
}
ORDEN_BANDAS = ['NO PASO', 'INCOMPLETO', 'RECHAZADO', 'PASO']

TITULO = Font(name='Arial', bold=True, size=18, color=MARINO)
MINI = Font(name='Arial', size=8.5, color='8A93A0')
NOTA = Font(name='Arial', size=9, color=GRIS_NOTA)
HEAD = Font(name='Arial', bold=True, color='FFFFFF', size=10)
HEAD_CH = Font(name='Arial', bold=True, color='FFFFFF', size=9)
BOLD = Font(name='Arial', bold=True, size=10)
NORM = Font(name='Arial', size=10)
ETIQ = Font(name='Arial', bold=True, size=10, color=MARINO)
BANDA_F = Font(name='Arial', bold=True, size=10, color='FFFFFF')
FILL_HEAD = PatternFill('solid', fgColor=AZUL)
FILL_HEAD_OSC = PatternFill('solid', fgColor=MARINO)
FILL_HEAD_MED = PatternFill('solid', fgColor=AZUL_MEDIO)
FILL_ETIQ = PatternFill('solid', fgColor=AZUL_ETIQUETA)
FILL_ZEBRA = PatternFill('solid', fgColor=ZEBRA)
CENTER = Alignment(horizontal='center', vertical='center')
CENTER_WRAP = Alignment(horizontal='center', vertical='center', wrap_text=True)
IZQ = Alignment(horizontal='left', vertical='center')
IZQ_WRAP = Alignment(horizontal='left', vertical='center', wrap_text=True)
thin = Side(style='thin', color='D9D9D9')
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
NUM2 = '#,##0.00'

CRITERIO = ('Criterio de aceptación por canal: Fase 1 — desviación estándar dentro de su rango; '
            'Fase 2 — promedio dentro del suyo (solo si pasa la Fase 1). La pieza pasa si todos '
            'sus canales pasan ambas fases.')


def _estado_prueba(detalle, prueba):
    fs = detalle.get(prueba, [])
    if not fs:
        return '—'
    if any(x['resultado'] == 'FALLA' for x in fs):
        return 'No pasó'
    # sin ninguna falla real: si algun canal no tiene estandar, no se puede
    # afirmar que paso -> se avisa que falta definir el limite (no es una falla)
    if any(x['resultado'] == 'SIN ESTANDAR' for x in fs):
        return 'Sin estándar'
    return 'Pasó'


def _pinta_estado(celda, texto):
    celda.alignment = CENTER
    celda.border = BORDER
    t = str(texto)
    if t in ('Pasó', 'PASÓ', 'PASA', 'Pasa') or t.startswith('✓'):
        celda.fill = PatternFill('solid', fgColor=VERDE_BG); celda.font = Font(name='Arial', bold=True, color=VERDE_TX, size=10)
    elif t in ('No pasó', 'NO PASÓ', 'FALLA') or t.startswith(('Falla', '✗')):
        celda.fill = PatternFill('solid', fgColor=ROJO_BG); celda.font = Font(name='Arial', bold=True, color=ROJO_TX, size=10)
    elif t in ('Sin estándar', 'SIN ESTANDAR'):
        celda.fill = PatternFill('solid', fgColor=AMBAR_BG); celda.font = Font(name='Arial', bold=True, color=AMBAR_TX, size=10)
    elif t in ('RECHAZADO', 'Rechazado'):
        celda.fill = PatternFill('solid', fgColor=GRIS_BG); celda.font = Font(name='Arial', bold=True, color=GRIS_TX, size=10)
    elif t.startswith('—'):
        celda.font = Font(name='Arial', color='8A93A0', size=10)
    else:
        celda.font = NORM


def _caja(ws, fila, c1, c2, fill=None):
    """Aplica borde (y fondo opcional) a todas las celdas de un rango de una
    fila; con celdas combinadas el borde debe ponerse celda por celda."""
    for c in range(c1, c2 + 1):
        celda = ws.cell(row=fila, column=c)
        celda.border = BORDER
        if fill is not None:
            celda.fill = fill


def _campo(ws, fila, col, etiqueta, valor, merge_hasta=None,
           valor_fill=None, valor_color=None):
    """Fila 'Etiqueta | Valor': etiqueta con fondo azul claro y valor en caja
    blanca (opcionalmente coloreada)."""
    e = ws.cell(row=fila, column=col, value=etiqueta)
    e.font = ETIQ; e.fill = FILL_ETIQ; e.border = BORDER; e.alignment = IZQ
    fin = merge_hasta or (col + 1)
    if fin > col + 1:
        ws.merge_cells(start_row=fila, start_column=col + 1, end_row=fila, end_column=fin)
    v = ws.cell(row=fila, column=col + 1, value=valor)
    v.font = Font(name='Arial', size=10, bold=bool(valor_color),
                  color=valor_color or '16212E')
    v.alignment = IZQ
    _caja(ws, fila, col + 1, fin,
          fill=PatternFill('solid', fgColor=valor_fill) if valor_fill else None)


def _titulo_hoja(ws, texto, ancho_cols, batch, acento=True):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ancho_cols)
    c = ws['A1']; c.value = texto; c.font = TITULO; c.alignment = IZQ
    ws.row_dimensions[1].height = 30
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ancho_cols)
    g = ws['A2']
    g.value = ' · '.join(p for p in [
        batch.get('nombre', ''),
        f"generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        'Hera Diagnostics · Control de Calidad'] if p)
    g.font = MINI; g.alignment = IZQ
    if acento:
        # línea de acento azul bajo el título, ancho completo de la tabla
        ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=ancho_cols)
        for c in range(1, ancho_cols + 1):
            ws.cell(row=3, column=c).fill = FILL_HEAD
        ws.row_dimensions[3].height = 3.5


def _banda(ws, fila, c1, c2, texto, color):
    ws.merge_cells(start_row=fila, start_column=c1, end_row=fila, end_column=c2)
    b = ws.cell(row=fila, column=c1, value=texto)
    b.font = BANDA_F; b.alignment = IZQ
    _caja(ws, fila, c1, c2, fill=PatternFill('solid', fgColor=color))
    ws.row_dimensions[fila].height = 17


def _preparar_impresion(ws, orientacion, filas_titulo=None, pie_izq=''):
    ws.page_setup.orientation = orientacion
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    if filas_titulo:
        ws.print_title_rows = filas_titulo
    ws.oddFooter.left.text = pie_izq
    ws.oddFooter.left.size = 8
    ws.oddFooter.right.text = 'Página &P de &N'
    ws.oddFooter.right.size = 8


# ================================================================ hoja Resumen
def _hoja_resumen(wb, batch, resultados):
    ws = wb.active
    ws.title = 'Resumen'
    ws.sheet_properties.tabColor = AZUL
    ws.sheet_view.showGridLines = False
    _titulo_hoja(ws, 'Reporte de Control de Calidad', 6, batch)

    # ---- bloque de datos del lote (izquierda) ----
    _campo(ws, 5, 1, 'Lote', batch.get('nombre', ''), merge_hasta=3)
    _campo(ws, 6, 1, 'Operador', batch.get('operador', ''), merge_hasta=3)
    _campo(ws, 7, 1, 'Fecha', (batch.get('fecha', '') or '')[:16].replace('T', ' '), merge_hasta=3)
    _campo(ws, 8, 1, 'Perfil de estándar', batch.get('perfil', ''), merge_hasta=3)

    # ---- indicadores (derecha), con el color de su estado ----
    total = len(resultados)
    pasaron = sum(1 for x in resultados if x['veredicto'] == 'PASO')
    incompletos = sum(1 for x in resultados if x['veredicto'] == 'INCOMPLETO')
    rechazados = sum(1 for x in resultados if x['veredicto'] == 'RECHAZADO')
    fallaron = total - pasaron - incompletos - rechazados
    aprobacion = f'{100 * pasaron / total:.0f}%' if total else '—'
    _campo(ws, 5, 5, 'Total piezas', total)
    _campo(ws, 6, 5, 'Pasaron', pasaron, valor_fill=VERDE_BG, valor_color=VERDE_TX)
    _campo(ws, 7, 5, 'Fallaron', fallaron,
           valor_fill=(ROJO_BG if fallaron else None), valor_color=(ROJO_TX if fallaron else None))
    _campo(ws, 8, 5, 'Incompletos', incompletos,
           valor_fill=(AMBAR_BG if incompletos else None), valor_color=(AMBAR_TX if incompletos else None))
    _campo(ws, 9, 5, 'Rechazados', rechazados,
           valor_fill=(GRIS_BG if rechazados else None), valor_color=(GRIS_TX if rechazados else None))
    _campo(ws, 10, 5, 'Aprobación', aprobacion,
           valor_fill=(VERDE_BG if total and pasaron == total else None),
           valor_color=(VERDE_TX if total and pasaron == total else None))

    # ---- gráfica de dona con la distribución del lote ----
    if total:
        dona = DoughnutChart(holeSize=55)
        dona.title = 'Distribución del lote'
        datos = Reference(ws, min_col=6, min_row=6, max_row=9)      # Pasaron..Rechazados
        cats = Reference(ws, min_col=5, min_row=6, max_row=9)
        dona.add_data(datos, titles_from_data=False)
        dona.set_categories(cats)
        puntos = []
        for i, colr in enumerate([VERDE_FUERTE, ROJO_FUERTE, AMBAR_FUERTE, GRIS_FUERTE]):
            dp = DataPoint(idx=i)
            dp.graphicalProperties.solidFill = colr
            puntos.append(dp)
        dona.series[0].data_points = puntos
        dona.dataLabels = DataLabelList(showVal=True, showCatName=False, showSerName=False,
                                        showPercent=False, showLegendKey=False)
        dona.legend.position = 'r'
        dona.height = 6.6
        dona.width = 9.6
        ws.add_chart(dona, 'H5')

    # ---- criterio de aceptación ----
    ws.merge_cells(start_row=12, start_column=1, end_row=12, end_column=6)
    cr = ws.cell(row=12, column=1, value=CRITERIO)
    cr.font = NOTA; cr.alignment = IZQ_WRAP
    ws.row_dimensions[12].height = 26

    # ---- tabla de piezas, agrupada en bandas por veredicto ----
    hr = 14
    headers = ['No. pieza', 'Archivo', 'Óptico', 'Eléctrico', 'Veredicto final', 'Alerta']
    for i, h in enumerate(headers, start=1):
        c = ws.cell(row=hr, column=i, value=h)
        c.font = HEAD; c.fill = FILL_HEAD; c.alignment = CENTER; c.border = BORDER
    ws.row_dimensions[hr].height = 17
    ws.freeze_panes = ws.cell(row=hr + 1, column=1)

    r = hr + 1
    ordenados = sorted(resultados, key=lambda z: str(z['pieza']))
    for veredicto in ORDEN_BANDAS:
        grupo = [x for x in ordenados if x['veredicto'] == veredicto]
        if not grupo:
            continue
        color, rotulo = BANDAS[veredicto]
        _banda(ws, r, 1, 6, f'{rotulo} ({len(grupo)})', color)
        r += 1
        for j, x in enumerate(grupo):
            zebra = FILL_ZEBRA if j % 2 else None
            _caja(ws, r, 1, 6, fill=zebra)
            ws.cell(row=r, column=1, value=x['pieza']).font = BOLD
            ws.cell(row=r, column=1).alignment = CENTER
            ws.cell(row=r, column=2, value=x['archivo']).font = NORM
            eo = _estado_prueba(x['detalle'], 'Optico')
            ee = _estado_prueba(x['detalle'], 'Electrico')
            _pinta_estado(ws.cell(row=r, column=3, value=eo), eo)
            _pinta_estado(ws.cell(row=r, column=4, value=ee), ee)
            if veredicto == 'PASO':
                vtxt, alerta = 'PASÓ', ''
            elif veredicto == 'INCOMPLETO':
                vtxt, alerta = 'Sin estándar', 'Completar perfil'
            elif veredicto == 'RECHAZADO':
                vtxt, alerta = 'RECHAZADO', 'Archivo inválido — reexportar el JSON del equipo'
            else:
                vtxt, alerta = 'NO PASÓ', 'Repetir prueba'
            _pinta_estado(ws.cell(row=r, column=5, value=vtxt), vtxt)
            ca = ws.cell(row=r, column=6, value=alerta)
            if alerta:
                color_al = (AMBAR_TX if veredicto == 'INCOMPLETO'
                            else GRIS_TX if veredicto == 'RECHAZADO' else ROJO_TX)
                ca.font = Font(name='Arial', bold=True, color=color_al, size=10)
            r += 1

    for col, w in zip('ABCDEF', [14, 30, 14, 14, 16, 40]):
        ws.column_dimensions[col].width = w
    _preparar_impresion(ws, 'portrait', filas_titulo=f'{hr}:{hr}',
                        pie_izq=batch.get('nombre', ''))
    return ws


# ==================================================== hoja Verificación de cálculos
# columnas: A pieza, B prueba, C canal, D n, E desv, F desv mín, G desv máx,
#           H fase 1, I media, J media mín, K media máx, L fase 2, M rango,
#           N estado (app), O comprobación Excel, P observación
COL_VER = 16


def _formula_comprobacion(fila, est):
    """Fórmula de Excel que recalcula el veredicto del canal con los valores y
    límites de la propia fila (solo con los límites que sí están definidos,
    igual que evalúa la app). Devuelve None si no hay ningún límite."""
    conds1 = []
    if est.get('desv_min') is not None:
        conds1.append(f'E{fila}<F{fila}')
    if est.get('desv_max') is not None:
        conds1.append(f'E{fila}>G{fila}')
    conds2 = []
    if est.get('media_min') is not None:
        conds2.append(f'I{fila}<J{fila}')
    if est.get('media_max') is not None:
        conds2.append(f'I{fila}>K{fila}')
    if not conds1 and not conds2:
        return None

    def _or(conds):
        return conds[0] if len(conds) == 1 else 'OR(' + ','.join(conds) + ')'

    if conds1 and conds2:
        return (f'=IF({_or(conds1)},"NO PASA (Fase 1)",'
                f'IF({_or(conds2)},"NO PASA (Fase 2)","PASA"))')
    if conds1:
        return f'=IF({_or(conds1)},"NO PASA (Fase 1)","PASA")'
    return f'=IF({_or(conds2)},"NO PASA (Fase 2)","PASA")'


def _num(celda, valor, bold=False, gris=False):
    celda.value = round(float(valor), 2)
    celda.number_format = NUM2
    celda.alignment = CENTER
    celda.font = Font(name='Arial', size=10, bold=bold,
                      color=('8A93A0' if gris else '16212E'))


def _limite(celda, valor):
    if valor is None:
        celda.value = None
        return
    _num(celda, valor)
    celda.font = Font(name='Arial', size=9.5, color=GRIS_NOTA)


def _hoja_verificacion(wb, batch, resultados):
    wd = wb.create_sheet('Verificación de cálculos')
    wd.sheet_properties.tabColor = AZUL_MEDIO
    wd.sheet_view.showGridLines = False
    _titulo_hoja(wd, 'Respaldo de verificación de cálculos', COL_VER, batch)

    wd.merge_cells(start_row=4, start_column=1, end_row=4, end_column=COL_VER)
    n1 = wd.cell(row=4, column=1, value=(
        CRITERIO + ' La columna "Comprobación Excel" recalcula el veredicto con fórmulas '
        'de esta misma hoja y debe coincidir con "Estado (app)".'))
    n1.font = NOTA; n1.alignment = IZQ_WRAP
    wd.row_dimensions[4].height = 28

    # ---- encabezado a dos niveles: grupos de fase ----
    sh = 6   # fila de super-encabezado
    hh = 7   # fila de encabezado
    grupos = [(1, 4, 'IDENTIFICACIÓN', FILL_HEAD_OSC),
              (5, 8, 'FASE 1 — DESVIACIÓN ESTÁNDAR (se evalúa primero)', FILL_HEAD),
              (9, 12, 'FASE 2 — PROMEDIO (solo si pasa la Fase 1)', FILL_HEAD_MED),
              (13, 16, 'RESULTADO', FILL_HEAD_OSC)]
    for c1, c2, texto, fill in grupos:
        wd.merge_cells(start_row=sh, start_column=c1, end_row=sh, end_column=c2)
        g = wd.cell(row=sh, column=c1, value=texto)
        g.font = HEAD_CH; g.alignment = CENTER
        _caja(wd, sh, c1, c2, fill=fill)
    wd.row_dimensions[sh].height = 16

    headers2 = ['No. pieza', 'Prueba', 'Canal', 'Mediciones (n)',
                'Desv. estándar', 'Mín', 'Máx', 'Fase 1',
                'Media', 'Mín', 'Máx', 'Fase 2',
                'Rango', 'Estado (app)', 'Comprobación Excel', 'Observación']
    for i, h in enumerate(headers2, start=1):
        c = wd.cell(row=hh, column=i, value=h)
        c.font = HEAD_CH; c.fill = FILL_HEAD; c.alignment = CENTER_WRAP; c.border = BORDER
    wd.row_dimensions[hh].height = 24
    wd.freeze_panes = wd.cell(row=hh + 1, column=1)

    VER_TXT = {'PASO': 'PASÓ', 'NO PASO': 'NO PASÓ',
               'INCOMPLETO': 'SIN ESTÁNDAR', 'RECHAZADO': 'RECHAZADO'}
    r = hh + 1
    primera_dato, ultima_dato = r, r - 1
    for x in sorted(resultados, key=lambda z: str(z['pieza'])):
        color, _ = BANDAS.get(x['veredicto'], (GRIS_FUERTE, ''))
        _banda(wd, r, 1, COL_VER, f"Pieza {x['pieza']} — {VER_TXT.get(x['veredicto'], x['veredicto'])}", color)
        r += 1
        # pieza rechazada: no hay canales evaluados; dejar constancia en el respaldo
        if x['veredicto'] == 'RECHAZADO':
            _caja(wd, r, 1, COL_VER)
            wd.cell(row=r, column=1, value=x['pieza']).alignment = CENTER
            _pinta_estado(wd.cell(row=r, column=14, value='Rechazado'), 'Rechazado')
            obs = wd.cell(row=r, column=16, value='Archivo rechazado — formato inválido, no se evaluó.')
            obs.font = NORM
            ultima_dato = max(ultima_dato, r)
            r += 1
            continue
        j = 0
        for prueba, filas in x['detalle'].items():
            for f in filas:
                est = f.get('estandar') or {}
                _caja(wd, r, 1, COL_VER, fill=(FILL_ZEBRA if j % 2 else None))
                wd.cell(row=r, column=1, value=x['pieza']).alignment = CENTER
                wd.cell(row=r, column=2, value='Óptica' if prueba == 'Optico' else 'Eléctrica').font = NORM
                wd.cell(row=r, column=3, value=f['canal']).font = NORM
                wd.cell(row=r, column=4, value=f.get('n', 20)).alignment = CENTER

                sin_est = f['resultado'] == 'SIN ESTANDAR'
                dmin, dmax = est.get('desv_min'), est.get('desv_max')
                mmin, mmax = est.get('media_min'), est.get('media_max')

                # ---- FASE 1: desviación + límites + resultado de fase ----
                fuera1 = ((dmin is not None and round(f['desv'], 2) < round(dmin, 2)) or
                          (dmax is not None and round(f['desv'], 2) > round(dmax, 2)))
                _num(wd.cell(row=r, column=5), f['desv'], bold=fuera1, gris=sin_est)
                if fuera1:
                    wd.cell(row=r, column=5).font = Font(name='Arial', size=10, bold=True, color=ROJO_TX)
                    wd.cell(row=r, column=5).fill = PatternFill('solid', fgColor=ROJO_BG)
                _limite(wd.cell(row=r, column=6), dmin)
                _limite(wd.cell(row=r, column=7), dmax)
                if sin_est or (dmin is None and dmax is None):
                    f1 = '— Sin límite'
                else:
                    f1 = '✗ Fuera' if fuera1 else '✓ Dentro'
                _pinta_estado(wd.cell(row=r, column=8, value=f1), f1)

                # ---- FASE 2: media + límites + resultado de fase ----
                fuera2 = ((mmin is not None and round(f['media'], 2) < round(mmin, 2)) or
                          (mmax is not None and round(f['media'], 2) > round(mmax, 2)))
                marca2 = (not fuera1) and fuera2
                _num(wd.cell(row=r, column=9), f['media'], bold=marca2, gris=sin_est)
                if marca2:
                    wd.cell(row=r, column=9).font = Font(name='Arial', size=10, bold=True, color=ROJO_TX)
                    wd.cell(row=r, column=9).fill = PatternFill('solid', fgColor=ROJO_BG)
                _limite(wd.cell(row=r, column=10), mmin)
                _limite(wd.cell(row=r, column=11), mmax)
                if sin_est or (mmin is None and mmax is None):
                    f2 = '— Sin límite'
                elif fuera1:
                    f2 = '— No evaluada'
                else:
                    f2 = '✗ Fuera' if fuera2 else '✓ Dentro'
                _pinta_estado(wd.cell(row=r, column=12, value=f2), f2)

                _num(wd.cell(row=r, column=13), f.get('rango', 0), gris=sin_est)

                # ---- estado app + comprobación con fórmula viva ----
                if f['resultado'] == 'PASA':
                    est_txt = 'Pasa'
                elif f['resultado'] == 'FALLA':
                    est_txt = f"Falla (Fase {f.get('fase_fallo') or '?'})"
                else:
                    est_txt = 'Sin estándar'
                _pinta_estado(wd.cell(row=r, column=14, value=est_txt), est_txt)

                formula = None if sin_est else _formula_comprobacion(r, est)
                cf = wd.cell(row=r, column=15, value=formula if formula else '—')
                cf.alignment = CENTER
                cf.font = Font(name='Arial', size=10, color=('8A93A0' if not formula else '16212E'))

                if f['resultado'] == 'FALLA':
                    obs = f"Fase {f.get('fase_fallo')}: " + ', '.join(f.get('motivos', []))
                elif f['resultado'] == 'SIN ESTANDAR':
                    obs = 'Este canal no tiene límite definido en el perfil seleccionado (no se evaluó).'
                else:
                    obs = ''
                oc = wd.cell(row=r, column=16, value=obs)
                oc.font = NORM; oc.alignment = IZQ_WRAP
                ultima_dato = max(ultima_dato, r)
                r += 1
                j += 1

    # ---- formato condicional de la columna Comprobación Excel ----
    if ultima_dato >= primera_dato:
        rango_cf = f'O{primera_dato}:O{ultima_dato}'
        wd.conditional_formatting.add(rango_cf, CellIsRule(
            operator='equal', formula=['"PASA"'],
            fill=PatternFill('solid', fgColor=VERDE_BG),
            font=Font(name='Arial', bold=True, color=VERDE_TX)))
        for txt in ('"NO PASA (Fase 1)"', '"NO PASA (Fase 2)"'):
            wd.conditional_formatting.add(rango_cf, CellIsRule(
                operator='equal', formula=[txt],
                fill=PatternFill('solid', fgColor=ROJO_BG),
                font=Font(name='Arial', bold=True, color=ROJO_TX)))

    widths2 = [10, 11, 12, 12, 14, 11, 11, 13, 14, 11, 11, 14, 11, 15, 17, 44]
    for i, w in enumerate(widths2, start=1):
        wd.column_dimensions[get_column_letter(i)].width = w
    _preparar_impresion(wd, 'landscape', filas_titulo=f'{sh}:{hh}',
                        pie_izq=batch.get('nombre', ''))
    return wd


def exportar_lote_excel(ruta_salida, batch, resultados):
    wb = Workbook()
    _hoja_resumen(wb, batch, resultados)
    _hoja_verificacion(wb, batch, resultados)
    wb.save(ruta_salida)
    return ruta_salida
