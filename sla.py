"""SLA uptime calculator: uptime %, allowed downtime per tier, error-budget burn."""
import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path

TIERS = {"99%": 99.0, "99.5%": 99.5, "99.9%": 99.9, "99.95%": 99.95, "99.99%": 99.99}


def allowed_downtime_minutes(sla_percent, period_minutes):
    """Minutes of downtime permitted in the period at this SLA."""
    return period_minutes * (100.0 - sla_percent) / 100.0


def load_incidents(path):
    """CSV columns: id,start,end,description (ISO timestamps)."""
    incidents = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            incidents.append({
                "id": row["id"],
                "start": datetime.fromisoformat(row["start"]),
                "end": datetime.fromisoformat(row["end"]),
                "description": row.get("description", ""),
            })
    return incidents


def downtime_minutes(incidents, window_start, window_end):
    """Total downtime in the window; overlapping incidents are merged, not double counted."""
    spans = []
    for i in incidents:
        s, e = max(i["start"], window_start), min(i["end"], window_end)
        if e > s:
            spans.append((s, e))
    spans.sort()
    total, cur_s, cur_e = timedelta(), None, None
    for s, e in spans:
        if cur_e is None or s > cur_e:
            if cur_e is not None:
                total += cur_e - cur_s
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_e is not None:
        total += cur_e - cur_s
    return total.total_seconds() / 60


def uptime_percent(down_min, period_min):
    return round(100.0 * (period_min - down_min) / period_min, 4)


def report(incidents, window_start, window_end, sla_percent=99.9):
    period = (window_end - window_start).total_seconds() / 60
    down = downtime_minutes(incidents, window_start, window_end)
    budget = allowed_downtime_minutes(sla_percent, period)
    return {
        "period_minutes": round(period, 1),
        "downtime_minutes": round(down, 1),
        "uptime_percent": uptime_percent(down, period),
        "sla_percent": sla_percent,
        "error_budget_minutes": round(budget, 1),
        "budget_burned_percent": round(100 * down / budget, 1) if budget else None,
        "sla_met": down <= budget,
    }


def tier_table(period_minutes):
    return {name: round(allowed_downtime_minutes(p, period_minutes), 1)
            for name, p in TIERS.items()}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compute uptime and error-budget burn.")
    ap.add_argument("incidents", help="CSV file of incidents")
    ap.add_argument("--start", required=True, help="window start, e.g. 2026-01-01")
    ap.add_argument("--end", required=True, help="window end, e.g. 2026-01-31")
    ap.add_argument("--sla", type=float, default=99.9)
    args = ap.parse_args(argv)
    ws, we = datetime.fromisoformat(args.start), datetime.fromisoformat(args.end)
    r = report(load_incidents(args.incidents), ws, we, args.sla)
    print(f"Window: {args.start} to {args.end} ({r['period_minutes']} min)")
    print(f"Downtime: {r['downtime_minutes']} min | Uptime: {r['uptime_percent']}%")
    print(f"SLA target {r['sla_percent']}% -> error budget {r['error_budget_minutes']} min, "
          f"burned {r['budget_burned_percent']}%")
    print("SLA MET" if r["sla_met"] else "SLA BREACHED")
    print("\nAllowed downtime per tier for this window:")
    for name, mins in tier_table(r["period_minutes"]).items():
        print(f"  {name:<7} {mins:>8} min")


if __name__ == "__main__":
    main()
