from healthfin.model import OUTCOMES, load, table


def test_models_saved_with_all_specs():
    m = load()
    for k in ("main", "robust_no_lag", "robust_excl_nigeria", "robust_gov_only", "long_difference", "cross_section"):
        assert k in m
    for o in OUTCOMES:
        assert o in m["main"]


def test_pinned_findings():
    m = load()
    # Government spending level: not significant within-country for child mortality
    assert m["main"]["u5mr"]["coef"]["ln_gov_pc"]["p"] > 0.05
    # Higher out-of-pocket share goes with higher child mortality in every spec, significant in the long run
    for k in ("main", "long_difference", "cross_section"):
        assert m[k]["u5mr"]["coef"]["oop10"]["b"] > 0
    assert m["long_difference"]["u5mr"]["coef"]["oop10"]["p"] < 0.05


def test_table_shape():
    t = table(load()["main"])
    assert {"Outcome", "Variable", "Coefficient", "p", "Countries"} <= set(t.columns)
    assert len(t) == 9  # 3 outcomes x 3 regressors
