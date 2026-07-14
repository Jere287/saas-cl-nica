"""
reporte.py — Genera los reportes PDF del sistema de control de calidad.

Dos modos:
  - generar_pdf(...)              -> reporte de UN desechable individual
  - generar_pdf_lote(...)         -> reporte del LOTE completo (portada + cada pieza)

Diseno monocromatico (blanco y negro, sin colores) y sobrio: tipografia con
serifa (Times), membrete con recuadro, datos de trazabilidad, resultado por
prueba (optico / electrico), DICTAMEN final y firmas del OPERADOR DESIGNADO y
el INGENIERO A CARGO. El estado se comunica con texto, no con color.

Criterio: media + desviacion estandar.
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, Image)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os

# --- tipografia sobria con serifa (documento formal) ---
FUENTE = 'Times-Roman'
FUENTE_B = 'Times-Bold'
FUENTE_I = 'Times-Italic'

# --- paleta monocromatica: solo negro, blanco y grises ---
NEGRO = colors.black
BLANCO = colors.white
GRIS_ENC = colors.HexColor('#E4E4E4')   # relleno de encabezados de tabla
GRIS_SUAVE = colors.HexColor('#F4F4F4')  # relleno muy claro (tarjetas)
GRIS_T = colors.HexColor('#4A4A4A')      # texto de etiquetas
LINEA_SUAVE = colors.HexColor('#999999')  # rejillas internas

ANCHO = 16.5 * cm   # ancho comun de todos los bloques (alineacion uniforme)

EMPRESA = '[Nombre de la empresa]'   # editable
SUBTITULO = 'Dispositivo de detección de cáncer cervicouterino'


def _styles():
    s = getSampleStyleSheet()
    return {
        'empresa': ParagraphStyle('emp', parent=s['Normal'], fontSize=13, leading=15,
                                  textColor=NEGRO, fontName=FUENTE_B, alignment=TA_CENTER),
        'titulo': ParagraphStyle('t', parent=s['Normal'], fontSize=10.5, leading=13,
                                 textColor=NEGRO, fontName=FUENTE_B, alignment=TA_CENTER),
        'subt': ParagraphStyle('st', parent=s['Normal'], fontSize=8.5, leading=11,
                               textColor=GRIS_T, fontName=FUENTE_I, alignment=TA_CENTER),
        'folio_l': ParagraphStyle('fl', parent=s['Normal'], fontSize=7.5, leading=9,
                                  textColor=GRIS_T, fontName=FUENTE, alignment=TA_CENTER),
        'folio_v': ParagraphStyle('fv', parent=s['Normal'], fontSize=10, leading=12,
                                  textColor=NEGRO, fontName=FUENTE_B, alignment=TA_CENTER),
        'label': ParagraphStyle('lb', parent=s['Normal'], fontSize=8, leading=10,
                                textColor=GRIS_T, fontName=FUENTE),
        'valor': ParagraphStyle('vl', parent=s['Normal'], fontSize=10.5, leading=12,
                                fontName=FUENTE_B, textColor=NEGRO),
        'kpi_lbl': ParagraphStyle('kl', parent=s['Normal'], fontSize=8, leading=10,
                                  textColor=GRIS_T, fontName=FUENTE, alignment=TA_CENTER),
        'kpi_val': ParagraphStyle('kv', parent=s['Normal'], fontSize=17, leading=19,
                                  fontName=FUENTE_B, textColor=NEGRO, alignment=TA_CENTER),
        'h2': ParagraphStyle('h2', parent=s['Normal'], fontSize=10.5, leading=13,
                             fontName=FUENTE_B, textColor=NEGRO, spaceBefore=8, spaceAfter=4),
        'justif': ParagraphStyle('ju', parent=s['Normal'], fontSize=8.5, leading=11.5,
                                 textColor=GRIS_T, fontName=FUENTE, alignment=TA_JUSTIFY),
        'firma': ParagraphStyle('fi', parent=s['Normal'], fontSize=8.5, leading=10,
                                textColor=NEGRO, alignment=TA_CENTER, fontName=FUENTE_B),
        'firma_sub': ParagraphStyle('fis', parent=s['Normal'], fontSize=7.5, leading=9,
                                    textColor=GRIS_T, alignment=TA_CENTER, fontName=FUENTE),
    }


def _encabezado(st, folio, logo_path=None):
    """Membrete monocromatico: recuadro con logo, nombre de empresa y folio."""
    if logo_path and os.path.exists(logo_path):
        logo = Image(logo_path, width=1.3 * cm, height=1.3 * cm)
    else:
        logo = Table([['LOGO']], colWidths=[1.3 * cm], rowHeights=[1.3 * cm])
        logo.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.7, NEGRO),
            ('TEXTCOLOR', (0, 0), (-1, -1), NEGRO),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTNAME', (0, 0), (-1, -1), FUENTE_B),
        ]))

    centro = Table([[Paragraph(EMPRESA, st['empresa'])],
                    [Paragraph('Certificado de control de calidad', st['titulo'])],
                    [Paragraph(SUBTITULO, st['subt'])]],
                   colWidths=[11.0 * cm])
    centro.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))

    der = Table([[Paragraph('Folio', st['folio_l'])], [Paragraph(folio, st['folio_v'])]],
                colWidths=[3.4 * cm], rowHeights=[0.55 * cm, 0.75 * cm])
    der.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.7, NEGRO),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, LINEA_SUAVE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3), ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))

    banda = Table([[logo, centro, der]], colWidths=[1.7 * cm, 11.4 * cm, 3.4 * cm])
    banda.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, NEGRO),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'), ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return banda


def _bloque_traza(st, datos):
    filas = [
        [Paragraph('No. de pieza', st['label']), Paragraph('Batch / lote', st['label']), Paragraph('Fecha y hora', st['label'])],
        [Paragraph(str(datos['pieza']), st['valor']), Paragraph(str(datos['batch']), st['valor']), Paragraph(str(datos['fecha']), st['valor'])],
        [Paragraph('Equipo / serie', st['label']), Paragraph('Operador', st['label']), Paragraph('Perfil de límites', st['label'])],
        [Paragraph(str(datos.get('equipo') or 'N/D'), st['valor']), Paragraph(str(datos['operador']), st['valor']), Paragraph(str(datos['perfil']), st['valor'])],
    ]
    t = Table(filas, colWidths=[ANCHO / 3] * 3)
    t.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.7, NEGRO),
        ('LINEBELOW', (0, 1), (-1, 1), 0.4, LINEA_SUAVE),
        ('FONTNAME', (0, 0), (-1, -1), FUENTE),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 3), ('TOPPADDING', (0, 2), (-1, 2), 8),
    ]))
    return t


def _estado_prueba(filas):
    """Texto de estado de una prueba, sin color."""
    total = len(filas)
    pasan = sum(1 for f in filas if f['resultado'] == 'PASA')
    hay_falla = any(f['resultado'] == 'FALLA' for f in filas)
    hay_sin = any(f['resultado'] == 'SIN ESTANDAR' for f in filas)
    if total and not hay_falla and not hay_sin:
        return f'PASÓ ({pasan} de {total})'
    if hay_falla:
        return f'NO PASÓ ({pasan} de {total})'
    return f'INCOMPLETO ({pasan} de {total})'


def _resumen_pruebas(st, detalle):
    """Dos tarjetas monocromaticas: resultado optico y electrico por separado."""
    celdas = []
    for prueba in ['Optico', 'Electrico']:
        filas = detalle.get(prueba, [])
        nombre = 'Prueba óptica' if prueba == 'Optico' else 'Prueba eléctrica'
        estado = _estado_prueba(filas)
        celda = Table([[Paragraph(nombre, st['label'])],
                       [Paragraph(estado, ParagraphStyle('e', parent=st['valor'], fontSize=12.5, leading=15))]],
                      colWidths=[ANCHO / 2 - 0.35 * cm])
        celda.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.7, NEGRO),
            ('LINEBEFORE', (0, 0), (0, -1), 2.5, NEGRO),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (0, 0), 7), ('BOTTOMPADDING', (0, 1), (0, 1), 8),
        ]))
        celdas.append(celda)
    cont = Table([celdas], colWidths=[ANCHO / 2, ANCHO / 2])
    cont.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0),
                              ('RIGHTPADDING', (0, 0), (0, 0), 0.7 * cm),
                              ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    return cont


def _banner_dictamen(st, veredicto, motivo):
    if veredicto == 'PASO':
        label = 'PASÓ'
        sub = 'Todos los canales se encuentran dentro de los límites establecidos.'
    elif veredicto == 'INCOMPLETO':
        label = 'INCOMPLETO'
        sub = motivo if motivo else ('Hay canales sin límite definido en el perfil. No es posible '
                                     'aprobar la pieza hasta completar el estándar.')
    elif veredicto == 'RECHAZADO':
        label = 'RECHAZADO'
        sub = motivo if motivo else ('El archivo no tiene el formato que entrega el equipo; la pieza '
                                     'no se evaluó. Vuelva a exportar el archivo del equipo y cárguelo de nuevo.')
    else:
        label = 'NO PASÓ'
        sub = motivo if motivo else 'Uno o más canales se encuentran fuera de los límites establecidos.'
    txt = f'Dictamen:  {label}'
    cont = Table([[Paragraph(txt, ParagraphStyle('vb', parent=st['valor'], fontSize=13.5, leading=16))],
                  [Paragraph(sub, st['justif'])]],
                 colWidths=[ANCHO])
    cont.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.2, NEGRO),
        ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 8), ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 2),
    ]))
    return cont


def _rango_txt(lo, hi):
    """Texto 'lo a hi' tolerante a que falte uno de los dos limites (o ambos)."""
    if lo is None and hi is None:
        return 'Sin límite'
    lo_t = f'{lo:.2f}' if lo is not None else 'N/D'
    hi_t = f'{hi:.2f}' if hi is not None else 'N/D'
    return f'{lo_t} a {hi_t}'


def _tabla_detalle(st, prueba, filas):
    data = [['Canal', 'Media', 'Rango de media', 'Desv.', 'Rango de desv.', 'Rango', 'Estado', 'Falla']]
    estilos = []
    for i, f in enumerate(filas, start=1):
        est = f.get('estandar') or {}
        rmedia = _rango_txt(est.get('media_min'), est.get('media_max'))
        rdesv = _rango_txt(est.get('desv_min'), est.get('desv_max'))
        if f['resultado'] == 'FALLA':
            estado_txt = 'Falla'; falla_txt = f"Fase {f.get('fase_fallo')}"
        elif f['resultado'] == 'PASA':
            estado_txt = 'Pasa'; falla_txt = 'Ninguna'
        else:
            estado_txt = 'Sin estándar'; falla_txt = 'Sin límite'
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
        # las filas con falla se resaltan en negrita, no con color
        if f['resultado'] == 'FALLA':
            estilos += [('FONTNAME', (6, i), (7, i), FUENTE_B)]
    t = Table(data, colWidths=[2.2*cm, 1.8*cm, 2.7*cm, 1.8*cm, 2.7*cm, 1.5*cm, 2.1*cm, 1.7*cm], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GRIS_ENC),
        ('TEXTCOLOR', (0, 0), (-1, 0), NEGRO),
        ('FONTNAME', (0, 0), (-1, -1), FUENTE),
        ('FONTNAME', (0, 0), (-1, 0), FUENTE_B),
        ('FONTSIZE', (0, 0), (-1, -1), 7.2),
        ('GRID', (0, 0), (-1, -1), 0.5, NEGRO),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (0, -1), 6),
    ] + estilos))
    return t


def _firmas(st, operador='', ingeniero=''):
    """Bloque de firmas: OPERADOR DESIGNADO e INGENIERO A CARGO."""
    def _bloque(rol, nombre):
        linea = Table([['']], colWidths=[6.6 * cm], rowHeights=[28])
        linea.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), 0.8, NEGRO)]))
        return Table([[linea],
                      [Paragraph(rol, st['firma'])],
                      [Paragraph(f'Nombre: {nombre}' if nombre else 'Nombre y firma', st['firma_sub'])]],
                     colWidths=[6.6 * cm])

    op = _bloque('Operador designado', str(operador or '').strip())
    ing = _bloque('Ingeniero a cargo', str(ingeniero or '').strip())
    for b in (op, ing):
        b.setStyle(TableStyle([
            ('TOPPADDING', (0, 1), (-1, -1), 3), ('BOTTOMPADDING', (0, 1), (-1, 1), 1),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
    cont = Table([[op, ing]], colWidths=[ANCHO / 2, ANCHO / 2])
    cont.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                              ('TOPPADDING', (0, 0), (-1, -1), 0)]))
    return cont


def _motivo_falla(detalle):
    # una falla real tiene prioridad para el mensaje
    for prueba, filas in detalle.items():
        for f in filas:
            if f['resultado'] == 'FALLA':
                m = ', '.join(f['motivos'])
                fase = f.get('fase_fallo')
                prueba_txt = 'Óptico' if prueba == 'Optico' else 'Eléctrico'
                return f"Canal {f['canal']} ({prueba_txt}), Fase {fase}: {m}. Se recomienda repetir la prueba."
    # sin fallas: si hay canales sin estandar, avisar cuales
    sin_est = [f"{f['canal']} ({'Óptico' if prueba == 'Optico' else 'Eléctrico'})"
               for prueba, filas in detalle.items()
               for f in filas if f['resultado'] == 'SIN ESTANDAR']
    if sin_est:
        muestra = ', '.join(sin_est[:6]) + ('…' if len(sin_est) > 6 else '')
        return (f"Canales sin límite definido en el perfil: {muestra}. "
                f"Complete el estándar para poder liberar la pieza.")
    return ''


def _contenido_pieza(st, pieza, batch, operador, fecha, equipo, perfil, veredicto, detalle,
                     logo_path, ingeniero=''):
    elems = [_encabezado(st, f'QC-{pieza}', logo_path), Spacer(1, 10),
             _bloque_traza(st, {'pieza': pieza, 'batch': batch, 'fecha': fecha,
                                'equipo': equipo, 'operador': operador, 'perfil': perfil}),
             Spacer(1, 8)]
    # una pieza RECHAZADA no tiene datos evaluados: sin tarjetas por prueba
    if veredicto != 'RECHAZADO':
        elems += [_resumen_pruebas(st, detalle), Spacer(1, 8)]
    elems += [_banner_dictamen(st, veredicto, _motivo_falla(detalle)), Spacer(1, 10)]
    for prueba, filas in detalle.items():
        nombre = 'Detalle de la prueba óptica' if prueba == 'Optico' else 'Detalle de la prueba eléctrica'
        elems.append(Paragraph(nombre, st['h2']))
        elems.append(_tabla_detalle(st, prueba, filas))
        elems.append(Spacer(1, 6))
    elems.append(Spacer(1, 18))
    elems.append(_firmas(st, operador, ingeniero))
    return elems


def generar_pdf(ruta_salida, no_pieza, batch, operador, fecha, veredicto, detalle,
                equipo='N/D', perfil='N/D', logo_path=None, ingeniero=''):
    """Reporte de UN desechable individual."""
    doc = SimpleDocTemplate(ruta_salida, pagesize=letter, topMargin=1.2 * cm,
                            bottomMargin=1.2 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    st = _styles()
    doc.build(_contenido_pieza(st, no_pieza, batch, operador, fecha, equipo, perfil,
                               veredicto, detalle, logo_path, ingeniero))
    return ruta_salida


def generar_pdf_lote(ruta_salida, batch, operador, fecha, resultados, perfil='N/D',
                     equipo='N/D', logo_path=None, ingeniero=''):
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
    tasa = f'{(100*pasaron/total):.0f}%' if total else 'N/D'

    elems.append(_encabezado(st, f'LOTE-{batch}', logo_path))
    elems.append(Spacer(1, 10))
    elems.append(Paragraph('Resumen del lote', st['h2']))
    resumen = Table([
        [Paragraph('Batch / lote', st['label']), Paragraph('Operador', st['label']), Paragraph('Fecha', st['label'])],
        [Paragraph(str(batch), st['valor']), Paragraph(str(operador), st['valor']), Paragraph(str(fecha), st['valor'])],
    ], colWidths=[ANCHO / 3] * 3)
    resumen.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.7, NEGRO),
        ('FONTNAME', (0, 0), (-1, -1), FUENTE),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 1), (-1, 1), 4), ('BOTTOMPADDING', (0, 1), (-1, 1), 5),
    ]))
    elems.append(resumen)
    elems.append(Spacer(1, 8))

    celdas_kpi = [
        ('Total', str(total)),
        ('Pasaron', str(pasaron)),
        ('Fallaron', str(fallaron)),
        ('Incompletos', str(incompletos)),
    ]
    if rechazados:
        celdas_kpi.append(('Rechazados', str(rechazados)))
    celdas_kpi.append(('Aprobación', tasa))
    col_w = ANCHO / len(celdas_kpi)
    def _tarjeta(lbl, val):
        c = Table([[Paragraph(lbl, st['kpi_lbl'])],
                   [Paragraph(val, st['kpi_val'])]], colWidths=[col_w])
        c.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2), ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, 0), 0), ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('TOPPADDING', (0, 1), (-1, 1), 0), ('BOTTOMPADDING', (0, 1), (-1, 1), 0),
        ]))
        return c
    tarjetas = Table([[_tarjeta(lbl, val) for lbl, val in celdas_kpi]],
                     colWidths=[col_w] * len(celdas_kpi))
    tarjetas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GRIS_SUAVE),
        ('BOX', (0, 0), (-1, -1), 0.7, NEGRO), ('INNERGRID', (0, 0), (-1, -1), 0.5, NEGRO),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 2), ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ]))
    elems.append(tarjetas)
    elems.append(Spacer(1, 12))

    elems.append(Paragraph('Resultado por desechable', st['h2']))
    data = [['Pieza', 'Óptico', 'Eléctrico', 'Dictamen']]
    estilos = []
    for i, r in enumerate(sorted(resultados, key=lambda x: str(x['pieza'])), start=1):
        det = r['detalle']
        def estado(p):
            fs = det.get(p, [])
            if not fs:
                return 'N/D'
            if any(x['resultado'] == 'FALLA' for x in fs):
                return 'No pasó'
            if any(x['resultado'] == 'SIN ESTANDAR' for x in fs):
                return 'Incompleto'
            return 'Pasó'
        eo, ee = estado('Optico'), estado('Electrico')
        vtxt = {'PASO': 'PASÓ', 'INCOMPLETO': 'INCOMPLETO',
                'RECHAZADO': 'RECHAZADO'}.get(r['veredicto'], 'NO PASÓ')
        data.append([str(r['pieza']), eo, ee, vtxt])
        # el dictamen final en negrita para que salte a la vista sin usar color
        estilos += [('FONTNAME', (3, i), (3, i), FUENTE_B)]
    tabla = Table(data, colWidths=[3.3 * cm, 4.4 * cm, 4.4 * cm, 4.4 * cm], repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GRIS_ENC), ('TEXTCOLOR', (0, 0), (-1, 0), NEGRO),
        ('FONTNAME', (0, 0), (-1, -1), FUENTE), ('FONTNAME', (0, 0), (-1, 0), FUENTE_B),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, NEGRO), ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LEFTPADDING', (0, 0), (0, -1), 8),
    ] + estilos))
    elems.append(tabla)
    elems.append(Spacer(1, 18))
    elems.append(_firmas(st, operador, ingeniero))

    # detalle por pieza (una pagina por desechable)
    for r in sorted(resultados, key=lambda x: str(x['pieza'])):
        elems.append(PageBreak())
        elems += _contenido_pieza(st, r['pieza'], batch, operador, fecha, equipo, perfil,
                                  r['veredicto'], r['detalle'], logo_path, ingeniero)

    doc.build(elems)
    return ruta_salida
