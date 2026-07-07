"""
evaluador.py — Evaluacion en DOS FASES segun el consultor.

Por cada canal (cada uno tiene su propio estandar, definido por el consultor):

  FASE 1 — Desviacion estandar (se evalua primero):
    a) la desviacion calculada debe estar dentro del rango [desv_min, desv_max]
       que da el consultor.
    b) ademas, la variabilidad NO puede ser mayor que el mejor (menor) historico
       registrado para ese canal. Es decir: desv_actual <= mejor_desv_historica.
    Si falla la fase 1 -> el canal NO pasa y se ALERTA (repetir prueba).

  FASE 2 — Promedio (solo si paso la fase 1):
    el promedio debe estar dentro del rango [media_min, media_max] del consultor.
    Si falla -> el canal NO pasa y se ALERTA.

  Si pasa ambas fases -> el canal paso.
  El desechable pasa si TODOS sus canales pasan ambas pruebas.

Formato del estandar (perfil), por canal:
  limites = {
    'Optico':    { 'Canal 1': {'desv_min':_, 'desv_max':_, 'media_min':_, 'media_max':_}, ... },
    'Electrico': { '2000Hz': {...}, ... },
  }

'mejor_historico' es un dict {prueba: {canal: menor_desv_vista}} que viene de la BD.
"""

DECIMALES = 2


def _r(x):
    return round(float(x), DECIMALES)


def evaluar_canal(stats, estandar, mejor_desv_hist=None):
    """Devuelve resultado del canal con el detalle de cada fase."""
    if not estandar:
        return {'resultado': 'SIN ESTANDAR', 'motivos': [], 'fase_fallo': None}

    motivos = []
    fase_fallo = None
    desv = _r(stats['desv'])
    media = _r(stats['media'])

    # ---- FASE 1: desviacion ----
    dmin = estandar.get('desv_min')
    dmax = estandar.get('desv_max')
    fase1_ok = True
    if dmin is not None and desv < _r(dmin):
        motivos.append('desviacion por debajo del rango'); fase1_ok = False
    if dmax is not None and desv > _r(dmax):
        motivos.append('desviacion por encima del rango'); fase1_ok = False
    # comparacion contra el mejor historico (variabilidad no mayor a la anterior)
    if mejor_desv_hist is not None and desv > _r(mejor_desv_hist):
        motivos.append(f'variabilidad mayor al mejor histórico ({_r(mejor_desv_hist)})')
        fase1_ok = False

    if not fase1_ok:
        return {'resultado': 'FALLA', 'motivos': motivos, 'fase_fallo': 1}

    # ---- FASE 2: promedio (solo si paso fase 1) ----
    mmin = estandar.get('media_min')
    mmax = estandar.get('media_max')
    fase2_ok = True
    if mmin is not None and media < _r(mmin):
        motivos.append('promedio por debajo del rango'); fase2_ok = False
    if mmax is not None and media > _r(mmax):
        motivos.append('promedio por encima del rango'); fase2_ok = False

    if not fase2_ok:
        return {'resultado': 'FALLA', 'motivos': motivos, 'fase_fallo': 2}

    return {'resultado': 'PASA', 'motivos': [], 'fase_fallo': None}


def evaluar_archivo(datos, limites, mejor_historico=None):
    """
    limites: {prueba: {canal: {desv_min,desv_max,media_min,media_max}}}
    mejor_historico: {prueba: {canal: menor_desv_historica}} o None
    """
    mejor_historico = mejor_historico or {}
    detalle = {}
    hay_falla = False
    hay_sin_estandar = False
    for prueba, canales in datos['pruebas'].items():
        lim_prueba = limites.get(prueba, {})
        hist_prueba = mejor_historico.get(prueba, {})
        filas = []
        for ch in canales:
            est = lim_prueba.get(str(ch['canal']))
            mejor = hist_prueba.get(str(ch['canal']))
            ev = evaluar_canal(ch, est, mejor)
            if ev['resultado'] == 'FALLA':
                hay_falla = True
            elif ev['resultado'] == 'SIN ESTANDAR':
                hay_sin_estandar = True
            filas.append({'canal': ch['canal'], 'media': ch['media'], 'desv': ch['desv'],
                          'rango': ch['rango'], 'n': ch.get('n', 20), 'resultado': ev['resultado'],
                          'motivos': ev['motivos'], 'fase_fallo': ev['fase_fallo'],
                          'estandar': est, 'mejor_hist': mejor})
        detalle[prueba] = filas
    # Si no se evaluó NINGÚN canal, el archivo no traía datos válidos: nunca 'PASO'.
    total_canales = sum(len(filas) for filas in detalle.values())
    # Prioridad: una falla real manda (NO PASO). Si no hubo falla pero quedaron
    # canales sin estandar, NO se puede afirmar que paso -> INCOMPLETO (dispositivo
    # medico: nunca aprobar algo que no se comparo contra un limite).
    if total_canales == 0:
        veredicto = 'INCOMPLETO'
    elif hay_falla:
        veredicto = 'NO PASO'
    elif hay_sin_estandar:
        veredicto = 'INCOMPLETO'
    else:
        veredicto = 'PASO'
    alerta = hay_falla or hay_sin_estandar
    return {'veredicto': veredicto, 'detalle': detalle, 'alerta': alerta,
            'sin_estandar': hay_sin_estandar}
