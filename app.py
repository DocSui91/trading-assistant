
import os
from datetime import datetime
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Trading Assistant MVP", page_icon="📈", layout="wide")

# --- Starter universe ---
STARTER = [
    {"isin":"DE000WCH8881","name":"Wacker Chemie","ticker":"WCH","exchange":"XETR","type":"Aktie","status":"Depot"},
    {"isin":"US7707001027","name":"Robinhood Markets","ticker":"HOOD","exchange":"NASDAQ","type":"Aktie","status":"Depot"},
    {"isin":"US67066G1040","name":"NVIDIA","ticker":"NVDA","exchange":"NASDAQ","type":"Aktie","status":"Depot"},
    {"isin":"US4581401001","name":"Intel","ticker":"INTC","exchange":"NASDAQ","type":"Aktie","status":"Depot"},
    {"isin":"DE000ENER6Y0","name":"Siemens Energy","ticker":"ENR","exchange":"XETR","type":"Aktie","status":"Depot"},
    {"isin":"US26740W1099","name":"D-Wave Quantum","ticker":"QBTS","exchange":"NYSE","type":"Aktie","status":"Depot"},
    {"isin":"US0079031078","name":"AMD","ticker":"AMD","exchange":"NASDAQ","type":"Aktie","status":"Watchlist"},
    {"isin":"NL0009805522","name":"ASML","ticker":"ASML","exchange":"NASDAQ","type":"Aktie","status":"Watchlist"},
]

TURBOS = [
    {"isin":"DE000JY1GWX1","name":"Turbo 1","type":"Turbo","status":"Watchlist"},
    {"isin":"DE000HM4UQX4","name":"Turbo 2","type":"Turbo","status":"Watchlist"},
    {"isin":"DE000HM5ULR4","name":"Turbo 3","type":"Turbo","status":"Watchlist"},
    {"isin":"DE000HM5BPP9","name":"Turbo 4","type":"Turbo","status":"Watchlist"},
]

def get_key():
    return os.getenv("TWELVE_DATA_API_KEY") or st.session_state.get("api_key","").strip()

def td_get(endpoint, params):
    key = get_key()
    if not key:
        return None, "Bitte Twelve-Data-API-Key in der Seitenleiste eingeben oder als TWELVE_DATA_API_KEY setzen."
    params = dict(params)
    params["apikey"] = key
    try:
        r = requests.get("https://api.twelvedata.com/" + endpoint, params=params, timeout=15)
        data = r.json()
        if r.status_code >= 400 or data.get("status") == "error":
            return None, data.get("message", f"HTTP {r.status_code}")
        return data, None
    except Exception as e:
        return None, str(e)

def quote(symbol, exchange=None):
    params = {"symbol": symbol}
    if exchange:
        params["exchange"] = exchange
    return td_get("quote", params)

def candles(symbol, exchange=None, interval="1day", outputsize=120):
    params = {"symbol": symbol, "interval": interval, "outputsize": outputsize, "order":"ASC"}
    if exchange:
        params["exchange"] = exchange
    data, err = td_get("time_series", params)
    if err:
        return None, err
    vals = data.get("values", [])
    if not vals:
        return None, "Keine Kursdaten zurückgegeben."
    df = pd.DataFrame(vals)
    df["datetime"] = pd.to_datetime(df["datetime"])
    for c in ["open","high","low","close","volume"]:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df, None

def score(df):
    if df is None or len(df) < 50:
        return None
    close = df["close"]
    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]
    last = close.iloc[-1]
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, pd.NA)
    rsi = float((100 - (100/(1+rs))).iloc[-1])
    momentum = float((last / close.iloc[-20] - 1) * 100)

    points = 50
    points += 15 if last > sma20 else -10
    points += 15 if sma20 > sma50 else -10
    points += 10 if momentum > 0 else -8
    points += 10 if 40 <= rsi <= 68 else (-5 if rsi > 75 else 0)
    return max(0, min(100, round(points))), rsi, momentum, sma20, sma50

def recommendation(s):
    if s is None:
        return "Keine Bewertung"
    if s >= 80: return "🟢 Kaufzone / Aufstocken"
    if s >= 68: return "🟢 Beobachten – Einstieg suchen"
    if s >= 50: return "🟡 Halten / abwarten"
    if s >= 35: return "🟠 Risiko erhöht"
    return "🔴 Reduzieren / kein Einstieg"

# --- Sidebar ---
st.sidebar.title("⚙️ Einstellungen")
api = st.sidebar.text_input("Twelve Data API-Key", type="password", help="Wird nur für diese Sitzung verwendet.")
if api:
    st.session_state["api_key"] = api

st.sidebar.caption("MVP: Kursdaten + technische Analyse. News, Push und Zertifikatedaten kommen als nächste Module.")

# --- State ---
if "assets" not in st.session_state:
    st.session_state.assets = STARTER.copy()
if "turbos" not in st.session_state:
    st.session_state.turbos = TURBOS.copy()

st.title("📈 Trading Assistant – MVP")
st.caption("Kurzfristig (1–15 Handelstage) + mittelfristig (1–6 Monate) | aktive Strategie")

tabs = st.tabs(["Dashboard", "Aktien", "Turbos / Knock-outs", "Analyse"])

with tabs[0]:
    st.subheader("Überblick")
    if not get_key():
        st.info("🔑 Bitte links deinen Twelve-Data-API-Key eingeben. Der MVP nutzt zunächst die kostenlose API.")
    else:
        rows = []
        for a in st.session_state.assets:
            data, err = quote(a["ticker"], a.get("exchange"))
            if data:
                price = float(data.get("close") or data.get("price") or 0)
                change = float(data.get("percent_change") or 0)
                rows.append({"Wert":a["name"], "Typ":a["status"], "Kurs":price, "Heute %":change})
            else:
                rows.append({"Wert":a["name"], "Typ":a["status"], "Kurs":"—", "Heute %":"—"})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.warning("Hinweis: Die Scores im MVP sind technische Testsignale und noch keine ausgereifte Handelsstrategie. Keine automatische Orderausführung.")

with tabs[1]:
    st.subheader("Aktien verwalten")
    c1,c2,c3 = st.columns(3)
    with c1:
        isin = st.text_input("ISIN")
    with c2:
        ticker = st.text_input("Ticker", placeholder="z. B. AAPL")
    with c3:
        status = st.selectbox("Kategorie", ["Watchlist","Depot"])
    name = st.text_input("Name (optional)")
    exchange = st.text_input("Börse (optional)", placeholder="z. B. NASDAQ oder XETR")
    if st.button("➕ Aktie hinzufügen"):
        if ticker:
            st.session_state.assets.append({
                "isin": isin or "", "name": name or ticker, "ticker": ticker.upper(),
                "exchange": exchange or "", "type":"Aktie", "status":status
            })
            st.success(f"{ticker.upper()} wurde hinzugefügt.")
        else:
            st.error("Für den MVP bitte mindestens den Ticker angeben. Die automatische ISIN-Auflösung bauen wir im nächsten Modul ein.")
    st.divider()
    for i,a in list(enumerate(st.session_state.assets)):
        c1,c2,c3,c4 = st.columns([3,2,2,1])
        c1.write(f"**{a['name']}**  \n`{a['isin']}`")
        c2.write(a["ticker"])
        c3.write(a["status"])
        if c4.button("🗑️", key=f"del_{i}"):
            st.session_state.assets.pop(i)
            st.rerun()

with tabs[2]:
    st.subheader("Turbos / Knock-outs verwalten")
    st.info("Die vier von dir genannten ISINs sind bereits angelegt. Die Produktauflösung (Basiswert, Knock-out, Hebel, Long/Short) wird als separates Zertifikatemodul ergänzt.")
    new_turbo = st.text_input("Turbo-/Knock-out-ISIN")
    if st.button("➕ Turbo hinzufügen"):
        if new_turbo:
            st.session_state.turbos.append({"isin":new_turbo.strip().upper(),"name":"Neuer Turbo","type":"Turbo","status":"Watchlist"})
            st.success("Turbo hinzugefügt.")
    for i,t in list(enumerate(st.session_state.turbos)):
        c1,c2,c3 = st.columns([4,2,1])
        c1.write(f"**{t['name']}**  \n`{t['isin']}`")
        c2.write("⚡ Watchlist")
        if c3.button("🗑️", key=f"tdel_{i}"):
            st.session_state.turbos.pop(i)
            st.rerun()

with tabs[3]:
    st.subheader("Einzelanalyse")
    options = {f"{a['name']} ({a['ticker']})": a for a in st.session_state.assets}
    selected = st.selectbox("Wert auswählen", list(options.keys()))
    a = options[selected]
    if st.button("🔎 Analyse starten"):
        df, err = candles(a["ticker"], a.get("exchange"), "1day", 120)
        if err:
            st.error(err)
        else:
            s = score(df)
            if s:
                total, rsi, mom, sma20, sma50 = s
                m1,m2,m3,m4 = st.columns(4)
                m1.metric("Technischer Score", f"{total}/100")
                m2.metric("RSI", f"{rsi:.1f}")
                m3.metric("20T Momentum", f"{mom:.1f}%")
                m4.metric("Signal", recommendation(total))
                chart = df.set_index("datetime")[["close"]].rename(columns={"close":"Kurs"})
                st.line_chart(chart)
                st.write(f"**SMA20:** {sma20:.2f} | **SMA50:** {sma50:.2f}")
                st.info("Nächster Ausbau: getrennte Kurzfrist-/Mittelfrist-Scores, News-Sentiment, Fundamentaldaten, Turbo-Matrix und Push-Alarme.")
            else:
                st.warning("Noch nicht genügend Daten für einen Score.")

st.divider()
st.caption(f"MVP • Stand {datetime.now().strftime('%d.%m.%Y %H:%M')} • Datenanbieter: Twelve Data")
