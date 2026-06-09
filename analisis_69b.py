"""
ANALISIS DE DATOS REALES DEL ARTICULO 69-B CFF (Parte III)
===========================================================
Tesis Doctoral: "Gobernanza de la IA en la Administracion Tributaria en Mexico"
Dr. David - Doctorado en Derecho

OBJETO: a diferencia de los proxies I (tabular) y II (grafos), que usan datos
sinteticos para demostrar MECANISMOS, este analisis usa DATOS REALES y publicos
del SAT (listado del articulo 69-B del CFF, al 30 de abril de 2026) para medir
RESULTADOS observables:
   1) Con que frecuencia se revoca la presuncion de operaciones inexistentes?
   2) A cuantos contribuyentes se les cancelo el Certificado de Sello Digital
      (CSD, art. 17-H) antes de tener una resolucion definitiva firme?

UNIDAD DE ANALISIS: RFC UNICO. El listado trae 14,424 filas pero 14,244 RFC
unicos (180 contribuyentes aparecen repetidos). Se des-duplica conservando la
situacion mas reciente (keep='last'). Convencion fija y documentada.
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

def ruta(*cands):
    return next((p for p in cands if os.path.exists(p)), cands[0])

RUTA_69B = ruta('datos/Listado_completo_69-B.csv', 'Listado_completo_69-B.csv')
RUTA_CSD = ruta('datos/CSDsinefectos.csv', 'CSDsinefectos.csv')
COL_SIT = 'Situacion del contribuyente'
ORDEN = ['Definitivo', 'Sentencia Favorable', 'Presunto', 'Desvirtuado']

df = pd.read_csv(RUTA_69B, encoding='latin-1', skiprows=2, sep=',', engine='python')
df.columns = [c.strip() for c in df.columns]
# La columna de situacion trae acento; localizarla de forma robusta
COL_SIT = [c for c in df.columns if c.lower().startswith('situaci')][0]
df['RFC'] = df['RFC'].astype(str).str.strip().str.upper()

filas = len(df)
df_u = df.drop_duplicates('RFC', keep='last')
total = len(df_u)

print("=" * 68)
print("ANALISIS DE DATOS REALES DEL 69-B CFF (Parte III)")
print("Fuente: SAT, listado publico art. 69-B, al 30 de abril de 2026")
print("=" * 68)
print("\nFilas en el listado:        %s" % f'{filas:,}')
print("RFC unicos (unidad usada):  %s" % f'{total:,}')
print("RFC repetidos descartados:  %s" % f'{filas-total:,}')

sit = df_u[COL_SIT].value_counts().reindex([s for s in ORDEN if s in df_u[COL_SIT].unique()])
print("\nDistribucion por situacion (RFC unico):")
for k, v in sit.items():
    print("  %-22s %8s  (%4.1f%%)" % (k, f'{v:,}', v/total*100))

defin = int(sit.get('Definitivo', 0)); favs = int(sit.get('Sentencia Favorable', 0))
pres = int(sit.get('Presunto', 0)); desv = int(sit.get('Desvirtuado', 0))

resueltos = defin + favs + desv
revocados = favs + desv
señalados = defin + favs
print("\n" + "-" * 68)
print("TASAS CLAVE (sobre RFC unicos)")
print("-" * 68)
print("  Senalamiento adverso inicial: %s/%s = %.2f%%" % (f'{señalados:,}', f'{total:,}', señalados/total*100))
print("  Salvacion administrativa:     %s/%s = %.2f%%" % (f'{desv:,}', f'{total:,}', desv/total*100))
print("  Rescate judicial:             %s/%s = %.2f%%" % (f'{favs:,}', f'{señalados:,}', favs/señalados*100))
print("  Revocacion entre resueltos:   %s/%s = %.1f%% (1 de cada %.1f)" % (f'{revocados:,}', f'{resueltos:,}', revocados/resueltos*100, resueltos/revocados))
print("  De las revocaciones: %.0f%% judicial vs %.0f%% administrativa" % (favs/revocados*100, desv/revocados*100))

df_u['anio'] = pd.to_datetime(df_u['Publicacion pagina SAT presuntos'] if 'Publicacion pagina SAT presuntos' in df_u.columns else df_u[[c for c in df_u.columns if 'gina SAT presuntos' in c][0]], dayfirst=True, errors='coerce').dt.year
serie = df_u['anio'].value_counts().sort_index(); serie = serie[serie.index.notna()]

# CRUCE CSD
csd = pd.read_csv(RUTA_CSD, encoding='latin-1', sep=',', engine='python')
csd.columns = [c.strip() for c in csd.columns]
csd['RFC'] = csd['RFC'].astype(str).str.strip().str.upper()
col_sup = [c for c in csd.columns if 'SUPUESTO' in c.upper()][0]
csd_u = csd.drop_duplicates('RFC')
cruce = df_u[['RFC', COL_SIT]].merge(csd_u[['RFC', col_sup]], on='RFC', how='inner')
n_cruce = cruce['RFC'].nunique()
sit_csd = cruce[COL_SIT].value_counts().reindex([s for s in ORDEN if s in cruce[COL_SIT].unique()])
c_def = int(sit_csd.get('Definitivo', 0)); c_pre = int(sit_csd.get('Presunto', 0))
c_fav = int(sit_csd.get('Sentencia Favorable', 0)); c_des = int(sit_csd.get('Desvirtuado', 0))
no_firmes = c_pre + c_fav + c_des
exonerados = c_fav + c_des

print("\n" + "-" * 68)
print("CRUCE 69-B  x  CSD SIN EFECTOS (art. 17-H)")
print("-" * 68)
print("  Contribuyentes en AMBOS listados: %s" % f'{n_cruce:,}')
print("  Supuesto de cancelacion: %s" % dict(cruce[col_sup].value_counts()))
print("  Situacion 69-B de los sancionados con CSD:")
for k, v in sit_csd.items():
    print("    %-22s %4s" % (k, f'{v:,}'))
print("\n  >> %s NO son EFOS definitivos firmes y aun asi perdieron el sello:" % no_firmes)
print("       . %s Presuntos (sancion ANTES de la resolucion definitiva)" % c_pre)
print("       . %s Exonerados que GANARON (%s Sent. Fav. + %s Desvirtuados)" % (exonerados, c_fav, c_des))

COL = {'Definitivo': '#C0392B', 'Sentencia Favorable': '#27AE60', 'Presunto': '#E67E22', 'Desvirtuado': '#2ECC71'}

# FIGURA 1
fig, axes = plt.subplots(2, 2, figsize=(14, 10)); fig.patch.set_facecolor('#F8F9FA')
fig.suptitle('Datos reales del articulo 69-B CFF - EFOS (RFC unicos: %s)\nFuente: SAT (listado publico), al 30 de abril de 2026' % f'{total:,}', fontsize=13, fontweight='bold', y=0.98)
ax1 = axes[0, 0]; nombres = list(sit.index); vals = list(sit.values)
b = ax1.barh(nombres, vals, color=[COL.get(n, '#3498DB') for n in nombres], alpha=0.9); ax1.invert_yaxis()
ax1.set_xlabel('Numero de contribuyentes (RFC unicos)'); ax1.set_title('Situacion de los %s contribuyentes del listado 69-B' % f'{total:,}', fontsize=10)
for bar, v in zip(b, vals):
    ax1.text(v + 80, bar.get_y() + bar.get_height()/2, '%s (%.1f%%)' % (f'{v:,}', v/total*100), va='center', fontsize=9)
ax1.set_xlim(0, max(vals) * 1.18); ax1.set_facecolor('#FFFFFF')
ax2 = axes[0, 1]
ax2.pie([defin, favs, desv], labels=['Confirmados\n%s\n(%.1f%%)' % (f'{defin:,}', defin/resueltos*100), 'Sentencia favorable\n%s\n(%.1f%%)' % (f'{favs:,}', favs/resueltos*100), 'Desvirtuado\n%s\n(%.1f%%)' % (f'{desv:,}', desv/resueltos*100)], colors=['#C0392B', '#27AE60', '#2ECC71'], startangle=90, wedgeprops=dict(width=0.42, edgecolor='white'), textprops={'fontsize': 9})
ax2.text(0, 0, '%.1f%%\nrevocados' % (revocados/resueltos*100), ha='center', va='center', fontsize=13, fontweight='bold', color='#27AE60')
ax2.set_title('Desenlace de las presunciones resueltas\n(1 de cada %.1f fue revocada)' % (resueltos/revocados), fontsize=10)
ax3 = axes[1, 0]; anios = [int(a) for a in serie.index]
ax3.bar([str(a) for a in anios], serie.values, color='#2980B9', alpha=0.85)
for i, a in enumerate(anios):
    if a in (2017, 2025): ax3.patches[i].set_color('#E74C3C')
ax3.set_xlabel('Ano de publicacion (presuncion)'); ax3.set_ylabel('Numero de presunciones')
ax3.set_title('Evolucion anual de presunciones\n(rojo: pico de 2017 y repunte de 2025)', fontsize=10)
ax3.tick_params(axis='x', rotation=45, labelsize=8); ax3.set_facecolor('#FFFFFF')
ax4 = axes[1, 1]
b4 = ax4.bar(['Via judicial\n(Sentencia\nFavorable)', 'Via administrativa\n(Desvirtuado)'], [favs, desv], color=['#27AE60', '#2ECC71'], alpha=0.9)
for bar, v in zip(b4, [favs, desv]):
    ax4.text(bar.get_x() + bar.get_width()/2, v + 15, '%s\n(%.0f%%)' % (f'{v:,}', v/revocados*100), ha='center', fontsize=10, fontweight='bold')
ax4.set_ylabel('Numero de revocaciones'); ax4.set_title('Por que via se revoca la presuncion?\nLa fase administrativa casi no corrige', fontsize=10)
ax4.set_ylim(0, max(favs, desv) * 1.22); ax4.set_facecolor('#FFFFFF')
plt.tight_layout(rect=[0, 0, 1, 0.95]); plt.savefig('graficas_69b.png', dpi=150, bbox_inches='tight', facecolor='#F8F9FA'); plt.close()
print("\n[OK] graficas_69b.png")

# FIGURA 2 (CSD)
fig2, ax = plt.subplots(1, 2, figsize=(14, 5.5)); fig2.patch.set_facecolor('#F8F9FA')
fig2.suptitle('Impacto en los Certificados de Sello Digital (art. 17-H) - %s contribuyentes con CSD cancelado\nTodos por "Fraccion X" (cancelacion ligada al 69-B)' % f'{n_cruce:,}', fontsize=12, fontweight='bold', y=1.02)
a = ax[0]; nom = list(sit_csd.index); vv = list(sit_csd.values)
bb = a.bar(nom, vv, color=[COL.get(n, '#3498DB') for n in nom], alpha=0.9)
for bar, v in zip(bb, vv): a.text(bar.get_x()+bar.get_width()/2, v+4, '%s' % v, ha='center', fontsize=10, fontweight='bold')
a.set_title('Situacion 69-B de los %s con sello cancelado' % f'{n_cruce:,}', fontsize=10); a.set_ylabel('Contribuyentes'); a.tick_params(axis='x', labelsize=8); a.set_facecolor('#FFFFFF')
a2 = ax[1]; cats = ['Definitivos\nfirmes', 'Presuntos\n(aun sin\nresolucion)', 'Exonerados\n(ganaron y\nfueron sancionados)']
valores = [c_def, c_pre, exonerados]
bb2 = a2.bar(cats, valores, color=['#C0392B', '#E67E22', '#27AE60'], alpha=0.9)
for bar, v in zip(bb2, valores): a2.text(bar.get_x()+bar.get_width()/2, v+4, '%s' % v, ha='center', fontsize=11, fontweight='bold')
a2.set_title('%s de %s NO eran EFOS firmes y aun asi perdieron el sello' % (no_firmes, n_cruce), fontsize=10); a2.set_ylabel('Contribuyentes'); a2.tick_params(axis='x', labelsize=8); a2.set_facecolor('#FFFFFF')
plt.tight_layout(); plt.savefig('graficas_69b_csd.png', dpi=150, bbox_inches='tight', facecolor='#F8F9FA'); plt.close()
print("[OK] graficas_69b_csd.png")
print("\n" + "=" * 68)
print("Analisis Parte III completado (RFC unicos + cruce CSD).")
print("=" * 68)
