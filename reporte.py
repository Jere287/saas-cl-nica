"""
reporte.py — Genera los reportes PDF corporativos del sistema de control de calidad.

Dos modos:
  - generar_pdf(...)              -> reporte de UN desechable individual
  - generar_pdf_lote(...)         -> reporte del LOTE completo (portada + cada pieza)

Diseno corporativo: encabezado azul con logo y nombre de empresa, datos de
trazabilidad, resultado separado por prueba (optico / electrico), veredicto final,
y campos de firma (operador + responsable de calidad).

Criterio: media + desviacion estandar.
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, Image)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

# --- paleta corporativa azul ---
AZUL = colors.HexColor('#0C447C')
AZUL_CLARO = colors.HexColor('#B5D4F4')
VERDE = colors.HexColor('#C6EFCE')
VERDE_T = colors.HexColor('#006100')
ROJO = colors.HexColor('#FFC7CE')
ROJO_T = colors.HexColor('#9C0006')
AMBAR = colors.HexColor('#FFF2CC')
AMBAR_T = colors.HexColor('#9C6500')
GRIS_T = colors.HexColor('#595959')
GRIS_BG = colors.HexColor('#EDEDED')
GRIS_OSC = colors.HexColor('#3A3A3A')
LINEA = colors.HexColor('#CCCCCC')

EMPRESA = '[Nombre de la empresa]'   # editable
SUBTITULO = 'Dispositivo de detección de cáncer cervicouterino'


def _styles():
    s = getSampleStyleSheet()
    return {
        'titulo': ParagraphStyle('t', parent=s['Normal'], fontSize=14, leading=17,
                                 textColor=colors.white, fontName='Helvetica-Bold'),
        'subt': ParagraphStyle('st', parent=s['Normal'], fontSize=8, leading=10,
                               textColor=AZUL_CLARO),
        'folio_l': ParagraphStyle('fl', parent=s['Normal'], fontSize=8, leading=10,
                                  textColor=AZUL_CLARO, alignment=2),
        'folio_v': ParagraphStyle('fv', parent=s['Normal'], fontSize=11, leading=13,
                                  textColor=colors.white, fontName='Helvetica-Bold', alignment=2),
        'label': ParagraphStyle('lb', parent=s['Normal'], fontSize=8, textColor=GRIS_T),
        'valor': ParagraphStyle('vl', parent=s['Normal'], fontSize=10, fontName='Helvetica-Bold'),
        'h2': ParagraphStyle('h2', parent=s['Normal'], fontSize=11, fontName='Helvetica-Bold',
                             textColor=AZUL, spaceBefore=8, spaceAfter=4),
        'normal': s['Normal'],
        'firma': ParagraphStyle('fi', parent=s['Normal'], fontSize=8, textColor=GRIS_T, alignment=TA_CENTER),
    }


def _encabezado(st, folio, logo_path=None):
    """Banda azul superior con logo, nombre de empresa y folio."""
    if logo_path and os.path.exists(logo_path):
        logo = Image(logo_path, width=1.1 * cm, height=1.1 * cm)
    else:
        logo = Table([['LOGO']], colWidths=[1.1 * cm], rowHeights=[1.1 * cm])
        logo.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), AZUL),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ]))
    titulo_celda = [[logo, Paragraph('Certificado de control de calidad', st['titulo'])],
                    ['', Paragraph(f'{EMPRESA} · {SUBTITULO}', st['subt'])]]
    izq = Table(titulo_celda, colWidths=[1.4 * cm, 10.3 * cm])
    izq.setStyle(TableStyle([
        ('SPAN', (0, 0), (0, 1)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    der = Table([[Paragraph('Folio', st['folio_l'])], [Paragraph(folio, st['folio_v'])]],
                colWidths=[4 * cm])
    der.setStyle(TableStyle([('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
    banda = Table([[izq, der]], colWidths=[11.7 * cm, 4.3 * cm])
    banda.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), AZUL),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    return banda


def _bloque_traza(st, datos):
    filas = [
        [Paragraph('No. de pieza', st['label']), Paragraph('Batch / lote', st['label']), Paragraph('Fecha y hora', st['label'])],
        [Paragraph(str(datos['pieza']), st['valor']), Paragraph(str(datos['batch']), st['valor']), Paragraph(str(datos['fecha']), st['valor'])],
        [Paragraph('Equipo / serie', st['label']), Paragraph('Operador', st['label']), Paragraph('Perfil de límites', st['label'])],
        [Paragraph(str(datos.get('equipo', '—')), st['valor']), Paragraph(str(datos['operador']), st['valor']), Paragraph(str(datos['perfil']), st['valor'])],
    ]
    t = Table(filas, colWidths=[5.5 * cm, 5.5 * cm, 5.5 * cm])
    t.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 3),
    ]))
    return t


def _resumen_pruebas(st, detalle):
    """Dos tarjetas: resultado optico y electrico por separado."""
    celdas = []
    for prueba in ['Optico', 'Electrico']:
        filas = detalle.get(prueba, [])
        total = len(filas)
        pasan = sum(1 for f in filas if f['resultado'] == 'PASA')
        hay_falla = any(f['resultado'] == 'FALLA' for f in filas)
        hay_sin = any(f['resultado'] == 'SIN ESTANDAR' for f in filas)
        nombre = 'Prueba óptica' if prueba == 'Optico' else 'Prueba eléctrica'
        if total and not hay_falla and not hay_sin:
            estado = f'Pasó · {pasan}/{total}'; color = VERDE_T; barra = colors.HexColor('#1D9E75')
        elif hay_falla:
            estado = f'No pasó · {pasan}/{total}'; color = ROJO_T; barra = colors.HexColor('#E24B4A')
        else:
            estado = f'Incompleto · {pasan}/{total}'; color = AMBAR_T; barra = colors.HexColor('#E0A800')
        celda = Table([[Paragraph(nombre, st['label'])],
                       [Paragraph(estado, ParagraphStyle('e', parent=st['valor'], fontSize=13, textColor=color))]],
                      colWidths=[7.3 * cm])
        celda.setStyle(TableStyle([
            ('LINEBEFORE', (0, 0), (0, -1), 3, barra),
            ('BOX', (0, 0), (-1, -1), 0.5, LINEA),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (0, 0), 8), ('BOTTOMPADDING', (0, 1), (0, 1), 8),
        ]))
        celdas.append(celda)
    cont = Table([celdas], colWidths=[7.6 * cm, 7.6 * cm])
    cont.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (0, 0), 12)]))
    return cont


def _banner_veredicto(st, veredicto, motivo):
    if veredicto == 'PASO':
        label = 'PASÓ'; tx = VERDE_T; bg = VERDE; borde = colors.HexColor('#3B6D11')
        sub = 'Todos los canales dentro de límites.'
    elif veredicto == 'INCOMPLETO':
        label = 'INCOMPLETO'; tx = AMBAR_T; bg = AMBAR; borde = colors.HexColor('#9C6500')
        sub = motivo if motivo else ('Hay canales sin límite definido en el perfil. No se puede '
                                     'aprobar la pieza hasta completar el estándar.')
    elif veredicto == 'RECHAZADO':
        label = 'RECHAZADO'; tx = GRIS_OSC; bg = GRIS_BG; borde = GRIS_OSC
        sub = motivo if motivo else ('El archivo no tiene el formato que entrega el equipo; la pieza '
                                     'NO se evaluó. Vuelve a exportar el JSON del equipo y súbelo de nuevo.')
    else:
        label = 'NO PASÓ'; tx = ROJO_T; bg = ROJO; borde = colors.HexColor('#A32D2D')
        sub = motivo if motivo else 'Uno o más canales fuera de límites.'
    txt = f'Veredicto final: {label}'
    cont = Table([[Paragraph(txt, ParagraphStyle('vb', parent=st['valor'], fontSize=12, textColor=tx))],
                  [Paragraph(sub, ParagraphStyle('vs', parent=st['normal'], fontSize=8, textColor=tx))]],
                 colWidths=[15.2 * cm])
    cont.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX', (0, 0), (-1, -1), 1, borde),
        ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 8), ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
    ]))
    return cont


def _rango_txt(lo, hi):
    """Texto 'lo–hi' tolerante a que falte uno de los dos limites (o ambos)."""
    if lo is None and hi is None:
        return '—'
    lo_t = f'{lo:.2f}' if lo is not None else '—'
    hi_t = f'{hi:.2f}' if hi is not None else '—'
    return f'{lo_t}–{hi_t}'


def _tabla_detalle(st, prueba, filas):
    data = [['Canal', 'Media', 'Rango media', 'Desv.', 'Rango desv.', 'Rango', 'Estado', 'Falla']]
    estilos = []
    for i, f in enumerate(filas, start=1):
        est = f.get('estandar') or {}
        rmedia = _rango_txt(est.get('media_min'), est.get('media_max'))
        rdesv = _rango_txt(est.get('desv_min'), est.get('desv_max'))
        if f['resultado'] == 'FALLA':
            estado_txt = 'Falla'; falla_txt = f"Fase {f.get('fase_fallo')}"
        elif f['resultado'] == 'PASA':
            estado_txt = 'Pasa'; falla_txt = '—'
        else:
            estado_txt = 'Sin est.'; falla_txt = 'Sin límite'
        data.append([
            str(f['canal']),
            f"{f['media']:.2f}",
            rmedia,
            f"{f['desv']:.2f}",
            rdesv,
            f"{f.get('rango', 0):.2f}",
            estado_txt,
            falla_txt,
        ])
        if f['resultado'] == 'FALLA':
            estilos += [('BACKGROUND', (6, i), (6, i), ROJO), ('TEXTCOLOR', (6, i), (6, i), ROJO_T)]
        elif f['resultado'] == 'PASA':
            estilos += [('TEXTCOLOR', (6, i), (6, i), VERDE_T)]
        else:
            estilos += [('BACKGROUND', (6, i), (6, i), AMBAR), ('TEXTCOLOR', (6, i), (6, i), AMBAR_T)]
    t = Table(data, colWidths=[2.5*cm, 1.6*cm, 2.2*cm, 1.6*cm, 2.2*cm, 1.5*cm, 1.3*cm, 1.3*cm], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6.8),
        ('GRID', (0, 0), (-1, -1), 0.4, LINEA),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ] + estilos))
    return t


def _firmas(st):
    linea = Table([['']], colWidths=[6 * cm], rowHeights=[24])
    linea.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), 0.7, GRIS_T)]))
    linea2 = Table([['']], colWidths=[6 * cm], rowHeights=[24])
    linea2.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), 0.7, GRIS_T)]))
    cont = Table([[linea, linea2],
                  [Paragraph('Operador que ejecuta', st['firma']), Paragraph('Responsable de calidad', st['firma'])]],
                 colWidths=[7.6 * cm, 7.6 * cm])
    cont.setStyle(TableStyle([('TOPPADDING', (0, 1), (-1, 1), 2), ('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    return cont


def _motivo_falla(detalle):
    # una falla real tiene prioridad para el mensaje
    for prueba, filas in detalle.items():
        for f in filas:
            if f['resultado'] == 'FALLA':
                m = ', '.join(f['motivos'])
                fase = f.get('fase_fallo')
                return f"Canal {f['canal']} ({prueba}) — Fase {fase}: {m}. Se recomienda repetir la prueba."
    # sin fallas: si hay canales sin estandar, avisar cuales
    sin_est = [f"{f['canal']} ({prueba})" for prueba, filas in detalle.items()
               for f in filas if f['resultado'] == 'SIN ESTANDAR']
    if sin_est:
        muestra = ', '.join(sin_est[:6]) + ('…' if len(sin_est) > 6 else '')
        return (f"Canales sin límite definido en el perfil: {muestra}. "
                f"Completa el estándar para poder liberar la pieza.")
    return ''


def _contenido_pieza(st, pieza, batch, operador, fecha, equipo, perfil, veredicto, detalle, logo_path):
    elems = [_encabezado(st, f'QC-{pieza}', logo_path), Spacer(1, 10),
             _bloque_traza(st, {'pieza': pieza, 'batch': batch, 'fecha': fecha,
                                'equipo': equipo, 'operador': operador, 'perfil': perfil}),
             Spacer(1, 8)]
    # una pieza RECHAZADA no tiene datos evaluados: sin tarjetas por prueba
    if veredicto != 'RECHAZADO':
        elems += [_resumen_pruebas(st, detalle), Spacer(1, 8)]
    elems += [_banner_veredicto(st, veredicto, _motivo_falla(detalle)), Spacer(1, 10)]
    for prueba, filas in detalle.items():
        nombre = 'Detalle — prueba óptica' if prueba == 'Optico' else 'Detalle — prueba eléctrica'
        elems.append(Paragraph(nombre, st['h2']))
        elems.append(_tabla_detalle(st, prueba, filas))
        elems.append(Spacer(1, 6))
    elems.append(Spacer(1, 16))
    elems.append(_firmas(st))
    return elems


def generar_pdf(ruta_salida, no_pieza, batch, operador, fecha, veredicto, detalle,
                equipo='—', perfil='—', logo_path=None):
    """Reporte de UN desechable individual."""
    doc = SimpleDocTemplate(ruta_salida, pagesize=letter, topMargin=1.2 * cm,
                            bottomMargin=1.2 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    st = _styles()
    doc.build(_contenido_pieza(st, no_pieza, batch, operador, fecha, equipo, perfil,
                               veredicto, detalle, logo_path))
    return ruta_salida


def generar_pdf_lote(ruta_salida, batch, operador, fecha, resultados, perfil='—',
                     equipo='—', logo_path=None):
    """Reporte del LOTE completo: portada con resumen + una pagina por pieza."""
    doc = SimpleDocTemplate(ruta_salida, pagesize=letter, topMargin=1.2 * cm,
                            bottomMargin=1.2 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    st = _styles()
    elems = []

    total = len(resultados)
    pasaron = sum(1 for r in resultados if r['veredicto'] == 'PASO')
    incompletos = sum(1 for r in resultados if r['veredicto'] == 'INCOMPLETO')
    rechazados = sum(1 for r in resultados if r['veredicto'] == 'RECHAZADO')
    fallaron = total - pasaron - incompletos - rechazados
    tasa = f'{(100*pasaron/total):.0f}%' if total else '—'

    elems.append(_encabezado(st, f'LOTE-{batch}', logo_path))
    elems.append(Spacer(1, 10))
    elems.append(Paragraph('Resumen del lote', st['h2']))
    resumen = Table([
        [Paragraph('Batch / lote', st['label']), Paragraph('Operador', st['label']), Paragraph('Fecha', st['label'])],
        [Paragraph(str(batch), st['valor']), Paragraph(str(operador), st['valor']), Paragraph(str(fecha), st['valor'])],
    ], colWidths=[5.5 * cm, 5.5 * cm, 5.5 * cm])
    resumen.setStyle(TableStyle([('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, 0), 8)]))
    elems.append(resumen)
    elems.append(Spacer(1, 6))

    celdas_kpi = [
        ('Total', str(total), None),
        ('Pasaron', str(pasaron), VERDE_T),
        ('Fallaron', str(fallaron), ROJO_T),
        ('Incompletos', str(incompletos), AMBAR_T),
    ]
    if rechazados:
        celdas_kpi.append(('Rechazados', str(rechazados), GRIS_OSC))
    celdas_kpi.append(('Aprobación', tasa, AZUL))
    tarjetas = Table([[
        Table([[Paragraph(lbl, st['label'])],
               [Paragraph(val, ParagraphStyle('n', parent=st['valor'], fontSize=18,
                                              textColor=col or colors.black))]])
        for lbl, val, col in celdas_kpi
    ]], colWidths=[15.2 * cm / len(celdas_kpi)] * len(celdas_kpi))
    tarjetas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1EFE8')),
        ('BOX', (0, 0), (-1, -1), 0.5, LINEA), ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elems.append(tarjetas)
    elems.append(Spacer(1, 12))

    elems.append(Paragraph('Resultado por desechable', st['h2']))
    data = [['Pieza', 'Óptico', 'Eléctrico', 'Veredicto final']]
    estilos = []
    def _color_estado(txt):
        if txt == 'Pasó':
            return VERDE_T
        if txt == 'Incompleto':
            return AMBAR_T
        return ROJO_T
    for i, r in enumerate(sorted(resultados, key=lambda x: str(x['pieza'])), start=1):
        det = r['detalle']
        def estado(p):
            fs = det.get(p, [])
            if not fs:
                return '—'
            if any(x['resultado'] == 'FALLA' for x in fs):
                return 'No pasó'
            if any(x['resultado'] == 'SIN ESTANDAR' for x in fs):
                return 'Incompleto'
            return 'Pasó'
        eo, ee = estado('Optico'), estado('Electrico')
        vtxt = {'PASO': 'PASÓ', 'INCOMPLETO': 'INCOMPLETO',
                'RECHAZADO': 'RECHAZADO'}.get(r['veredicto'], 'NO PASÓ')
        data.append([str(r['pieza']), eo, ee, vtxt])
        if r['veredicto'] == 'RECHAZADO':
            col_final, col_final_t = GRIS_BG, GRIS_OSC
        else:
            col_final = VERDE if r['veredicto'] == 'PASO' else AMBAR if r['veredicto'] == 'INCOMPLETO' else ROJO
            col_final_t = _color_estado('Pasó' if r['veredicto'] == 'PASO' else 'Incompleto' if r['veredicto'] == 'INCOMPLETO' else 'No pasó')
        estilos += [('BACKGROUND', (3, i), (3, i), col_final), ('TEXTCOLOR', (3, i), (3, i), col_final_t)]
        estilos += [('TEXTCOLOR', (1, i), (1, i), _color_estado(eo))]
        estilos += [('TEXTCOLOR', (2, i), (2, i), _color_estado(ee))]
    tabla = Table(data, colWidths=[3 * cm, 4 * cm, 4 * cm, 4.2 * cm], repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.4, LINEA), ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ] + estilos))
    elems.append(tabla)
    elems.append(Spacer(1, 16))
    elems.append(_firmas(st))

    # detalle por pieza (una pagina por desechable)
    for r in sorted(resultados, key=lambda x: str(x['pieza'])):
        elems.append(PageBreak())
        elems += _contenido_pieza(st, r['pieza'], batch, operador, fecha, equipo, perfil,
                                  r['veredicto'], r['detalle'], logo_path)

    doc.build(elems)
    return ruta_salida
