"""
db.py — Capa de datos SQLite. Estructura de 3 niveles para el historial:
  perfiles   : estandares de calidad reutilizables (por prueba)
  batches    : cada lote evaluado (resumen) -> para el historial y tendencias
  resultados : cada pieza de un lote (con su detalle por canal en JSON)
  usuarios   : login simple

Disenado para que migrar a la nube solo cambie esta capa.
"""
import sqlite3
import json
import hashlib
import os
from datetime import datetime

# Ruta ABSOLUTA junto a este archivo: asi la app siempre usa la misma base de
# datos aunque el servidor se arranque desde otro directorio de trabajo (si
# fuera relativa, se crearia una base nueva y vacia y "desapareceria" el historial).
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qc_datos.db')


def conectar(path=DB_PATH):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def _hash(p):
    return hashlib.sha256(p.encode('utf-8')).hexdigest()


def inicializar(path=DB_PATH):
    con = conectar(path)
    c = con.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        clave_hash TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS perfiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        creado TEXT,
        limites TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT, fecha TEXT, operador TEXT, perfil TEXT,
        total INTEGER, pasaron INTEGER, fallaron INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resultados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER, no_pieza TEXT, archivo TEXT, fecha TEXT,
        veredicto TEXT, detalle TEXT,
        FOREIGN KEY(batch_id) REFERENCES batches(id))''')
    # usuario por defecto: admin / 1234
    cur = con.execute('SELECT COUNT(*) AS n FROM usuarios').fetchone()
    if cur['n'] == 0:
        con.execute('INSERT INTO usuarios (usuario, clave_hash) VALUES (?,?)',
                    ('admin', _hash('1234')))
    con.commit()
    con.close()


# ---------- usuarios / login ----------
def verificar_login(usuario, clave, path=DB_PATH):
    con = conectar(path)
    row = con.execute('SELECT clave_hash FROM usuarios WHERE usuario=?', (usuario,)).fetchone()
    con.close()
    return bool(row) and row['clave_hash'] == _hash(clave)


def cambiar_clave(usuario, nueva, path=DB_PATH):
    con = conectar(path)
    con.execute('UPDATE usuarios SET clave_hash=? WHERE usuario=?', (_hash(nueva), usuario))
    con.commit()
    con.close()


# ---------- perfiles ----------
def guardar_perfil(nombre, limites, path=DB_PATH):
    con = conectar(path)
    con.execute('INSERT OR REPLACE INTO perfiles (nombre, creado, limites) VALUES (?,?,?)',
                (nombre, datetime.now().isoformat(timespec='seconds'), json.dumps(limites)))
    con.commit()
    con.close()


def listar_perfiles(path=DB_PATH):
    con = conectar(path)
    rows = con.execute('SELECT nombre, creado FROM perfiles ORDER BY nombre').fetchall()
    con.close()
    return [dict(r) for r in rows]


def cargar_perfil(nombre, path=DB_PATH):
    con = conectar(path)
    row = con.execute('SELECT limites FROM perfiles WHERE nombre=?', (nombre,)).fetchone()
    con.close()
    return json.loads(row['limites']) if row else None


def borrar_perfil(nombre, path=DB_PATH):
    con = conectar(path)
    con.execute('DELETE FROM perfiles WHERE nombre=?', (nombre,))
    con.commit()
    con.close()


# ---------- batches / resultados ----------
def crear_batch(nombre, operador, perfil, path=DB_PATH):
    con = conectar(path)
    cur = con.execute('INSERT INTO batches (nombre,fecha,operador,perfil,total,pasaron,fallaron) VALUES (?,?,?,?,0,0,0)',
                      (nombre, datetime.now().isoformat(timespec='seconds'), operador, perfil))
    bid = cur.lastrowid
    con.commit()
    con.close()
    return bid


def guardar_resultado(batch_id, no_pieza, archivo, veredicto, detalle, path=DB_PATH):
    con = conectar(path)
    con.execute('INSERT INTO resultados (batch_id,no_pieza,archivo,fecha,veredicto,detalle) VALUES (?,?,?,?,?,?)',
                (batch_id, no_pieza, archivo, datetime.now().isoformat(timespec='seconds'),
                 veredicto, json.dumps(detalle)))
    con.commit()
    con.close()


def cerrar_batch(batch_id, total, pasaron, fallaron, path=DB_PATH):
    con = conectar(path)
    con.execute('UPDATE batches SET total=?, pasaron=?, fallaron=? WHERE id=?',
                (total, pasaron, fallaron, batch_id))
    con.commit()
    con.close()


def borrar_batch(batch_id, path=DB_PATH):
    """Elimina un lote completo y todas sus piezas (irreversible)."""
    con = conectar(path)
    con.execute('DELETE FROM resultados WHERE batch_id=?', (batch_id,))
    con.execute('DELETE FROM batches WHERE id=?', (batch_id,))
    con.commit()
    con.close()


def borrar_resultado(resultado_id, path=DB_PATH):
    """Elimina una pieza suelta y recalcula el resumen (total/pasaron/fallaron)
    de su lote. Devuelve el batch_id afectado (o None si no existia)."""
    con = conectar(path)
    row = con.execute('SELECT batch_id FROM resultados WHERE id=?', (resultado_id,)).fetchone()
    if not row:
        con.close()
        return None
    bid = row['batch_id']
    con.execute('DELETE FROM resultados WHERE id=?', (resultado_id,))
    filas = con.execute('SELECT veredicto FROM resultados WHERE batch_id=?', (bid,)).fetchall()
    total = len(filas)
    pasaron = sum(1 for f in filas if f['veredicto'] == 'PASO')
    # 'fallaron' = todas las que NO pasaron (falla + incompletas + rechazadas)
    con.execute('UPDATE batches SET total=?, pasaron=?, fallaron=? WHERE id=?',
                (total, pasaron, total - pasaron, bid))
    con.commit()
    con.close()
    return bid


def listar_batches(path=DB_PATH):
    con = conectar(path)
    rows = con.execute('SELECT * FROM batches ORDER BY fecha DESC').fetchall()
    con.close()
    return [dict(r) for r in rows]


def obtener_batch(batch_id, path=DB_PATH):
    con = conectar(path)
    row = con.execute('SELECT * FROM batches WHERE id=?', (batch_id,)).fetchone()
    con.close()
    return dict(row) if row else None


def resultados_de_batch(batch_id, path=DB_PATH):
    con = conectar(path)
    rows = con.execute('SELECT * FROM resultados WHERE batch_id=? ORDER BY no_pieza', (batch_id,)).fetchall()
    con.close()
    out = []
    for r in rows:
        d = dict(r)
        d['detalle'] = json.loads(d['detalle'])
        out.append(d)
    return out


def todos_los_resultados(path=DB_PATH):
    con = conectar(path)
    rows = con.execute('''SELECT r.*, b.nombre as batch_nombre FROM resultados r
                          JOIN batches b ON r.batch_id=b.id ORDER BY r.fecha''').fetchall()
    con.close()
    out = []
    for r in rows:
        d = dict(r)
        d['detalle'] = json.loads(d['detalle'])
        out.append(d)
    return out


def alertas_abiertas(path=DB_PATH):
    """Desechables que NO pasaron (falla / incompleto / rechazado): los que hay que
    repetir. Devuelve una lista lista para el panel de alertas del operador, con el
    lote, la pieza, el veredicto y los canales que fallaron (con su fase)."""
    out = []
    for r in todos_los_resultados(path):
        v = r['veredicto']
        if v == 'PASO':
            continue
        canales = []
        for prueba, filas in r['detalle'].items():
            pr = 'Óptica' if prueba == 'Optico' else 'Eléctrica'
            for f in filas:
                res = f.get('resultado')
                if res == 'FALLA':
                    canales.append({'prueba': pr, 'canal': f.get('canal'), 'fase': f.get('fase_fallo')})
                elif res == 'SIN ESTANDAR':
                    canales.append({'prueba': pr, 'canal': f.get('canal'), 'fase': None})
        out.append({'resultado_id': r['id'], 'batch_id': r['batch_id'],
                    'lote': r['batch_nombre'], 'pieza': r['no_pieza'],
                    'veredicto': v, 'fecha': (r['fecha'] or '')[:10], 'canales': canales})
    return out


def conteo_fallas_por_canal(path=DB_PATH):
    conteo = {}
    for r in todos_los_resultados(path):
        for prueba, filas in r['detalle'].items():
            for f in filas:
                if f['resultado'] == 'FALLA':
                    clave = f"{prueba} · {f['canal']}"
                    conteo[clave] = conteo.get(clave, 0) + 1
    return conteo


def mejor_desviacion_historica(path=DB_PATH):
    """Devuelve {prueba: {canal: menor_desviacion_vista}} a traves de TODOS los
    resultados historicos.

    NOTA: actualmente NO se usa. La comparacion contra el historico se
    desactivo a la espera de la definicion exacta del consultor sobre
    "variabilidad no mayor a las anteriores" (hoy la evaluacion usa SOLO los
    limites del perfil). Se conserva para reactivarla cuando haya definicion."""
    mejor = {}
    for r in todos_los_resultados(path):
        for prueba, filas in r['detalle'].items():
            mejor.setdefault(prueba, {})
            for f in filas:
                canal = str(f['canal'])
                desv = f.get('desv')
                if desv is None:
                    continue
                if canal not in mejor[prueba] or desv < mejor[prueba][canal]:
                    mejor[prueba][canal] = desv
    return mejor
