# legacy/

Código anterior que ya no forma parte de la app actual. Se conserva solo como
referencia histórica; **no está mantenido** y no debe usarse en producción.

- `app.py` — la app de escritorio original (Tkinter) que leía carpetas de
  Excel. Usa un esquema de límites viejo (solo `desv_max`, sin `desv_min`) y no
  conoce los veredictos INCOMPLETO/RECHAZADO. Fue reemplazada por la app web
  (`servidor.py` + `web/`).
