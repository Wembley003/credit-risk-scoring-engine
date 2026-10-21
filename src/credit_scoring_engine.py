"""
Credit Risk Assessment, WoE/IV Scorecard Calibration, IFRS 9 Staging & Model Governance (PSI, KS, Gini).
Aligned with CNBV CUB & IFRS 9 Expected Credit Loss (ECL) standards.
Author: Wembley Emmanuel Ibarra Tepato
"""
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Tuple


class CreditScoringEngine:
    """
    Parametric FICO-like Scorecard (300-850 scale, Base=600, PDO=40) with:
    - Weight of Evidence (WoE) & Information Value (IV) feature power calculation
    - IFRS 9 3-Stage classification (12m vs Lifetime ECL = PD * LGD * EAD)
    - Discriminatory & stability validation: Kolmogorov-Smirnov (KS), Gini/AUROC, and PSI
    """

    def __init__(self, base_score: float = 600.0, target_odds: float = 10.0, pdo: float = 40.0):
        self.base_score = base_score
        self.target_odds = target_odds
        self.pdo = pdo
        self.factor = pdo / np.log(2.0)
        self.offset = base_score - self.factor * np.log(target_odds)

    def evaluate_applicant(self, data: dict) -> dict:
        monthly_income = float(data.get("ingreso_mensual_neto", 0.0))
        requested_amount = float(data.get("monto_solicitado", 0.0))
        term_months = int(data.get("plazo_meses", 12))
        existing_debts = float(data.get("deudas_actuales_mensuales", 0.0))
        historical_delinquency_days = int(data.get("max_dias_mora_historica", 0))
        credit_history_months = int(data.get("antiguedad_crediticia_meses", 0))
        employment_stability_months = int(data.get("estabilidad_laboral_meses", 0))
        lgd = float(data.get("lgd_severidad", 0.45))
        pd_originacion = float(data.get("pd_originacion", 0.03))

        annual_rate = 0.35
        monthly_rate = annual_rate / 12.0
        if monthly_rate > 0 and term_months > 0:
            monthly_payment = (requested_amount * monthly_rate) / (1.0 - (1.0 + monthly_rate) ** (-term_months))
        else:
            monthly_payment = requested_amount / max(term_months, 1)

        total_monthly_debt = existing_debts + monthly_payment
        dti = (total_monthly_debt / monthly_income) if monthly_income > 0 else 1.0

        # Calibrated WoE-weighted log-odds
        logit = -1.8
        if dti > 0.50:
            logit += 1.35
        elif dti > 0.40:
            logit += 0.70
        elif dti < 0.25:
            logit -= 0.55

        if historical_delinquency_days >= 90:
            logit += 2.20
        elif historical_delinquency_days >= 30:
            logit += 1.10
        elif historical_delinquency_days == 0:
            logit -= 0.60

        if credit_history_months >= 36:
            logit -= 0.50
        elif credit_history_months < 12:
            logit += 0.45

        if employment_stability_months >= 24:
            logit -= 0.40
        elif employment_stability_months < 6:
            logit += 0.50

        pd_12m = float(1.0 / (1.0 + np.exp(-logit)))
        odds = (1.0 - pd_12m) / max(pd_12m, 1e-9)
        score = int(np.clip(np.round(self.offset + self.factor * np.log(odds)), 300, 850))

        # IFRS 9 Staging & Expected Credit Loss (ECL)
        sicr_triggered = (pd_12m / max(pd_originacion, 1e-6)) >= 2.0 or historical_delinquency_days >= 30
        if historical_delinquency_days >= 90:
            ifrs9_stage = "STAGE_3_DEFAULT"
            effective_pd = 1.0
        elif sicr_triggered:
            ifrs9_stage = "STAGE_2_LIFETIME_SICR"
            # Multi-period lifetime PD over remaining term
            years = max(term_months / 12.0, 1.0)
            effective_pd = float(1.0 - (1.0 - pd_12m) ** years)
        else:
            ifrs9_stage = "STAGE_1_PERFORMING_12M"
            effective_pd = pd_12m

        expected_loss_mxn = requested_amount * effective_pd * lgd

        # Underwriting Decision Policy
        if historical_delinquency_days >= 90 or dti > 0.60 or score < 520:
            decision = "RECHAZADO"
            reason = "Riesgo crediticio fuera de apetito (DTI elevado o morosidad severa)."
            max_approved_amount = 0.0
        elif score >= 680 and dti <= 0.35:
            decision = "APROBADO_AUTOMATICO"
            reason = "Perfil con excelente solvencia y bajo riesgo de cartera."
            max_approved_amount = requested_amount
        elif score >= 580 and dti <= 0.45:
            decision = "APROBADO_CONDICIONADO"
            reason = "Aprobado con ajuste de monto para mantener DTI saludable."
            max_approved_amount = min(requested_amount, monthly_income * 0.35 * term_months)
        else:
            decision = "REVISION_MANUAL"
            reason = "Requiere análisis documental complementario por área de riesgos."
            max_approved_amount = min(requested_amount * 0.75, monthly_income * 0.30 * term_months)

        return {
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "probabilidad_default_12m_pct": round(pd_12m * 100.0, 2),
            "ifrs9_stage": ifrs9_stage,
            "expected_loss_ecl_mxn": round(expected_loss_mxn, 2),
            "decision": decision,
            "motivo": reason,
            "cuota_mensual_estimada": round(monthly_payment, 2),
            "ratio_dti_pct": round(dti * 100.0, 2),
            "monto_maximo_sugerido": round(max_approved_amount, 2),
        }

    @staticmethod
    def compute_woe_iv(df: pd.DataFrame, feature_col: str, target_col: str, bins: int = 5) -> Tuple[pd.DataFrame, float]:
        """
        Calculates Weight of Evidence (WoE) and Information Value (IV) with Laplace smoothing.
        """
        working = df[[feature_col, target_col]].copy()
        working["bucket"] = pd.qcut(working[feature_col], q=bins, duplicates="drop")
        grouped = working.groupby("bucket", observed=False)[target_col].agg(["count", "sum"])
        grouped.columns = ["total", "bads"]
        grouped["goods"] = grouped["total"] - grouped["bads"]

        dist_good = (grouped["goods"] + 0.5) / (grouped["goods"].sum() + 0.5 * len(grouped))
        dist_bad = (grouped["bads"] + 0.5) / (grouped["bads"].sum() + 0.5 * len(grouped))

        grouped["woe"] = np.log(dist_good / dist_bad)
        grouped["iv_component"] = (dist_good - dist_bad) * grouped["woe"]
        total_iv = float(grouped["iv_component"].sum())
        return grouped.reset_index(), round(total_iv, 4)

    @staticmethod
    def compute_ks_and_gini(y_true: np.ndarray, pd_scores: np.ndarray) -> Dict[str, float]:
        """
        Computes Kolmogorov-Smirnov (KS) statistic, AUROC, and Gini coefficient (2*AUC - 1).
        """
        order = np.argsort(pd_scores)[::-1]
        y_sorted = y_true[order]
        n_bad = np.sum(y_sorted == 1)
        n_good = np.sum(y_sorted == 0)

        cum_bad = np.cumsum(y_sorted == 1) / max(n_bad, 1)
        cum_good = np.cumsum(y_sorted == 0) / max(n_good, 1)
        ks_stat = float(np.max(np.abs(cum_bad - cum_good)))

        # Trapezoidal AUROC
        auc = float(np.trapz(cum_bad, cum_good))
        gini = 2.0 * auc - 1.0
        return {
            "ks_statistic": round(ks_stat, 4),
            "auroc": round(auc, 4),
            "gini_coefficient": round(gini, 4),
        }

    @staticmethod
    def compute_psi(expected_scores: np.ndarray, actual_scores: np.ndarray, bins: int = 10) -> Dict[str, object]:
        """
        Computes Population Stability Index (PSI) to monitor score distribution drift in production.
        """
        quantiles = np.linspace(0, 100, bins + 1)
        breakpoints = np.percentile(expected_scores, quantiles)
        breakpoints[0] = -np.inf
        breakpoints[-1] = np.inf

        exp_counts, _ = np.histogram(expected_scores, bins=breakpoints)
        act_counts, _ = np.histogram(actual_scores, bins=breakpoints)

        exp_pct = np.clip(exp_counts / max(len(expected_scores), 1), 1e-4, None)
        act_pct = np.clip(act_counts / max(len(actual_scores), 1), 1e-4, None)

        psi_val = float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))
        if psi_val < 0.10:
            status = "STABLE_NO_DRIFT"
        elif psi_val < 0.25:
            status = "MODERATE_DRIFT_MONITOR"
        else:
            status = "SIGNIFICANT_DRIFT_RECALIBRATE"

        return {"psi": round(psi_val, 4), "drift_status": status}


if __name__ == "__main__":
    engine = CreditScoringEngine()
    sample = {
        "ingreso_mensual_neto": 58000,
        "monto_solicitado": 180000,
        "plazo_meses": 24,
        "deudas_actuales_mensuales": 6500,
        "max_dias_mora_historica": 0,
        "antiguedad_crediticia_meses": 48,
        "estabilidad_laboral_meses": 30,
    }
    print(engine.evaluate_applicant(sample))
