import numpy as np
import pandas as pd
from src.credit_scoring_engine import CreditScoringEngine


def test_score_bounds_and_auto_approval():
    engine = CreditScoringEngine()
    prime = {
        "ingreso_mensual_neto": 65000,
        "monto_solicitado": 120000,
        "plazo_meses": 24,
        "deudas_actuales_mensuales": 4000,
        "max_dias_mora_historica": 0,
        "antiguedad_crediticia_meses": 60,
        "estabilidad_laboral_meses": 36,
    }
    res = engine.evaluate_applicant(prime)
    assert 300 <= res["score"] <= 850
    assert res["decision"] == "APROBADO_AUTOMATICO"
    assert res["ifrs9_stage"] == "STAGE_1_PERFORMING_12M"


def test_ifrs9_stage3_and_rejection_on_90dpd():
    engine = CreditScoringEngine()
    subprime = {
        "ingreso_mensual_neto": 20000,
        "monto_solicitado": 150000,
        "plazo_meses": 12,
        "deudas_actuales_mensuales": 8000,
        "max_dias_mora_historica": 120,
        "antiguedad_crediticia_meses": 6,
        "estabilidad_laboral_meses": 3,
    }
    res = engine.evaluate_applicant(subprime)
    assert res["decision"] == "RECHAZADO"
    assert res["ifrs9_stage"] == "STAGE_3_DEFAULT"
    assert res["monto_maximo_sugerido"] == 0.0


def test_ks_gini_and_psi_metrics():
    rng = np.random.default_rng(42)
    y_true = np.array([0] * 400 + [1] * 100)
    pd_scores = np.concatenate([rng.uniform(0.01, 0.15, 400), rng.uniform(0.12, 0.65, 100)])
    metrics = CreditScoringEngine.compute_ks_and_gini(y_true, pd_scores)
    assert metrics["ks_statistic"] > 0.50
    assert metrics["auroc"] > 0.80

    base_scores = rng.normal(640, 45, 1000)
    prod_scores_stable = rng.normal(638, 46, 1000)
    psi_res = CreditScoringEngine.compute_psi(base_scores, prod_scores_stable)
    assert psi_res["psi"] < 0.10
    assert psi_res["drift_status"] == "STABLE_NO_DRIFT"
