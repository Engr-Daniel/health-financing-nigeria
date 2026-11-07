from pathlib import Path

import pytest

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")


@pytest.mark.parametrize("target", ["Abuja: 15% of government budget", "5% of GDP", "Custom"])
def test_app_runs(target):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=180).run()
    assert not at.exception
    at.selectbox[0].set_value(target).run()
    assert not at.exception
