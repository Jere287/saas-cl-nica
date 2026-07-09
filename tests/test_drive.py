"""
test_drive.py — Copia automática de las exportaciones a la carpeta del Drive.

La app no usa internet: "guardar en Drive" = copiar el Excel a la carpeta que
el programa de escritorio (Google Drive / OneDrive / Dropbox) sincroniza.
Reglas que se verifican:
  - sin carpeta configurada no se copia nada (y no falla),
  - la copia crea las subcarpetas que falten,
  - si la copia anterior está bloqueada (abierta en Excel) se usa otro nombre,
  - un fallo se informa como texto y NUNCA rompe la exportación local.

Correr:  py -m unittest discover -s tests -v
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db     # noqa: E402
import drive  # noqa: E402


def _crear_origen(carpeta, nombre='datos_lote_8.xlsx', contenido='contenido'):
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, 'w') as f:
        f.write(contenido)
    return ruta


class TestCopiarADrive(unittest.TestCase):
    def test_sin_carpeta_configurada_no_copia_ni_falla(self):
        with tempfile.TemporaryDirectory() as d:
            origen = _crear_origen(d)
            copia, error = drive.copiar_a_drive(origen, carpeta='')
            self.assertIsNone(copia)
            self.assertIsNone(error)

    def test_copia_y_crea_subcarpetas_que_faltan(self):
        with tempfile.TemporaryDirectory() as d:
            origen = _crear_origen(d)
            destino_dir = os.path.join(d, 'MiDrive', 'Reportes_QC')  # aún no existe
            copia, error = drive.copiar_a_drive(origen, carpeta=destino_dir)
            self.assertIsNone(error)
            self.assertEqual(copia, os.path.join(destino_dir, 'datos_lote_8.xlsx'))
            with open(copia) as f:
                self.assertEqual(f.read(), 'contenido')

    def test_si_el_destino_esta_bloqueado_copia_con_otro_nombre(self):
        # Simula el caso real de Windows: la copia anterior está abierta en
        # Excel y sobreescribirla lanza PermissionError (Errno 13).
        with tempfile.TemporaryDirectory() as d:
            origen = _crear_origen(d)
            destino_dir = os.path.join(d, 'MiDrive')
            intentos = []
            copy2_real = drive.shutil.copy2

            def copy2_bloqueado(src, dst):
                intentos.append(dst)
                if len(intentos) == 1:
                    raise PermissionError(13, 'Permission denied', dst)
                return copy2_real(src, dst)

            drive.shutil.copy2 = copy2_bloqueado
            try:
                copia, error = drive.copiar_a_drive(origen, carpeta=destino_dir)
            finally:
                drive.shutil.copy2 = copy2_real
            self.assertIsNone(error)
            self.assertEqual(len(intentos), 2)
            self.assertNotEqual(copia, os.path.join(destino_dir, 'datos_lote_8.xlsx'))
            self.assertTrue(copia.endswith('.xlsx'))  # conserva la extensión
            self.assertTrue(os.path.basename(copia).startswith('datos_lote_8_'))
            self.assertTrue(os.path.exists(copia))

    def test_fallo_devuelve_mensaje_y_no_lanza(self):
        with tempfile.TemporaryDirectory() as d:
            origen_inexistente = os.path.join(d, 'no_existe.xlsx')
            copia, error = drive.copiar_a_drive(origen_inexistente, carpeta=d)
            self.assertIsNone(copia)
            self.assertIn('No se pudo copiar', error)


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
