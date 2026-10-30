import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evals"))
os.environ.setdefault("DATA_MODE", "sample")


@pytest.fixture(scope="session")
def warehouse(tmp_path_factory):
    """Build a fresh warehouse from the committed sample files, once per test session."""
    from oda import pipeline

    return pipeline.build(tmp_path_factory.mktemp("wh") / "test.duckdb", verbose=False)
