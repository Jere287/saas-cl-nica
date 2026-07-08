"""
test_servidor.py — Utilidades del servidor web local.

Cubre _escribir_salida: en Windows, un Excel/PDF abierto bloquea el archivo y
sobreescribirlo lanza PermissionError (Errno 13). La app no debe fallar:
reintenta con un nombre alternativo con la hora.

Correr:  py -m unittest discover -s tests -v
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import servidor  # noqa: E402


class TestEscribirSalida(unittest.TestCase):
    def test_guarda_normal_si_no_hay_bloqueo(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = os.path.join(d, 'datos_lote_8.xlsx')
            out = servidor._escribir_salida(ruta, lambda p: open(p, 'w').close())
            self.assertEqual(out, ruta)
            self.assertTrue(os.path.exists(out))

    def test_reintenta_con_otro_nombre_si_esta_bloqueado(self):
        # Simula el caso real: el primer intento falla con Errno 13 porque el
        # archivo está abierto en Excel; el reintento debe usar otro nombre.
        with tempfile.TemporaryDirectory() as d:
            ruta = os.path.join(d, 'datos_lote_8.xlsx')
            intentos = []

            def generar(p):
                intentos.append(p)
                if len(intentos) == 1:
                    raise PermissionError(13, 'Permission denied', p)
                open(p, 'w').close()

            out = servidor._escribir_salida(ruta, generar)
            self.assertEqual(len(intentos), 2)
            self.assertNotEqual(out, ruta)          # nombre alternativo
            self.assertTrue(out.endswith('.xlsx'))  # conserva la extensión
            self.assertTrue(os.path.basename(out).startswith('datos_lote_8_'))
            self.assertTrue(os.path.exists(out))

    def test_nombre_seguro_quita_caracteres_de_windows(self):
        self.assertEqual(servidor._nombre_seguro('Lote 8/2026: *final*'),
                         'Lote 8-2026- -final-')
        self.assertEqual(servidor._nombre_seguro(''), 'sin_nombre')


if __name__ == '__main__':
    unittest.main()
