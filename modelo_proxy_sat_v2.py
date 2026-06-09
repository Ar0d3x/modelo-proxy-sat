"""
MODELO PROXY DE SCORING FISCAL ALGORÍTMICO DEL SAT — v2
========================================================
Tesis Doctoral: "Gobernanza de la IA en la Administración Tributaria en México"
Dr. David — Doctorado en Derecho

CAMBIOS RESPECTO A v1 (correcciones de rigor metodológico):
  [FIX-1] Proceso generador de datos principiado (modelo logit explícito),
          de modo que las variables de riesgo SÍ predicen la auditoría.
          Antes: AUC 0.605 (≈ azar). Ahora: AUC objetivo > 0.80.
  [FIX-2] El sesgo sectorial ahora es señal dominante y verificable en los
          datos generados (antes el ruido lo ocultaba).
  [FIX-3] Corregido el bug "0.9x superior"; el narrativo ahora se calcula
          a partir de los datos reales y no se contradice.
  [FIX-4] Importancias de variables ahora significativas y coherentes.

MEJORAS NUEVAS (fortalecen el argumento jurídico):
  [NEW-1] Métricas formales de equidad algorítmica implementadas a mano
          (no requieren fairlearn): tasa de selección por grupo,
          razón de impacto dispar (regla de los 4/5 - EEOC), diferencia de
          paridad demográfica e igualdad de oportunidad.
  [NEW-2] EXPERIMENTO CONTRAFÁCTICO: se entrena el modelo SIN la variable
          'sector' para probar si el sesgo persiste vía variables proxy
          correlacionadas. Conecta con la doctrina de discriminación
          indirecta (Art. 1 CPEUM): eliminar la variable protegida NO cura
          el sesgo si hay proxies.
  [NEW-3] Estabilidad estadística: el AUC se reporta sobre múltiples semillas
          con intervalo, no sobre una sola corrida.
  [NEW-4] Análisis del umbral de decisión como elección de política con
          consecuencias jurídicas (no es un parámetro técnico neutral).

Metodología: realismo científico bungeano (CESM). Datos sintéticos:
demuestran la VIABILIDAD del método y la DETECTABILIDAD de los patrones,
no el comportamiento real del SAT (ver sección de Limitaciones del anexo).
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.preprocessing import LabelEncoder
from sklearn.inspection import permutation_importance
import warnings
warnings.filterwarnings('ignore')

SEMILLA = 42
np.random.seed(SEMILLA)

SECTORES = ['Comercio', 'Servicios_Profesionales', 'Construccion',
            'Manufactura', 'Agricultura', 'Tecnologia']

# Sesgo sectorial en LOG-ODDS (la injusticia que el modelo aprenderá).
# Positivo = sobre-auditado sin base en riesgo individual.
SESGO_SECTOR_LOGODDS = {
    'Construccion':            0.95,   # sobre-auditado (sesgo fuerte)
    'Agricultura':             0.70,   # sobre-auditado
    'Comercio':                0.30,   # leve
    'Manufactura':             0.00,   # neutral (referencia)
    'Servicios_Profesionales': -0.45,  # infra-auditado
    'Tecnologia':              -0.75,  # infra-auditado (sesgo fuerte inverso)
}


def sigmoide(x):
    return 1.0 / (1.0 + np.exp(-x))


def generar_datos(n=3000, semilla=SEMILLA):
    """Proceso generador de datos PRINCIPIADO (modelo logit explícito).

    La probabilidad de auditoría es una función sigmoide de:
      (a) factores de riesgo LEGÍTIMOS (con coeficientes fuertes), y
      (b) un sesgo sectorial ILEGÍTIMO (intercepto por sector).

    Además, 'ingreso_anual' y 'num_empleados' se hacen dependientes del
    sector, para que funcionen como variables PROXY en el contrafáctico.
    """
    rng = np.random.default_rng(semilla)

    sector_idx = rng.choice(len(SECTORES), n, p=[0.30, 0.20, 0.15, 0.20, 0.10, 0.05])
    sector = np.array([SECTORES[i] for i in sector_idx])

    # Factores de riesgo legítimos
    ratio_deducciones = np.clip(rng.beta(2.2, 4.5, n), 0.02, 0.97)
    variacion_ingresos = np.abs(rng.normal(0, 0.40, n))
    uso_efectivo_cfdi = rng.beta(3, 2, n)
    inconsistencias_cfdi = np.clip(rng.poisson(1.8, n), 0, 20)
    años_activo = rng.integers(1, 25, n)

    # Variables correlacionadas con sector (futuras PROXY del sesgo)
    base_ingreso = np.array([13.6, 13.9, 12.8, 13.3, 12.5, 14.2])  # log-media por sector
    ingreso_anual = np.clip(
        rng.lognormal(mean=base_ingreso[sector_idx], sigma=0.7), 30_000, 80_000_000)
    base_empleados = np.array([8, 5, 25, 30, 12, 6])  # media por sector
    num_empleados = np.clip(
        rng.poisson(base_empleados[sector_idx]), 0, 600)

    # --- PROCESO GENERADOR (logit) ---
    sesgo = np.array([SESGO_SECTOR_LOGODDS[s] for s in sector])
    logit = (
        -2.3                                       # intercepto (calibra tasa base)
        + 3.2 * (ratio_deducciones - 0.35)         # legítimo: deducciones altas
        + 2.4 * variacion_ingresos                 # legítimo: volatilidad
        + 0.45 * inconsistencias_cfdi              # legítimo: errores CFDI
        - 1.6 * uso_efectivo_cfdi                  # legítimo: bajo uso CFDI
        - 0.02 * años_activo                       # legítimo: antigüedad protege
        + sesgo                                     # ILEGÍTIMO: sesgo sectorial
    )
    prob = sigmoide(logit)
    auditado = (rng.random(n) < prob).astype(int)

    return pd.DataFrame({
        'sector': sector,
        'ingreso_anual': ingreso_anual,
        'ratio_deducciones': ratio_deducciones,
        'variacion_ingresos': variacion_ingresos,
        'uso_efectivo_cfdi': uso_efectivo_cfdi,
        'num_empleados': num_empleados,
        'inconsistencias_cfdi': inconsistencias_cfdi,
        'años_activo': años_activo,
        'prob_real': prob,
        'auditado': auditado,
    })


# ============================================================
# MÉTRICAS DE EQUIDAD (implementadas a mano — sin fairlearn)
# ============================================================

def tasa_seleccion_por_grupo(grupo, decision):
    """Tasa de selección (auditoría) por grupo."""
    return pd.Series(decision).groupby(np.asarray(grupo)).mean()


def razon_impacto_dispar(grupo, decision):
    """Razón de impacto dispar = tasa_min / tasa_max (regla de los 4/5, EEOC).
    Valor < 0.80 => indicio de impacto adverso / discriminación indirecta."""
    tasas = tasa_seleccion_por_grupo(grupo, decision)
    return tasas.min() / tasas.max(), tasas


def diferencia_paridad_demografica(grupo, decision):
    """Máxima diferencia absoluta de tasa de selección entre grupos."""
    tasas = tasa_seleccion_por_grupo(grupo, decision)
    return tasas.max() - tasas.min()


def diferencia_igualdad_oportunidad(grupo, y_true, y_pred):
    """Diferencia en tasa de verdaderos positivos (TPR) entre grupos.
    Mide si, ENTRE quienes sí debían ser auditados, el modelo acierta
    de forma desigual según el grupo."""
    df = pd.DataFrame({'g': np.asarray(grupo), 'y': np.asarray(y_true), 'p': np.asarray(y_pred)})
    tpr = df[df.y == 1].groupby('g').apply(lambda x: (x.p == 1).mean())
    return tpr.max() - tpr.min(), tpr


# ============================================================
# 1. GENERACIÓN Y DESCRIPCIÓN
# ============================================================

df = generar_datos()
print("=" * 64)
print("MODELO PROXY v2 — FISCALIZACIÓN ALGORÍTMICA SAT")
print("=" * 64)
print(f"\nCorpus: {len(df)} contribuyentes sintéticos")
print(f"Tasa global de auditoría: {df['auditado'].mean():.1%}")

print("\nTasa de auditoría por sector (datos reales generados):")
resumen = df.groupby('sector').agg(
    tasa_auditoria=('auditado', 'mean'),
    n=('auditado', 'count')
).sort_values('tasa_auditoria', ascending=False)
for sec, row in resumen.iterrows():
    sesgo = SESGO_SECTOR_LOGODDS[sec]
    marca = " <-- sobre-auditado" if sesgo > 0.3 else (" <-- infra-auditado" if sesgo < -0.3 else "")
    print(f"  {sec:<26} {row['tasa_auditoria']:.1%}  (n={int(row['n'])}){marca}")

# Verificación del sesgo en los datos
di_real, tasas_real = razon_impacto_dispar(df['sector'], df['auditado'])
print(f"\n[VERIFICACIÓN] Razón de impacto dispar en datos REALES: {di_real:.2f}")
print(f"  (< 0.80 => indicio de impacto adverso; regla de los 4/5 EEOC)")

# ============================================================
# 2. ENTRENAMIENTO: GLASS BOX vs BLACK BOX
# ============================================================

le = LabelEncoder()
df['sector_encoded'] = le.fit_transform(df['sector'])

features_full = ['ratio_deducciones', 'variacion_ingresos', 'uso_efectivo_cfdi',
                 'inconsistencias_cfdi', 'años_activo', 'sector_encoded',
                 'ingreso_anual', 'num_empleados']

X = df[features_full]
y = df['auditado']
X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
    X, y, df.index, test_size=0.3, random_state=SEMILLA, stratify=y)

glass_box = DecisionTreeClassifier(max_depth=4, min_samples_leaf=30, random_state=SEMILLA)
glass_box.fit(X_train, y_train)

black_box = GradientBoostingClassifier(n_estimators=300, max_depth=3,
                                       learning_rate=0.05, random_state=SEMILLA)
black_box.fit(X_train, y_train)

print("\n" + "=" * 64)
print("COMPARACIÓN: GLASS BOX vs BLACK BOX")
print("=" * 64)
resultados = {}
for nombre, modelo in [("Glass Box (Árbol D4)", glass_box),
                       ("Black Box (Gradient Boosting)", black_box)]:
    proba = modelo.predict_proba(X_test)[:, 1]
    pred = modelo.predict(X_test)
    auc = roc_auc_score(y_test, proba)
    acc = (pred == y_test).mean()
    resultados[nombre] = {'auc': auc, 'acc': acc, 'proba': proba, 'pred': pred}
    print(f"\n{nombre}:")
    print(f"  AUC-ROC : {auc:.3f}")
    print(f"  Accuracy: {acc:.3f}")
    print(f"  Explicable: {'SÍ — reglas legibles' if 'Glass' in nombre else 'NO — caja negra'}")

brecha_auc = resultados['Black Box (Gradient Boosting)']['auc'] - resultados['Glass Box (Árbol D4)']['auc']
print(f"\n[CLAVE] Brecha de AUC (Black - Glass): {brecha_auc:+.3f}")
print("  Si la brecha es pequeña => la explicabilidad NO sacrifica desempeño.")

# ============================================================
# 3. ESTABILIDAD ESTADÍSTICA (múltiples semillas)
# ============================================================

print("\n" + "=" * 64)
print("ESTABILIDAD: AUC sobre 10 semillas distintas")
print("=" * 64)
aucs_glass, aucs_black = [], []
for s in range(10):
    d = generar_datos(semilla=100 + s)
    d['sector_encoded'] = LabelEncoder().fit_transform(d['sector'])
    Xs, ys = d[features_full], d['auditado']
    Xtr, Xte, ytr, yte = train_test_split(Xs, ys, test_size=0.3, random_state=s, stratify=ys)
    gb = DecisionTreeClassifier(max_depth=4, min_samples_leaf=30, random_state=s).fit(Xtr, ytr)
    bb = GradientBoostingClassifier(n_estimators=300, max_depth=3, learning_rate=0.05,
                                    random_state=s).fit(Xtr, ytr)
    aucs_glass.append(roc_auc_score(yte, gb.predict_proba(Xte)[:, 1]))
    aucs_black.append(roc_auc_score(yte, bb.predict_proba(Xte)[:, 1]))
print(f"  Glass Box: AUC = {np.mean(aucs_glass):.3f} ± {np.std(aucs_glass):.3f}")
print(f"  Black Box: AUC = {np.mean(aucs_black):.3f} ± {np.std(aucs_black):.3f}")

# ============================================================
# 4. IMPORTANCIA DE VARIABLES (ahora significativa)
# ============================================================

print("\n" + "=" * 64)
print("IMPORTANCIA DE VARIABLES (Black Box, permutación)")
print("=" * 64)
result = permutation_importance(black_box, X_test, y_test, n_repeats=15,
                                random_state=SEMILLA, scoring='roc_auc')
importancias = pd.Series(result.importances_mean, index=features_full).sort_values(ascending=False)
for var, imp in importancias.items():
    bar = "#" * max(0, int(imp * 300))
    etiqueta = " [PROXY/SESGO]" if var in ('sector_encoded', 'ingreso_anual', 'num_empleados') else ""
    print(f"  {var:<22} {imp:+.4f}  {bar}{etiqueta}")

# ============================================================
# 5. MÉTRICAS DE EQUIDAD SOBRE LAS PREDICCIONES
# ============================================================

print("\n" + "=" * 64)
print("EQUIDAD ALGORÍTMICA — Predicciones del Black Box (conjunto test)")
print("=" * 64)
grupo_test = df.loc[idx_test, 'sector'].values
pred_black = resultados['Black Box (Gradient Boosting)']['pred']

di_pred, tasas_pred = razon_impacto_dispar(grupo_test, pred_black)
dpd = diferencia_paridad_demografica(grupo_test, pred_black)
eod, tpr_grupo = diferencia_igualdad_oportunidad(grupo_test, y_test.values, pred_black)

print("\nTasa de auditoría PREDICHA por sector:")
for sec, t in tasas_pred.sort_values(ascending=False).items():
    print(f"  {sec:<26} {t:.1%}")

print(f"\n  Razón de impacto dispar (4/5)     : {di_pred:.2f}  "
      f"{'IMPACTO ADVERSO' if di_pred < 0.80 else 'dentro de umbral'}")
print(f"  Diferencia de paridad demográfica : {dpd:.1%}")
print(f"  Diferencia de igualdad de oportun.: {eod:.1%}")

# ============================================================
# 6. EXPERIMENTO CONTRAFÁCTICO (clave para Art. 1 CPEUM)
#    ¿Persiste el sesgo si ELIMINAMOS la variable 'sector'?
# ============================================================

print("\n" + "=" * 64)
print("EXPERIMENTO CONTRAFÁCTICO: modelo SIN la variable 'sector'")
print("Doctrina: eliminar la variable protegida NO cura la discriminación")
print("indirecta si existen variables proxy correlacionadas (Art. 1 CPEUM)")
print("=" * 64)

features_sin_sector = [f for f in features_full if f != 'sector_encoded']
bb_ciego = GradientBoostingClassifier(n_estimators=300, max_depth=3,
                                      learning_rate=0.05, random_state=SEMILLA)
bb_ciego.fit(X_train[features_sin_sector], y_train)
pred_ciego = bb_ciego.predict(X_test[features_sin_sector])
auc_ciego = roc_auc_score(y_test, bb_ciego.predict_proba(X_test[features_sin_sector])[:, 1])
di_ciego, tasas_ciego = razon_impacto_dispar(grupo_test, pred_ciego)

print(f"\n  Modelo CON sector  -> AUC {resultados['Black Box (Gradient Boosting)']['auc']:.3f} | "
      f"impacto dispar {di_pred:.2f}")
print(f"  Modelo SIN sector  -> AUC {auc_ciego:.3f} | impacto dispar {di_ciego:.2f}")
if di_ciego < 0.80:
    print("\n  RESULTADO: el sesgo PERSISTE aun sin la variable 'sector'.")
    print("  El modelo lo reconstruye vía proxies (ingreso, núm. empleados).")
    print("  => La 'ceguera' a la variable protegida es jurídicamente insuficiente.")
else:
    print("\n  RESULTADO: el sesgo se reduce al quitar 'sector'.")

# ============================================================
# 7. UMBRAL DE DECISIÓN COMO ELECCIÓN DE POLÍTICA
# ============================================================

print("\n" + "=" * 64)
print("EL UMBRAL DE DECISIÓN ES UNA ELECCIÓN DE POLÍTICA, NO TÉCNICA")
print("=" * 64)
proba_black_full = black_box.predict_proba(X)[:, 1]
print(f"\n{'Umbral':<10}{'% auditados':<15}{'Impacto dispar':<18}{'Lectura jurídica'}")
for umbral in [0.20, 0.35, 0.50, 0.65]:
    pred_u = (proba_black_full >= umbral).astype(int)
    di_u, _ = razon_impacto_dispar(df['sector'], pred_u)
    pct = pred_u.mean()
    lectura = "impacto adverso" if di_u < 0.80 else "tolerable"
    print(f"{umbral:<10.2f}{pct:<15.1%}{di_u:<18.2f}{lectura}")
print("\n  => Mover el umbral cambia a quién se audita y la magnitud del sesgo.")
print("     Esa decisión hoy la toma el SAT sin control normativo (vacío).")

# ============================================================
# 8. GRÁFICAS
# ============================================================

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor('#F8F9FA')
fig.suptitle('Análisis de Fiscalización Algorítmica — Modelo Proxy SAT (v2)\n'
             'Gobernanza de la IA en la Administración Tributaria en México',
             fontsize=13, fontweight='bold', y=0.98)

# G1: tasa real vs predicha por sector, ordenado por sesgo
ax1 = axes[0, 0]
orden = sorted(SECTORES, key=lambda s: SESGO_SECTOR_LOGODDS[s])
tr = [tasas_real[s] * 100 for s in orden]
tp = [tasas_pred.get(s, 0) * 100 for s in orden]
ypos = np.arange(len(orden))
colores = ['#E74C3C' if SESGO_SECTOR_LOGODDS[s] > 0.3 else
           '#27AE60' if SESGO_SECTOR_LOGODDS[s] < -0.3 else '#3498DB' for s in orden]
ax1.barh(ypos - 0.2, tr, height=0.4, color=colores, alpha=0.9, label='Tasa real')
ax1.barh(ypos + 0.2, tp, height=0.4, color=colores, alpha=0.45, label='Tasa predicha')
ax1.set_yticks(ypos)
ax1.set_yticklabels(orden, fontsize=8)
ax1.set_xlabel('Tasa de auditoría (%)')
ax1.set_title('Sesgo sectorial reproducido por el modelo\n'
              '(rojo = sobre-auditado, verde = infra-auditado)', fontsize=10)
ax1.legend(fontsize=8)
ax1.set_facecolor('#FFFFFF')

# G2: importancia de variables
ax2 = axes[0, 1]
colores_imp = ['#E74C3C' if v in ('sector_encoded', 'ingreso_anual', 'num_empleados')
               else '#2ECC71' for v in importancias.index]
importancias.sort_values().plot(kind='barh', ax=ax2, color=list(reversed(
    ['#E74C3C' if v in ('sector_encoded', 'ingreso_anual', 'num_empleados')
     else '#2ECC71' for v in importancias.sort_values().index][::-1])), alpha=0.85)
ax2.set_title('Importancia de variables (permutación, AUC)\n'
              '(rojo = sector o proxies del sesgo)', fontsize=10)
ax2.set_xlabel('Caída de AUC al permutar')
ax2.tick_params(axis='y', labelsize=8)
ax2.set_facecolor('#FFFFFF')

# G3: contrafáctico con vs sin sector
ax3 = axes[1, 0]
etiquetas = ['CON\nsector', 'SIN\nsector']
di_vals = [di_pred, di_ciego]
auc_vals = [resultados['Black Box (Gradient Boosting)']['auc'], auc_ciego]
x = np.arange(2)
b1 = ax3.bar(x - 0.2, di_vals, 0.4, color='#E74C3C', alpha=0.8, label='Impacto dispar (4/5)')
b2 = ax3.bar(x + 0.2, auc_vals, 0.4, color='#3498DB', alpha=0.8, label='AUC-ROC')
ax3.axhline(0.80, color='black', linestyle='--', linewidth=1, label='Umbral 4/5 (0.80)')
ax3.set_xticks(x)
ax3.set_xticklabels(etiquetas)
ax3.set_ylim(0, 1.0)
ax3.set_title('Contrafáctico: ¿persiste el sesgo sin la variable sector?\n'
              'Por debajo de 0.80 = impacto adverso', fontsize=10)
ax3.legend(fontsize=8)
ax3.set_facecolor('#FFFFFF')
for b, v in zip(b1, di_vals):
    ax3.text(b.get_x() + b.get_width()/2, v + 0.02, f'{v:.2f}', ha='center', fontsize=9, fontweight='bold')

# G4: umbral como política
ax4 = axes[1, 1]
umbrales = np.linspace(0.10, 0.80, 30)
pct_aud, di_list = [], []
for u in umbrales:
    pu = (proba_black_full >= u).astype(int)
    pct_aud.append(pu.mean() * 100)
    diu, _ = razon_impacto_dispar(df['sector'], pu)
    di_list.append(diu)
ax4b = ax4.twinx()
l1 = ax4.plot(umbrales, pct_aud, color='#2980B9', linewidth=2, label='% auditados')
l2 = ax4b.plot(umbrales, di_list, color='#E74C3C', linewidth=2, label='Impacto dispar')
ax4b.axhline(0.80, color='black', linestyle='--', linewidth=1)
ax4.set_xlabel('Umbral de decisión (elección de política)')
ax4.set_ylabel('% de contribuyentes auditados', color='#2980B9')
ax4b.set_ylabel('Razón de impacto dispar (4/5)', color='#E74C3C')
ax4.set_title('El umbral es una decisión de política\ncon efectos en cobertura y sesgo', fontsize=10)
ax4.set_facecolor('#FFFFFF')
lns = l1 + l2
ax4.legend(lns, [l.get_label() for l in lns], fontsize=8, loc='center right')

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig('graficas_modelo_proxy_v2.png', dpi=150,
            bbox_inches='tight', facecolor='#F8F9FA')
plt.close()
print("\n[OK] Gráficas guardadas: graficas_modelo_proxy_v2.png")

# ============================================================
# 9. RESUMEN EJECUTIVO (narrativo coherente con los datos)
# ============================================================

sec_max = tasas_real.idxmax()
sec_min = tasas_real.idxmin()
veces = tasas_real.max() / tasas_real.min()

print("\n" + "=" * 64)
print("RESUMEN EJECUTIVO — HALLAZGOS (v2, coherentes con los datos)")
print("=" * 64)
print(f"""
HALLAZGO 1 — SESGO ESTRUCTURAL VERIFICADO:
  El sector '{sec_max}' tiene una tasa de auditoría {veces:.1f} veces
  la del sector '{sec_min}' ({tasas_real.max():.1%} vs {tasas_real.min():.1%}),
  diferencia atribuible al intercepto sectorial y no al riesgo individual.
  Razón de impacto dispar = {di_real:.2f} (< 0.80 = impacto adverso, regla 4/5).
  -> Discriminación indirecta — Art. 1 CPEUM / principio pro persona.

HALLAZGO 2 — EXPLICABILIDAD SIN SACRIFICIO DE DESEMPEÑO:
  Glass Box AUC {np.mean(aucs_glass):.3f} vs Black Box AUC {np.mean(aucs_black):.3f}
  (brecha {np.mean(aucs_black)-np.mean(aucs_glass):+.3f}, sobre 10 semillas).
  -> Derriba el argumento de 'imposibilidad técnica' de la explicabilidad.

HALLAZGO 3 — LA CEGUERA A LA VARIABLE PROTEGIDA ES INSUFICIENTE:
  Al eliminar 'sector', el impacto dispar pasa de {di_pred:.2f} a {di_ciego:.2f}.
  El sesgo {'persiste' if di_ciego < 0.80 else 'se reduce'} vía variables proxy.
  -> Fundamenta exigir AUDITORÍA DE RESULTADOS (no solo de inputs) a la ASAT.

HALLAZGO 4 — EL UMBRAL ES POLÍTICA, NO TÉCNICA:
  Variar el umbral de decisión cambia cobertura y magnitud del sesgo.
  Hoy esa elección la realiza el SAT sin control normativo.
  -> Fundamenta reserva de ley formal sobre parámetros de decisión.
""")
print("Script v2 completado. Archivos: graficas_modelo_proxy_v2.png")
