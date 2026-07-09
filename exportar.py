"""
exportar.py — Exporta los datos finales de un lote a un archivo Excel (.xlsx)
con formato de reporte profesional (estilo plantilla de gestión de proyectos):
título, bloque de datos del lote con etiquetas sombreadas, indicadores con
color, bandas de sección y estados coloreados.

Genera dos hojas:
  - Resumen: datos del lote + indicadores + una fila por pieza agrupada en
    bandas por veredicto (primero las que requieren atención).
  - Verificación de cálculos: una banda por pieza y debajo sus canales
    (media, desviación, rango y estado), como respaldo del cálculo.
"""
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ---- paleta (alineada con la interfaz de la app) ----
MARINO = '0C2E52'       # título y textos fuertes
AZUL = '0C447C'         # encabezados de tabla
AZUL_ETIQUETA = 'DCE9F7'  # fondo de las etiquetas del bloque de datos
ZEBRA = 'F2F6FB'        # fila alterna de las tablas

VERDE_BG = 'C6EFCE'; VERDE_TX = '006100'
ROJO_BG = 'FFC7CE'; ROJO_TX = '9C0006'
AMBAR_BG = 'FFF2CC'; AMBAR_TX = '9C6500'
GRIS_BG = 'EDEDED'; GRIS_TX = '3A3A3A'

# bandas de sección por veredicto (fondo fuerte + texto blanco, como las
# bandas "Initiation / Planning / ..." de la plantilla de ejemplo)
BANDAS = {
    'NO PASO':    ('D03B3B', 'NO PASARON — repetir la prueba'),
    'INCOMPLETO': ('E9A23B', 'SIN ESTÁNDAR — completar el perfil'),
    'RECHAZADO':  ('5A6472', 'RECHAZADOS — archivo inválido'),
    'PASO':       ('12A15A', 'PASARON'),
}
ORDEN_BANDAS = ['NO PASO', 'INCOMPLETO', 'RECHAZADO', 'PASO']

TITULO = Font(name='Arial', bold=True, size=18, color=MARINO)
MINI = Font(name='Arial', size=8.5, color='8A93A0')
HEAD = Font(name='Arial', bold=True, color='FFFFFF', size=10)
BOLD = Font(name='Arial', bold=True, size=10)
NORM = Font(name='Arial', size=10)
ETIQ = Font(name='Arial', bold=True, size=10, color=MARINO)
BANDA_F = Font(name='Arial', bold=True, size=10, color='FFFFFF')
FILL_HEAD = PatternFill('solid', fgColor=AZUL)
FILL_ETIQ = PatternFill('solid', fgColor=AZUL_ETIQUETA)
FILL_ZEBRA = PatternFill('solid', fgColor=ZEBRA)
CENTER = Alignment(horizontal='center', vertical='center')
IZQ = Alignment(horizontal='left', vertical='center')
thin = Side(style='thin', color='D9D9D9')
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)


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
    if texto in ('Pasó', 'PASÓ', 'PASA', 'Pasa'):
        celda.fill = PatternFill('solid', fgColor=VERDE_BG); celda.font = Font(name='Arial', bold=True, color=VERDE_TX, size=10)
    elif texto in ('No pasó', 'NO PASÓ', 'FALLA', 'Falla'):
        celda.fill = PatternFill('solid', fgColor=ROJO_BG); celda.font = Font(name='Arial', bold=True, color=ROJO_TX, size=10)
    elif texto in ('Sin estándar', 'SIN ESTANDAR'):
        celda.fill = PatternFill('solid', fgColor=AMBAR_BG); celda.font = Font(name='Arial', bold=True, color=AMBAR_TX, size=10)
    elif texto in ('RECHAZADO', 'Rechazado'):
        celda.fill = PatternFill('solid', fgColor=GRIS_BG); celda.font = Font(name='Arial', bold=True, color=GRIS_TX, size=10)
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
    """Fila 'Etiqueta | Valor' al estilo de la plantilla: etiqueta con fondo
    azul claro y valor en caja blanca (opcionalmente coloreada)."""
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


def _titulo_hoja(ws, texto, ancho_cols, batch):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ancho_cols)
    c = ws['A1']; c.value = texto; c.font = TITULO; c.alignment = IZQ
    ws.row_dimensions[1].height = 30
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ancho_cols)
    g = ws['A2']
    g.value = ' · '.join(p for p in [
        batch.get('nombre', ''),
        f"generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        'Sistema de Control de Calidad'] if p)
    g.font = MINI; g.alignment = IZQ


def _banda(ws, fila, c1, c2, texto, color):
    ws.merge_cells(start_row=fila, start_column=c1, end_row=fila, end_column=c2)
    b = ws.cell(row=fila, column=c1, value=texto)
    b.font = BANDA_F; b.alignment = IZQ
    _caja(ws, fila, c1, c2, fill=PatternFill('solid', fgColor=color))
    ws.row_dimensions[fila].height = 17


def exportar_lote_excel(ruta_salida, batch, resultados):
    wb = Workbook()

    # ================= Hoja Resumen =================
    ws = wb.active
    ws.title = 'Resumen'
    ws.sheet_view.showGridLines = False
    _titulo_hoja(ws, 'Reporte de Control de Calidad', 6, batch)

    # ---- bloque de datos del lote (izquierda) ----
    _campo(ws, 4, 1, 'Lote', batch.get('nombre', ''), merge_hasta=3)
    _campo(ws, 5, 1, 'Operador', batch.get('operador', ''), merge_hasta=3)
    _campo(ws, 6, 1, 'Fecha', (batch.get('fecha', '') or '')[:16].replace('T', ' '), merge_hasta=3)
    _campo(ws, 7, 1, 'Perfil de estándar', batch.get('perfil', ''), merge_hasta=3)

    # ---- indicadores (derecha), con el color de su estado ----
    total = len(resultados)
    pasaron = sum(1 for x in resultados if x['veredicto'] == 'PASO')
    incompletos = sum(1 for x in resultados if x['veredicto'] == 'INCOMPLETO')
    rechazados = sum(1 for x in resultados if x['veredicto'] == 'RECHAZADO')
    fallaron = total - pasaron - incompletos - rechazados
    aprobacion = f'{100 * pasaron / total:.0f}%' if total else '—'
    _campo(ws, 4, 5, 'Total piezas', total)
    _campo(ws, 5, 5, 'Pasaron', pasaron, valor_fill=VERDE_BG, valor_color=VERDE_TX)
    _campo(ws, 6, 5, 'Fallaron', fallaron,
           valor_fill=(ROJO_BG if fallaron else None), valor_color=(ROJO_TX if fallaron else None))
    _campo(ws, 7, 5, 'Incompletos', incompletos,
           valor_fill=(AMBAR_BG if incompletos else None), valor_color=(AMBAR_TX if incompletos else None))
    _campo(ws, 8, 5, 'Rechazados', rechazados,
           valor_fill=(GRIS_BG if rechazados else None), valor_color=(GRIS_TX if rechazados else None))
    _campo(ws, 9, 5, 'Aprobación', aprobacion,
           valor_fill=(VERDE_BG if total and pasaron == total else None),
           valor_color=(VERDE_TX if total and pasaron == total else None))

    # ---- tabla de piezas, agrupada en bandas por veredicto ----
    hr = 11
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

    # ================= Hoja Verificación de cálculos =================
    wd = wb.create_sheet('Verificación de cálculos')
    wd.sheet_view.showGridLines = False
    _titulo_hoja(wd, 'Respaldo de verificación de cálculos', 9, batch)
    wd.merge_cells(start_row=3, start_column=1, end_row=3, end_column=9)
    n = wd['A3']
    n.value = 'Cálculos hechos por la app para cada canal de cada pieza: media, desviación estándar y rango.'
    n.font = Font(name='Arial', size=9, color='5A6472'); n.alignment = IZQ

    fila_head = 5
    headers2 = ['No. pieza', 'Prueba', 'Canal', 'Mediciones', 'Media',
                'Desv. estándar', 'Rango', 'Estado', 'Observación']
    for i, h in enumerate(headers2, start=1):
        c = wd.cell(row=fila_head, column=i, value=h)
        c.font = HEAD; c.fill = FILL_HEAD; c.alignment = CENTER; c.border = BORDER
    wd.row_dimensions[fila_head].height = 17
    wd.freeze_panes = wd.cell(row=fila_head + 1, column=1)

    VER_TXT = {'PASO': 'PASÓ', 'NO PASO': 'NO PASÓ',
               'INCOMPLETO': 'SIN ESTÁNDAR', 'RECHAZADO': 'RECHAZADO'}
    r = fila_head + 1
    for x in sorted(resultados, key=lambda z: str(z['pieza'])):
        color, _ = BANDAS.get(x['veredicto'], ('5A6472', ''))
        _banda(wd, r, 1, 9, f"Pieza {x['pieza']} — {VER_TXT.get(x['veredicto'], x['veredicto'])}", color)
        r += 1
        # pieza rechazada: no hay canales evaluados; dejar constancia en el respaldo
        if x['veredicto'] == 'RECHAZADO':
            _caja(wd, r, 1, 9)
            wd.cell(row=r, column=1, value=x['pieza']).alignment = CENTER
            _pinta_estado(wd.cell(row=r, column=8, value='Rechazado'), 'Rechazado')
            wd.cell(row=r, column=9, value='Archivo rechazado — formato inválido, no se evaluó.').font = NORM
            r += 1
            continue
        j = 0
        for prueba, filas in x['detalle'].items():
            for f in filas:
                _caja(wd, r, 1, 9, fill=(FILL_ZEBRA if j % 2 else None))
                wd.cell(row=r, column=1, value=x['pieza']).alignment = CENTER
                wd.cell(row=r, column=2, value='Óptica' if prueba == 'Optico' else 'Eléctrica').font = NORM
                wd.cell(row=r, column=3, value=f['canal']).font = NORM
                wd.cell(row=r, column=4, value=f.get('n', 20)).alignment = CENTER
                wd.cell(row=r, column=5, value=round(f['media'], 2)).font = NORM
                wd.cell(row=r, column=6, value=round(f['desv'], 2)).font = NORM
                wd.cell(row=r, column=7, value=round(f.get('rango', 0), 2)).font = NORM
                if f['resultado'] == 'PASA':
                    est = 'Pasa'
                elif f['resultado'] == 'FALLA':
                    est = 'Falla'
                else:
                    est = 'Sin estándar'
                _pinta_estado(wd.cell(row=r, column=8, value=est), est)
                if f['resultado'] == 'FALLA':
                    obs = f"Fase {f.get('fase_fallo')}: " + ', '.join(f.get('motivos', []))
                elif f['resultado'] == 'SIN ESTANDAR':
                    obs = 'Este canal no tiene límite definido en el perfil seleccionado (no se evaluó).'
                else:
                    obs = ''
                wd.cell(row=r, column=9, value=obs).font = NORM
                r += 1
                j += 1
    widths2 = [12, 12, 16, 12, 14, 16, 14, 14, 46]
    for i, w in enumerate(widths2, start=1):
        wd.column_dimensions[get_column_letter(i)].width = w

    wb.save(ruta_salida)
    return ruta_salida
