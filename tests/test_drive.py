"""
test_drive.py — Los Excel exportados se guardan directo en la carpeta del Drive.

La app no usa internet: "guardar en Drive" = escribir el Excel en la carpeta
que el programa de escritorio (OneDrive / Google Drive / Dropbox) sincroniza.
Reglas que se verifican sobre _carpeta_exportacion (la decisión de destino):
  - sin carpeta configurada -> carpeta local Reportes_QC (como siempre),
  - con carpeta configurada -> esa carpeta (creándola si falta),
  - carpeta configurada NO disponible -> cae a Reportes_QC y avisa el motivo
    (la exportación nunca se pierde por culpa del Drive).

Correr:  py -m unittest discover -s tests -v
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db        # noqa: E402
import drive     # noqa: E402
import servidor  # noqa: E402


class TestCarpetaExportacion(unittest.TestCase):
    """Prueba la decisión de destino con HOME y configuración controlados."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        # expanduser('~') lee HOME en Linux/Mac y USERPROFILE en Windows:
        # se apuntan las dos al directorio temporal para que Reportes_QC caiga ahí
        self._env_real = {v: os.environ.get(v) for v in ('HOME', 'USERPROFILE')}
        os.environ['HOME'] = os.environ['USERPROFILE'] = self._tmp.name
        self._config_real = drive.carpeta_configurada

    def tearDown(self):
        drive.carpeta_configurada = self._config_real
        for var, valor in self._env_real.items():
            if valor is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = valor
        self._tmp.cleanup()

    def _configurar(self, carpeta):
        # servidor importa el mismo objeto módulo, así que basta parchear aquí
        drive.carpeta_configurada = lambda: carpeta

    def test_sin_carpeta_configurada_usa_reportes_qc(self):
        self._configurar('')
        carpeta, en_drive, aviso = servidor._carpeta_exportacion()
        self.assertEqual(carpeta, os.path.join(self._tmp.name, 'Reportes_QC'))
        self.assertFalse(en_drive)
        self.assertIsNone(aviso)
        self.assertTrue(os.path.isdir(carpeta))

    def test_con_carpeta_configurada_guarda_directo_en_el_drive(self):
        destino = os.path.join(self._tmp.name, 'OneDrive', 'Reportes_QC')  # aún no existe
        self._configurar(destino)
        carpeta, en_drive, aviso = servidor._carpeta_exportacion()
        self.assertEqual(carpeta, destino)
        self.assertTrue(en_drive)
        self.assertIsNone(aviso)
        self.assertTrue(os.path.isdir(destino))   # la crea si falta

    def test_carpeta_no_disponible_cae_a_reportes_qc_y_avisa(self):
        # una ruta imposible (dentro de un archivo) simula la unidad del
        # Drive desconectada: el Excel debe salir igual, en la carpeta local
        archivo = os.path.join(self._tmp.name, 'no_soy_carpeta')
        open(archivo, 'w').close()
        self._configurar(os.path.join(archivo, 'sub'))
        carpeta, en_drive, aviso = servidor._carpeta_exportacion()
        self.assertEqual(carpeta, os.path.join(self._tmp.name, 'Reportes_QC'))
        self.assertFalse(en_drive)
        self.assertIn('No se pudo usar la carpeta del Drive', aviso)
        self.assertTrue(os.path.isdir(carpeta))


class TestConfigDrive(unittest.TestCase):
    def test_guardar_y_leer_la_carpeta_en_la_base(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'qc.db')
            db.inicializar(path)
            self.assertIsNone(db.obtener_config(drive.CLAVE_CONFIG, path))
            db.guardar_config(drive.CLAVE_CONFIG, 'G:\\Mi unidad\\Reportes_QC', path)
            self.assertEqual(db.obtener_config(drive.CLAVE_CONFIG, path),
                             'G:\\Mi unidad\\Reportes_QC')
            # sobreescribir ('' = desactivar) debe reemplazar, no duplicar
            db.guardar_config(drive.CLAVE_CONFIG, '', path)
            self.assertEqual(db.obtener_config(drive.CLAVE_CONFIG, path), '')

    def test_detectar_carpetas_devuelve_solo_las_que_existen(self):
        # No se puede asumir qué Drives hay en la máquina de prueba; solo se
        # exige que lo devuelto exista de verdad y tenga el formato esperado.
        for c in drive.detectar_carpetas():
            self.assertIn(c['nombre'], ('Google Drive', 'OneDrive', 'Dropbox'))
            self.assertTrue(os.path.isdir(c['ruta']))


if __name__ == '__main__':
    unittest.main()
