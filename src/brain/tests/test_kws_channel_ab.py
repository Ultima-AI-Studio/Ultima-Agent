from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]


def _load_ab_module():
    path = ROOT / "data" / "logs" / "kws-44k-vs-48k-ab-20261030.py"
    spec = importlib.util.spec_from_file_location("kws_channel_ab_20261030", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ab_uses_eight_disjoint_real_samples_per_class() -> None:
    module = _load_ab_module()

    assert len(module.POSITIVE_SAMPLES) == 8
    assert len(module.NEGATIVE_SAMPLES) == 8
    assert set(module.POSITIVE_SAMPLES).isdisjoint(module.NEGATIVE_SAMPLES)
    assert all((module.SAMPLE_DIR / name).is_file() for name in module.POSITIVE_SAMPLES)
    assert all((module.SAMPLE_DIR / name).is_file() for name in module.NEGATIVE_SAMPLES)


def test_ab_builds_equal_16k_channel_inputs() -> None:
    module = _load_ab_module()
    samples = np.linspace(-0.5, 0.5, 44100, dtype=np.float32)

    baseline, simulated_48k = module.build_channel_inputs(samples, 44100)

    assert baseline.dtype == np.float32
    assert simulated_48k.dtype == np.float32
    assert len(baseline) == 16000
    assert len(simulated_48k) == 16000
