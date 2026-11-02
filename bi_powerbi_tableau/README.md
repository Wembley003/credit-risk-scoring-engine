---

## Executive Business Intelligence Module (`bi_powerbi_tableau/`)

This repository includes an executive BI calibration & governance layer for **Power BI** and **Tableau Desktop**:

* **`bi_powerbi_tableau/datasets_estrella/Fact_Scorecard_WoE_PSI_KS.csv`**: Star-schema table across FICO-style score bands (`300–850`), automated decision cutoffs, logit-calibrated $\text{PD}$, Kolmogorov-Smirnov ($\text{KS}$) separation, $\text{WoE}$/$\text{IV}$, and $\text{PSI}$ drift metrics.
* **`bi_powerbi_tableau/powerbi/Medidas_DAX_Scorecard_WoE_KS.dax`**: DAX measures for application-weighted $\text{PD}$, maximum $\text{KS}$ statistic, and automated $\text{PSI}$ model-drift diagnostics (`<0.10 Stable`, `0.10–0.25 Watch`, `>0.25 Recalibrate`).
* **`bi_powerbi_tableau/powerbi/Tema_Ejecutivo_Scorecard.json`**: Corporate Power BI JSON theme.
* **`bi_powerbi_tableau/tableau/Tablero_Calibracion_Scorecard_FICO.twb`**: Native Tableau workbook for score-to-PD calibration curves, KS/ROC discriminatory power, and PSI stability monitoring.
