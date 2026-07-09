"""
servidor.py — Servidor web local de la app de Control de Calidad.

Usa solo la libreria estandar de Python (http.server) + el motor ya existente,
para que no haya que instalar nada extra mas alla de openpyxl y reportlab.

Arranca un servidor local y abre el navegador en la interfaz web moderna.
"""
import json
import os
import base64
import tempfile
import threading
import webbrowser
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

import parser as qparser
import evaluador
import db
import reporte
import exportar
import drive

PUERTO = 8765
HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'index.html')


def _json(handler, obj, code=200):
    data = json.dumps(obj).encode('utf-8')
    handler.send_response(code)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _nombre_seguro(texto):
    """Quita caracteres que Windows no permite en nombres de archivo: / \\ : * ? " < > |"""
    s = str(texto)
    for c in '/\\:*?"<>|':
        s = s.replace(c, '-')
    return s.strip() or 'sin_nombre'


def _escribir_salida(ruta, generar):
    """Ejecuta generar(ruta). Si Windows niega el permiso (tipicamente porque el
    archivo esta abierto en Excel o en el visor de PDF, que lo bloquean),
    reintenta con un nombre alternativo con la hora para no perder la
    exportacion. Devuelve la ruta donde realmente se guardo."""
    try:
        generar(ruta)
        return ruta
    except PermissionError:
        base, ext = os.path.splitext(ruta)
        alt = f"{base}_{datetime.now().strftime('%H.%M.%S')}{ext}"
        generar(alt)
        return alt


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # silenciar logs

    def _leer_body(self):
        n = int(self.headers.get('Content-Length', 0))
        if n == 0:
            return {}
        return json.loads(self.rfile.read(n).decode('utf-8'))

    def _servir_estatico(self, nombre, mime):
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', nombre)
        try:
            with open(ruta, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self.send_error(404, f'{nombre} no encontrado')

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            return self._servir_estatico('index.html', 'text/html; charset=utf-8')
        if self.path == '/app.js':
            return self._servir_estatico('app.js', 'application/javascript; charset=utf-8')
        if self.path == '/api/perfiles':
            return _json(self, {'perfiles': db.listar_perfiles()})
        if self.path == '/api/batches':
            return _json(self, {'batches': db.listar_batches()})
        if self.path == '/api/fallas_canal':
            return _json(self, {'conteo': db.conteo_fallas_por_canal()})
        if self.path == '/api/alertas':
            return _json(self, {'alertas': db.alertas_abiertas()})
        if self.path == '/api/drive':
            return _json(self, {'carpeta': drive.carpeta_configurada(),
                                'detectadas': drive.detectar_carpetas()})
        if self.path.startswith('/api/batch/'):
            try:
                bid = int(self.path.rsplit('/', 1)[1])
            except ValueError:
                return _json(self, {'error': 'id de lote inválido'}, code=400)
            return _json(self, {'batch': db.obtener_batch(bid),
                                'resultados': db.resultados_de_batch(bid)})
        self.send_error(404)

    def do_POST(self):
        body = self._leer_body()
        ruta = self.path

        if ruta == '/api/login':
            ok = db.verificar_login(body.get('usuario', ''), body.get('clave', ''))
            return _json(self, {'ok': ok})

        if ruta == '/api/guardar_perfil':
            db.guardar_perfil(body['nombre'], body['limites'])
            return _json(self, {'ok': True})

        if ruta == '/api/cargar_perfil':
            return _json(self, {'limites': db.cargar_perfil(body['nombre'])})

        if ruta == '/api/borrar_perfil':
            db.borrar_perfil(body['nombre'])
            return _json(self, {'ok': True})

        if ruta == '/api/detectar_canales':
            # recibe un archivo base64, devuelve los canales detectados
            try:
                raw = base64.b64decode(body['archivo_b64'])
                nombre = body.get('nombre', '')
                sufijo = '.json' if nombre.lower().endswith('.json') else '.xlsx'
                with tempfile.NamedTemporaryFile(suffix=sufijo, delete=False) as tf:
                    tf.write(raw)
                    tmp = tf.name
                try:
                    datos = qparser.leer_archivo(tmp)
                finally:
                    os.unlink(tmp)
                pruebas = {p: [c['canal'] for c in cs] for p, cs in datos['pruebas'].items()}
                return _json(self, {'ok': True, 'pruebas': pruebas})
            except Exception as e:
                return _json(self, {'ok': False, 'error': str(e)})

        if ruta == '/api/evaluar':
            # recibe lista de archivos {nombre, pieza, b64} + perfil + datos del lote
            try:
                limites = db.cargar_perfil(body['perfil'])
                if limites is None:
                    return _json(self, {'ok': False,
                                        'error': f"El perfil \"{body['perfil']}\" no existe."})
                # La evaluacion se basa UNICAMENTE en los limites de calidad del
                # perfil, NO en el mejor historico. (Se deja de pasar mejor_hist.)
                bid = db.crear_batch(body['lote'], body['operador'], body['perfil'])
                resultados = []
                pasaron = fallaron = incompletos = rechazados = 0
                for arch in body['archivos']:
                    nombre = arch['nombre']
                    error = None
                    try:
                        raw = base64.b64decode(arch['b64'])
                        sufijo = '.json' if nombre.lower().endswith('.json') else '.xlsx'
                        with tempfile.NamedTemporaryFile(suffix=sufijo, delete=False) as tf:
                            tf.write(raw)
                            tmp = tf.name
                        try:
                            datos = qparser.leer_archivo(tmp)   # valida el formato
                        finally:
                            os.unlink(tmp)
                        ev = evaluador.evaluar_archivo(datos, limites)
                        veredicto, detalle, alerta = ev['veredicto'], ev['detalle'], ev['alerta']
                    except Exception as e:
                        # archivo que no es del formato / corrupto -> RECHAZADO (nunca 'pasa')
                        veredicto, detalle, alerta, error = 'RECHAZADO', {}, True, str(e)
                    db.guardar_resultado(bid, arch['pieza'], nombre, veredicto, detalle)
                    if veredicto == 'PASO':
                        pasaron += 1
                    elif veredicto == 'INCOMPLETO':
                        incompletos += 1
                    elif veredicto == 'RECHAZADO':
                        rechazados += 1
                    else:
                        fallaron += 1
                    resultados.append({'pieza': arch['pieza'], 'archivo': nombre,
                                       'veredicto': veredicto, 'detalle': detalle,
                                       'alerta': alerta, 'error': error})
                # en la BD 'fallaron' = piezas que NO pasaron (falla + incompletas + rechazadas),
                # para que total = pasaron + fallaron y la tasa de aprobacion sea correcta.
                db.cerrar_batch(bid, len(body['archivos']), pasaron, fallaron + incompletos + rechazados)
                return _json(self, {'ok': True, 'batch_id': bid, 'resultados': resultados,
                                    'pasaron': pasaron, 'fallaron': fallaron,
                                    'incompletos': incompletos, 'rechazados': rechazados})
            except Exception as e:
                import traceback
                return _json(self, {'ok': False, 'error': str(e), 'tb': traceback.format_exc()})

        if ruta == '/api/reporte_pieza' or ruta == '/api/reporte_lote':
            try:
                bid = body['batch_id']
                batch = db.obtener_batch(bid)
                resultados = db.resultados_de_batch(bid)
                outdir = os.path.join(os.path.expanduser('~'), 'Reportes_QC')
                os.makedirs(outdir, exist_ok=True)
                if ruta == '/api/reporte_pieza':
                    r = next(x for x in resultados if str(x['no_pieza']) == str(body['pieza']))
                    out = os.path.join(outdir, f"reporte_pieza_{_nombre_seguro(r['no_pieza'])}.pdf")
                    out = _escribir_salida(out, lambda p: reporte.generar_pdf(
                        p, r['no_pieza'], batch['nombre'], batch['operador'],
                        batch['fecha'][:16].replace('T', ' '), r['veredicto'],
                        r['detalle'], perfil=batch['perfil']))
                else:
                    out = os.path.join(outdir, f"reporte_lote_{_nombre_seguro(batch['nombre'])}.pdf")
                    res2 = [{'pieza': x['no_pieza'], 'archivo': x['archivo'],
                             'veredicto': x['veredicto'], 'detalle': x['detalle']} for x in resultados]
                    out = _escribir_salida(out, lambda p: reporte.generar_pdf_lote(
                        p, batch['nombre'], batch['operador'],
                        batch['fecha'][:16].replace('T', ' '), res2,
                        perfil=batch['perfil']))
                return _json(self, {'ok': True, 'ruta': out})
            except PermissionError:
                return _json(self, {'ok': False, 'error':
                    'Windows no permitió escribir en la carpeta Reportes_QC. '
                    'Cierra el PDF si lo tienes abierto y vuelve a intentar.'})
            except Exception as e:
                return _json(self, {'ok': False, 'error': str(e)})

        if ruta == '/api/exportar_excel':
            try:
                bid = body['batch_id']
                batch = db.obtener_batch(bid)
                resultados = db.resultados_de_batch(bid)
                outdir = os.path.join(os.path.expanduser('~'), 'Reportes_QC')
                os.makedirs(outdir, exist_ok=True)
                out = os.path.join(outdir, f"datos_lote_{_nombre_seguro(batch['nombre'])}.xlsx")
                res2 = [{'pieza': x['no_pieza'], 'archivo': x['archivo'],
                         'veredicto': x['veredicto'], 'detalle': x['detalle']} for x in resultados]
                out = _escribir_salida(out, lambda p: exportar.exportar_lote_excel(p, batch, res2))
                # copia a la carpeta del Drive (si esta configurada en Ajustes);
                # si falla, el Excel local ya quedo guardado y se avisa el motivo
                copia_drive, error_drive = drive.copiar_a_drive(out)
                return _json(self, {'ok': True, 'ruta': out,
                                    'drive_ruta': copia_drive, 'drive_error': error_drive})
            except PermissionError:
                return _json(self, {'ok': False, 'error':
                    'Windows no permitió escribir en la carpeta Reportes_QC. '
                    'Cierra el Excel si lo tienes abierto y vuelve a intentar.'})
            except Exception as e:
                import traceback
                return _json(self, {'ok': False, 'error': str(e), 'tb': traceback.format_exc()})

        if ruta == '/api/borrar_batch':
            db.borrar_batch(body['batch_id'])
            return _json(self, {'ok': True})

        if ruta == '/api/borrar_pieza':
            bid = db.borrar_resultado(body['resultado_id'])
            return _json(self, {'ok': True, 'batch_id': bid})

        if ruta == '/api/drive':
            try:
                carpeta = drive.configurar_carpeta(body.get('carpeta', ''))
                return _json(self, {'ok': True, 'carpeta': carpeta})
            except Exception as e:
                return _json(self, {'ok': False,
                                    'error': f'No se pudo usar esa carpeta: {e}'})

        if ruta == '/api/cambiar_clave':
            db.cambiar_clave(body.get('usuario', 'admin'), body['nueva'])
            return _json(self, {'ok': True})

        self.send_error(404)


def main():
    db.inicializar()
    servidor = HTTPServer(('127.0.0.1', PUERTO), Handler)
    url = f'http://127.0.0.1:{PUERTO}/'
    print(f'Servidor de Control de Calidad corriendo en {url}')
    print('Cierra esta ventana para apagar la app.')
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        servidor.shutdown()


if __name__ == '__main__':
    main()
