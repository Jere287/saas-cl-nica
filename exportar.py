"""
exportar.py — Exporta los datos finales de un lote a un archivo Excel (.xlsx)
limpio y formateado, para que el area de calidad lo guarde donde quiera (Drive, etc.).

Genera dos hojas:
  - Resumen: una fila por pieza con su veredicto y resultado por prueba.
  - Detalle: una fila por canal de cada pieza (media, desviacion, rango y estado).
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

AZUL = '0C447C'
VERDE_BG = 'C6EFCE'; VERDE_TX = '006100'
ROJO_BG = 'FFC7CE'; ROJO_TX = '9C0006'

HEAD = Font(name='Arial', bold=True, color='FFFFFF', size=10)
BOLD = Font(name='Arial', bold=True, size=10)
NORM = Font(name='Arial', size=10)
FILL_HEAD = PatternFill('solid', fgColor=AZUL)
CENTER = Alignment(horizontal='center', vertical='center')
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
        celda.fill = PatternFill('solid', fgColor='FFF2CC'); celda.font = Font(name='Arial', bold=True, color='9C6500', size=10)
    elif texto in ('RECHAZADO', 'Rechazado'):
        celda.fill = PatternFill('solid', fgColor='EDEDED'); celda.font = Font(name='Arial', bold=True, color='3A3A3A', size=10)
    else:
        celda.font = NORM


def exportar_lote_excel(ruta_salida, batch, resultados):
    wb = Workbook()

    # ---- Hoja Resumen ----
    ws = wb.active
    ws.title = 'Resumen'
    ws['A1'] = 'Reporte de control de calidad — Resumen del lote'
    ws['A1'].font = Font(name='Arial', bold=True, size=14, color=AZUL)
    ws['A3'] = 'Lote:'; ws['B3'] = batch.get('nombre', '')
    ws['A4'] = 'Operador:'; ws['B4'] = batch.get('operador', '')
    ws['A5'] = 'Fecha:'; ws['B5'] = (batch.get('fecha', '') or '')[:16].replace('T', ' ')
    ws['A6'] = 'Perfil de estándar:'; ws['B6'] = batch.get('perfil', '')
    for r in range(3, 7):
        ws.cell(row=r, column=1).font = BOLD

    total = len(resultados)
    pasaron = sum(1 for x in resultados if x['veredicto'] == 'PASO')
    incompletos = sum(1 for x in resultados if x['veredicto'] == 'INCOMPLETO')
    rechazados = sum(1 for x in resultados if x['veredicto'] == 'RECHAZADO')
    fallaron = total - pasaron - incompletos - rechazados
    ws['A8'] = 'Total piezas:'; ws['B8'] = total
    ws['A9'] = 'Pasaron:'; ws['B9'] = pasaron
    ws['A10'] = 'Fallaron:'; ws['B10'] = fallaron
    ws['A11'] = 'Incompletos:'; ws['B11'] = incompletos
    ws['A12'] = 'Rechazados:'; ws['B12'] = rechazados
    ws['A13'] = 'Aprobación:'; ws['B13'] = (f'{100*pasaron/total:.0f}%' if total else '—')
    for r in range(8, 14):
        ws.cell(row=r, column=1).font = BOLD

    hr = 15
    headers = ['No. pieza', 'Archivo', 'Óptico', 'Eléctrico', 'Veredicto final', 'Alerta']
    for i, h in enumerate(headers, start=1):
        c = ws.cell(row=hr, column=i, value=h)
        c.font = HEAD; c.fill = FILL_HEAD; c.alignment = CENTER; c.border = BORDER
    for j, x in enumerate(sorted(resultados, key=lambda z: str(z['pieza'])), start=1):
        r = hr + j
        ws.cell(row=r, column=1, value=x['pieza']).border = BORDER
        ws.cell(row=r, column=2, value=x['archivo']).border = BORDER
        _pinta_estado(ws.cell(row=r, column=3, value=_estado_prueba(x['detalle'], 'Optico')), _estado_prueba(x['detalle'], 'Optico'))
        _pinta_estado(ws.cell(row=r, column=4, value=_estado_prueba(x['detalle'], 'Electrico')), _estado_prueba(x['detalle'], 'Electrico'))
        if x['veredicto'] == 'PASO':
            vtxt = 'PASÓ'; alerta = ''
        elif x['veredicto'] == 'INCOMPLETO':
            vtxt = 'Sin estándar'; alerta = 'Completar perfil'
        elif x['veredicto'] == 'RECHAZADO':
            vtxt = 'RECHAZADO'; alerta = 'Archivo inválido — reexportar el JSON del equipo'
        else:
            vtxt = 'NO PASÓ'; alerta = 'Repetir prueba'
        _pinta_estado(ws.cell(row=r, column=5, value=vtxt), vtxt)
        ca = ws.cell(row=r, column=6, value=alerta); ca.border = BORDER
        if alerta:
            color_al = ('9C6500' if x['veredicto'] == 'INCOMPLETO'
                        else '3A3A3A' if x['veredicto'] == 'RECHAZADO' else ROJO_TX)
            ca.font = Font(name='Arial', bold=True, color=color_al, size=10)
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 26
    for col in 'CDEF':
        ws.column_dimensions[col].width = 16

    # ---- Hoja Verificación de cálculos ----
    wd = wb.create_sheet('Verificación de cálculos')
    wd['A1'] = 'Respaldo de verificación — cálculos hechos por la app (media, desviación y rango por canal)'
    wd['A1'].font = Font(name='Arial', bold=True, size=11, color=AZUL)
    fila_head = 3
    headers2 = ['No. pieza', 'Prueba', 'Canal', 'Mediciones', 'Media', 'Desv. estándar', 'Rango', 'Estado', 'Observación']
    for i, h in enumerate(headers2, start=1):
        c = wd.cell(row=fila_head, column=i, value=h)
        c.font = HEAD; c.fill = FILL_HEAD; c.alignment = CENTER; c.border = BORDER
    r = fila_head + 1
    for x in sorted(resultados, key=lambda z: str(z['pieza'])):
        # pieza rechazada: no hay canales evaluados; dejar constancia en el respaldo
        if x['veredicto'] == 'RECHAZADO':
            wd.cell(row=r, column=1, value=x['pieza']).border = BORDER
            _pinta_estado(wd.cell(row=r, column=8, value='Rechazado'), 'Rechazado')
            wd.cell(row=r, column=9, value='Archivo rechazado — formato inválido, no se evaluó.').border = BORDER
            r += 1
            continue
        for prueba, filas in x['detalle'].items():
            for f in filas:
                wd.cell(row=r, column=1, value=x['pieza']).border = BORDER
                wd.cell(row=r, column=2, value=prueba).border = BORDER
                wd.cell(row=r, column=3, value=f['canal']).border = BORDER
                wd.cell(row=r, column=4, value=f.get('n', 20)).border = BORDER
                wd.cell(row=r, column=5, value=round(f['media'], 2)).border = BORDER
                wd.cell(row=r, column=6, value=round(f['desv'], 2)).border = BORDER
                wd.cell(row=r, column=7, value=round(f.get('rango', 0), 2)).border = BORDER
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
                wd.cell(row=r, column=9, value=obs).border = BORDER
                r += 1
    widths2 = [12, 12, 16, 12, 14, 16, 14, 10, 42]
    for i, w in enumerate(widths2):
        wd.column_dimensions[chr(65 + i)].width = w

    wb.save(ruta_salida)
    return ruta_salida
