"""
drive.py — Copia automática de las exportaciones a la carpeta de un Drive.

La app es 100% local (no usa internet), así que NO llama a ninguna API en la
nube: guarda una copia del archivo en la carpeta que el programa de
escritorio del Drive (Google Drive para escritorio, OneDrive o Dropbox)
mantiene sincronizada en esta computadora. Ese programa es el que sube el
archivo a la nube, no la app.

La carpeta destino se elige una vez en la sección "Ajustes" y queda guardada
en la base de datos (tabla config). Si no hay carpeta configurada, no se
copia nada y la exportación funciona igual que siempre.
"""
import os
import shutil
import string
from datetime import datetime

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


def copiar_a_drive(ruta_archivo, carpeta=None):
    """Copia el archivo exportado a la carpeta del Drive.

    Devuelve (ruta_copia, None) si se copió, (None, None) si no hay carpeta
    configurada, o (None, mensaje_de_error) si falló. Nunca lanza: el archivo
    local ya quedó guardado y la exportación no debe fallar por el Drive."""
    if carpeta is None:
        carpeta = carpeta_configurada()
    if not carpeta:
        return None, None
    try:
        os.makedirs(carpeta, exist_ok=True)
        destino = os.path.join(carpeta, os.path.basename(ruta_archivo))
        try:
            shutil.copy2(ruta_archivo, destino)
        except PermissionError:
            # la copia anterior está abierta en Excel (bloqueada): otro nombre
            base, ext = os.path.splitext(destino)
            destino = f"{base}_{datetime.now().strftime('%H.%M.%S')}{ext}"
            shutil.copy2(ruta_archivo, destino)
        return destino, None
    except Exception as e:
        return None, f'No se pudo copiar a la carpeta del Drive ({carpeta}): {e}'
