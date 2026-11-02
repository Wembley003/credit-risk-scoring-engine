# Credit Risk Assessment, IFRS 9 & Scoring Engine

**Author:** Wembley Emmanuel Ibarra Tepato ([github.com/Wembley003](https://github.com/Wembley003))  
**Focus:** Parametric Credit Scoring (FICO 300–850, PDO=40), WoE/IV Calibration, IFRS 9 / CNBV Staging, and Model Drift Monitoring (PSI, KS, Gini).

## Key Features
- **Scorecard Calibration**: Maps log-odds to a 300–850 point scale ($Base = 600$, $PDO = 40$, $Odds = 50:1$) with automated **Weight of Evidence (WoE)** and **Information Value (IV)** calculation.
- **IFRS 9 / NIIF 9 & CNBV Staging**: Classifies exposures into **Stage 1** (12-month ECL), **Stage 2** (Lifetime ECL upon Significant Increase in Credit Risk - SICR), and **Stage 3** (Default $\ge 90	ext{ DPD}$), computing $EL = PD 	imes LGD 	imes EAD$.
- **Model Governance & Validation**: Built-in **Kolmogorov-Smirnov (KS)**, **AUROC / Gini coefficient**, and **Population Stability Index (PSI)** drift detection.

## Quickstart
```bash
pip install -r requirements.txt
python -m src.credit_scoring_engine
pytest -v
```

---

## Executive Business Intelligence Module (`bi_powerbi_tableau/`)

This repository includes an executive BI calibration & governance layer for **Power BI** and **Tableau Desktop**:

* **`bi_powerbi_tableau/datasets_estrella/Fact_Scorecard_WoE_PSI_KS.csv`**: Star-schema table across FICO-style score bands (`300–850`), automated decision cutoffs, logit-calibrated $\text{PD}$, Kolmogorov-Smirnov ($\text{KS}$) separation, $\text{WoE}$/$\text{IV}$, and $\text{PSI}$ drift metrics.
* **`bi_powerbi_tableau/powerbi/Medidas_DAX_Scorecard_WoE_KS.dax`**: DAX measures for application-weighted $\text{PD}$, maximum $\text{KS}$ statistic, and automated $\text{PSI}$ model-drift diagnostics (`<0.10 Stable`, `0.10–0.25 Watch`, `>0.25 Recalibrate`).
* **`bi_powerbi_tableau/powerbi/Tema_Ejecutivo_Scorecard.json`**: Corporate Power BI JSON theme.
* **`bi_powerbi_tableau/tableau/Tablero_Calibracion_Scorecard_FICO.twb`**: Native Tableau workbook for score-to-PD calibration curves, KS/ROC discriminatory power, and PSI stability monitoring.
