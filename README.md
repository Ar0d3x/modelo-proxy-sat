# Modelo Proxy de Fiscalización Algorítmica del SAT

**Anexo técnico de la tesis doctoral:** *Gobernanza de la IA en la Administración Tributaria en México*

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20617924.svg)](https://doi.org/10.5281/zenodo.20617924)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)

---

## Resumen

Este repositorio reúne el material empírico que ancla el argumento normativo de la tesis. Combina **dos modelos proxy con datos sintéticos** —que reproducen los *mecanismos* de la fiscalización algorítmica (scoring de riesgo individual y detección por grafos) con un **análisis de datos reales y públicos del SAT** que mide los *resultados* del procedimiento del artículo 69-B. Mecanismo y resultado se sostienen mutuamente.

Las técnicas de explicabilidad (XAI) y de equidad algorítmica aplicadas en el modelo tabular (Parte I) demuestran cuatro proposiciones que sostienen el argumento normativo de la tesis:

| | Proposición | Cómo se demuestra |
|---|---|---|
| **P1** | La fiscalización algorítmica puede ser explicable sin sacrificar desempeño | Glass Box (árbol) alcanza un AUC cercano al Black Box (gradient boosting); brecha ≈ 0.06 estable sobre 10 semillas |
| **P2** | La opacidad es una elección, no una necesidad técnica | Igual desempeño en modalidad explicable y opaca |
| **P3** | El sesgo algorítmico es estructural, medible y persistente | Razón de impacto dispar = 0.37 (regla de los 4/5); persiste aun eliminando la variable de sector |
| **P4** | Las obligaciones normativas propuestas son operacionalizables | Métricas de equidad, monotonicidad y umbral definidas como criterios verificables para la ASAT |

> **Marco metodológico:** realismo científico bungeano (modelo CESM). Toda afirmación normativa de la tesis se ancla a una proposición empírica reproducible.

---

## Advertencia sobre los datos

El repositorio usa **dos tipos de datos**, con alcances distintos:

- **Partes I y II (datos sintéticos):** generados mediante un proceso logit explícito con semilla fija. **No** miden el comportamiento real del SAT, cuyos microdatos de scoring no son de acceso público —circunstancia que, en sí misma, ilustra el problema de opacidad que la tesis denuncia. Demuestran la **viabilidad** de la auditoría algorítmica y la **detectabilidad** de los patrones de sesgo con herramientas estándar.
- **Parte III (datos reales y públicos):** el listado del artículo 69-B y el de Certificados de Sello Digital sin efectos, ambos de carácter público conforme al CFF. Sí miden un resultado real del procedimiento (tasa de revocación, vía de corrección, impacto de la cancelación de sellos).

La medición empírica del *sistema de scoring* real seguiría requiriendo acceso a los datos internos del SAT, acceso que la reforma propuesta busca habilitar para la Agencia Supervisora de Algoritmos Tributarios (ASAT).

---

## Requisitos

- Python 3.11 o superior
- Dependencias en [`requirements.txt`](requirements.txt)

```bash
pip install -r requirements.txt
```

## El anexo tiene tres partes

| | Modelo / análisis | Pregunta que responde | Datos |
|---|---|---|---|
| **Parte I** | `modelo_proxy_sat_v2.py` (tabular) | ¿Qué *hiciste*? Scoring de riesgo individual y sesgo | Sintéticos |
| **Parte II** | `modelo_proxy_grafos.py` (grafos) | ¿Con *quién* te relacionaste? Culpabilidad por asociación | Sintéticos |
| **Parte III** | `analisis_69b.py` (datos reales) | ¿Qué pasa en los *hechos*? Tasa de revocación del 69-B | **Reales (SAT)** |

Las Partes I y II demuestran *mecanismos* con datos sintéticos; la Parte III mide un *resultado* observable con datos reales y públicos del SAT. Mecanismo + resultado se sostienen mutuamente (anclaje empírico bungeano).

## Ejecución

```bash
python3 modelo_proxy_sat_v2.py     # Parte I — modelo tabular
python3 modelo_proxy_grafos.py     # Parte II — analítica de grafos
python3 analisis_69b.py            # Parte III — datos reales del 69-B
```

Las Partes I y II son **deterministas** (semilla fija = 42). La Parte III lee `datos/Listado_completo_69-B.csv` (listado público del SAT, al 30 de abril de 2026).

## Salidas

Cada script imprime sus resultados y genera su panel de gráficas:

- `graficas_modelo_proxy_v2.png` (Parte I): sesgo sectorial, importancia de variables, contrafáctico de sector, umbral como política.
- `graficas_modelo_grafos.png` (Parte II): subred de CFDI, puntaje por tipo, contrafáctico de una factura, contagio por distancia.
- `graficas_69b.png` (Parte III): situación del listado (14,244 RFC únicos), desenlace de presunciones (14.7% revocadas), evolución anual, vía de revocación (judicial vs administrativa).
- `graficas_69b_csd.png` (Parte III): cruce con Certificados de Sello Digital (art. 17-H) — 539 con sello cancelado, de los cuales 175 no son EFOS firmes.

## Datos (carpeta `datos/`)

- `Listado_completo_69-B.csv` - listado público del SAT (art. 69-B CFF), datos al 30 de abril de 2026.
- `CSDsinefectos.csv` - listado público de Certificados de Sello Digital sin efectos (art. 17-H CFF).
- `DOF_4to_parr.pdf` - listado global definitivo, DOF 5-jun-2026 (código 5789646).
- `DOF_presuncion_69b_5jun26.pdf` - listado global de presunción, DOF 5-jun-2026 (código 5789645).

> Son datos de carácter público conforme al artículo 69-B del CFF. Se incluyen para reproducibilidad; la fuente primaria es el Portal del SAT y el DOF.

---

## Estructura del modelo

```
modelo_proxy_sat_v2.py
├── generar_datos()                      # proceso generador logit (datos sintéticos)
├── Métricas de equidad (sin fairlearn):
│   ├── tasa_seleccion_por_grupo()
│   ├── razon_impacto_dispar()           # regla de los 4/5 (EEOC)
│   ├── diferencia_paridad_demografica()
│   └── diferencia_igualdad_oportunidad()
├── Glass Box (DecisionTreeClassifier)   # modelo explicable
├── Black Box (GradientBoostingClassifier) # modelo opaco
├── Estabilidad sobre 10 semillas
├── Importancia de variables (permutación)
├── Experimento contrafáctico (sin variable de sector)
└── Análisis del umbral de decisión
```

---

## Cómo citar

**APA 7 (software):**

> Nieto Olvera, P. D. (2026). *Modelo proxy de fiscalización algorítmica del SAT: Anexo técnico de la tesis "Gobernanza de la IA en la Administración Tributaria en México"* (Versión 3.0.0) [Software]. Zenodo. https://doi.org/10.5281/zenodo.20617924

**En el cuerpo de la tesis (cita en texto):** (Nieto Olvera, 2026).

Véase también el archivo [`CITATION.cff`](CITATION.cff) para metadatos de cita legibles por máquina.

---

## Licencia

Código distribuido bajo licencia [MIT](LICENSE). 
---
