# Modelo Proxy de Fiscalización Algorítmica del SAT

**Anexo técnico de la tesis doctoral:** *Gobernanza de la IA en la Administración Tributaria en México*

[![DOI](https://zenodo.org/badge/DOI/PENDIENTE.svg)](https://doi.org/PENDIENTE)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)

> Reemplaza `PENDIENTE` por el DOI que Zenodo asigne al publicar (ver sección *Cómo depositar en Zenodo*).

---

## Resumen

Este repositorio reúne el material empírico que ancla el argumento normativo de la tesis. Combina **dos modelos proxy con datos sintéticos** —que reproducen los *mecanismos* de la fiscalización algorítmica (scoring de riesgo individual y detección por grafos)— con un **análisis de datos reales y públicos del SAT** —que mide los *resultados* del procedimiento del artículo 69-B—. Mecanismo y resultado se sostienen mutuamente, conforme a la disciplina empírica del realismo bungeano.

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

- `Listado_completo_69-B.csv` — listado público del SAT (art. 69-B CFF), datos al 30 de abril de 2026.
- `CSDsinefectos.csv` — listado público de Certificados de Sello Digital sin efectos (art. 17-H CFF).
- `DOF_4to_parr.pdf` — listado global definitivo, DOF 5-jun-2026 (código 5789646).
- `DOF_presuncion_69b_5jun26.pdf` — listado global de presunción, DOF 5-jun-2026 (código 5789645).

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

## Cómo depositar en Zenodo

> La forma más simple de no olvidar ningún archivo es subir **todo el repositorio**. Si lo descargaste como `modelo-proxy-sat.zip`, descomprímelo y sube la carpeta completa (cualquiera de las dos opciones de abajo lo hace).

### Opción A — Carga manual (rápida)

1. Crea una cuenta en [zenodo.org](https://zenodo.org).
2. *New upload* → arrastra **todos** los archivos del repositorio:

   **Scripts (3):** `modelo_proxy_sat_v2.py`, `modelo_proxy_grafos.py`, `analisis_69b.py`
   **Anexos Word (3):** `Anexo_I_Modelo_Proxy_v3.docx`, `Anexo_II_Analitica_Grafos_v2.docx`, `Anexo_III_Datos_Empiricos_v2.docx`
   **Gráficas (5):** `graficas_modelo_proxy_v2.png`, `graficas_modelo_grafos.png`, `graficas_69b.png`, `graficas_69b_csd.png`
   **Datos reales del SAT (carpeta `datos/`):** `Listado_completo_69-B.csv`, `CSDsinefectos.csv`, `DOF_4to_parr.pdf`, `DOF_presuncion_69b_5jun26.pdf`
   **Metadatos y soporte:** `README.md`, `requirements.txt`, `LICENSE`, `CITATION.cff`, `.zenodo.json`

3. Completa los metadatos (Zenodo puede pre-cargar parte desde `.zenodo.json` y `CITATION.cff`).
4. *Publish* → Zenodo acuña el **DOI** de inmediato.

> Zenodo conserva la estructura de carpetas, así que la subcarpeta `datos/` se preserva. Si la interfaz no permite arrastrar carpetas, súbela comprimida (`datos.zip`) o sube todo el repositorio como un único `.zip`.

### Opción B — Integración GitHub ↔ Zenodo (recomendada para tu flujo)

Aprovecha tu uso de GitHub y self-hosting. Archiva el repositorio **completo** (los tres scripts, los tres anexos, las cinco gráficas y la carpeta `datos/`) en un solo paso:

1. Sube el repositorio a GitHub (ver *Publicar en GitHub* más abajo).
2. En Zenodo → *Settings* → *GitHub* → activa el repositorio (toggle ON).
3. En GitHub, crea un *Release*. Como el repositorio ya integra las tres partes (no solo el modelo tabular v2), usa una etiqueta que lo refleje, p. ej. **`v3.0.0`** ("modelo tabular + grafos + datos reales del 69-B").
4. Zenodo archiva automáticamente ese release \u2014con todo su contenido, incluida la carpeta `datos/`\u2014 y acuña un DOI versionado.

> **DOI de concepto vs. de versión:** Zenodo genera un *concept DOI* (siempre apunta a la última versión, ideal para citar en la tesis) y un *version DOI* por cada release. Cita el **concept DOI** en el cuerpo de la tesis.

> **Sobre el tamaño:** la carpeta `datos/` pesa ~14 MB (los CSV del SAT y los dos PDF del DOF). Está muy por debajo del límite de Zenodo (50 GB por depósito), así que puede publicarse sin problema. Si prefieres un repositorio más ligero en GitHub, puedes excluir los CSV grandes ahí y subirlos solo a Zenodo; pero incluirlos en ambos es lo más reproducible.

Una vez publicado, reemplaza `PENDIENTE` (en la insignia del DOI al inicio, en este texto y en la propuesta de cita) por el DOI real que asigne Zenodo.

---

## Publicar en GitHub

Comandos para subir el repositorio firmando los commits con tu llave GPG (`969C0614`):

```bash
cd modelo-proxy-sat
git init
git add .

# Firmar los commits con tu llave GPG
git config user.signingkey 969C0614
git config commit.gpgsign true

git commit -S -m "Anexo técnico: proxy tabular + grafos + análisis de datos reales del 69-B"
git branch -M main

# Crear el repositorio remoto y subirlo (requiere GitHub CLI)
gh repo create modelo-proxy-sat --public --source=. --remote=origin --push

# Crear el release que Zenodo archivará
git tag -s v3.0.0 -m "v3.0.0 — tres partes (tabular, grafos, datos reales)"
git push origin v3.0.0
```

Si no usas GitHub CLI (`gh`), crea el repositorio vacío en github.com y luego:

```bash
git remote add origin git@github.com:<usuario>/modelo-proxy-sat.git
git push -u origin main
git push origin v3.0.0
```

> Activa antes la integración en Zenodo (Opción B, paso 2) para que el release `v3.0.0` se archive y se acuñe el DOI de forma automática.

---

## Cómo citar

> Sustituye los campos entre corchetes por tus datos reales antes de publicar.

**APA 7 (software):**

> [Apellido], D. (2026). *Modelo proxy de fiscalización algorítmica del SAT: Anexo técnico de la tesis "Gobernanza de la IA en la Administración Tributaria en México"* (Versión 3.0.0) [Software]. Zenodo. https://doi.org/[DOI]

**En el cuerpo de la tesis (cita en texto):** ([Apellido], 2026).

Véase también el archivo [`CITATION.cff`](CITATION.cff) para metadatos de cita legibles por máquina.

---

## Licencia

Código distribuido bajo licencia [MIT](LICENSE). Si prefieres una licencia copyleft (GPL-3.0) o una licencia Creative Commons (CC-BY-4.0) para el conjunto del depósito, puedes sustituir el archivo `LICENSE` antes de publicar.

---

## Reconocimiento metodológico

Inspirado en el realismo científico de Mario Bunge (modelo CESM: Composición–Entorno–Estructura–Mecanismo). Las métricas de equidad siguen estándares de la literatura *Fairness in Machine Learning* (Barocas, Hardt & Narayanan, 2023) y la *four-fifths rule* (EEOC, 1978).
