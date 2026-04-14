"""
Market analysis engine — sections A through F + MEFS Score.

Returns a JSON-serializable dict whose shape matches exactly what
Dashboard.jsx expects. Competitor dates are ISO strings ("YYYY-MM-DD");
the frontend API layer converts them back to JS Date objects.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

_SPANISH_MONTHS = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
    7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _num(val: Any) -> float | None:
    if val is None or val == "" or val == "N/A":
        return None
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _pct(value: float, total: float) -> float:
    return (value / total * 100) if total else 0.0


def _parse_date(s: Any) -> datetime | None:
    if not s or s == "N/A":
        return None
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(str(s).strip(), fmt)
        except (ValueError, TypeError):
            pass
    return None


def _fmt_date_es(dt: datetime | None) -> str:
    if dt is None:
        return "N/A"
    return f"{_SPANISH_MONTHS[dt.month]} {dt.year}"


def _months_ago(dt: datetime, now: datetime) -> int:
    return (now.year - dt.year) * 12 + (now.month - dt.month)


# ── Engine ────────────────────────────────────────────────────────────────────

def run_market_analysis(
    raw_records: list[dict],
    unique_records: list[dict],
    usd_rate: float = 17.0,
    top_n: int = 10,
) -> dict[str, Any]:
    """
    Run the full market analysis (A–F + MEFS Score).

    Args:
        raw_records:    All rows from the xlsx (before dedup).
        unique_records: Deduplicated rows (one per ASIN).
        usd_rate:       MXN per USD conversion rate.
        top_n:          Number of top competitors to include.

    Returns:
        JSON-serializable analysis dict.
    """
    now = datetime.now()
    total_r = len(unique_records)

    # ── Brand aggregates ──────────────────────────────────────────────────────
    brand_rev: dict[str, float] = {}
    brand_date: dict[str, datetime] = {}
    brand_origin: dict[str, str] = {}

    for r in unique_records:
        brand = r.get("Brand") or "Unknown"
        rev = _num(r.get("Parent Level Revenue"))
        dt = _parse_date(r.get("Creation Date"))
        origin = r.get("Seller Country/Region") or "N/A"

        if rev:
            brand_rev[brand] = max(brand_rev.get(brand, 0.0), rev)
        if dt:
            prev = brand_date.get(brand)
            if prev is None or dt < prev:
                brand_date[brand] = dt
        if brand not in brand_origin:
            brand_origin[brand] = origin

    total_market_rev = sum(brand_rev.values())

    # ── A. Market Size ────────────────────────────────────────────────────────
    market_size = {
        "revMXN":        total_market_rev,
        "revUSD":        total_market_rev / usd_rate,
        "annualMXN":     total_market_rev * 12,
        "annualUSD":     (total_market_rev * 12) / usd_rate,
        "uniqueProducts": total_r,
        "uniqueBrands":  len(brand_rev),
    }

    # ── B. HHI + Brand Breakdown ──────────────────────────────────────────────
    shares: dict[str, float] = {
        b: _pct(r, total_market_rev) for b, r in brand_rev.items()
    }
    hhi: float = sum((s / 100) ** 2 * 10_000 for s in shares.values())

    sorted_brands = sorted(brand_rev.items(), key=lambda x: -x[1])
    sorted_share_vals = sorted(shares.values(), reverse=True)
    top3_share = sum(sorted_share_vals[:3])
    top5_share = sum(sorted_share_vals[:5])

    brand_breakdown = [
        {
            "brand":     brand,
            "rev":       rev,
            "share":     shares.get(brand, 0.0),
            "startDate": _fmt_date_es(brand_date.get(brand)),
            "origin":    brand_origin.get(brand, "N/A"),
            "ageMo":     _months_ago(brand_date[brand], now) if brand in brand_date else None,
        }
        for brand, rev in sorted_brands
    ]

    # ── C. Top N Competitors — newest → oldest ────────────────────────────────
    top_brand_names = [b for b, _ in sorted_brands[:top_n]]
    competitors = sorted(
        [
            {
                "brand":  b,
                "date":   brand_date[b].strftime("%Y-%m-%d") if b in brand_date else None,
                "rev":    brand_rev.get(b, 0.0),
                "share":  shares.get(b, 0.0),
                "origin": brand_origin.get(b, "N/A"),
                "months": _months_ago(brand_date[b], now) if b in brand_date else None,
            }
            for b in top_brand_names
        ],
        key=lambda x: x["date"] or "",
        reverse=True,
    )

    # ── D. Market Freshness ───────────────────────────────────────────────────
    ages_mo: list[int] = []
    for r in unique_records:
        dt = _parse_date(r.get("Creation Date"))
        if dt:
            ages_mo.append(_months_ago(dt, now))

    freshness = None
    if ages_mo:
        new12  = sum(1 for a in ages_mo if a <= 12)
        new24  = sum(1 for a in ages_mo if a <= 24)
        old36p = sum(1 for a in ages_mo if a > 36)
        total_d = len(ages_mo)
        avg_age = sum(ages_mo) / total_d

        freshness = {
            "total":    total_d,
            "avgAgeMo": avg_age,
            "new12":    new12,
            "new24":    new24,
            "old36p":   old36p,
            "pct12":    _pct(new12,  total_d),
            "pct24":    _pct(new24,  total_d),
            "pct36p":   _pct(old36p, total_d),
            "chartData": [
                {"name": "< 12 meses",  "value": new12,              "pct": _pct(new12,              total_d)},
                {"name": "12-24 meses", "value": new24 - new12,      "pct": _pct(new24 - new12,      total_d)},
                {"name": "24-36 meses", "value": total_d - new24 - old36p, "pct": _pct(total_d - new24 - old36p, total_d)},
                {"name": "> 36 meses",  "value": old36p,             "pct": _pct(old36p,             total_d)},
            ],
        }

    # ── E. Margins & Price ────────────────────────────────────────────────────
    margin_data: list[dict] = []
    for r in unique_records:
        price = _num(r.get("Price  MX$")) or _num(r.get("Price MX$")) or _num(r.get("Price"))
        fees  = _num(r.get("Fees  MX$"))  or _num(r.get("Fees MX$"))  or _num(r.get("Fees"))
        rev   = _num(r.get("ASIN Revenue"))
        brand = r.get("Brand") or "?"
        bsr   = _num(r.get("BSR"))
        if price and fees and price > 0:
            margin_data.append({
                "brand":  brand,
                "price":  price,
                "fees":   fees,
                "margin": (price - fees) / price * 100,
                "rev":    rev or 0.0,
                "bsr":    bsr,
            })

    margins = None
    if margin_data:
        top_sellers = sorted(margin_data, key=lambda x: -x["rev"])[:top_n]
        all_prices  = [d["price"]  for d in margin_data]
        all_margins = [d["margin"] for d in margin_data]
        avg_price   = sum(all_prices)  / len(all_prices)
        avg_margin  = sum(all_margins) / len(all_margins)

        price_buckets = [
            {"label": "< MX$500",       "count": sum(1 for p in all_prices if p < 500)},
            {"label": "MX$500–799",      "count": sum(1 for p in all_prices if 500 <= p < 800)},
            {"label": "MX$800–1,099",    "count": sum(1 for p in all_prices if 800 <= p < 1100)},
            {"label": "MX$1,100–1,499",  "count": sum(1 for p in all_prices if 1100 <= p < 1500)},
            {"label": ">= MX$1,500",     "count": sum(1 for p in all_prices if p >= 1500)},
        ]
        for b in price_buckets:
            b["pct"] = _pct(b["count"], len(all_prices))

        margins = {
            "topSellers":   top_sellers,
            "avgPrice":     avg_price,
            "avgMargin":    avg_margin,
            "priceBuckets": price_buckets,
            "total":        len(margin_data),
        }

    # ── F. Seller Origins ─────────────────────────────────────────────────────
    origins_count: dict[str, int] = {}
    for r in unique_records:
        o = r.get("Seller Country/Region") or "N/A"
        origins_count[o] = origins_count.get(o, 0) + 1

    total_o = sum(origins_count.values())
    sorted_origins = [
        {"origin": o, "count": c, "pct": _pct(c, total_o)}
        for o, c in sorted(origins_count.items(), key=lambda x: -x[1])
    ]
    cn_share = _pct(origins_count.get("CN", 0), total_o)
    mx_share = _pct(origins_count.get("MX", 0), total_o)

    # ── MEFS Score ────────────────────────────────────────────────────────────
    score = 0
    notes: list[dict] = []

    usd_rev = total_market_rev / usd_rate
    if usd_rev > 150_000:
        score += 12; notes.append({"type": "good", "text": "Tamaño de mercado sólido (>USD $150K/mes)"})
    elif usd_rev > 50_000:
        score += 7;  notes.append({"type": "warn", "text": "Mercado mediano ($50K–$150K/mes)"})
    else:
        score += 3;  notes.append({"type": "bad",  "text": "Mercado pequeño (<USD $50K/mes)"})

    if hhi < 1500:
        score += 15; notes.append({"type": "good", "text": f"Mercado fragmentado (HHI {hhi:.0f})"})
    elif hhi < 2500:
        score += 8;  notes.append({"type": "warn", "text": f"Concentración moderada (HHI {hhi:.0f})"})
    else:
        score += 3;  notes.append({"type": "bad",  "text": f"Mercado concentrado (HHI {hhi:.0f})"})

    if freshness:
        pct12 = freshness["pct12"]
        if pct12 >= 30:
            score += 15; notes.append({"type": "good", "text": f"Mercado dinámico ({pct12:.0f}% sellers <12 meses)"})
        elif pct12 >= 15:
            score += 9;  notes.append({"type": "warn", "text": f"Frescura moderada ({pct12:.0f}% sellers <12 meses)"})
        else:
            score += 4;  notes.append({"type": "bad",  "text": f"Mercado maduro ({pct12:.0f}% sellers <12 meses)"})

    if margins:
        am = margins["avgMargin"]
        if am >= 70:
            score += 15; notes.append({"type": "good", "text": f"Margen post-fees alto ({am:.1f}%)"})
        elif am >= 60:
            score += 9;  notes.append({"type": "warn", "text": f"Margen aceptable ({am:.1f}%)"})
        else:
            score += 3;  notes.append({"type": "bad",  "text": f"Margen bajo ({am:.1f}%)"})

        ap = margins["avgPrice"]
        if ap >= 600:
            score += 10; notes.append({"type": "good", "text": f"Precio promedio alto (MX$ {ap:.0f}) — margen para COGS"})
        elif ap >= 350:
            score += 6;  notes.append({"type": "warn", "text": f"Precio promedio medio (MX$ {ap:.0f})"})
        else:
            score += 2;  notes.append({"type": "bad",  "text": f"Precio promedio bajo (MX$ {ap:.0f})"})

    if cn_share < 30:
        score += 10; notes.append({"type": "good", "text": f"Baja presión China ({cn_share:.0f}%)"})
    elif cn_share < 50:
        score += 6;  notes.append({"type": "warn", "text": f"Presión China moderada ({cn_share:.0f}%)"})
    else:
        score += 2;  notes.append({"type": "bad",  "text": f"Alta presión China ({cn_share:.0f}%)"})

    fba_count = sum(1 for r in unique_records if r.get("Fulfillment") == "FBA")
    fba_pct = _pct(fba_count, total_r)
    if fba_pct >= 80:
        score += 10; notes.append({"type": "good", "text": f"Alta adopción FBA ({fba_pct:.0f}%) — logística estándar"})
    elif fba_pct >= 50:
        score += 6;  notes.append({"type": "warn", "text": f"FBA mixto ({fba_pct:.0f}%)"})
    else:
        score += 2;  notes.append({"type": "bad",  "text": f"Baja adopción FBA ({fba_pct:.0f}%)"})

    return {
        "rawCount":       len(raw_records),
        "uniqueCount":    total_r,
        "marketSize":     market_size,
        "hhi":            hhi,
        "top3Share":      top3_share,
        "top5Share":      top5_share,
        "brandBreakdown": brand_breakdown,
        "competitors":    competitors,
        "freshness":      freshness,
        "margins":        margins,
        "origins":        sorted_origins,
        "cnShare":        cn_share,
        "mxShare":        mx_share,
        "mefs":           {"score": (score / 87) * 100, "notes": notes},
    }
