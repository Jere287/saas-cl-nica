"""
app.py — Aplicación de escritorio de control de calidad.

Une todo el flujo:
  1. Configurar límites (con perfiles reutilizables)
  2. Procesar una carpeta de Excels — el número de pieza se toma del NOMBRE
     del archivo (editable antes de evaluar)
  3. Ver resultados y generar reportes PDF (individuales y resumen de batch)
  4. Dashboard con gráficas, agrupable por día / mes / año

Requisitos: Python 3.9+, openpyxl, reportlab, matplotlib. (Tkinter viene con Python.)
Ejecutar:  python app.py
"""
import os
import glob
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from collections import defaultdict

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import parser as qparser
import evaluador
import db
import reporte
import piezas

DEFAULT_OPT = [f'Canal {i}' for i in range(1, 11)]
CAMPOS_LIMITE = ['media_min', 'media_max', 'desv_max']


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Control de Calidad — Dispositivo médico')
        self.geometry('1080x720')
        db.inicializar()
        self.entries = {}
        self._ultimo_batch = None
        self._ultimos_resultados = []
        self._build()

    def _build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True)
        self.tab_lim = ttk.Frame(nb); nb.add(self.tab_lim, text='1 · Límites de calidad')
        self.tab_proc = ttk.Frame(nb); nb.add(self.tab_proc, text='2 · Procesar corrida')
        self.tab_dash = ttk.Frame(nb); nb.add(self.tab_dash, text='3 · Dashboard')
        self._build_limites()
        self._build_procesar()
        self._build_dashboard()

    # ============ TAB 1: LÍMITES + PERFILES ============
    def _build_limites(self):
        top = ttk.Frame(self.tab_lim); top.pack(fill='x', padx=10, pady=8)
        ttk.Label(top, text='Perfil:').pack(side='left')
        self.cb_perfil = ttk.Combobox(top, width=30, state='readonly')
        self.cb_perfil.pack(side='left', padx=5)
        ttk.Button(top, text='Cargar', command=self._cargar_perfil).pack(side='left', padx=2)
        ttk.Button(top, text='Eliminar', command=self._borrar_perfil).pack(side='left', padx=2)
        ttk.Button(top, text='Autocompletar canales desde un Excel',
                   command=self._autocompletar).pack(side='left', padx=12)
        self._refrescar_perfiles()

        info = ttk.Label(self.tab_lim, foreground='#555',
                         text='Llena los límites de cada canal. Deja vacío un campo para no evaluar ese criterio. '
                              'Luego guarda como perfil para reutilizarlo en futuras corridas.')
        info.pack(fill='x', padx=10)

        cont = ttk.Frame(self.tab_lim); cont.pack(fill='both', expand=True, padx=10, pady=6)
        canvas = tk.Canvas(cont, highlightthickness=0)
        sb = ttk.Scrollbar(cont, orient='vertical', command=canvas.yview)
        self.frame_tabla = ttk.Frame(canvas)
        self.frame_tabla.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self.frame_tabla, anchor='nw')
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side='left', fill='both', expand=True); sb.pack(side='right', fill='y')

        bot = ttk.Frame(self.tab_lim); bot.pack(fill='x', padx=10, pady=8)
        ttk.Label(bot, text='Guardar como perfil:').pack(side='left')
        self.ent_nombre_perfil = ttk.Entry(bot, width=30); self.ent_nombre_perfil.pack(side='left', padx=5)
        ttk.Button(bot, text='Guardar perfil', command=self._guardar_perfil).pack(side='left', padx=2)

        self._construir_tabla({'Optico': DEFAULT_OPT})

    def _construir_tabla(self, pruebas_canales):
        for w in self.frame_tabla.winfo_children():
            w.destroy()
        self.entries = {}
        fila = 0
        for prueba, canales in pruebas_canales.items():
            ttk.Label(self.frame_tabla, text=f'Prueba: {prueba}',
                      font=('Arial', 11, 'bold')).grid(row=fila, column=0, sticky='w', pady=(8, 2), columnspan=5)
            fila += 1
            encabezados = ['Canal', 'Media mín', 'Media máx', 'Desv. máx']
            for j, h in enumerate(encabezados):
                ttk.Label(self.frame_tabla, text=h, font=('Arial', 9, 'bold')).grid(row=fila, column=j, padx=4, pady=2)
            fila += 1
            self.entries[prueba] = {}
            for canal in canales:
                ttk.Label(self.frame_tabla, text=str(canal)).grid(row=fila, column=0, padx=4, pady=1, sticky='w')
                self.entries[prueba][str(canal)] = {}
                for j, campo in enumerate(CAMPOS_LIMITE, start=1):
                    e = ttk.Entry(self.frame_tabla, width=12)
                    e.grid(row=fila, column=j, padx=4, pady=1)
                    self.entries[prueba][str(canal)][campo] = e
                fila += 1

    def _leer_tabla(self):
        limites = {}
        for prueba, canales in self.entries.items():
            limites[prueba] = {}
            for canal, campos in canales.items():
                d = {}
                for campo, e in campos.items():
                    txt = e.get().strip().replace(',', '.')
                    d[campo] = float(txt) if txt else None
                limites[prueba][canal] = d
        return limites

    def _escribir_tabla(self, limites):
        self._construir_tabla({p: list(c.keys()) for p, c in limites.items()})
        for prueba, canales in limites.items():
            for canal, d in canales.items():
                for campo, val in d.items():
                    if val is not None and canal in self.entries[prueba]:
                        self.entries[prueba][canal][campo].insert(0, str(val))

    def _autocompletar(self):
        ruta = filedialog.askopenfilename(title='Selecciona un Excel de muestra',
                                          filetypes=[('Excel', '*.xlsx *.xlsm')])
        if not ruta:
            return
        datos = qparser.leer_archivo(ruta)
        pc = {prueba: [str(ch['canal']) for ch in canales]
              for prueba, canales in datos['pruebas'].items()}
        if pc:
            self._construir_tabla(pc)
            messagebox.showinfo('Listo', f'Canales detectados: {sum(len(v) for v in pc.values())}')

    def _refrescar_perfiles(self):
        nombres = [p['nombre'] for p in db.listar_perfiles()]
        self.cb_perfil['values'] = nombres

    def _guardar_perfil(self):
        nombre = self.ent_nombre_perfil.get().strip()
        if not nombre:
            messagebox.showwarning('Falta nombre', 'Escribe un nombre para el perfil.')
            return
        db.guardar_perfil(nombre, self._leer_tabla())
        self._refrescar_perfiles()
        messagebox.showinfo('Guardado', f'Perfil "{nombre}" guardado.')

    def _cargar_perfil(self):
        nombre = self.cb_perfil.get()
        if not nombre:
            return
        lim = db.cargar_perfil(nombre)
        if lim:
            self._escribir_tabla(lim)
            self.ent_nombre_perfil.delete(0, 'end'); self.ent_nombre_perfil.insert(0, nombre)

    def _borrar_perfil(self):
        nombre = self.cb_perfil.get()
        if nombre and messagebox.askyesno('Confirmar', f'¿Eliminar el perfil "{nombre}"?'):
            db.borrar_perfil(nombre); self._refrescar_perfiles()

    # ============ TAB 2: PROCESAR CORRIDA ============
    def _build_procesar(self):
        f = ttk.Frame(self.tab_proc); f.pack(fill='x', padx=10, pady=8)
        ttk.Label(f, text='Carpeta con los Excels:').grid(row=0, column=0, sticky='w')
        self.ent_carpeta = ttk.Entry(f, width=60); self.ent_carpeta.grid(row=0, column=1, padx=5)
        ttk.Button(f, text='Examinar...', command=self._elegir_carpeta).grid(row=0, column=2)
        ttk.Button(f, text='Leer carpeta →', command=self._previsualizar).grid(row=0, column=3, padx=6)

        ttk.Label(f, text='Perfil de límites:').grid(row=1, column=0, sticky='w', pady=4)
        self.cb_perfil2 = ttk.Combobox(f, width=30, state='readonly'); self.cb_perfil2.grid(row=1, column=1, sticky='w', padx=5)
        ttk.Button(f, text='↻', width=3, command=lambda: self.cb_perfil2.configure(
            values=[p['nombre'] for p in db.listar_perfiles()])).grid(row=1, column=1, sticky='e')

        ttk.Label(f, text='Nombre del batch / corrida:').grid(row=2, column=0, sticky='w')
        self.ent_batch = ttk.Entry(f, width=30); self.ent_batch.grid(row=2, column=1, sticky='w', padx=5)
        self.ent_batch.insert(0, datetime.now().strftime('Corrida %Y-%m-%d'))

        ttk.Label(f, text='Operador:').grid(row=3, column=0, sticky='w')
        self.ent_operador = ttk.Entry(f, width=30); self.ent_operador.grid(row=3, column=1, sticky='w', padx=5)

        self.cb_perfil2.configure(values=[p['nombre'] for p in db.listar_perfiles()])

        prev_frame = ttk.LabelFrame(self.tab_proc, text='Piezas detectadas (revisa y corrige antes de evaluar)')
        prev_frame.pack(fill='both', expand=False, padx=10, pady=6)
        cols_p = ('archivo', 'pieza')
        self.tree_prev = ttk.Treeview(prev_frame, columns=cols_p, show='headings', height=6)
        self.tree_prev.heading('archivo', text='Archivo'); self.tree_prev.column('archivo', width=420)
        self.tree_prev.heading('pieza', text='No. de pieza (doble clic para editar)'); self.tree_prev.column('pieza', width=260)
        self.tree_prev.pack(side='left', fill='both', expand=True, padx=6, pady=6)
        self.tree_prev.bind('<Double-1>', self._editar_pieza)
        sb_p = ttk.Scrollbar(prev_frame, orient='vertical', command=self.tree_prev.yview)
        self.tree_prev.configure(yscrollcommand=sb_p.set); sb_p.pack(side='left', fill='y')

        ttk.Button(self.tab_proc, text='► Evaluar corrida', command=self._procesar).pack(anchor='w', padx=10, pady=6)

        cols = ('pieza', 'archivo', 'veredicto', 'fallas')
        self.tree = ttk.Treeview(self.tab_proc, columns=cols, show='headings', height=12)
        for c, t, w in [('pieza', 'No. pieza', 80), ('archivo', 'Archivo', 260),
                        ('veredicto', 'Veredicto', 100), ('fallas', 'Canales en falla', 360)]:
            self.tree.heading(c, text=t); self.tree.column(c, width=w)
        self.tree.tag_configure('paso', background='#C6EFCE')
        self.tree.tag_configure('nopaso', background='#FFC7CE')
        self.tree.pack(fill='both', expand=True, padx=10, pady=6)

        bf = ttk.Frame(self.tab_proc); bf.pack(fill='x', padx=10, pady=6)
        self.lbl_resumen = ttk.Label(bf, text='', font=('Arial', 10, 'bold')); self.lbl_resumen.pack(side='left')
        ttk.Button(bf, text='Generar PDFs individuales', command=self._generar_pdfs).pack(side='right', padx=4)
        ttk.Button(bf, text='Reporte del lote completo', command=self._generar_pdf_resumen).pack(side='right', padx=4)

    def _elegir_carpeta(self):
        d = filedialog.askdirectory(title='Carpeta con los Excels de la corrida')
        if d:
            self.ent_carpeta.delete(0, 'end'); self.ent_carpeta.insert(0, d)
            self._previsualizar()

    def _listar_archivos(self, carpeta):
        return sorted(glob.glob(os.path.join(carpeta, '*.xlsx')) +
                      glob.glob(os.path.join(carpeta, '*.xlsm')))

    def _previsualizar(self):
        carpeta = self.ent_carpeta.get().strip()
        if not carpeta or not os.path.isdir(carpeta):
            messagebox.showwarning('Carpeta', 'Selecciona una carpeta válida.'); return
        archivos = self._listar_archivos(carpeta)
        for i in self.tree_prev.get_children():
            self.tree_prev.delete(i)
        if not archivos:
            messagebox.showinfo('Sin archivos', 'No se encontraron Excels en esa carpeta.'); return
        sin_numero = 0
        for ruta in archivos:
            nombre = os.path.basename(ruta)
            num = piezas.extraer_numero(nombre)
            if num is None:
                num = ''
                sin_numero += 1
            self.tree_prev.insert('', 'end', values=(nombre, num))
        if sin_numero:
            messagebox.showwarning('Revisar', f'{sin_numero} archivo(s) no traen número en el nombre. '
                                   'Edítalos manualmente (doble clic) antes de evaluar.')

    def _editar_pieza(self, event):
        item = self.tree_prev.identify_row(event.y)
        col = self.tree_prev.identify_column(event.x)
        if not item or col != '#2':
            return
        x, y, w, h = self.tree_prev.bbox(item, col)
        valor_actual = self.tree_prev.set(item, 'pieza')
        edit = tk.Entry(self.tree_prev)
        edit.insert(0, valor_actual)
        edit.select_range(0, 'end')
        edit.place(x=x, y=y, width=w, height=h)
        edit.focus()

        def guardar(_=None):
            self.tree_prev.set(item, 'pieza', edit.get().strip())
            edit.destroy()
        edit.bind('<Return>', guardar)
        edit.bind('<FocusOut>', guardar)

    def _mapa_piezas(self):
        mapa = {}
        for item in self.tree_prev.get_children():
            archivo, pieza = self.tree_prev.item(item)['values']
            mapa[str(archivo)] = str(pieza)
        return mapa

    def _procesar(self):
        carpeta = self.ent_carpeta.get().strip()
        perfil = self.cb_perfil2.get()
        if not carpeta or not os.path.isdir(carpeta):
            messagebox.showwarning('Carpeta', 'Selecciona una carpeta válida.'); return
        if not perfil:
            messagebox.showwarning('Perfil', 'Selecciona un perfil de límites.'); return
        if not self.tree_prev.get_children():
            self._previsualizar()
        mapa = self._mapa_piezas()
        if any(not p for p in mapa.values()):
            messagebox.showwarning('Piezas', 'Hay archivos sin número de pieza. Corrígelos en la tabla de arriba '
                                   '(doble clic) antes de evaluar.'); return
        limites = db.cargar_perfil(perfil)
        archivos = self._listar_archivos(carpeta)

        for i in self.tree.get_children():
            self.tree.delete(i)

        bid = db.crear_batch(self.ent_batch.get().strip(), self.ent_operador.get().strip(), perfil)
        self._ultimo_batch = {'id': bid, 'nombre': self.ent_batch.get().strip(),
                              'operador': self.ent_operador.get().strip(), 'perfil': perfil}
        self._ultimos_resultados = []
        pasaron = fallaron = 0

        for ruta in archivos:
            nombre = os.path.basename(ruta)
            pieza = mapa.get(nombre, '')
            try:
                datos = qparser.leer_archivo(ruta)
                ev = evaluador.evaluar_archivo(datos, limites)
            except Exception as e:
                self.tree.insert('', 'end', values=(pieza, nombre, 'ERROR', str(e)))
                continue
            # adjuntar limites a cada canal para que el reporte muestre min/max
            for prueba, filas in ev['detalle'].items():
                for frow in filas:
                    frow['limite'] = limites.get(prueba, {}).get(str(frow['canal']))
            fallas = []
            for prueba, filas in ev['detalle'].items():
                for frow in filas:
                    if frow['resultado'] == 'FALLA':
                        fallas.append(f"{frow['canal']}({','.join(frow['motivos'])})")
            tag = 'paso' if ev['veredicto'] == 'PASO' else 'nopaso'
            if ev['veredicto'] == 'PASO':
                pasaron += 1
            else:
                fallaron += 1
            self.tree.insert('', 'end', tags=(tag,),
                             values=(pieza, nombre, ev['veredicto'], '; '.join(fallas) if fallas else '—'))
            db.guardar_resultado(bid, pieza, nombre, ev['veredicto'], ev['detalle'])
            self._ultimos_resultados.append({'pieza': pieza, 'archivo': nombre,
                                             'veredicto': ev['veredicto'], 'detalle': ev['detalle']})

        db.cerrar_batch(bid, len(archivos), pasaron, fallaron)
        self.lbl_resumen.config(text=f'Resultado: {pasaron} pasaron · {fallaron} fallaron · {len(archivos)} en total')
        self._refrescar_dashboard()

    def _generar_pdfs(self):
        if not self._ultimos_resultados:
            messagebox.showinfo('Sin datos', 'Primero evalúa una corrida.'); return
        carpeta = filedialog.askdirectory(title='¿Dónde guardar los PDFs?')
        if not carpeta:
            return
        b = self._ultimo_batch
        for r in self._ultimos_resultados:
            ruta = os.path.join(carpeta, f"reporte_pieza_{r['pieza']}.pdf")
            reporte.generar_pdf(ruta, r['pieza'], b['nombre'], b['operador'],
                                datetime.now().strftime('%Y-%m-%d %H:%M'), r['veredicto'], r['detalle'],
                                perfil=b.get('perfil', '—'))
        messagebox.showinfo('Listo', f"{len(self._ultimos_resultados)} reportes PDF generados en:\n{carpeta}")

    def _generar_pdf_resumen(self):
        if not self._ultimos_resultados:
            messagebox.showinfo('Sin datos', 'Primero evalúa una corrida.'); return
        ruta = filedialog.asksaveasfilename(title='Guardar reporte del lote', defaultextension='.pdf',
                                            filetypes=[('PDF', '*.pdf')],
                                            initialfile=f"reporte_lote_{self._ultimo_batch['nombre']}.pdf")
        if not ruta:
            return
        b = self._ultimo_batch
        reporte.generar_pdf_lote(ruta, b['nombre'], b['operador'],
                                 datetime.now().strftime('%Y-%m-%d %H:%M'), self._ultimos_resultados,
                                 perfil=b.get('perfil', '—'))
        messagebox.showinfo('Listo', f'Reporte del lote completo guardado en:\n{ruta}')

    # ============ TAB 3: DASHBOARD ============
    def _build_dashboard(self):
        top = ttk.Frame(self.tab_dash); top.pack(fill='x', padx=10, pady=8)
        ttk.Label(top, text='Agrupar por:').pack(side='left')
        self.cb_group = ttk.Combobox(top, width=10, state='readonly', values=['Día', 'Mes', 'Año'])
        self.cb_group.set('Día'); self.cb_group.pack(side='left', padx=5)
        self.cb_group.bind('<<ComboboxSelected>>', lambda e: self._refrescar_dashboard())
        ttk.Button(top, text='Actualizar', command=self._refrescar_dashboard).pack(side='left', padx=5)

        cols = ('batch', 'fecha', 'operador', 'total', 'pasaron', 'fallaron', 'tasa')
        self.tree_dash = ttk.Treeview(self.tab_dash, columns=cols, show='headings', height=8)
        for c, t, w in [('batch', 'Batch', 180), ('fecha', 'Fecha', 110), ('operador', 'Operador', 120),
                        ('total', 'Total', 60), ('pasaron', 'Pasaron', 70),
                        ('fallaron', 'Fallaron', 70), ('tasa', '% Aprob.', 70)]:
            self.tree_dash.heading(c, text=t); self.tree_dash.column(c, width=w)
        self.tree_dash.pack(fill='x', padx=10, pady=6)

        graf_frame = ttk.Frame(self.tab_dash)
        graf_frame.pack(fill='both', expand=True, padx=10, pady=6)
        self.fig = Figure(figsize=(10.2, 4.2), dpi=90)
        self.ax1 = self.fig.add_subplot(1, 3, 1)
        self.ax2 = self.fig.add_subplot(1, 3, 2)
        self.ax3 = self.fig.add_subplot(1, 3, 3)
        self.fig.tight_layout(pad=3.0)
        self.canvas_graf = FigureCanvasTkAgg(self.fig, master=graf_frame)
        self.canvas_graf.get_tk_widget().pack(fill='both', expand=True)

        self._refrescar_dashboard()

    def _refrescar_dashboard(self):
        for i in self.tree_dash.get_children():
            self.tree_dash.delete(i)
        batches = db.listar_batches()
        for b in batches:
            tasa = f"{(100*b['pasaron']/b['total']):.0f}%" if b['total'] else '—'
            fecha = b['fecha'][:10]
            self.tree_dash.insert('', 'end', values=(b['nombre'], fecha, b['operador'],
                                                     b['total'], b['pasaron'], b['fallaron'], tasa))
        self._dibujar_graficas(batches)

    def _agrupar_fecha(self, fecha_iso):
        modo = self.cb_group.get()
        if modo == 'Mes':
            return fecha_iso[:7]
        if modo == 'Año':
            return fecha_iso[:4]
        return fecha_iso[:10]

    def _dibujar_graficas(self, batches):
        self.ax1.clear(); self.ax2.clear(); self.ax3.clear()

        agg = defaultdict(lambda: [0, 0])
        for b in batches:
            clave = self._agrupar_fecha(b['fecha'])
            agg[clave][0] += b['pasaron']; agg[clave][1] += b['total']
        claves = sorted(agg.keys())
        tasas = [100 * agg[k][0] / agg[k][1] if agg[k][1] else 0 for k in claves]
        self.ax1.plot(claves, tasas, marker='o', color='#1F3864')
        self.ax1.set_title('Tasa de aprobación en el tiempo', fontsize=9)
        self.ax1.set_ylabel('% aprobación'); self.ax1.set_ylim(0, 105)
        self.ax1.tick_params(axis='x', rotation=45, labelsize=7)

        nombres = [b['nombre'][:12] for b in batches]
        pasaron = [b['pasaron'] for b in batches]
        fallaron = [b['fallaron'] for b in batches]
        idx = range(len(batches))
        self.ax2.bar(idx, pasaron, color='#1D9E75', label='Pasaron')
        self.ax2.bar(idx, fallaron, bottom=pasaron, color='#E24B4A', label='Fallaron')
        self.ax2.set_xticks(list(idx)); self.ax2.set_xticklabels(nombres, rotation=45, ha='right', fontsize=7)
        self.ax2.set_title('Pasaron vs fallaron por batch', fontsize=9)
        self.ax2.legend(fontsize=7)

        conteo = db.conteo_fallas_por_canal()
        top = sorted(conteo.items(), key=lambda x: -x[1])[:8]
        if top:
            etiquetas = [t[0] for t in top]
            valores = [t[1] for t in top]
            self.ax3.barh(etiquetas, valores, color='#D85A30')
            self.ax3.invert_yaxis()
            self.ax3.tick_params(axis='y', labelsize=7)
        self.ax3.set_title('Canales que más fallan', fontsize=9)

        self.fig.tight_layout(pad=2.0)
        self.canvas_graf.draw()


if __name__ == '__main__':
    App().mainloop()
