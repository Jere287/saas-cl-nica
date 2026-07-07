"""
test_parser.py — Verifica que el parser calcula media / desviación estándar /
rango EXACTAMENTE igual que el cálculo manual del área de calidad.

Caso de referencia ("golden file"): una corrida REAL del equipo
(SN 13, 2026-03-19) en tests/datos/. Los valores esperados vienen de la hoja
de cálculos manuales del área de calidad (calculos_manuales.xlsx) para esa
misma corrida — son datos medidos, NO límites de calidad.

Correr:  py -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import parser as qparser  # noqa: E402

DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'datos')
JSON_REAL = os.path.join(DATOS, 'eq1_sn13_corrida_2026-03-19.json')

# Valores de la hoja manual (promedio, desviación estándar muestral, rango),
# redondeados a 3 decimales tal como aparecen en la hoja.
ESPERADO_OPTICO = {
    '415':   (40.5,      4.829,    14),
    '445':   (135.8,     12.45,    38),
    '480':   (155.75,    14.811,   44),
    '515':   (161.65,    16.891,   51),
    '555':   (484.95,    53.758,   164),
    '590':   (755.95,    89.024,   268),
    '630':   (714.65,    91.397,   272),
    '680':   (315.5,     44.09,    128),
    'CLEAR': (1133.6,    135.591,  421),
    '>700':  (12917.15,  3276.978, 8654),
}
ESPERADO_ELECTRICO = {
    '2000Hz': (2034182.776, 242122.490, 1290474.211),
    '3000Hz': (938009.488,  45295.483,  187636.330),
    '4000Hz': (500909.499,  228445.013, 1341438.090),
    '5000Hz': (624038.747,  26160.646,  102656.444),
}
TOLERANCIA = 0.01  # la hoja manual redondea a 3 decimales


class TestParserCorridaReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datos = qparser.leer_archivo(JSON_REAL)

    def test_cabecera(self):
        cab = self.datos['cabecera']
        self.assertEqual(cab['Equipment number'], '13')
        self.assertEqual(cab['MAC'], '00:1E:C0:3B:F5:9D')

    def test_estructura_canales(self):
        opt = self.datos['pruebas']['Optico']
        ele = self.datos['pruebas']['Electrico']
        self.assertEqual([c['canal'] for c in opt], list(ESPERADO_OPTICO.keys()))
        self.assertEqual([c['canal'] for c in ele], list(ESPERADO_ELECTRICO.keys()))

    def test_n_mediciones(self):
        # Óptico: 20 mediciones por canal. Eléctrico: 60 (3 electrodos x 20),
        # agrupando POR FRECUENCIA igual que el cálculo manual.
        for c in self.datos['pruebas']['Optico']:
            self.assertEqual(c['n'], 20, c['canal'])
        for c in self.datos['pruebas']['Electrico']:
            self.assertEqual(c['n'], 60, c['canal'])

    def _comparar(self, prueba, esperado):
        for c in self.datos['pruebas'][prueba]:
            media, desv, rango = esperado[c['canal']]
            self.assertAlmostEqual(c['media'], media, delta=TOLERANCIA,
                                   msg=f"{prueba} {c['canal']}: media")
            self.assertAlmostEqual(c['desv'], desv, delta=TOLERANCIA,
                                   msg=f"{prueba} {c['canal']}: desviación")
            self.assertAlmostEqual(c['rango'], rango, delta=TOLERANCIA,
                                   msg=f"{prueba} {c['canal']}: rango")

    def test_optico_coincide_con_calculo_manual(self):
        self._comparar('Optico', ESPERADO_OPTICO)

    def test_electrico_coincide_con_calculo_manual(self):
        self._comparar('Electrico', ESPERADO_ELECTRICO)


class TestValidacionFormato(unittest.TestCase):
    def test_archivo_no_valido_es_rechazado(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                         delete=False) as tf:
            tf.write('esto no es un JSON del equipo')
            ruta = tf.name
        try:
            with self.assertRaises(qparser.FormatoInvalido):
                qparser.leer_archivo(ruta)
        finally:
            os.unlink(ruta)

    def test_json_sin_secciones_es_rechazado(self):
        import json
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                         delete=False) as tf:
            json.dump({'exam': {'SN': '13'}}, tf)   # sin OPT ni IMP
            ruta = tf.name
        try:
            with self.assertRaises(qparser.FormatoInvalido):
                qparser.leer_archivo(ruta)
        finally:
            os.unlink(ruta)


if __name__ == '__main__':
    unittest.main()
