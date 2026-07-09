"""
drive.py — Carpeta de un Drive como destino de los Excel exportados.

La app es 100% local (no usa internet), así que NO llama a ninguna API en la
nube: guarda el Excel directamente en la carpeta que el programa de
escritorio del Drive (Google Drive para escritorio, OneDrive o Dropbox)
mantiene sincronizada en esta computadora. Ese programa es el que sube el
archivo a la nube, no la app.

La carpeta destino se elige una vez en la sección "Ajustes" y queda guardada
en la base de datos (tabla config). Si no hay carpeta configurada (o no está
disponible), la exportación cae a la carpeta local Reportes_QC como siempre.
"""
import os
import string

import db

CLAVE_CONFIG = 'carpeta_drive'


def carpeta_configurada():
    """Devuelve la carpeta destino configurada, o '' si no hay ninguna."""
    return db.obtener_config(CLAVE_CONFIG) or ''


def configurar_carpeta(ruta):
    """Guarda la carpeta destino ('' = desactivar la copia). Si no existe la
    crea (p. ej. una subcarpeta nueva dentro del Drive), para que el error
    salga aquí al configurar y no después al exportar. Devuelve la ruta
    normalizada tal como quedó guardada."""
    ruta = str(ruta or '').strip()
    if ruta:
        ruta = os.path.abspath(os.path.expanduser(ruta))
        os.makedirs(ruta, exist_ok=True)
    db.guardar_config(CLAVE_CONFIG, ruta)
    return ruta


def detectar_carpetas():
    """Busca en esta computadora las carpetas sincronizadas más comunes
    (Google Drive para escritorio, OneDrive y Dropbox) para ofrecerlas en
    Ajustes. Devuelve [{'nombre': ..., 'ruta': ...}] solo con las que existen."""
    home = os.path.expanduser('~')
    candidatas = []
    # Google Drive para escritorio monta una unidad (G:\ por defecto, pero
    # puede ser otra letra) con "Mi unidad" / "My Drive"; instalaciones
    # viejas sincronizaban en una carpeta "Google Drive" del usuario.
    for letra in string.ascii_uppercase[3:]:  # D: a Z:
        for raiz in ('Mi unidad', 'My Drive'):
            candidatas.append(('Google Drive', f'{letra}:\\{raiz}'))
    candidatas += [('Google Drive', os.path.join(home, 'Google Drive')),
                   ('Google Drive', os.path.join(home, 'GoogleDrive'))]
    # OneDrive: Windows publica su ruta en variables de entorno.
    for var in ('OneDrive', 'OneDriveCommercial', 'OneDriveConsumer'):
        if os.environ.get(var):
            candidatas.append(('OneDrive', os.environ[var]))
    candidatas.append(('OneDrive', os.path.join(home, 'OneDrive')))
    candidatas.append(('Dropbox', os.path.join(home, 'Dropbox')))

    vistas, out = set(), []
    for nombre, ruta in candidatas:
        if os.path.isdir(ruta):
            clave = os.path.normcase(os.path.abspath(ruta))
            if clave not in vistas:
                vistas.add(clave)
                out.append({'nombre': nombre, 'ruta': os.path.abspath(ruta)})
    return out
