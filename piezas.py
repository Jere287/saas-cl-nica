"""
piezas.py — Extrae el numero de pieza/desechable a partir del nombre del archivo,
para que el operador solo tenga que nombrar sus Excels con el numero correcto.
"""
import re


def extraer_numero(nombre_archivo):
    """Devuelve el ultimo grupo de digitos encontrado en el nombre (sin extension),
    o None si el nombre no contiene ningun numero."""
    base = nombre_archivo.rsplit('.', 1)[0]
    matches = re.findall(r'\d+', base)
    return matches[-1] if matches else None
