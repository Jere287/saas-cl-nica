"""
test_evaluador.py — Verifica la LÓGICA de evaluación en dos fases.

IMPORTANTE: los límites usados aquí son FIXTURES SINTÉTICOS para probar la
lógica (orden de fases, veredictos, casos borde). NO son límites de calidad
reales — esos los define el consultor y viven en los perfiles de la app.

Correr:  py -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import evaluador  # noqa: E402


def _stats(media, desv, rango=1.0, n=20):
    return {'media': media, 'desv': desv, 'rango': rango, 'n': n}


# Fixture sintético: un canal con desv permitida [0.5, 2.0] y media [10, 20].
LIM = {'desv_min': 0.5, 'desv_max': 2.0, 'media_min': 10.0, 'media_max': 20.0}


class TestEvaluarCanal(unittest.TestCase):
    def test_pasa_ambas_fases(self):
        r = evaluador.evaluar_canal(_stats(media=15, desv=1.0), LIM)
        self.assertEqual(r['resultado'], 'PASA')
        self.assertIsNone(r['fase_fallo'])

    def test_fase1_desviacion_alta(self):
        r = evaluador.evaluar_canal(_stats(media=15, desv=5.0), LIM)
        self.assertEqual(r['resultado'], 'FALLA')
        self.assertEqual(r['fase_fallo'], 1)

    def test_fase1_desviacion_baja(self):
        r = evaluador.evaluar_canal(_stats(media=15, desv=0.1), LIM)
        self.assertEqual(r['resultado'], 'FALLA')
        self.assertEqual(r['fase_fallo'], 1)

    def test_fase2_media_fuera(self):
        r = evaluador.evaluar_canal(_stats(media=50, desv=1.0), LIM)
        self.assertEqual(r['resultado'], 'FALLA')
        self.assertEqual(r['fase_fallo'], 2)

    def test_orden_de_fases(self):
        # Si la fase 1 falla, la fase 2 NO se evalúa aunque la media también
        # esté fuera: el fallo debe reportarse como fase 1.
        r = evaluador.evaluar_canal(_stats(media=50, desv=5.0), LIM)
        self.assertEqual(r['fase_fallo'], 1)
        self.assertTrue(all('desviacion' in m for m in r['motivos']))

    def test_limite_parcial_no_evalua_criterio_vacio(self):
        # Campo en None = ese criterio no se evalúa (así funcionan los perfiles).
        solo_media = {'desv_min': None, 'desv_max': None,
                      'media_min': 10.0, 'media_max': 20.0}
        r = evaluador.evaluar_canal(_stats(media=15, desv=999), solo_media)
        self.assertEqual(r['resultado'], 'PASA')

    def test_sin_estandar(self):
        r = evaluador.evaluar_canal(_stats(media=15, desv=1.0), None)
        self.assertEqual(r['resultado'], 'SIN ESTANDAR')

    def test_redondeo_a_2_decimales(self):
        # La comparación se hace con valores redondeados a 2 decimales
        # (DECIMALES=2): 2.004 se redondea a 2.00 y pasa con máx 2.0.
        r = evaluador.evaluar_canal(_stats(media=15, desv=2.004), LIM)
        self.assertEqual(r['resultado'], 'PASA')

    def test_historico_inactivo_por_defecto(self):
        # Sin 'mejor_desv_hist' (como llama hoy el servidor) el histórico no
        # interviene. PENDIENTE consultor: definición exacta de la regla.
        r = evaluador.evaluar_canal(_stats(media=15, desv=1.9), LIM)
        self.assertEqual(r['resultado'], 'PASA')


class TestEvaluarArchivo(unittest.TestCase):
    def _datos(self, canales):
        return {'pruebas': {'Optico': canales}}

    def test_todos_pasan(self):
        datos = self._datos([{'canal': 'A', **_stats(15, 1.0)}])
        ev = evaluador.evaluar_archivo(datos, {'Optico': {'A': LIM}})
        self.assertEqual(ev['veredicto'], 'PASO')
        self.assertFalse(ev['alerta'])

    def test_una_falla_manda(self):
        datos = self._datos([{'canal': 'A', **_stats(15, 1.0)},
                             {'canal': 'B', **_stats(50, 1.0)}])
        ev = evaluador.evaluar_archivo(datos, {'Optico': {'A': LIM, 'B': LIM}})
        self.assertEqual(ev['veredicto'], 'NO PASO')
        self.assertTrue(ev['alerta'])

    def test_canal_sin_estandar_es_incompleto(self):
        # Dispositivo médico: nunca aprobar lo que no se comparó contra un límite.
        datos = self._datos([{'canal': 'A', **_stats(15, 1.0)},
                             {'canal': 'B', **_stats(15, 1.0)}])
        ev = evaluador.evaluar_archivo(datos, {'Optico': {'A': LIM}})  # B sin límite
        self.assertEqual(ev['veredicto'], 'INCOMPLETO')
        self.assertTrue(ev['alerta'])

    def test_sin_canales_es_incompleto(self):
        ev = evaluador.evaluar_archivo({'pruebas': {}}, {})
        self.assertEqual(ev['veredicto'], 'INCOMPLETO')

    def test_falla_tiene_prioridad_sobre_sin_estandar(self):
        datos = self._datos([{'canal': 'A', **_stats(50, 1.0)},
                             {'canal': 'B', **_stats(15, 1.0)}])
        ev = evaluador.evaluar_archivo(datos, {'Optico': {'A': LIM}})
        self.assertEqual(ev['veredicto'], 'NO PASO')


if __name__ == '__main__':
    unittest.main()
