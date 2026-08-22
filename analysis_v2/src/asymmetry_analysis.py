"""Research question B: does the Supported/Refuted error-direction asymmetry
persist after conditioning on claim/evidence covariates?

Approach: among evidence-condition errors only, model error direction
(gold Supported predicted Refuted vs gold Refuted predicted Supported)
with logistic regression including claim/evidence covariates and the gold
label. The coefficient on gold_label tests whether the label asymmetry
survives conditioning. Also reports raw direction counts and unconditional
binomial tests per model.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

COVARS = [
    "claim_len_words", "evidence_len_words", "claim_evidence_len_ratio",
    "claim_negation", "claim_comparative", "claim_numbers", "claim_dates",
    "claim_pronouns", "claim_modals", "claim_conjunctions",
    "evidence_negation", "evidence_numbers", "evidence_set_size",
    "n_evidence_sentences", "n_evidence_pages",
    "lexical_overlap", "numerical_overlap",
    "cosine_sim_claim_evidence",
]


def asymmetry_analysis():
    config.ensure_dirs()
    df = pd.read_parquet(config.ENRICHED_PARQUET)
    out = []
    for m in config.MODELS:
        errs = df[~df[f"{m}_evidence_correct"]].copy()
        n_sup = int((errs["gold_label"] == "Supported").sum())  # Sup -> Refuted
        n_ref = int((errs["gold_label"] == "Refuted").sum())    # Ref -> Sup
        p_bin = stats.binomtest(n_sup, n_sup + n_ref, 0.5).pvalue
        out.append({"analysis": "raw_direction_counts", "model": m,
                    "sup_to_ref": n_sup, "ref_to_sup": n_ref,
                    "binom_p": p_bin})

        # Conditioned: does gold label still predict direction given covariates?
        covs = [c for c in COVARS if c in errs.columns]
        X = errs[covs].copy()
        for c in covs:
            X[c] = pd.to_numeric(X[c], errors="coerce")
        X = X.fillna(X.median(numeric_only=True))
        X["gold_refuted"] = (errs["gold_label"] == "Refuted").astype(int)
        y = (errs[f"{m}_evidence_pred"] == "Supported").astype(int)  # direction of prediction
        Xs = sm.add_constant(X.astype(float))
        try:
            fit = sm.Logit(y.to_numpy(), Xs.to_numpy()).fit(disp=0)
            idx = list(Xs.columns).index("gold_refuted")
            ci = fit.conf_int()[idx]
            out.append({"analysis": "conditioned_logit_label_effect", "model": m,
                        "n_errors": len(errs), "covariates": ";".join(covs),
                        "logit_coef_gold_refuted": fit.params[idx],
                        "ci_low": ci[0], "ci_high": ci[1],
                        "p_value": fit.pvalues[idx]})
        except Exception as e:
            out.append({"analysis": "conditioned_logit_label_effect", "model": m,
                        "error": str(e)})

    res = pd.DataFrame(out)
    res.to_csv(config.TABLES_DIR / "label_asymmetry_conditioned.csv", index=False)
    print(res.to_string(index=False))
    return res


if __name__ == "__main__":
    asymmetry_analysis()
