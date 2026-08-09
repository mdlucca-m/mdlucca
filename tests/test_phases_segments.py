"""
Testes: deteccao robusta de fases concentrica/excentrica, componente elastico
e seletor de segmentos.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import phases as Ph  # noqa: E402
from app import segments as Seg  # noqa: E402


def _cmj_signal(fs=100.0):
    """Sinal sintetico tipo CMJ: desce (excentrica), sobe (concentrica), desce."""
    t = np.arange(0, 3, 1 / fs)
    y = np.zeros_like(t)
    y += -0.3 * np.exp(-((t - 0.8) ** 2) / 0.05)     # agachamento (desce)
    y += 0.5 * np.exp(-((t - 1.5) ** 2) / 0.03)      # subida (sobe)
    return t, y


def test_detect_phases_finds_ecc_then_conc():
    t, y = _cmj_signal()
    r = Ph.detect_phases(y, t, min_dur=0.08)
    types = [p["type"] for p in r["phases"]]
    assert "excentrica" in types and "concentrica" in types
    # existe ao menos uma transicao excentrica->concentrica (SSC)
    assert any(tr["ssc"] for tr in r["transitions"])


def test_min_dur_merges_jitter():
    fs = 100.0
    t = np.arange(0, 2, 1 / fs)
    y = np.sin(2 * np.pi * 0.5 * t) + 0.02 * np.random.default_rng(0).standard_normal(t.size)
    r = Ph.detect_phases(y, t, min_dur=0.2)
    # nenhuma fase menor que min_dur (jitter fundido)
    assert all(p["duration_s"] >= 0.19 or p is r["phases"][0] or p is r["phases"][-1]
               for p in r["phases"])


def test_elastic_metrics_shape():
    t, y = _cmj_signal()
    power = np.gradient(y, t)  # proxy so p/ teste
    ph = Ph.detect_phases(y, t, min_dur=0.08)
    e = Ph.elastic_metrics(y, t, ph, power)
    assert e["n_transicoes_ssc"] >= 1
    tr = e["transicoes"][0]
    assert "amortizacao_ms" in tr and "EUR" in tr


def test_segments_resolve():
    r = Seg.resolve("sem_bracos")
    assert "braco_E" not in r["segments"] and "perna_E" in r["segments"]
    # articulacoes de perna presentes, de braco ausentes
    assert "joelho_E" in r["joints"] and "cotovelo_E" not in r["joints"]
    r2 = Seg.resolve(["braco_E", "braco_D"])
    assert set(r2["segments"]) == {"braco_E", "braco_D"}
    assert "cotovelo_E" in r2["joints"]
    # bones nao vazios e pontos unicos
    assert r["bones"] and len(r["points"]) == len(set(r["points"]))


def test_segments_catalog_has_groups():
    c = Seg.catalog()
    assert "sem_bracos" in c["groups"] and "all" in c["groups"]
    assert 0 in c["landmarks"]  # nariz


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    fail = 0
    for fn in fns:
        try:
            fn(); print("PASS", fn.__name__)
        except Exception as e:  # noqa: BLE001
            fail += 1; print("FAIL", fn.__name__, e)
    print(f"\n{len(fns)-fail}/{len(fns)} ok")
    sys.exit(1 if fail else 0)
