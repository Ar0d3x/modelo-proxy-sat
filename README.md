# Modelo Proxy de Fiscalización Algorítmica del SAT

**Anexo técnico de la tesis doctoral:** *Gobernanza de la IA en la Administración Tributaria en México*

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20617924.svg)](https://doi.org/10.5281/zenodo.20617924)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)


## 🔬 Proyecto de investigación

Este anexo forma parte del proyecto de investigación doctoral registrado en el **Open Science Framework (OSF)**:

> **Gobernanza de la IA en la Administración Tributaria en México**  
> 📂 OSF: https://osf.io/cxwjt  
> 🆔 DOI: [10.17605/OSF.IO/CXWJT](https://doi.org/10.17605/OSF.IO/CXWJT)

Ecosistema completo de la investigación:

| Componente | Plataforma | Enlace |
|---|---|---|
| Proyecto de investigación | OSF | [osf.io/cxwjt](https://osf.io/cxwjt) |
| Anexo técnico (este repo) | Zenodo + GitHub | [DOI](https://doi.org/10.5281/zenodo.20617924) |
| Tracker EFOS/EDOS en vivo | GitHub | [sat-efos-tracker](https://github.com/Ar0d3x/sat-efos-tracker) |
| Análisis del listado 69-B | GitHub | [Analisis_Contribuyentes_69B_SAT](https://github.com/Ar0d3x/Analisis_Contribuyentes_69B_SAT) |

---
---

## Resumen

Este repositorio reúne el material empírico que ancla el argumento normativo de la tesis. Combina **dos modelos proxy con datos sintéticos** que reproducen los *mecanismos* de la fiscalización algorítmica (scoring de riesgo individual y detección por grafos) con un **análisis de datos reales y públicos del SAT** que mide los *resultados* del procedimiento del artículo 69-B. Mecanismo y resultado se sostienen mutuamente.

Las técnicas de explicabilidad (XAI) y de equidad algorítmica aplicadas en el modelo tabular (Parte I) demuestran cuatro proposiciones que sostienen el argumento normativo de la tesis:

| | Proposición | Cómo se demuestra |
|---|---|---|
| **P1** | La fiscalización algorítmica puede ser explicable sin sacrificar desempeño | Glass Box (árbol) alcanza un AUC cercano al Black Box (gradient boosting); brecha ≈ 0.06 estable sobre 10 semillas |
| **P2** | La opacidad es una elección, no una necesidad técnica | Igual desempeño en modalidad explicable y opaca |
| **P3** | El sesgo algorítmico es estructural, medible y persistente | Razón de impacto dispar = 0.37 (regla de los 4/5); persiste aun eliminando la variable de sector |
| **P4** | Las obligaciones normativas propuestas son operacionalizables | Métricas de equidad, monotonicidad y umbral definidas como criterios verificables para la ASAT |

> **Marco metodológico:** Modelo CESM. Toda afirmación normativa de la tesis se ancla a una proposición empírica reproducible.

---

## Advertencia sobre los datos

El repositorio usa **dos tipos de datos**, con alcances distintos:

- **Partes I y II (datos sintéticos):** generados mediante un proceso logit explícito con semilla fija. **No** miden el comportamiento real del SAT, cuyos microdatos de scoring no son de acceso público, circunstancia que, en sí misma, ilustra el problema de opacidad que la tesis señala. Demuestran la **viabilidad** de la auditoría algorítmica y la **detectabilidad** de los patrones de sesgo con herramientas estándar.
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

### Archivos incluidos en el repositorio (reproducibilidad)

Estos archivos son el **corte acumulado al 30 de abril de 2026** que sustenta los resultados citados en la tesis (14,244 RFC únicos):

- `Listado_completo_69-B.csv` — listado público **acumulado** del SAT (art. 69-B CFF). 14,424 filas / 14,244 RFC únicos tras des-duplicar (`keep='last'`).
- `CSDsinefectos.csv` — listado público de Certificados de Sello Digital sin efectos (art. 17-H CFF).

> ⚠️ **Snapshot histórico.** El SAT solo publica el listado *vigente*, no versiones anteriores. Estos archivos se incluyen para garantizar la reproducibilidad exacta de los números de la tesis; el listado en línea del SAT diferirá de este corte porque se actualiza de forma continua.

### Acumulado (SAT) vs. incremental (DOF)

Es clave distinguir dos cosas que **no son equivalentes**:

- **El CSV del SAT es acumulado:** contiene a *todos* los contribuyentes en cada situación a una fecha de corte. Es la "foto completa" al 30-abr-2026.
- **Los oficios del DOF son incrementales:** cada publicación agrega *únicamente* los contribuyentes nuevos de ese acto; no reproduce el acumulado. El listado completo es la suma histórica de todas las publicaciones incrementales del DOF.

**La fuente con validez jurídica es el DOF.** El portal de datos abiertos del SAT ([contribuyentes_publicados](https://www.sat.gob.mx/minisitio/DatosAbiertos/contribuyentes_publicados.html)) es una referencia operativa consolidada que puede diferir del Diario Oficial.

### Oficios incrementales de referencia (DOF 5-jun-2026)

Publicaciones incrementales posteriores al corte de datos del anexo, citadas como ejemplo del procedimiento del art. 69-B:

| Oficio | Etapa | Fecha oficio | Contrib. | DOF |
|---|---|---|---|---|
| 500-05-2026-11484 | Presunción (párr. 1°) | 08-abr-2026 | 64 | [nota 5789645](https://dof.gob.mx/nota_detalle.php?codigo=5789645&fecha=05/06/2026) |
| 500-05-00-00-00-2026-11587 | Definitivo — no aportaron pruebas (párr. 4°) | 15-abr-2026 | 89 | [nota 5789646](https://dof.gob.mx/nota_detalle.php?codigo=5789646&fecha=05/06/2026) |
| 500-05-00-00-00-2026-15917 | Definitivo — aportaron pero no desvirtuaron (párr. 4°) | 24-abr-2026 | 26 | [nota 5789647](https://dof.gob.mx/nota_detalle.php?codigo=5789647&fecha=05/06/2026) |

### Los plazos del procedimiento (según los propios oficios y criterios)

El art. 69-B CFF distingue plazos que conviene no confundir:

* **15 días hábiles** — para que el presunto EFOS aporte pruebas y desvirtúe, contados desde que surte efectos la última notificación (párr. 2°).
* **50 días hábiles** — plazo perentorio para que la autoridad valore las pruebas y notifique la resolución definitiva; si el SAT no lo hace en este tiempo, la presunción queda sin efectos (párr. 4°).
* **40 días hábiles** — plazo para que el contribuyente presente su aclaración (Regla 2.2.4 de la RMF 2026) ante una restricción provisional preventiva de su Certificado de Sello Digital (Art. 17-H Bis CFF).
* **30 días hábiles** — plazo mínimo que la autoridad debe esperar tras notificar la resolución definitiva antes de publicar el listado (párr. 4°).
* **30 días** — para que el EDOS (quien dedujo los comprobantes) acredite materialidad o corrija su situación mediante la Ficha de trámite 83/CFF (Regla 2.9.18). El criterio sustantivo 8/2018/CTN/CS-SASEN de Prodecon señala como uno de los momentos para desvirtuar los 30 días siguientes a la publicación del listado definitivo (párr. 5°). - Ver nota relevante -
* **10 días hábiles (+10 de prórroga)** — plazo con el que cuenta el EDOS para desahogar requerimientos de información o documentación adicional que la autoridad emita para resolver el caso. La prórroga se debe solicitar dentro de los 10 días iniciales (Regla 2.9.18, párr. 2°).
* **30 días hábiles** — plazo máximo con el que cuenta la autoridad para dictar la resolución definitiva del EDOS, contados a partir de que se presenta la solicitud de aclaración o se tiene por cumplido el requerimiento adicional (Regla 2.9.18, párr. 4°).

> **Nota relevante:** el amparo en revisión 165/2023 del Primer Tribunal Colegiado en Materia Administrativa del Decimosexto Circuito, resolvió que el cómputo de esos 30 días para el EDOS debe iniciar a partir del día siguiente en que surte efectos la notificación personal al contribuyente afectado —no de la mera publicación del listado en el DOF—, en observancia a la garantía de audiencia del artículo 14 constitucional, pues la publicación no genera certeza de un emplazamiento real.

> Datos de carácter público conforme al art. 69-B del CFF. La fuente primaria y jurídicamente válida es el DOF; el portal del SAT es referencia operativa que puede diferir.

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
## Referencias técnicas

El encuadre de las técnicas reproducidas en este anexo se apoya en la literatura de referencia de cada campo:

- **Parte I (modelo tabular):** equidad algorítmica y explicabilidad (XAI) sobre datos estructurados; la razón de impacto dispar (regla de los 4/5) sigue el criterio de la EEOC.
- **Parte II (analítica de grafos):** detección de anomalías y fraude sobre grafos (*graph-based anomaly detection*). El análisis estructural de redes tiene su formulación en Wasserman y Faust (1994). El fenómeno de *culpabilidad por asociación* (*guilt-by-association*) que el modelo reproduce (la propagación de la señal de riesgo a través de los enlaces, con independencia de la conducta individual del nodo) está documentado como propiedad estructural del método en Akoglu et al. (2015). Cuando estas técnicas incorporan aprendizaje sobre la topología de la red, se inscriben en las Redes Neuronales de Grafos (*Graph Neural Networks*, GNN), subcategoría del aprendizaje profundo sistematizada en Wu et al. (2021).

> El SAT ha confirmado públicamente el uso de "analítica de grafos" y "análisis de redes", pero no ha especificado el tipo del modo de empleo de arquitecturas GNN en particular. Este anexo reproduce el *tipo* de mecanismo, no un modelo concreto atribuido al SAT.

**Bibliografía técnica:**

- Akoglu, L., Tong, H., & Koutra, D. (2015). Graph based anomaly detection and description: A survey. *Data Mining and Knowledge Discovery, 29*(3), 626–688. https://doi.org/10.1007/s10618-014-0365-y
- Wasserman, S., & Faust, K. (1994). *Social network analysis: Methods and applications*. Cambridge University Press.
- Wu, Z., Pan, S., Chen, F., Long, G., Zhang, C., & Yu, P. S. (2021). A comprehensive survey on graph neural networks. *IEEE Transactions on Neural Networks and Learning Systems, 32*(1), 4–24. https://doi.org/10.1109/TNNLS.2020.2978386

---
---

## Cómo citar

**APA 7 (software):**

> Nieto Olvera, P.D. (2026). *Modelo proxy de fiscalización algorítmica del SAT: Anexo técnico de la tesis "Gobernanza de la IA en la Administración Tributaria en México"* (Versión 3.0.0) [Software]. Zenodo. https://doi.org/10.5281/zenodo.20617924

Véase también el archivo [`CITATION.cff`](CITATION.cff) para metadatos de cita legibles por máquina.

---

## Licencia

Distribuido bajo licencia [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE). 
---
