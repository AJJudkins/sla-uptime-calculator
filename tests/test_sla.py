import sys
from datetime import datetime as D
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sla

WS, WE = D(2026, 1, 1), D(2026, 1, 31)  # 30 days = 43200 min


def inc(s, e):
    return {"id": "x", "start": D.fromisoformat(s), "end": D.fromisoformat(e), "description": ""}


def test_allowed_downtime_999_30_days():
    assert round(sla.allowed_downtime_minutes(99.9, 43200), 2) == 43.2


def test_overlap_merged():
    d = sla.downtime_minutes([inc("2026-01-02T00:00:00", "2026-01-02T00:30:00"),
                              inc("2026-01-02T00:20:00", "2026-01-02T00:50:00")], WS, WE)
    assert d == 50


def test_incident_clipped_to_window():
    d = sla.downtime_minutes([inc("2025-12-31T23:30:00", "2026-01-01T00:30:00")], WS, WE)
    assert d == 30


def test_report_breach_and_burn():
    r = sla.report([inc("2026-01-02T00:00:00", "2026-01-02T01:00:00")], WS, WE, 99.9)
    assert r["downtime_minutes"] == 60 and not r["sla_met"]
    assert r["budget_burned_percent"] == round(100 * 60 / 43.2, 1)


def test_sample_file_loads_and_breaches_sla():
    p = Path(__file__).resolve().parent.parent / "sample_data" / "incidents.csv"
    r = sla.report(sla.load_incidents(p), WS, WE, 99.9)
    assert not r["sla_met"]
    assert r["downtime_minutes"] == 65


def test_cli_validation_and_exit_codes(tmp_path):
    import sla
    f = tmp_path / "i.csv"
    f.write_text("id,start,end,description\nA,2026-01-05T00:00,2026-01-05T10:00,big outage\n")
    base = [str(f), "--start", "2026-01-01", "--end", "2026-01-31"]
    assert sla.main(base) == 0
    assert sla.main(base + ["--fail-on-breach"]) == 1
    assert sla.main([str(f), "--start", "2026-02-01", "--end", "2026-01-01"]) == 2
    assert sla.main(base + ["--sla", "100"]) == 2
    assert sla.main([str(tmp_path / "missing.csv"), "--start", "2026-01-01", "--end", "2026-01-31"]) == 2
    bad = tmp_path / "b.csv"
    bad.write_text("id,start,end\nA,2026-01-05T10:00,2026-01-05T09:00\n")
    assert sla.main([str(bad), "--start", "2026-01-01", "--end", "2026-01-31"]) == 2
    nocols = tmp_path / "n.csv"
    nocols.write_text("foo,bar\n1,2\n")
    assert sla.main([str(nocols), "--start", "2026-01-01", "--end", "2026-01-31"]) == 2
