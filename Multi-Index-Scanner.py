"""
Multi-Index-Scanner (ENDGÜLTIG) — Python 3.13
---------------------------------------------
✅ Stabil (ohne pandas_datareader)
✅ Daten: Yahoo Finance via yfinance
✅ Globales Regime: VIX (^VIX) + US10Y (^TNX, auto-skaliert)
✅ 13 Indizes (DAX, CAC40, ITA40, IBEX35, AEX, EuroStoxx50, UK100, SMI,
              SP500, DowJones, Nasdaq100, Nikkei225, Hang Seng)
✅ FX-Filter: UK (GBPUSD), Schweiz (EURCHF), Japan (USDJPY)
✅ Hang Seng ohne CNH-Filter (stabil)
✅ Index-Scores (unterschiedlich pro Index!) = Trendstärke + Momentum + Stabilität
✅ H4-Trigger standardmäßig AUS (maximal stabil; kann man später einschalten)

Interpretation:
- Regime + Direction + Allowed = "Darf ich diesen Index in dieser Richtung traden?"
- Score = "Wie gut ist dieser Index relativ zu den anderen?" (Ranking)
"""

import numpy as np
import pandas as pd
import yfinance as yf

try:
    from tabulate import tabulate
    HAVE_TABULATE = True
except Exception:
    HAVE_TABULATE = False

# -----------------------------
# CONFIG
# -----------------------------
START = "2015-01-01"

# Regime quantiles (VIX dominiert)
VIX_LOW_Q  = 0.35
VIX_HIGH_Q = 0.65

# US10Y-slope "Bremse"
SLOPE_BRAKE_Q = 0.80  # very positive slope => brake risk-on
SLOPE_GAS_Q   = 0.20  # very negative slope => brake risk-off

# Trend filters
EMA_D1 = 50
EMA_FX = 20

# Optional H4 trigger (stable default OFF)
USE_H4_TRIGGER = False
EMA_H4 = 20
H4_LOOKBACK_BARS = 3

DEBUG = True

# -----------------------------
# SYMBOL MAP (Yahoo)
# -----------------------------
INDICES = {
    "DAX":          "^GDAXI",
    "CAC40":        "^FCHI",
    "ITA40":        "FTSEMIB.MI",
    "IBEX35":       "^IBEX",
    "AEX":          "^AEX",
    "EUROSTOXX50":  "^STOXX50E",
    "UK100":        "^FTSE",
    "SMI":          "^SSMI",
    "SP500":        "^GSPC",
    "DOWJONES":     "^DJI",
    "NASDAQ100":    "^NDX",
    "NIKKEI225":    "^N225",
    "HANGSENG":     "^HSI",
}

FX = {
    "GBPUSD": "GBPUSD=X",
    "EURCHF": "EURCHF=X",
    "USDJPY": "USDJPY=X",
}

# FX filter rules:
# - "UP_FOR_LONG":   Long needs FX above EMA; Short needs FX below EMA
# - "DOWN_FOR_LONG": Long needs FX below EMA; Short needs FX above EMA
FX_FILTERS = {
    "UK100":     ("GBPUSD", "DOWN_FOR_LONG"),
    "SMI":       ("EURCHF", "UP_FOR_LONG"),
    "NIKKEI225": ("USDJPY", "UP_FOR_LONG"),
}

# -----------------------------
# HELPERS
# -----------------------------
def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def regime_label(x: int) -> str:
    return {1: "RISK-ON", -1: "RISK-OFF", 0: "NEUTRAL"}.get(int(x), "NEUTRAL")

def download_close(symbol: str, start: str) -> pd.Series:
    """
    Robust close downloader with fallback:
    - Try with start=...
    - If empty/fails -> try period="10y"
    - Always returns pd.Series of Close prices
    """
    def _dl(**kwargs):
        return yf.download(symbol, auto_adjust=True, progress=False, group_by="column", **kwargs)

    df = None
    try:
        df = _dl(start=start)
    except Exception:
        df = None

    if df is None or df.empty:
        df = _dl(period="10y")

    if df is None or df.empty:
        raise ValueError(f"No data for {symbol}")

    # MultiIndex handling
    if isinstance(df.columns, pd.MultiIndex):
        if "Close" in df.columns.get_level_values(0):
            close = df["Close"]
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
        else:
            close = df.iloc[:, 0]
    else:
        close = df["Close"] if "Close" in df.columns else df.iloc[:, 0]

    close = close.dropna().astype(float)
    close.name = symbol
    return close

def fx_supports(regime_val: int, fx_close: pd.Series, rule: str) -> bool:
    fx_ema = ema(fx_close, EMA_FX)
    last_fx = float(fx_close.iloc[-1])
    last_ema = float(fx_ema.iloc[-1])

    if rule == "UP_FOR_LONG":
        if regime_val == 1:
            return last_fx > last_ema
        if regime_val == -1:
            return last_fx < last_ema
        return True

    if rule == "DOWN_FOR_LONG":
        if regime_val == 1:
            return last_fx < last_ema
        if regime_val == -1:
            return last_fx > last_ema
        return True

    return True

def compute_regime(vix: pd.Series, us10y: pd.Series) -> tuple[pd.Series, dict]:
    """
    Regime: VIX quantiles + US10Y slope brake
    """
    us10y_slope = ema(us10y, 10).diff().rename("US10Y_SLOPE")
    df = pd.concat([vix.rename("VIX"), us10y_slope], axis=1).dropna()

    vix_low  = float(df["VIX"].quantile(VIX_LOW_Q))
    vix_high = float(df["VIX"].quantile(VIX_HIGH_Q))

    slope_brake_high = float(df["US10Y_SLOPE"].quantile(SLOPE_BRAKE_Q))
    slope_brake_low  = float(df["US10Y_SLOPE"].quantile(SLOPE_GAS_Q))

    regime = pd.Series(0, index=df.index, dtype=int)

    # Base from VIX
    regime[df["VIX"] <= vix_low] = 1
    regime[df["VIX"] >= vix_high] = -1

    # Brakes
    regime[(regime == 1) & (df["US10Y_SLOPE"] >= slope_brake_high)] = 0
    regime[(regime == -1) & (df["US10Y_SLOPE"] <= slope_brake_low)] = 0

    info = {
        "vix_low": vix_low,
        "vix_high": vix_high,
        "slope_brake_high": slope_brake_high,
        "slope_brake_low": slope_brake_low,
    }
    return regime.rename("Regime"), info

# --- Index Score (0..1) ---
def compute_index_score(close: pd.Series, ema50: pd.Series) -> float:
    """
    IndexScore in [0,1] combining:
    - Trend strength: distance from EMA50 (bigger = stronger)
    - Momentum: 20D return magnitude (bigger = stronger)
    - Stability: inverse 20D volatility (less noisy = better)
    """
    last_close = float(close.iloc[-1])
    last_ema50 = float(ema50.iloc[-1])

    # Trend strength (normalized)
    trend_strength = abs(last_close - last_ema50) / max(1e-9, last_ema50)
    trend_strength = min(trend_strength * 10.0, 1.0)

    # Momentum (normalized)
    if len(close) >= 21:
        mom = (last_close / float(close.iloc[-21])) - 1.0
        momentum = min(abs(mom) * 5.0, 1.0)
    else:
        momentum = 0.0

    # Stability (inverse volatility)
    rets = close.pct_change().dropna()
    vol = float(rets.tail(20).std()) if len(rets) >= 20 else float(rets.std()) if len(rets) > 0 else 0.0
    stability = 1.0 / (1.0 + vol) if vol > 0 else 0.5
    stability = min(max(stability, 0.0), 1.0)

    score = 0.5 * trend_strength + 0.3 * momentum + 0.2 * stability
    return round(float(score), 3)

# -----------------------------
# OPTIONAL H4 TRIGGER (SAFE)
# -----------------------------
def download_h4(symbol: str) -> pd.Series:
    df = yf.download(symbol, period="120d", interval="1h", auto_adjust=True, progress=False)
    if df is None or df.empty or "Close" not in df.columns:
        raise ValueError("No intraday data")
    s = df["Close"].dropna()
    s.index = pd.to_datetime(s.index)
    h4 = s.resample("4h").last().dropna()
    h4.name = symbol
    return h4

def h4_pullback_trigger(symbol: str, direction: str) -> tuple[bool, str]:
    """
    Robust bool logic; if intraday missing -> ignored.
    """
    try:
        h4 = download_h4(symbol)
    except Exception:
        return True, "H4 n/a (ignored)"

    if len(h4) < 60:
        return True, "H4 short (ignored)"

    e = ema(h4, EMA_H4)

    # last CLOSED bars only
    h4c = h4.iloc[:-1]
    ec  = e.iloc[:-1]

    n = min(H4_LOOKBACK_BARS, len(h4c))
    if n < 2:
        return True, "H4 too short (ignored)"

    c_win = h4c.iloc[-n:]
    e_win = ec.iloc[-n:]

    if direction == "LONG":
        touched = bool((c_win <= e_win).any())
        reclaimed = bool(c_win.iloc[-1] > e_win.iloc[-1])
        ok = bool(touched and reclaimed)
        return ok, ("H4 OK" if ok else "H4 NO")

    if direction == "SHORT":
        touched = bool((c_win >= e_win).any())
        reclaimed = bool(c_win.iloc[-1] < e_win.iloc[-1])
        ok = bool(touched and reclaimed)
        return ok, ("H4 OK" if ok else "H4 NO")

    return True, "H4 ignored"

# -----------------------------
# SCAN
# -----------------------------
def scan():
    # Global inputs
    vix = download_close("^VIX", START).rename("VIX")
    tnx = download_close("^TNX", START).rename("TNX")

    # Auto-scale for ^TNX (sometimes 42->4.2, sometimes already 4.2)
    tnx_last = float(tnx.iloc[-1])
    scale = 10.0 if tnx_last > 20.0 else 1.0
    us10y = (tnx / scale)
    us10y.name = "US10Y"

    base = pd.concat([vix, us10y], axis=1).ffill().dropna()
    reg, rinfo = compute_regime(base["VIX"], base["US10Y"])

    # FX data
    fx_data = {}
    for k, sym in FX.items():
        try:
            fx_data[k] = download_close(sym, START).rename(k)
        except Exception:
            fx_data[k] = None

    # Debug
    if DEBUG:
        us10y_slope_last = float(ema(base["US10Y"], 10).diff().iloc[-1])
        print("\n=== DEBUG (latest) ===")
        print(f"VIX last:    {float(base['VIX'].iloc[-1]):.2f}")
        print(f"TNX raw:     {tnx_last:.3f} (scale {scale}) -> US10Y {float(base['US10Y'].iloc[-1]):.2f}")
        print(f"US10Y slope: {us10y_slope_last:.6f}")
        print("Thresholds:")
        print(f"  VIX low/high: {rinfo['vix_low']:.2f} / {rinfo['vix_high']:.2f}")
        print(f"  Slope brake high/low: {rinfo['slope_brake_high']:.6f} / {rinfo['slope_brake_low']:.6f}")

    results = []
    for name, sym in INDICES.items():
        try:
            close = download_close(sym, START)
        except Exception as e:
            results.append({"Index": name, "Yahoo": sym, "Allowed": "NO", "Status": f"NO DATA ({e})"})
            continue

        df = pd.concat([close.rename("Close"), reg], axis=1).ffill().dropna()
        df["EMA50"] = ema(df["Close"], EMA_D1)

        last = df.iloc[-1]
        last_close = float(last["Close"])
        last_regime = int(last["Regime"])

        trend_long  = last_close > float(last["EMA50"])
        trend_short = last_close < float(last["EMA50"])
        trend_txt = "UP" if trend_long else ("DOWN" if trend_short else "FLAT")

        allowed = False
        direction = "NEUTRAL"
        if last_regime == 1 and trend_long:
            allowed = True
            direction = "LONG"
        elif last_regime == -1 and trend_short:
            allowed = True
            direction = "SHORT"

        # FX filter (if missing -> ignored; if BLOCK -> Allowed NO)
        fx_note = "-"
        if name in FX_FILTERS and last_regime != 0:
            fx_key, rule = FX_FILTERS[name]
            fx_series = fx_data.get(fx_key)

            if fx_series is None:
                fx_note = f"{fx_key} missing (ignored)"
            else:
                fx_aligned = fx_series.reindex(df.index).ffill().dropna()
                if len(fx_aligned) < 50:
                    fx_note = f"{fx_key} too short (ignored)"
                else:
                    ok = fx_supports(last_regime, fx_aligned, rule)
                    fx_note = f"{fx_key} {'OK' if ok else 'BLOCK'}"
                    if not ok:
                        allowed = False

        # Optional H4 trigger (safe; default OFF)
        h4_note = "-"
        if USE_H4_TRIGGER and allowed and direction in ("LONG", "SHORT"):
            ok_h4, h4_note = h4_pullback_trigger(sym, direction)
            if not ok_h4:
                allowed = False

        # IndexScore (ranking)
        index_score = compute_index_score(df["Close"], df["EMA50"])

        results.append({
            "Index": name,
            "Regime": regime_label(last_regime),
            "Direction": direction,
            "Trend(D1)": trend_txt,
            "Allowed": "YES" if allowed else "NO",
            "Close": round(last_close, 2),
            "FX": fx_note,
            "H4": h4_note,
            "Yahoo": sym,
            "Score": index_score,
        })

    res = pd.DataFrame(results).sort_values(by=["Allowed", "Score"], ascending=[False, False])

    print("\n=== GLOBAL INPUTS (latest) ===")
    print(f"VIX (^VIX):        {float(base['VIX'].iloc[-1]):.2f}")
    print(f"US10Y (^TNX adj):  {float(base['US10Y'].iloc[-1]):.2f}")
    print(f"H4 trigger:        {'ON' if USE_H4_TRIGGER else 'OFF'}")

    print("\n=== MULTI-INDEX SCAN (latest) ===")
    cols = ["Index","Regime","Direction","Trend(D1)","Allowed","Close","FX","H4","Yahoo","Score"]
    if HAVE_TABULATE:
        print(tabulate(res[cols], headers="keys", tablefmt="github", showindex=False))
    else:
        print(res[cols].to_string(index=False))

    return res

if __name__ == "__main__":
    scan()
