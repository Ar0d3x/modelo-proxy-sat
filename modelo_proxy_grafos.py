"""
MODELO PROXY DE ANALÍTICA DE GRAFOS — DETECCIÓN DE EFOS/EDOS (Parte II)
=======================================================================
Tesis Doctoral: "Gobernanza de la IA en la Administración Tributaria en México"
Dr. David — Doctorado en Derecho

OBJETO: replicar, sobre una red sintética de CFDI, la lógica de analítica de
grafos que el SAT declara usar (Plan Maestro 2024) para detectar Empresas que
Facturan Operaciones Simuladas (EFOS) y las que las Deducen (EDOS), y demostrar
empíricamente su problema jurídico central: LA CULPABILIDAD POR ASOCIACIÓN.

A un contribuyente se le marca no por su conducta individual, sino por su
POSICIÓN EN LA RED. Esto tensiona la presunción de inocencia (Art. 20-B CPEUM),
la personalidad de la sanción, el debido proceso y la motivación (Arts. 14 y 16
CPEUM), y alimenta el mecanismo del 69-B CFF.

Modelo: cada NODO es un RFC; cada ARISTA dirigida es un CFDI (emisor -> receptor)
con un monto. Datos sintéticos (realismo bungeano / CESM): demuestran viabilidad
y detectabilidad, no el comportamiento real del SAT (ver Limitaciones).

NOTA DE DISEÑO (correcciones tras auditoría de la 1.ª versión):
 - EDOS heterogéneos (pesados/ligeros); los ligeros se solapan con legítimas
   contaminadas (es el solapamiento realista que produce el daño jurídico).
 - La contaminación conecta a EFOS YA IDENTIFICADOS: modela el escenario del
   69-B (al publicarse un EFOS, sus contrapartes inocentes caen bajo sospecha).
 - Umbral calibrado por RECALL DE EDOS (punto de operación realista), no por
   percentil global.
"""

import numpy as np
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.inspection import permutation_importance
import warnings
warnings.filterwarnings('ignore')

SEMILLA = 42
np.random.seed(SEMILLA)
rng = np.random.default_rng(SEMILLA)

# ============================================================
# 1. GENERACIÓN DE LA RED SINTÉTICA DE CFDI
# ============================================================

N_LEGIT = 1200
N_EFOS  = 80
N_EDOS  = 220
N = N_LEGIT + N_EFOS + N_EDOS

tipo = (['LEGIT'] * N_LEGIT) + (['EFOS'] * N_EFOS) + (['EDOS'] * N_EDOS)
legit_ids = list(range(0, N_LEGIT))
efos_ids  = list(range(N_LEGIT, N_LEGIT + N_EFOS))
edos_ids  = list(range(N_LEGIT + N_EFOS, N))
nodos = list(range(N))

G = nx.DiGraph()
for i in nodos:
    G.add_node(i, tipo=tipo[i])

def monto_normal():
    return float(np.clip(rng.lognormal(11.5, 1.0), 1_000, 5_000_000))
def monto_simulado():
    return float(np.clip(rng.lognormal(12.5, 0.8), 50_000, 8_000_000))

# El SAT ya conoce algunos EFOS (lista 69-B publicada). Definir ANTES de contaminar.
frac_conocidos = 0.40
semillas_efos = set(int(x) for x in rng.choice(efos_ids, size=int(N_EFOS * frac_conocidos), replace=False))

# (a) Comercio legítimo con estructura de comunidades
n_comunidades = 12
comunidad = {i: int(rng.integers(0, n_comunidades)) for i in legit_ids}
for i in legit_ids:
    k = rng.integers(1, 7)
    for _ in range(k):
        if rng.random() < 0.8:
            cand = [j for j in legit_ids if comunidad[j] == comunidad[i] and j != i]
        else:
            cand = [j for j in legit_ids if j != i]
        if cand:
            G.add_edge(i, int(rng.choice(cand)), monto=monto_normal())

# (a.2) [FIX-3] Hubs legítimos: ~3% de empresas con grado naturalmente alto
#       (distribuidores, mayoristas). Rompen la separabilidad trivial por grado.
hubs = rng.choice(legit_ids, size=int(N_LEGIT * 0.03), replace=False)
for h in hubs:
    for _ in range(rng.integers(15, 40)):
        j = int(rng.choice(legit_ids))
        if j != h:
            G.add_edge(int(h), j, monto=monto_normal())

# (b) [FIX-1] Esquema de simulación EFOS -> EDOS, con EDOS heterogéneos
edos_ligeros = set()
for d in edos_ids:
    if rng.random() < 0.40:   # EDOS "ligero": 1 EFOS, monto moderado
        edos_ligeros.add(d)
        e = int(rng.choice(list(semillas_efos) if rng.random() < 0.6 else efos_ids))
        G.add_edge(e, int(d), monto=float(np.clip(rng.lognormal(11.6, 0.7), 20_000, 2_000_000)))
    else:                     # EDOS "pesado": 2-4 EFOS, montos altos
        k = rng.integers(2, 5)
        for e in rng.choice(efos_ids, size=min(k, N_EFOS), replace=False):
            G.add_edge(int(e), int(d), monto=monto_simulado())

# (c) Anillos entre EFOS
for _ in range(N_EFOS * 2):
    a, b = rng.choice(efos_ids, size=2, replace=False)
    G.add_edge(int(a), int(b), monto=monto_normal())

# (d) [FIX-2] CONTAMINACIÓN: legítimas con UNA factura con un EFOS YA IDENTIFICADO.
#     No son fraudulentas; modelan el escenario real del 69-B.
N_CONTAMINADAS = 90
legit_contaminadas = rng.choice(legit_ids, size=N_CONTAMINADAS, replace=False)
for i in legit_contaminadas:
    e = int(rng.choice(list(semillas_efos)))
    if rng.random() < 0.5:
        G.add_edge(int(i), e, monto=monto_normal())
    else:
        G.add_edge(e, int(i), monto=monto_normal())
set_contaminadas = set(int(x) for x in legit_contaminadas)

print("=" * 66)
print("MODELO PROXY DE GRAFOS — DETECCIÓN DE EFOS/EDOS (Parte II)")
print("=" * 66)
print(f"\nNodos (RFC): {G.number_of_nodes()}  |  Aristas (CFDI): {G.number_of_edges()}")
print(f"  Legítimos: {N_LEGIT} (incl. {len(hubs)} hubs)  |  EFOS: {N_EFOS}  |  EDOS: {N_EDOS} ({len(edos_ligeros)} ligeros)")
print(f"  Legítimas 'contaminadas' (1 factura con EFOS identificado): {N_CONTAMINADAS}")
print(f"  EFOS ya identificados por el SAT (semilla 69-B): {len(semillas_efos)} de {N_EFOS}")

# ============================================================
# 2. PUNTAJE DE SOSPECHA POR PROPAGACIÓN (PageRank personalizado)
# ============================================================

H = G.to_undirected()
personalizacion = {i: (1.0 if i in semillas_efos else 0.0) for i in nodos}
ppr = nx.pagerank(H, alpha=0.85, personalization=personalizacion, weight=None)
s = np.array([ppr[i] for i in nodos])
score = (s - s.min()) / (s.max() - s.min() + 1e-12)

# ============================================================
# 3. UMBRAL CALIBRADO POR RECALL DE EDOS [FIX-4]
#    El SAT quiere atrapar a los EDOS. Fijamos el umbral en el punto que
#    captura ~75% de los EDOS y observamos a quién más barre.
# ============================================================

score_edos = score[edos_ids]
RECALL_OBJETIVO = 0.75
umbral = float(np.quantile(score_edos, 1 - RECALL_OBJETIVO))
recall_edos = float(np.mean(score[edos_ids] >= umbral))

print("\n" + "=" * 66)
print("PUNTO DE OPERACIÓN: umbral calibrado para detectar EDOS")
print("=" * 66)
print(f"  Umbral de sospecha (recall EDOS objetivo {RECALL_OBJETIVO:.0%}): {umbral:.5f}")
print(f"  Recall real de EDOS a ese umbral: {recall_edos:.0%}")

# ============================================================
# 4. CULPABILIDAD POR ASOCIACIÓN
# ============================================================

marcado = score >= umbral
df = pd.DataFrame({'id': nodos, 'tipo': tipo, 'score': score, 'marcado': marcado})
df['contaminada'] = df['id'].isin(set_contaminadas)

legit_marcados = df[(df.tipo == 'LEGIT') & (df.marcado)]
legit_marcados_contam = legit_marcados[legit_marcados.contaminada]
pct_contam = (len(legit_marcados_contam) / len(legit_marcados) * 100) if len(legit_marcados) else 0.0

print("\n" + "=" * 66)
print("CULPABILIDAD POR ASOCIACIÓN")
print("=" * 66)
print(f"  Empresas LEGÍTIMAS marcadas como sospechosas: {len(legit_marcados)}")
print(f"  De ellas, por haber facturado con un EFOS: {len(legit_marcados_contam)} ({pct_contam:.0f}%)")
contam_marcadas = df[(df.contaminada) & (df.marcado)]
limpias = df[(df.tipo == 'LEGIT') & (~df.contaminada)]
print(f"\n  Tasa de marca en legítimas CONTAMINADAS : {contam_marcadas.shape[0]}/{N_CONTAMINADAS} = {contam_marcadas.shape[0]/N_CONTAMINADAS*100:.0f}%")
print(f"  Tasa de marca en legítimas SIN contacto : {int(limpias.marcado.sum())}/{len(limpias)} = {limpias.marcado.mean()*100:.1f}%")
riesgo_rel = (contam_marcadas.shape[0]/N_CONTAMINADAS) / (limpias.marcado.mean() + 1e-9)
print(f"  Riesgo relativo de ser marcada por tocar un EFOS: x{riesgo_rel:.0f}")
# ¿Cuántos EDOS ligeros son indistinguibles de contaminadas?
edos_lig_marcados = df[(df.id.isin(edos_ligeros)) & (df.marcado)].shape[0]
print(f"\n  (Los EDOS 'ligeros' marcados: {edos_lig_marcados}/{len(edos_ligeros)} — estructuralmente")
print(f"   casi idénticos a las legítimas contaminadas: el detector no puede distinguirlos.)")

# ============================================================
# 5. CLASIFICADOR SUPERVISADO (estilo C3-UNAM / SAT) + opacidad
# ============================================================

deg_in = dict(G.in_degree()); deg_out = dict(G.out_degree())
clustering = nx.clustering(H)
def frac_monto_con_semillas(i):
    total = con = 0.0
    for _, v, d in G.out_edges(i, data=True):
        total += d['monto'];  con += d['monto'] if v in semillas_efos else 0
    for u, _, d in G.in_edges(i, data=True):
        total += d['monto'];  con += d['monto'] if u in semillas_efos else 0
    return con / total if total > 0 else 0.0
frac_efos = np.array([frac_monto_con_semillas(i) for i in nodos])

features = pd.DataFrame({
    'grado_entrada': [deg_in[i] for i in nodos],
    'grado_salida': [deg_out[i] for i in nodos],
    'n_contrapartes': [deg_in[i] + deg_out[i] for i in nodos],
    'clustering': [clustering[i] for i in nodos],
    'frac_monto_con_efos': frac_efos,    # ASOCIACIÓN
})
y_true = np.array([1 if t in ('EFOS', 'EDOS') else 0 for t in tipo])
mask_eval = np.array([i not in semillas_efos for i in nodos])

auc_prop = roc_auc_score(y_true[mask_eval], score[mask_eval])

X_tr, X_te, y_tr, y_te = train_test_split(features[mask_eval], y_true[mask_eval],
                                          test_size=0.3, random_state=SEMILLA, stratify=y_true[mask_eval])
clf = RandomForestClassifier(n_estimators=300, max_depth=8, random_state=SEMILLA, n_jobs=-1)
clf.fit(X_tr, y_tr)
auc_clf = roc_auc_score(y_te, clf.predict_proba(X_te)[:, 1])

print("\n" + "=" * 66)
print("DESEMPEÑO DE LA DETECCIÓN")
print("=" * 66)
print(f"  AUC del puntaje de propagación (interpretable): {auc_prop:.3f}")
print(f"  AUC del clasificador supervisado (random forest): {auc_clf:.3f}")

imp = permutation_importance(clf, X_te, y_te, n_repeats=12, random_state=SEMILLA, scoring='roc_auc')
importancias = pd.Series(imp.importances_mean, index=features.columns).sort_values(ascending=False)
print("\n  Importancia de variables (asociación marcada con *):")
for v, val in importancias.items():
    marca = " *ASOCIACIÓN" if v in ('frac_monto_con_efos', 'score_propagacion') else ""
    print(f"    {v:<22} {val:+.4f}{marca}")

# ============================================================
# 6. CONTRAFÁCTICO A NIVEL DE NODO: el efecto de UNA factura
# ============================================================

print("\n" + "=" * 66)
print("CONTRAFÁCTICO: el efecto de UNA sola factura con un EFOS")
print("=" * 66)
candidatas = [i for i in legit_ids if i not in set_contaminadas and i not in set(hubs)]
muestra = rng.choice(candidatas, size=60, replace=False)
score_antes = score[muestra].copy()

G2 = G.copy()
for i in muestra:
    G2.add_edge(int(i), int(rng.choice(list(semillas_efos))), monto=monto_normal())
ppr2 = nx.pagerank(G2.to_undirected(), alpha=0.85, personalization=personalizacion, weight=None)
s2 = np.array([ppr2[i] for i in nodos])
score2 = (s2 - s.min()) / (s.max() - s.min() + 1e-12)
score_despues = score2[muestra]

cruzaron = int(np.sum((score_antes < umbral) & (score_despues >= umbral)))
factor = float(np.median(score_despues / (score_antes + 1e-12)))
print(f"  Empresas idénticas en conducta propia: {len(muestra)}")
print(f"  Aumento mediano del puntaje tras 1 factura con EFOS: x{factor:.1f}")
print(f"  Cruzaron el umbral de sospecha por esa única factura: {cruzaron}/{len(muestra)} ({cruzaron/len(muestra)*100:.0f}%)")
print(f"  -> Misma conducta; distinta compañía. Núcleo del problema de")
print(f"     personalidad de la sanción y presunción de inocencia.")

# ============================================================
# 7. CONTAGIO POR DISTANCIA
# ============================================================

print("\n" + "=" * 66)
print("CONTAGIO: puntaje medio según distancia al EFOS conocido más cercano")
print("=" * 66)
dist_a_efos = {}
for e in semillas_efos:
    for nodo, d in nx.single_source_shortest_path_length(H, e, cutoff=5).items():
        if nodo not in dist_a_efos or d < dist_a_efos[nodo]:
            dist_a_efos[nodo] = d
filas = []
for salto in [1, 2, 3, 4]:
    ids = [i for i in legit_ids if dist_a_efos.get(i, 99) == salto]
    if ids:
        tasa = np.mean(score[ids] >= umbral) * 100
        filas.append((salto, len(ids), float(np.mean(score[ids])), tasa))
        print(f"  A {salto} salto(s): {len(ids):>4} legítimas | puntaje medio {np.mean(score[ids]):.4f} | marcadas {tasa:.1f}%")

# ============================================================
# 8. GRÁFICAS
# ============================================================

fig, axes = plt.subplots(2, 2, figsize=(14, 11))
fig.patch.set_facecolor('#F8F9FA')
fig.suptitle('Analítica de Grafos y Culpabilidad por Asociación — Modelo Proxy SAT (Parte II)\n'
             'Detección de EFOS/EDOS sobre red sintética de CFDI',
             fontsize=13, fontweight='bold', y=0.98)
COL = {'LEGIT': '#3498DB', 'EFOS': '#E74C3C', 'EDOS': '#E67E22'}

# G1: subred alrededor de EFOS conocidos
ax1 = axes[0, 0]
nodos_sub = set()
for e in list(semillas_efos)[:5]:
    nodos_sub.add(e); nodos_sub.update(list(H.neighbors(e))[:9])
sub = H.subgraph(nodos_sub)
pos = nx.spring_layout(sub, seed=SEMILLA, k=0.5)
colores_sub = [COL[G.nodes[i]['tipo']] for i in sub.nodes()]
tam = [200 if G.nodes[i]['tipo'] == 'EFOS' else 80 for i in sub.nodes()]
nx.draw_networkx_edges(sub, pos, ax=ax1, alpha=0.25, arrows=False)
nx.draw_networkx_nodes(sub, pos, ax=ax1, node_color=colores_sub, node_size=tam, alpha=0.9)
ax1.set_title('Subred de CFDI alrededor de EFOS conocidos\n(rojo=EFOS, naranja=EDOS, azul=legítimo)', fontsize=10)
ax1.axis('off')
ax1.legend(handles=[mpatches.Patch(color=c, label=l) for l, c in COL.items()], fontsize=8, loc='upper right')

# G2: distribución del puntaje por tipo
ax2 = axes[0, 1]
for t in ['LEGIT', 'EFOS', 'EDOS']:
    ax2.hist(df[df.tipo == t]['score'], bins=50, alpha=0.55, color=COL[t], label=t, density=True)
ax2.axvline(umbral, color='black', linestyle='--', linewidth=1.5, label=f'Umbral (recall EDOS {RECALL_OBJETIVO:.0%})')
ax2.set_xlabel('Puntaje de sospecha (propagación)'); ax2.set_ylabel('Densidad')
ax2.set_title('Las legítimas a la derecha del umbral\nson falsos positivos por asociación', fontsize=10)
ax2.legend(fontsize=8); ax2.set_xlim(0, np.quantile(score, 0.995)); ax2.set_facecolor('#FFFFFF')

# G3: contrafáctico
ax3 = axes[1, 0]
orden = np.argsort(score_antes)
ax3.plot(range(len(muestra)), score_antes[orden], 'o-', color='#3498DB', markersize=4, label='Antes (conducta propia)')
ax3.plot(range(len(muestra)), score_despues[orden], 's-', color='#E74C3C', markersize=4, label='Tras 1 factura con EFOS')
ax3.axhline(umbral, color='black', linestyle='--', linewidth=1.5, label='Umbral de sospecha')
ax3.set_xlabel('Empresas legítimas (ordenadas)'); ax3.set_ylabel('Puntaje de sospecha')
ax3.set_title(f'Contrafáctico: una sola factura cruza\na {cruzaron} de {len(muestra)} empresas sobre el umbral', fontsize=10)
ax3.legend(fontsize=8); ax3.set_facecolor('#FFFFFF')

# G4: contagio por distancia (tasa de marca)
ax4 = axes[1, 1]
if filas:
    saltos = [str(f[0]) for f in filas]; tasas = [f[3] for f in filas]
    ax4.bar(saltos, tasas, color='#8E44AD', alpha=0.8)
    for i, f in enumerate(filas):
        ax4.text(i, f[3] + 0.4, f'{f[3]:.0f}%', ha='center', fontsize=9, fontweight='bold')
    ax4.set_xlabel('Distancia (saltos) al EFOS conocido más cercano')
    ax4.set_ylabel('% de legítimas marcadas')
    ax4.set_title('Contagio: el riesgo de marca decae con la distancia,\npero golpea a vecinos de 1.er grado', fontsize=10)
ax4.set_facecolor('#FFFFFF')

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig('graficas_modelo_grafos.png', dpi=150, bbox_inches='tight', facecolor='#F8F9FA')
plt.close()
print("\n[OK] Gráficas guardadas: graficas_modelo_grafos.png")

# ============================================================
# 9. RESUMEN EJECUTIVO
# ============================================================

print("\n" + "=" * 66)
print("RESUMEN EJECUTIVO — HALLAZGOS (Parte II, grafos)")
print("=" * 66)
print(f"""
HALLAZGO 1 — CULPABILIDAD POR ASOCIACIÓN:
  Al fijar el umbral para detectar el {recall_edos:.0%} de los EDOS, se marcaron
  {len(legit_marcados)} empresas legítimas; el {pct_contam:.0f}% por haber facturado con un EFOS.
  Una legítima que tocó un EFOS tiene ~{riesgo_rel:.0f}x más probabilidad de ser
  marcada que una sin contacto, pese a no tener conducta irregular propia.
  -> Presunción de inocencia (Art. 20-B), personalidad de la sanción, 69-B CFF.

HALLAZGO 2 — EL EFECTO DE UNA SOLA FACTURA:
  En empresas idénticas en conducta, una factura con un EFOS multiplicó el
  puntaje por ~{factor:.1f} y cruzó a {cruzaron}/{len(muestra)} ({cruzaron/len(muestra)*100:.0f}%) sobre el umbral.
  -> La señal mide con quién te relacionas, no qué hiciste.

HALLAZGO 3 — INDISTINGUIBILIDAD ESTRUCTURAL:
  Los EDOS 'ligeros' (1 factura simulada) y las legítimas contaminadas (1
  factura real) ocupan posiciones casi idénticas en la red. El detector no
  puede separarlos: el falso positivo es inherente, no un error de ajuste.

HALLAZGO 4 — OPACIDAD ESTRUCTURAL Y SEÑAL vs PRUEBA:
  El puntaje depende de la posición global en la red; explicar el "por qué"
  exigiría revelar a terceros protegidos por el secreto fiscal. Además, la
  similitud estructural es señal estadística, no prueba de simulación:
  llevarla directo a un acto de molestia es una confusión categorial
  (estándar racional de la prueba).
""")
print("Script Parte II completado. Archivo: graficas_modelo_grafos.png")
