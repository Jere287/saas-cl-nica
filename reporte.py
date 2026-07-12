"""
reporte.py — Genera los reportes PDF corporativos del sistema de control de calidad.

Dos modos:
  - generar_pdf(...)              -> reporte de UN desechable individual
  - generar_pdf_lote(...)         -> reporte del LOTE completo (portada + cada pieza)

Diseno corporativo tipo "documento controlado":
  - encabezado azul con logo, empresa y folio + franja con el criterio y fecha de emision
  - pie de pagina en todas las hojas: folio, fecha de generacion y "Pagina X de Y"
  - bloque de trazabilidad en cajas etiquetadas (mismo estilo que el Excel exportado)
  - veredicto final con glifo (check / cruz) y motivo
  - tabla de detalle separada por FASE 1 (desviacion) y FASE 2 (promedio), con los
    limites de cada fase, el valor fuera de rango resaltado y una barra grafica
    "posicion en rango" que muestra donde cae el valor dentro de la zona permitida
  - portada de lote con tarjetas KPI, barra de distribucion del lote y tabla por pieza
  - area de firmas con nombre, rol y fecha

Criterio: dos fases por canal — Fase 1 desviacion estandar, Fase 2 promedio.
"""
from datetime import datetime
import os

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.graphics.shapes import Drawing, Rect, Circle, PolyLine, Line
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, Image, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# --- paleta corporativa Hera Diagnostics (alineada con la interfaz web y el Excel) ---
# Colores de marca centralizados aquí: ajustar estos 6 valores basta para retematizar el PDF.
AZUL = colors.HexColor('#5E2379')        # morado principal de marca
MARINO = colors.HexColor('#3B1B55')      # morado profundo (franjas y encabezados)
AZUL_CLARO = colors.HexColor('#D9C2EC')  # texto claro sobre morado
AZUL_TINTE = colors.HexColor('#EDE3F6')  # fondos suaves / zona permitida
AZUL_BORDE = colors.HexColor('#D6C2E8')
ZEBRA = colors.HexColor('#F7F3FB')
VERDE = colors.HexColor('#C6EFCE')
VERDE_T = colors.HexColor('#006100')
VERDE_BAR = colors.HexColor('#12A15A')
ROJO = colors.HexColor('#FFC7CE')
ROJO_T = colors.HexColor('#9C0006')
ROJO_BAR = colors.HexColor('#D03B3B')
AMBAR = colors.HexColor('#FFF2CC')
AMBAR_T = colors.HexColor('#9C6500')
AMBAR_BAR = colors.HexColor('#E9A23B')
GRIS_T = colors.HexColor('#595959')
GRIS_BG = colors.HexColor('#EDEDED')
GRIS_OSC = colors.HexColor('#3A3A3A')
GRIS_BAR = colors.HexColor('#5A6472')
LINEA = colors.HexColor('#CCCCCC')
TINTA = colors.HexColor('#16212E')
PISTA = colors.HexColor('#E7EAEE')

EMPRESA = 'Hera Diagnostics'   # editable
SUBTITULO = 'Dispositivo de detección de cáncer cervicouterino'
ANCHO_UTIL = 18.5 * cm   # carta (21.6 cm) menos márgenes laterales


# ---------------------------------------------------------------- pie de página
def _lienzo(folio):
    """Lienzo con pie de página 'Página X de Y' (dos pasadas) + folio y fecha."""
    fecha_gen = datetime.now().strftime('%d/%m/%Y %H:%M')

    class _Lienzo(rl_canvas.Canvas):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self._paginas = []

        def showPage(self):
            self._paginas.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._paginas)
            for estado in self._paginas:
                self.__dict__.update(estado)
                self._pie(total)
                super().showPage()
            super().save()

        def _pie(self, total):
            ancho, _ = letter
            self.setStrokeColor(LINEA)
            self.setLineWidth(0.6)
            self.line(1.5 * cm, 1.15 * cm, ancho - 1.5 * cm, 1.15 * cm)
            self.setFont('Helvetica', 7)
            self.setFillColor(GRIS_T)
            self.drawString(1.5 * cm, 0.8 * cm,
                            f'{folio} · Sistema de Control de Calidad · generado el {fecha_gen}')
            self.drawRightString(ancho - 1.5 * cm, 0.8 * cm,
                                 f'Página {self._pageNumber} de {total}')

    return _Lienzo


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
        'franja': ParagraphStyle('fr', parent=s['Normal'], fontSize=7, leading=9,
                                 textColor=AZUL_CLARO),
        'franja_r': ParagraphStyle('frr', parent=s['Normal'], fontSize=7, leading=9,
                                   textColor=AZUL_CLARO, alignment=2),
        'label': ParagraphStyle('lb', parent=s['Normal'], fontSize=6.8, leading=9,
                                textColor=colors.HexColor('#40546B')),
        'valor': ParagraphStyle('vl', parent=s['Normal'], fontSize=10, leading=13,
                                fontName='Helvetica-Bold', textColor=TINTA),
        'h2': ParagraphStyle('h2', parent=s['Normal'], fontSize=11, fontName='Helvetica-Bold',
                             textColor=AZUL, spaceBefore=8, spaceAfter=2),
        'normal': s['Normal'],
        'nota': ParagraphStyle('no', parent=s['Normal'], fontSize=7, leading=9.5,
                               textColor=GRIS_T),
        'celda': ParagraphStyle('ce', parent=s['Normal'], fontSize=7.5, leading=9.5),
        'firma': ParagraphStyle('fi', parent=s['Normal'], fontSize=8, textColor=GRIS_T,
                                alignment=TA_CENTER),
        'firma_rol': ParagraphStyle('fro', parent=s['Normal'], fontSize=9,
                                    fontName='Helvetica-Bold', textColor=TINTA,
                                    alignment=TA_CENTER),
    }


def _seccion(st, texto):
    """Título de sección con regla azul debajo."""
    return [Paragraph(texto, st['h2']),
            HRFlowable(width='100%', thickness=0.9, color=AZUL_TINTE,
                       spaceBefore=1, spaceAfter=5)]


def _encabezado(st, folio, logo_path=None, emitido='—'):
    """Banda azul superior (logo, empresa, folio) + franja con criterio y emisión."""
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
    izq = Table(titulo_celda, colWidths=[1.4 * cm, 12.2 * cm])
    izq.setStyle(TableStyle([
        ('SPAN', (0, 0), (0, 1)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    der = Table([[Paragraph('Folio', st['folio_l'])], [Paragraph(folio, st['folio_v'])]],
                colWidths=[4.3 * cm])
    der.setStyle(TableStyle([('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
    banda = Table([[izq, der]], colWidths=[13.9 * cm, 4.6 * cm])
    banda.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), AZUL),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    franja = Table([[Paragraph('Criterio de aceptación: Fase 1 — desviación estándar · '
                               'Fase 2 — promedio (si pasa la Fase 1)', st['franja']),
                     Paragraph(f'Emitido: {emitido}', st['franja_r'])]],
                   colWidths=[13.2 * cm, 5.3 * cm])
    franja.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), MARINO),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return [banda, franja]


def _bloque_traza(st, campos):
    """Rejilla de trazabilidad: cajas con etiqueta pequeña arriba y valor en negrita,
    mismo lenguaje visual que el bloque de datos del Excel exportado."""
    filas = []
    for i in range(0, len(campos), 3):
        terna = campos[i:i + 3]
        while len(terna) < 3:
            terna.append(('', ''))
        filas.append([[Paragraph(e, st['label']), Paragraph(str(v) if v not in (None, '') else '—', st['valor'])]
                      if e else '' for e, v in terna])
    t = Table(filas, colWidths=[ANCHO_UTIL / 3] * 3)
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.6, AZUL_BORDE),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FBFCFE')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
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
            estado = 'Pasó'; color = VERDE_T; barra = VERDE_BAR
        elif hay_falla:
            estado = 'No pasó'; color = ROJO_T; barra = ROJO_BAR
        else:
            estado = 'Incompleto'; color = AMBAR_T; barra = AMBAR_BAR
        detalle_txt = f'{pasan} de {total} canales dentro de límites' if total else 'Sin canales evaluados'
        celda = Table([[Paragraph(nombre, st['label'])],
                       [Paragraph(estado, ParagraphStyle('e', parent=st['valor'], fontSize=13, textColor=color))],
                       [Paragraph(detalle_txt, st['nota'])]],
                      colWidths=[8.7 * cm])
        celda.setStyle(TableStyle([
            ('LINEBEFORE', (0, 0), (0, -1), 3, barra),
            ('BOX', (0, 0), (-1, -1), 0.5, LINEA),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FBFCFE')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (0, 0), 7), ('BOTTOMPADDING', (0, 2), (0, 2), 7),
        ]))
        celdas.append(celda)
    cont = Table([celdas], colWidths=[ANCHO_UTIL / 2, ANCHO_UTIL / 2])
    cont.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (0, 0), 11),
        ('RIGHTPADDING', (1, 0), (1, 0), 0), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return cont


def _glifo_veredicto(tipo, color):
    """Glifo vectorial (check / cruz / exclamación) dentro de un círculo."""
    d = Drawing(26, 26)
    d.add(Circle(13, 13, 10.5, strokeColor=color, strokeWidth=1.7, fillColor=None))
    if tipo == 'check':
        d.add(PolyLine([8.2, 13.2, 11.6, 9.4, 18.2, 17.2], strokeColor=color,
                       strokeWidth=2.2, strokeLineCap=1, strokeLineJoin=1))
    elif tipo == 'cruz':
        d.add(Line(9.2, 9.2, 16.8, 16.8, strokeColor=color, strokeWidth=2.2, strokeLineCap=1))
        d.add(Line(9.2, 16.8, 16.8, 9.2, strokeColor=color, strokeWidth=2.2, strokeLineCap=1))
    else:  # exclamación
        d.add(Line(13, 17.5, 13, 11.5, strokeColor=color, strokeWidth=2.4, strokeLineCap=1))
        d.add(Circle(13, 8, 1.5, strokeColor=None, fillColor=color))
    return d


def _banner_veredicto(st, veredicto, motivo):
    if veredicto == 'PASO':
        label = 'PASÓ'; tx = VERDE_T; bg = VERDE; borde = colors.HexColor('#3B6D11')
        sub = 'Todos los canales dentro de límites.'
        glifo = 'check'
    elif veredicto == 'INCOMPLETO':
        label = 'INCOMPLETO'; tx = AMBAR_T; bg = AMBAR; borde = colors.HexColor('#9C6500')
        sub = motivo if motivo else ('Hay canales sin límite definido en el perfil. No se puede '
                                     'aprobar la pieza hasta completar el estándar.')
        glifo = 'exclamacion'
    elif veredicto == 'RECHAZADO':
        label = 'RECHAZADO'; tx = GRIS_OSC; bg = GRIS_BG; borde = GRIS_OSC
        sub = motivo if motivo else ('El archivo no tiene el formato que entrega el equipo; la pieza '
                                     'NO se evaluó. Vuelve a exportar el JSON del equipo y súbelo de nuevo.')
        glifo = 'cruz'
    else:
        label = 'NO PASÓ'; tx = ROJO_T; bg = ROJO; borde = colors.HexColor('#A32D2D')
        sub = motivo if motivo else 'Uno o más canales fuera de límites.'
        glifo = 'cruz'
    glifo_p = _glifo_veredicto(glifo, tx)
    cont = Table([[glifo_p, Paragraph(f'Veredicto final: {label}',
                                      ParagraphStyle('vb', parent=st['valor'], fontSize=12.5, textColor=tx))],
                  ['', Paragraph(sub, ParagraphStyle('vs', parent=st['normal'], fontSize=8,
                                                     leading=10, textColor=tx))]],
                 colWidths=[1.5 * cm, ANCHO_UTIL - 1.5 * cm])
    cont.setStyle(TableStyle([
        ('SPAN', (0, 0), (0, 1)),
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX', (0, 0), (-1, -1), 1, borde),
        ('VALIGN', (0, 0), (0, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 7), ('BOTTOMPADDING', (0, 1), (-1, 1), 7),
    ]))
    return cont


# ---------------------------------------------------------------- detalle por canal
def _fuera(valor, lo, hi):
    """True si el valor (redondeado a 2, como evalúa la app) queda fuera de [lo, hi]."""
    v = round(float(valor), 2)
    if lo is not None and v < round(float(lo), 2):
        return True
    if hi is not None and v > round(float(hi), 2):
        return True
    return False


def _fmt(v):
    """Formato numérico compacto: los valores grandes (p. ej. canales ópticos en
    decenas de miles) pierden decimales para que quepan en su columna sin
    encimarse con la celda vecina."""
    v = float(v)
    if abs(v) >= 1000:
        return f'{v:,.0f}'
    if abs(v) >= 100:
        return f'{v:,.1f}'
    return f'{v:.2f}'


def _rango_txt(lo, hi):
    """Texto 'lo–hi' tolerante a que falte uno de los dos limites (o ambos)."""
    if lo is None and hi is None:
        return '—'
    lo_t = _fmt(lo) if lo is not None else '—'
    hi_t = _fmt(hi) if hi is not None else '—'
    return f'{lo_t}–{hi_t}'


def _barra_rango(valor, lo, hi):
    """Barra 'posición en rango': franja azul = zona permitida [lo, hi]; el punto
    marca dónde cae el valor (verde dentro, rojo fuera)."""
    W, H = 2.3 * cm, 10
    d = Drawing(W, H)
    fuera = _fuera(valor, lo, hi)
    if lo is not None and hi is not None:
        span = (hi - lo) or max(abs(hi), 1) * 0.2
    else:
        span = max(abs(valor), 1) * 0.5
    pad = span * 0.45
    dlo = (lo if lo is not None else valor) - pad
    dhi = (hi if hi is not None else valor) + pad
    dlo = min(dlo, valor)
    dhi = max(dhi, valor)
    rng = (dhi - dlo) or 1.0
    mx = 4.0

    def X(v):
        return mx + (v - dlo) / rng * (W - 2 * mx)

    d.add(Rect(0, H / 2 - 1.1, W, 2.2, rx=1.1, ry=1.1, fillColor=PISTA, strokeColor=None))
    x1 = X(lo) if lo is not None else 0
    x2 = X(hi) if hi is not None else W
    d.add(Rect(x1, 1.1, max(x2 - x1, 2), H - 2.2, rx=1.5, ry=1.5,
               fillColor=AZUL_TINTE, strokeColor=colors.HexColor('#C4A5DF'), strokeWidth=0.4))
    xv = min(max(X(valor), mx), W - mx)
    d.add(Circle(xv, H / 2, 2.4, fillColor=(ROJO_BAR if fuera else VERDE_BAR),
                 strokeColor=colors.white, strokeWidth=0.6))
    return d


def _tabla_detalle(st, prueba, filas):
    head1 = ['Canal', 'n', 'FASE 1 — Desviación estándar', '', '',
             'FASE 2 — Promedio', '', '', 'Rango', 'Resultado']
    head2 = ['', '', 'Valor', 'Límites', 'Posición', 'Valor', 'Límites', 'Posición', '', '']
    data = [head1, head2]
    estilos = []
    for i, f in enumerate(filas):
        r = i + 2                     # fila real en la tabla
        est = f.get('estandar') or {}
        desv, media = f['desv'], f['media']
        dmin, dmax = est.get('desv_min'), est.get('desv_max')
        mmin, mmax = est.get('media_min'), est.get('media_max')

        if f['resultado'] == 'SIN ESTANDAR':
            barra_d = barra_m = '—'
            resultado = 'Sin estándar'
        else:
            barra_d = _barra_rango(desv, dmin, dmax) if (dmin is not None or dmax is not None) else '—'
            barra_m = _barra_rango(media, mmin, mmax) if (mmin is not None or mmax is not None) else '—'
            if f['resultado'] == 'FALLA':
                resultado = f"Falla · F{f.get('fase_fallo') or '—'}"
            else:
                resultado = 'Pasa'

        data.append([str(f['canal']), str(f.get('n', 20)),
                     _fmt(desv), _rango_txt(dmin, dmax), barra_d,
                     _fmt(media), _rango_txt(mmin, mmax), barra_m,
                     _fmt(f.get('rango', 0)), resultado])

        # cebra
        if i % 2:
            estilos.append(('BACKGROUND', (0, r), (-1, r), ZEBRA))
        # valores fuera de rango resaltados (la fase que falló)
        if est and _fuera(desv, dmin, dmax):
            estilos += [('TEXTCOLOR', (2, r), (2, r), ROJO_T),
                        ('FONTNAME', (2, r), (2, r), 'Helvetica-Bold'),
                        ('BACKGROUND', (2, r), (2, r), ROJO)]
        if est and not _fuera(desv, dmin, dmax) and _fuera(media, mmin, mmax):
            estilos += [('TEXTCOLOR', (5, r), (5, r), ROJO_T),
                        ('FONTNAME', (5, r), (5, r), 'Helvetica-Bold'),
                        ('BACKGROUND', (5, r), (5, r), ROJO)]
        # columna resultado
        if f['resultado'] == 'FALLA':
            estilos += [('BACKGROUND', (9, r), (9, r), ROJO), ('TEXTCOLOR', (9, r), (9, r), ROJO_T),
                        ('FONTNAME', (9, r), (9, r), 'Helvetica-Bold')]
        elif f['resultado'] == 'PASA':
            estilos += [('BACKGROUND', (9, r), (9, r), VERDE), ('TEXTCOLOR', (9, r), (9, r), VERDE_T),
                        ('FONTNAME', (9, r), (9, r), 'Helvetica-Bold')]
        else:
            estilos += [('BACKGROUND', (9, r), (9, r), AMBAR), ('TEXTCOLOR', (9, r), (9, r), AMBAR_T),
                        ('FONTNAME', (9, r), (9, r), 'Helvetica-Bold'),
                        ('TEXTCOLOR', (2, r), (8, r), GRIS_T)]

    t = Table(data, colWidths=[1.7 * cm, 0.9 * cm, 1.5 * cm, 2.2 * cm, 2.3 * cm,
                               1.5 * cm, 2.2 * cm, 2.3 * cm, 1.4 * cm, 1.9 * cm],
              repeatRows=2)
    t.setStyle(TableStyle([
        # encabezado a dos niveles
        ('SPAN', (0, 0), (0, 1)), ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (2, 0), (4, 0)), ('SPAN', (5, 0), (7, 0)),
        ('SPAN', (8, 0), (8, 1)), ('SPAN', (9, 0), (9, 1)),
        ('BACKGROUND', (0, 0), (-1, 0), MARINO),
        ('BACKGROUND', (0, 1), (-1, 1), AZUL),
        ('BACKGROUND', (0, 0), (1, 1), MARINO),
        ('BACKGROUND', (8, 0), (9, 1), MARINO),
        ('TEXTCOLOR', (0, 0), (-1, 1), colors.white),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 1), 6.4),
        ('FONTSIZE', (0, 2), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.4, LINEA),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, 1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ] + estilos))
    return t


def _firmas(st):
    def panel(rol):
        p = Table([[''],
                   [Paragraph('Nombre y firma', st['firma'])],
                   [Paragraph(rol, st['firma_rol'])],
                   [Paragraph('Fecha: ____________________', st['firma'])]],
                  colWidths=[8.3 * cm], rowHeights=[26, None, None, None])
        p.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (0, 0), 0.7, GRIS_T),
            ('TOPPADDING', (0, 1), (0, 1), 3),
            ('TOPPADDING', (0, 3), (0, 3), 5),
            ('BOTTOMPADDING', (0, 3), (0, 3), 2),
        ]))
        caja = Table([[p]], colWidths=[8.9 * cm])
        caja.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, LINEA),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FBFCFE')),
            ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        return caja

    cont = Table([[panel('Operador que ejecuta'), '', panel('Responsable de calidad')]],
                 colWidths=[8.9 * cm, 0.7 * cm, 8.9 * cm])
    cont.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
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
    elems = _encabezado(st, f'QC-{pieza}', logo_path, emitido=fecha)
    elems += [Spacer(1, 10)]
    elems += _seccion(st, 'Trazabilidad')
    elems.append(_bloque_traza(st, [('No. de pieza', pieza), ('Batch / lote', batch),
                                    ('Fecha y hora', fecha), ('Equipo / serie', equipo),
                                    ('Operador', operador), ('Perfil de límites', perfil)]))
    elems.append(Spacer(1, 8))
    # una pieza RECHAZADA no tiene datos evaluados: sin tarjetas por prueba
    if veredicto != 'RECHAZADO':
        elems += [_resumen_pruebas(st, detalle), Spacer(1, 8)]
    elems += [_banner_veredicto(st, veredicto, _motivo_falla(detalle)), Spacer(1, 8)]
    for prueba, filas in detalle.items():
        nombre = 'Detalle — prueba óptica' if prueba == 'Optico' else 'Detalle — prueba eléctrica'
        elems += _seccion(st, nombre)
        elems.append(_tabla_detalle(st, prueba, filas))
        elems.append(Spacer(1, 6))
    elems.append(Spacer(1, 14))
    elems += _seccion(st, 'Aprobación')
    elems.append(_firmas(st))
    return elems


def generar_pdf(ruta_salida, no_pieza, batch, operador, fecha, veredicto, detalle,
                equipo='—', perfil='—', logo_path=None):
    """Reporte de UN desechable individual."""
    doc = SimpleDocTemplate(ruta_salida, pagesize=letter, topMargin=1.2 * cm,
                            bottomMargin=1.7 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    st = _styles()
    doc.build(_contenido_pieza(st, no_pieza, batch, operador, fecha, equipo, perfil,
                               veredicto, detalle, logo_path),
              canvasmaker=_lienzo(f'QC-{no_pieza}'))
    return ruta_salida


# ---------------------------------------------------------------- portada de lote
def _tarjetas_kpi(st, celdas):
    """Fila de tarjetas KPI separadas, con acento de color arriba."""
    gap = 0.25 * cm
    n = len(celdas)
    wcard = (ANCHO_UTIL - gap * (n - 1)) / n
    fila, anchos = [], []
    for i, (lbl, val, col) in enumerate(celdas):
        tarjeta = Table([[Paragraph(lbl, st['label'])],
                         [Paragraph(str(val), ParagraphStyle(
                             'kpi', parent=st['valor'], fontSize=17, leading=20,
                             textColor=col or TINTA))]],
                        colWidths=[wcard])
        tarjeta.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 2.5, col or AZUL),
            ('BOX', (0, 0), (-1, -1), 0.5, LINEA),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FBFCFE')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (0, 0), 6), ('BOTTOMPADDING', (0, 1), (0, 1), 6),
        ]))
        fila.append(tarjeta)
        anchos.append(wcard)
        if i < n - 1:
            fila.append('')
            anchos.append(gap)
    cont = Table([fila], colWidths=anchos)
    cont.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return cont


def _barra_distribucion(st, partes, total):
    """Barra apilada con la proporción de veredictos del lote + leyenda."""
    W, H = ANCHO_UTIL, 12
    d = Drawing(W, H)
    d.add(Rect(0, 2.5, W, 7, rx=2, ry=2, fillColor=PISTA, strokeColor=None))
    x = 0.0
    for count, color, _ in partes:
        if count:
            w = W * count / total
            d.add(Rect(x, 2.5, w, 7, fillColor=color, strokeColor=colors.white, strokeWidth=0.6))
            x += w
    # leyenda con chips de color
    fila, anchos = [], []
    for count, color, nombre in partes:
        chip = Table([['']], colWidths=[0.26 * cm], rowHeights=[0.26 * cm])
        chip.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), color)]))
        fila += [chip, Paragraph(f'{nombre} ({count})', st['nota'])]
        anchos += [0.4 * cm, (ANCHO_UTIL - 0.4 * cm * len(partes)) / len(partes)]
    ley = Table([fila], colWidths=anchos)
    ley.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return [d, ley]


def generar_pdf_lote(ruta_salida, batch, operador, fecha, resultados, perfil='—',
                     equipo='—', logo_path=None):
    """Reporte del LOTE completo: portada con resumen + una pagina por pieza."""
    doc = SimpleDocTemplate(ruta_salida, pagesize=letter, topMargin=1.2 * cm,
                            bottomMargin=1.7 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    st = _styles()
    elems = []

    total = len(resultados)
    pasaron = sum(1 for r in resultados if r['veredicto'] == 'PASO')
    incompletos = sum(1 for r in resultados if r['veredicto'] == 'INCOMPLETO')
    rechazados = sum(1 for r in resultados if r['veredicto'] == 'RECHAZADO')
    fallaron = total - pasaron - incompletos - rechazados
    tasa = f'{(100 * pasaron / total):.0f}%' if total else '—'

    # si el nombre del lote ya empieza con "LOTE", no duplicar el prefijo del folio
    folio = str(batch) if str(batch).upper().startswith('LOTE') else f'LOTE-{batch}'
    elems += _encabezado(st, folio, logo_path, emitido=fecha)
    elems.append(Spacer(1, 10))
    elems += _seccion(st, 'Datos del lote')
    elems.append(_bloque_traza(st, [('Batch / lote', batch), ('Operador', operador),
                                    ('Fecha', fecha), ('Perfil de límites', perfil),
                                    ('Equipo / serie', equipo), ('Piezas evaluadas', total)]))
    elems.append(Spacer(1, 10))

    elems += _seccion(st, 'Resumen del lote')
    celdas_kpi = [('Total', total, None),
                  ('Pasaron', pasaron, VERDE_T),
                  ('Fallaron', fallaron, ROJO_T),
                  ('Incompletos', incompletos, AMBAR_T)]
    if rechazados:
        celdas_kpi.append(('Rechazados', rechazados, GRIS_OSC))
    celdas_kpi.append(('Aprobación', tasa, AZUL))
    elems.append(_tarjetas_kpi(st, celdas_kpi))
    elems.append(Spacer(1, 8))
    if total:
        partes = [(pasaron, VERDE_BAR, 'Pasaron'), (fallaron, ROJO_BAR, 'Fallaron'),
                  (incompletos, AMBAR_BAR, 'Incompletos')]
        if rechazados:
            partes.append((rechazados, GRIS_BAR, 'Rechazados'))
        elems += _barra_distribucion(st, partes, total)
    elems.append(Spacer(1, 10))

    elems += _seccion(st, 'Resultado por desechable')
    data = [['Pieza', 'Archivo', 'Óptico', 'Eléctrico', 'Canales con falla', 'Veredicto final']]
    estilos = []

    def _color_estado(txt):
        if txt == 'Pasó':
            return VERDE_T
        if txt in ('Incompleto', 'Sin estándar'):
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
        n_fallas = sum(1 for fs in det.values() for x in fs if x['resultado'] == 'FALLA')
        vtxt = {'PASO': 'PASÓ', 'INCOMPLETO': 'INCOMPLETO',
                'RECHAZADO': 'RECHAZADO'}.get(r['veredicto'], 'NO PASÓ')
        data.append([str(r['pieza']),
                     Paragraph(str(r.get('archivo', '—')), st['celda']),
                     eo, ee, str(n_fallas) if det else '—', vtxt])
        if i % 2 == 0:
            estilos.append(('BACKGROUND', (0, i), (-1, i), ZEBRA))
        if r['veredicto'] == 'RECHAZADO':
            col_final, col_final_t = GRIS_BG, GRIS_OSC
        else:
            col_final = VERDE if r['veredicto'] == 'PASO' else AMBAR if r['veredicto'] == 'INCOMPLETO' else ROJO
            col_final_t = _color_estado('Pasó' if r['veredicto'] == 'PASO'
                                        else 'Incompleto' if r['veredicto'] == 'INCOMPLETO' else 'No pasó')
        estilos += [('BACKGROUND', (5, i), (5, i), col_final), ('TEXTCOLOR', (5, i), (5, i), col_final_t),
                    ('FONTNAME', (5, i), (5, i), 'Helvetica-Bold')]
        estilos += [('TEXTCOLOR', (2, i), (2, i), _color_estado(eo))]
        estilos += [('TEXTCOLOR', (3, i), (3, i), _color_estado(ee))]
        if n_fallas:
            estilos += [('TEXTCOLOR', (4, i), (4, i), ROJO_T), ('FONTNAME', (4, i), (4, i), 'Helvetica-Bold')]
    tabla = Table(data, colWidths=[2.2 * cm, 5.7 * cm, 2.4 * cm, 2.4 * cm, 2.8 * cm, 3.0 * cm],
                  repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTSIZE', (0, 0), (-1, 0), 7.5),
        ('GRID', (0, 0), (-1, -1), 0.4, LINEA), ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ] + estilos))
    elems.append(tabla)
    elems.append(Spacer(1, 14))
    elems += _seccion(st, 'Aprobación')
    elems.append(_firmas(st))

    # detalle por pieza (una pagina por desechable)
    for r in sorted(resultados, key=lambda x: str(x['pieza'])):
        elems.append(PageBreak())
        elems += _contenido_pieza(st, r['pieza'], batch, operador, fecha, equipo, perfil,
                                  r['veredicto'], r['detalle'], logo_path)

    doc.build(elems, canvasmaker=_lienzo(folio))
    return ruta_salida
