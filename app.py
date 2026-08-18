import os, json, hashlib, calendar, re
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd
import streamlit as st
import feedparser
from supabase import create_client, Client
from openai import OpenAI

st.set_page_config(page_title="Trading Assistant", page_icon="📈", layout="wide")

# ---------- Stammdaten ----------
COMPANY_PROFILES = {
 "WCH":{"company":"Wacker Chemie AG","sector":"Chemie / Spezialchemie","summary":"Wacker Chemie ist ein deutscher Chemiekonzern mit Schwerpunkten in Silikonen, Polymeren, Biosolutions und hochreinem Polysilicium.","drivers":["Chemiezyklus","Energiepreise","Industrienachfrage","Halbleiter/Solar"],"risk":"zyklisch"},
 "HOOD":{"company":"Robinhood Markets","sector":"Fintech / Brokerage","summary":"Robinhood betreibt eine digitale Handelsplattform für Aktien, Optionen, Kryptowährungen und weitere Finanzprodukte.","drivers":["Handelsaktivität","Krypto-Märkte","Zinsumfeld","Kundenzuwachs"],"risk":"hoch"},
 "NVDA":{"company":"NVIDIA","sector":"Halbleiter / KI-Infrastruktur","summary":"NVIDIA entwickelt GPUs, KI-Beschleuniger, Rechenzentrumsplattformen und Software für moderne KI-Infrastruktur.","drivers":["KI-Investitionen","Rechenzentren","Produktzyklen","Exportregeln"],"risk":"mittel-hoch"},
 "INTC":{"company":"Intel","sector":"Halbleiter","summary":"Intel entwickelt Prozessoren und Halbleiterlösungen und baut parallel sein Foundry-Geschäft aus.","drivers":["PC-/Server-Nachfrage","Foundry-Ausbau","Kapitalbedarf","Wettbewerb"],"risk":"hoch"},
 "ENR":{"company":"Siemens Energy","sector":"Energie / Infrastruktur","summary":"Siemens Energy liefert Technik für Stromerzeugung, Netze und Energiewende; zum Konzern gehört Siemens Gamesa.","drivers":["Netzausbau","Energiewende","Auftragseingang","Gamesa-Turnaround"],"risk":"mittel-hoch"},
 "QBTS":{"company":"D-Wave Quantum","sector":"Quantencomputing","summary":"D-Wave entwickelt Quantencomputing-Systeme und Software mit Fokus auf Quantum Annealing und hybride Optimierung.","drivers":["Kommerzielle Aufträge","Technologieakzeptanz","Cash-Burn","Quanten-Hype"],"risk":"sehr hoch"},
 "AMD":{"company":"Advanced Micro Devices","sector":"Halbleiter / KI","summary":"AMD entwickelt CPUs, GPUs und Rechenzentrumsbeschleuniger für PCs, Server, Gaming und KI.","drivers":["KI-Beschleuniger","Server-Marktanteile","PC-Zyklus","Wettbewerb"],"risk":"mittel-hoch"},
 "ASML":{"company":"ASML","sector":"Halbleiterausrüstung","summary":"ASML entwickelt Lithographiesysteme für die Halbleiterindustrie und ist insbesondere bei EUV-Anlagen technologisch führend.","drivers":["Chip-Investitionen","EUV-Nachfrage","Exportrestriktionen","Auftragsbestand"],"risk":"mittel"},
}
STARTER_ASSETS = [
 {"isin":"DE000WCH8881","name":"Wacker Chemie","symbol":"WCH","exchange":"XETR","status":"Depot","quantity":0.0,"avg_entry":0.0},
 {"isin":"US7707001027","name":"Robinhood Markets","symbol":"HOOD","exchange":"NASDAQ","status":"Depot","quantity":0.0,"avg_entry":0.0},
 {"isin":"US67066G1040","name":"NVIDIA","symbol":"NVDA","exchange":"NASDAQ","status":"Depot","quantity":0.0,"avg_entry":0.0},
 {"isin":"US4581401001","name":"Intel","symbol":"INTC","exchange":"NASDAQ","status":"Depot","quantity":0.0,"avg_entry":0.0},
 {"isin":"DE000ENER6Y0","name":"Siemens Energy","symbol":"ENR","exchange":"XETR","status":"Depot","quantity":0.0,"avg_entry":0.0},
 {"isin":"US26740W1099","name":"D-Wave Quantum","symbol":"QBTS","exchange":"NYSE","status":"Depot","quantity":0.0,"avg_entry":0.0},
 {"isin":"US0079031078","name":"AMD","symbol":"AMD","exchange":"NASDAQ","status":"Watchlist","quantity":0.0,"avg_entry":0.0},
 {"isin":"NL0009805522","name":"ASML","symbol":"ASML","exchange":"NASDAQ","status":"Watchlist","quantity":0.0,"avg_entry":0.0},
]
STARTER_TURBOS = [
 {"isin":"DE000JY1GWX1","name":"Turbo 1","status":"Watchlist","underlying":""},
 {"isin":"DE000HM4UQX4","name":"Turbo 2","status":"Watchlist","underlying":""},
 {"isin":"DE000HM5ULR4","name":"Turbo 3","status":"Watchlist","underlying":""},
 {"isin":"DE000HM5BPP9","name":"Turbo 4","status":"Watchlist","underlying":""},
]

SERVICE_CATALOG = {
    "Twelve Data": {
        "zweck":"Kursdaten / technische Analyse",
        "verwaltung":"https://twelvedata.com/account",
        "preise":"https://twelvedata.com/pricing",
        "default_status":"Kostenlos",
        "default_cost":0.0,
    },
    "Marketaux": {
        "zweck":"Finanznachrichten / Sentiment",
        "verwaltung":"https://www.marketaux.com/account",
        "preise":"https://www.marketaux.com/pricing",
        "default_status":"Kostenlos",
        "default_cost":0.0,
    },
    "OpenAI API": {
        "zweck":"Deutsche KI-Zusammenfassung / Einordnung",
        "verwaltung":"https://platform.openai.com/settings/organization/billing/overview",
        "preise":"https://openai.com/api/pricing/",
        "default_status":"Nicht eingerichtet",
        "default_cost":0.0,
    },
}

GERMAN_RESEARCH = [
    {"name":"finanzen.net","focus":"Deutschsprachige Aktien-News, Analystenmeldungen und Marktnachrichten","url":"https://www.finanzen.net/nachrichten/ressort/aktien","cost":"kostenlos nutzbar"},
    {"name":"boerse.de","focus":"Deutschsprachige Finanznachrichten, Analysen und Aktieninformationen","url":"https://www.boerse.de/finanznachrichten/","cost":"kostenlos nutzbar"},
    {"name":"Tagesschau Finanzen","focus":"Deutsche Markt- und Börsennachrichten mit makroökonomischem Fokus","url":"https://www.tagesschau.de/wirtschaft/finanzen/","cost":"kostenlos"},
]

GERMAN_RSS_FEEDS = [
    {"name":"finanzen.net News","url":"https://www.finanzen.net/rss/news","type":"News"},
    {"name":"finanzen.net Analysen","url":"https://www.finanzen.net/rss/analysen","type":"Analyse"},
    {"name":"Tagesschau Finanzen","url":"https://www.tagesschau.de/wirtschaft/finanzen/index~rss2.xml","type":"News"},
    {"name":"Tagesschau Unternehmen","url":"https://www.tagesschau.de/wirtschaft/unternehmen/index~rss2.xml","type":"News"},
]

SEARCH_ALIASES = {
    "WCH":["Wacker Chemie","WACKER CHEMIE","WCH"],
    "HOOD":["Robinhood","Robinhood Markets","HOOD"],
    "NVDA":["NVIDIA","Nvidia","NVDA"],
    "INTC":["Intel","Intel Corp","INTC"],
    "ENR":["Siemens Energy","Siemens Gamesa","ENR"],
    "QBTS":["D-Wave","D Wave","D-Wave Quantum","QBTS"],
    "AMD":["AMD","Advanced Micro Devices"],
    "ASML":["ASML"],
}

# ---------- Konfiguration ----------
DEFAULT_MONTHLY_LIMIT_EUR = 2.00
DEFAULT_DAILY_AI_LIMIT = 25
MIN_RELEVANCE_AI = 5
PUSH_RELEVANCE = 8
USD_TO_EUR_BUFFER = 0.95   # konservative Näherung für die lokale Kostenschätzung
# Kostenschätzung passend zur ursprünglich geplanten GPT-5-mini-Kalkulation.
INPUT_USD_PER_M = 0.25
OUTPUT_USD_PER_M = 2.00
MODEL = "gpt-5-mini"

DATA_DIR = Path(".trading_assistant_data")
DATA_DIR.mkdir(exist_ok=True)
SETTINGS_FILE = DATA_DIR / "settings.json"
USAGE_FILE = DATA_DIR / "usage.json"
CACHE_FILE = DATA_DIR / "ai_cache.json"
SERVICES_FILE = DATA_DIR / "services.json"
SIGNALS_FILE = DATA_DIR / "signals.json"

def load_json(path, default):
    try:
        if path.exists(): return json.loads(path.read_text(encoding="utf-8"))
    except Exception: pass
    return default

def save_json(path, data):
    try: path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception: pass

def secret(name):
    try: return st.secrets[name]
    except Exception: return os.getenv(name, "")

TD_KEY=secret("TWELVE_DATA_API_KEY")
MA_KEY=secret("MARKETAUX_API_KEY")
OPENAI_KEY=secret("OPENAI_API_KEY")
SUPABASE_URL=secret("SUPABASE_URL")
SUPABASE_SECRET_KEY=secret("SUPABASE_SECRET_KEY")

settings=load_json(SETTINGS_FILE, {"monthly_limit_eur":DEFAULT_MONTHLY_LIMIT_EUR,"daily_ai_limit":DEFAULT_DAILY_AI_LIMIT})
usage=load_json(USAGE_FILE, {})
signals_store=load_json(SIGNALS_FILE, [])
ai_cache=load_json(CACHE_FILE, {})
services=load_json(SERVICES_FILE, {
    name:{
        "status":cfg["default_status"],
        "monthly_cost":cfg["default_cost"],
        "next_renewal":"",
        "notes":""
    } for name,cfg in SERVICE_CATALOG.items()
})

def month_key(): return datetime.now().strftime("%Y-%m")
def day_key(): return datetime.now().strftime("%Y-%m-%d")
def month_usage():
    return usage.get(month_key(), {"estimated_eur":0.0,"calls":0,"days":{}})
def daily_calls():
    return month_usage().get("days",{}).get(day_key(),0)

def can_use_ai():
    u=month_usage()
    if not OPENAI_KEY: return False,"OPENAI_API_KEY fehlt."
    if u.get("estimated_eur",0)>=float(settings["monthly_limit_eur"]): return False,"Monatslimit erreicht."
    if daily_calls()>=int(settings["daily_ai_limit"]): return False,"Tageslimit erreicht."
    return True,""

def register_usage(input_tokens, output_tokens):
    est_usd=(input_tokens/1_000_000)*INPUT_USD_PER_M+(output_tokens/1_000_000)*OUTPUT_USD_PER_M
    est_eur=est_usd/USD_TO_EUR_BUFFER
    mk=month_key(); dk=day_key()
    u=usage.setdefault(mk,{"estimated_eur":0.0,"calls":0,"days":{}})
    u["estimated_eur"]=round(u.get("estimated_eur",0)+est_eur,6)
    u["calls"]=u.get("calls",0)+1
    u.setdefault("days",{})[dk]=u.get("days",{}).get(dk,0)+1
    save_json(USAGE_FILE,usage)
    return est_eur

def td(endpoint,params):
    if not TD_KEY:return None,"TWELVE_DATA_API_KEY fehlt."
    p=dict(params);p["apikey"]=TD_KEY
    try:
        r=requests.get("https://api.twelvedata.com/"+endpoint,params=p,timeout=15);d=r.json()
        if r.status_code>=400 or d.get("status")=="error":return None,d.get("message",f"HTTP {r.status_code}")
        return d,None
    except Exception as e:return None,str(e)

def marketaux(params):
    if not MA_KEY:return None,"MARKETAUX_API_KEY fehlt."
    p=dict(params);p["api_token"]=MA_KEY
    try:
        r=requests.get("https://api.marketaux.com/v1/news/all",params=p,timeout=15);d=r.json()
        if r.status_code>=400 or d.get("error"):return None,str(d.get("error",f"HTTP {r.status_code}"))
        return d,None
    except Exception as e:return None,str(e)

def quote(a):
    p={"symbol":a["symbol"]}
    if a.get("exchange"):p["exchange"]=a["exchange"]
    return td("quote",p)

def candles(a):
    p={"symbol":a["symbol"],"interval":"1day","outputsize":200,"order":"ASC"}
    if a.get("exchange"):p["exchange"]=a["exchange"]
    d,e=td("time_series",p)
    if e:return None,e
    df=pd.DataFrame(d.get("values",[]))
    if df.empty:return None,"Keine Kursdaten."
    df["datetime"]=pd.to_datetime(df["datetime"])
    for c in ["open","high","low","close","volume"]:
        if c in df:df[c]=pd.to_numeric(df[c],errors="coerce")
    return df.sort_values("datetime"),None

def technical(df):
    if len(df)<50:return None
    c=df.close;s20=c.rolling(20).mean();s50=c.rolling(50).mean();s200=c.rolling(200).mean()
    d=c.diff();g=d.clip(lower=0).rolling(14).mean();l=(-d.clip(upper=0)).rolling(14).mean()
    rsi=float((100-100/(1+g/l.replace(0,pd.NA))).iloc[-1]);last=float(c.iloc[-1])
    m5=(last/c.iloc[-6]-1)*100;m20=(last/c.iloc[-21]-1)*100
    short=50+(15 if last>s20.iloc[-1] else -10)+(15 if s20.iloc[-1]>s50.iloc[-1] else -10)+(10 if m5>0 else -5)+(8 if 42<=rsi<=67 else -10 if rsi>=80 else -5 if rsi>=73 else 3 if rsi<=35 else 0)
    medium=50+(15 if last>s50.iloc[-1] else -10)+(15 if len(df)>=200 and last>s200.iloc[-1] else 0)+(10 if s20.iloc[-1]>s50.iloc[-1] else -8)+(10 if m20>0 else -5)
    risk=35+(35 if rsi>=80 else 20 if rsi>=73 else 10 if rsi<=30 else 0)+min(25,abs(m5)*2.2)
    return {"short":max(0,min(100,round(short))),"medium":max(0,min(100,round(medium))),"rsi":rsi,"risk":max(0,min(100,round(risk)))}

def strict_text_match(text, term):
    """Exakte Wort-/Token-Grenzen statt bloßer Teilstrings."""
    text=(text or "").lower()
    term=(term or "").lower().strip()
    if not term:
        return False
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None

def marketaux_article_matches_asset(article, asset):
    """
    Akzeptiert einen Marketaux-Artikel nur, wenn
    - das Entity-Symbol exakt zum Ticker passt, oder
    - ein eindeutiger Firmenname im Titel steht.
    Dadurch werden bloße Neben-Erwähnungen reduziert.
    """
    symbol=(asset.get("symbol") or "").upper().strip()

    for ent in article.get("entities", []):
        if (ent.get("symbol") or "").upper().strip() == symbol and symbol:
            return True

    title=article.get("title") or ""
    strong_names=SEARCH_ALIASES.get(symbol, []) + [asset.get("name","")]
    for name in strong_names:
        name=(name or "").strip()
        if len(name) >= 5 and strict_text_match(title, name):
            return True

    return False

def news_for(symbol,limit=6,asset=None):
    data,err=marketaux({
        "symbols":symbol,
        "filter_entities":"true",
        "must_have_entities":"true",
        "language":"en",
        "limit":limit,
        "sort":"published_at",
        "sort_order":"desc"
    })
    if err:
        return data,err
    if asset is not None and data:
        filtered=[x for x in data.get("data",[]) if marketaux_article_matches_asset(x,asset)]
        data=dict(data)
        data["data"]=filtered
    return data,None

def article_sentiment(article,symbol=None):
    vals=[]
    for e in article.get("entities",[]):
        if symbol and e.get("symbol") and e.get("symbol")!=symbol:continue
        try:
            if e.get("sentiment_score") is not None:vals.append(float(e["sentiment_score"]))
        except Exception:pass
    return sum(vals)/len(vals) if vals else None

def relevance(article,symbol=None):
    score=4;text=((article.get("title") or "")+" "+(article.get("description") or "")).lower()
    for w in ["earnings","guidance","forecast","acquisition","merger","lawsuit","investigation","approval","partnership","contract","order","recall","ceo","cfo","dividend","buyback","offering","export","ban","regulation","profit warning"]:
        if w in text:score+=1
    s=article_sentiment(article,symbol)
    if s is not None and abs(s)>=.55:score+=1
    return max(1,min(10,score))

def cache_key(asset,article):
    raw=(asset["symbol"]+"|"+str(article.get("url",""))+"|"+str(article.get("title",""))).encode()
    return hashlib.sha256(raw).hexdigest()

def ai_news(asset,article,rel):
    key=cache_key(asset,article)
    if key in ai_cache:return ai_cache[key],None,True
    ok,why=can_use_ai()
    if not ok:return None,why,False
    if rel<MIN_RELEVANCE_AI:return None,"Unterhalb der KI-Relevanzschwelle.",False
    client=OpenAI(api_key=OPENAI_KEY)
    prompt=f"""Analysiere ausschließlich die folgende Börsenmeldung. Schreibe vollständig auf Deutsch.
Unternehmen: {asset['name']} ({asset['symbol']})
Status: {asset['status']}
Vorbewertete Relevanz: {rel}/10
Titel: {article.get('title','')}
Beschreibung: {article.get('description','')}

Antworte ausschließlich als gültiges JSON mit:
deutsche_ueberschrift, kurzfassung, auswirkung (positiv|neutral|negativ),
relevanz (1-10), zeithorizont (kurzfristig|mittelfristig|beides),
begruendung, hinweis.
Der Hinweis darf keine definitive Kauf-/Verkaufsanweisung sein, sondern soll beschreiben, was beobachtet oder geprüft werden sollte.
Keine Fakten ergänzen, die nicht in der Meldung stehen."""
    try:
        resp=client.responses.create(model=MODEL,input=prompt,max_output_tokens=350)
        text=resp.output_text.strip()
        if text.startswith("```"):text=text.replace("```json","").replace("```","").strip()
        result=json.loads(text)
        inp=getattr(resp.usage,"input_tokens",0) if getattr(resp,"usage",None) else 0
        out=getattr(resp.usage,"output_tokens",0) if getattr(resp,"usage",None) else 0
        register_usage(inp,out)
        ai_cache[key]=result;save_json(CACHE_FILE,ai_cache)
        return result,None,False
    except Exception as e:return None,f"KI-Auswertung fehlgeschlagen: {e}",False

def combined(tech,sent):
    ns=50 if sent is None else max(0,min(100,50+sent*50))
    base=.48*tech["short"]+.34*tech["medium"]+.18*ns
    return max(0,min(100,round(base-max(0,tech["risk"]-70)*.22)))

def action(score,risk,rsi):
    if risk>=80 and score>=70:return "🟡 Stark, aber überhitzt – Rücksetzer abwarten"
    if score>=82 and rsi<73:return "🟢 Einstiegszone prüfen"
    if score>=70:return "🟢 Einstieg beobachten"
    if score>=55:return "🟡 Halten / abwarten"
    if score>=40:return "🟠 Risiko erhöht – Position prüfen"
    return "🔴 Aktuell kein attraktives Einstiegssignal"


@st.cache_data(ttl=900)
def load_rss_feed(url):
    try:
        feed = feedparser.parse(url)
        items=[]
        for entry in feed.entries[:80]:
            items.append({
                "title":getattr(entry,"title",""),
                "summary":re.sub("<[^>]+>"," ",getattr(entry,"summary","") or ""),
                "link":getattr(entry,"link",""),
                "published":getattr(entry,"published",""),
            })
        return items
    except Exception:
        return []

def aliases_for_asset(asset):
    aliases=list(SEARCH_ALIASES.get(asset.get("symbol",""),[]))
    for val in [asset.get("name",""),asset.get("symbol",""),asset.get("isin","")]:
        val=(val or "").strip()
        if val and val not in aliases:
            aliases.append(val)
    return aliases

def german_article_matches_asset(item, asset):
    """
    Deutsche RSS-Zuordnung:
    - exakter Firmen-/Ticker-Treffer im Titel bevorzugt
    - Beschreibung allein nur mit längeren, eindeutigen Firmennamen
    """
    title=item.get("title","")
    summary=item.get("summary","")
    aliases=aliases_for_asset(asset)

    for alias in aliases:
        if strict_text_match(title, alias):
            return True

    for alias in aliases:
        alias=(alias or "").strip()
        # keine kurzen Ticker/ISINs als Body-only-Match
        if len(alias) >= 6 and strict_text_match(summary, alias):
            return True

    return False

def german_news_for_asset(asset, limit=8):
    matches=[]
    seen=set()
    for feed_cfg in GERMAN_RSS_FEEDS:
        for item in load_rss_feed(feed_cfg["url"]):
            if not stock_specific_article_is_coherent(item,asset):
                continue
            key=item["link"] or item["title"]
            if key in seen:
                continue
            seen.add(key)
            matches.append({
                **item,
                "source":feed_cfg["name"],
                "type":feed_cfg["type"],
            })
    return matches[:limit]

def turbo_aliases(underlying):
    underlying=(underlying or "").strip()
    if not underlying:
        return []
    aliases=[underlying]
    upper=underlying.upper()
    if upper in SEARCH_ALIASES:
        aliases += SEARCH_ALIASES[upper]

    for ticker, vals in SEARCH_ALIASES.items():
        if underlying.lower() in [v.lower() for v in vals]:
            aliases += [ticker] + vals

    out=[]
    for alias in aliases:
        if alias and alias not in out:
            out.append(alias)
    return out

def german_news_for_turbo(turbo, limit=8):
    underlying=(turbo.get("underlying") or "").strip()
    if not underlying:
        return []

    aliases=turbo_aliases(underlying)
    matches=[]
    seen=set()

    for feed_cfg in GERMAN_RSS_FEEDS:
        for item in load_rss_feed(feed_cfg["url"]):
            title=item.get("title","")
            summary=item.get("summary","")

            # Der Basiswert muss im Titel eindeutig vorkommen.
            matched_alias=None
            for alias in aliases:
                if strict_text_match(title,alias):
                    matched_alias=alias
                    break
            if not matched_alias:
                continue

            # Wenn der Body klar nur ein anderes Unternehmen behandelt, verwerfen.
            current_body_match=any(
                len((a or "").strip()) >= 5 and strict_text_match(summary,a)
                for a in aliases
            )
            unrelated=False
            for other_symbol, other_aliases in SEARCH_ALIASES.items():
                for other_alias in other_aliases:
                    if len((other_alias or "").strip()) >= 5 and strict_text_match(summary,other_alias):
                        if not current_body_match and other_alias.lower() not in [x.lower() for x in aliases]:
                            unrelated=True
                            break
                if unrelated:
                    break
            if unrelated:
                continue

            key=item["link"] or item["title"]
            if key in seen:
                continue
            seen.add(key)
            matches.append({
                **item,
                "source":feed_cfg["name"],
                "type":feed_cfg["type"],
            })

    return matches[:limit]


def german_market_news(limit=12):
    """
    Allgemeine deutsche Börsen-/Aktien-News ohne Zuordnung zu einer einzelnen Aktie.
    """
    items=[]
    seen=set()
    for feed_cfg in GERMAN_RSS_FEEDS:
        for item in load_rss_feed(feed_cfg["url"]):
            key=item.get("link") or item.get("title")
            if not key or key in seen:
                continue
            seen.add(key)
            items.append({
                **item,
                "source":feed_cfg["name"],
                "type":feed_cfg["type"],
            })
            if len(items) >= limit:
                return items
    return items[:limit]

def stock_specific_article_is_coherent(item, asset):
    """
    Für aktienspezifische Zusammenfassungen muss die Überschrift eindeutig
    zum Unternehmen passen. Der Inhalt darf nicht offensichtlich nur ein
    anderes beobachtetes Unternehmen behandeln.
    """
    title=item.get("title","")
    summary=item.get("summary","")
    aliases=aliases_for_asset(asset)

    matched_alias=None
    for alias in aliases:
        if strict_text_match(title,alias):
            matched_alias=alias
            break

    if not matched_alias:
        return False

    # Falls derselbe Firmenbezug auch im Body vorkommt: sehr starker Match.
    if strict_text_match(summary,matched_alias):
        return True

    # Sonst prüfen wir, ob der Body klar auf ein anderes bekanntes Unternehmen zielt.
    current_symbol=(asset.get("symbol") or "").upper()
    current_body_match=any(
        len((a or "").strip()) >= 5 and strict_text_match(summary,a)
        for a in aliases
    )

    for other_symbol, other_aliases in SEARCH_ALIASES.items():
        if other_symbol == current_symbol:
            continue
        for other_alias in other_aliases:
            if len((other_alias or "").strip()) >= 5 and strict_text_match(summary,other_alias):
                if not current_body_match:
                    return False

    return True


# ---------- Persistente Speicherung (Supabase optional) ----------
def supabase_client():
    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    except Exception:
        return None

def persistence_mode():
    return "Supabase" if supabase_client() else "Sitzung / lokal"

def db_load_assets():
    sb = supabase_client()
    if not sb:
        return None
    try:
        res = sb.table("assets").select("*").order("sort_order").execute()
        rows = res.data or []
        if not rows:
            return None
        return [{
            "isin": r.get("isin",""),
            "name": r.get("name",""),
            "symbol": r.get("symbol",""),
            "exchange": r.get("exchange",""),
            "status": r.get("status","Watchlist"),
            "quantity": float(r.get("quantity") or 0.0),
            "avg_entry": float(r.get("avg_entry") or 0.0),
        } for r in rows]
    except Exception:
        return None

def db_save_assets(assets):
    sb = supabase_client()
    if not sb:
        return False
    try:
        sb.table("assets").delete().neq("id", 0).execute()
        payload = []
        for idx, a in enumerate(assets):
            payload.append({
                "isin": a.get("isin",""),
                "name": a.get("name",""),
                "symbol": a.get("symbol",""),
                "exchange": a.get("exchange",""),
                "status": a.get("status","Watchlist"),
                "quantity": float(a.get("quantity",0.0) or 0.0),
                "avg_entry": float(a.get("avg_entry",0.0) or 0.0),
                "sort_order": idx,
            })
        if payload:
            sb.table("assets").insert(payload).execute()
        return True
    except Exception:
        return False

def db_load_turbos():
    sb = supabase_client()
    if not sb:
        return None
    try:
        res = sb.table("turbos").select("*").order("sort_order").execute()
        rows = res.data or []
        if not rows:
            return None
        return [{
            "isin": r.get("isin",""),
            "name": r.get("name","Turbo"),
            "status": r.get("status","Watchlist"),
            "underlying": r.get("underlying",""),
        } for r in rows]
    except Exception:
        return None

def db_save_turbos(turbos):
    sb = supabase_client()
    if not sb:
        return False
    try:
        sb.table("turbos").delete().neq("id", 0).execute()
        payload = []
        for idx, t in enumerate(turbos):
            payload.append({
                "isin": t.get("isin",""),
                "name": t.get("name","Turbo"),
                "status": t.get("status","Watchlist"),
                "underlying": t.get("underlying",""),
                "sort_order": idx,
            })
        if payload:
            sb.table("turbos").insert(payload).execute()
        return True
    except Exception:
        return False

def save_current_portfolio():
    # Ohne Supabase ist dies absichtlich ein No-op.
    if not supabase_client():
        return False
    return db_save_assets(st.session_state.assets) and db_save_turbos(st.session_state.turbos)

def load_initial_state():
    db_assets = db_load_assets()
    db_turbos = db_load_turbos()

    if "assets" not in st.session_state:
        st.session_state.assets = db_assets if db_assets else [x.copy() for x in STARTER_ASSETS]

    if "turbos" not in st.session_state:
        st.session_state.turbos = db_turbos if db_turbos else [x.copy() for x in STARTER_TURBOS]

load_initial_state()


def db_load_signals():
    sb=supabase_client()
    if not sb:
        return None
    try:
        res=sb.table("signals").select("*").order("created_at",desc=True).execute()
        return res.data or []
    except Exception:
        return None

def db_add_signal(signal):
    sb=supabase_client()
    if not sb:
        return False
    try:
        sb.table("signals").insert(signal).execute()
        return True
    except Exception:
        return False

def db_update_signal(signal_id,payload):
    sb=supabase_client()
    if not sb:
        return False
    try:
        sb.table("signals").update(payload).eq("id",signal_id).execute()
        return True
    except Exception:
        return False

def save_signal_local(signal):
    signals_store.append(signal)
    save_json(SIGNALS_FILE,signals_store)

def all_signals():
    dbs=db_load_signals()
    return dbs if dbs is not None else signals_store

def latest_close(asset):
    q,_=quote(asset)
    if q:
        for key in ["close","price"]:
            try:
                if q.get(key) is not None:
                    return float(q.get(key))
            except Exception:
                pass
    df,_=candles(asset)
    if df is not None and not df.empty:
        return float(df["close"].iloc[-1])
    return None

def store_signal(asset,score,tech,sent,recommendation):
    payload={
        "asset_name":asset.get("name",""),
        "symbol":asset.get("symbol",""),
        "isin":asset.get("isin",""),
        "status":asset.get("status",""),
        "signal_date":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "entry_price":latest_close(asset),
        "score":int(score),
        "short_score":int(tech.get("short",0)),
        "medium_score":int(tech.get("medium",0)),
        "risk_score":int(tech.get("risk",0)),
        "rsi":round(float(tech.get("rsi",0)),2),
        "news_sentiment":None if sent is None else round(float(sent),4),
        "recommendation":recommendation,
        "quantity":float(asset.get("quantity",0.0) or 0.0),
        "avg_entry":float(asset.get("avg_entry",0.0) or 0.0),
        "price_5d":None,"price_10d":None,"price_20d":None,
        "perf_5d":None,"perf_10d":None,"perf_20d":None,
    }
    if not db_add_signal(payload):
        payload["id"]=f"local-{len(signals_store)+1}"
        save_signal_local(payload)
    return payload

def perf_pct(start,end):
    try:
        if start in (None,0) or end is None:
            return None
        return round((float(end)/float(start)-1)*100,2)
    except Exception:
        return None

def refresh_signal_performance():
    sigs=all_signals()
    assets_by_symbol={a.get("symbol"):a for a in st.session_state.assets}
    changed=0
    for sig in sigs:
        asset=assets_by_symbol.get(sig.get("symbol"))
        if not asset:
            continue
        try:
            sig_date=pd.to_datetime(sig.get("signal_date"))
        except Exception:
            continue
        elapsed=(pd.Timestamp.now()-sig_date).days
        if elapsed < 5:
            continue
        df,_=candles(asset)
        if df is None or df.empty:
            continue
        dfx=df.copy()
        dfx["datetime"]=pd.to_datetime(dfx["datetime"])
        dfx=dfx[dfx["datetime"]>=sig_date.normalize()]
        if dfx.empty:
            continue
        updates={}
        for days,pk,perfkey in [(5,"price_5d","perf_5d"),(10,"price_10d","perf_10d"),(20,"price_20d","perf_20d")]:
            if elapsed < days or sig.get(pk) is not None:
                continue
            idx=min(days,len(dfx)-1)
            px=float(dfx.iloc[idx]["close"])
            updates[pk]=px
            updates[perfkey]=perf_pct(sig.get("entry_price"),px)
        if updates:
            if str(sig.get("id","")).startswith("local-"):
                for local_sig in signals_store:
                    if local_sig.get("id")==sig.get("id"):
                        local_sig.update(updates)
                        break
                save_json(SIGNALS_FILE,signals_store)
            else:
                db_update_signal(sig.get("id"),updates)
            changed+=1
    return changed

def signal_summary_dataframe():
    rows=[]
    for s in all_signals():
        rows.append({
            "Datum":s.get("signal_date",""),
            "Aktie":s.get("asset_name",""),
            "Ticker":s.get("symbol",""),
            "Signal":s.get("recommendation",""),
            "Score":s.get("score"),
            "Einstieg":s.get("entry_price"),
            "5T %":s.get("perf_5d"),
            "10T %":s.get("perf_10d"),
            "20T %":s.get("perf_20d"),
        })
    return pd.DataFrame(rows)

def win_rate(df,col):
    if df.empty or col not in df:
        return None,None
    vals=pd.to_numeric(df[col],errors="coerce").dropna()
    if vals.empty:
        return None,None
    return round(vals.gt(0).mean()*100,1),round(vals.mean(),2)


def position_metrics(asset):
    qty=float(asset.get("quantity",0.0) or 0.0)
    avg=float(asset.get("avg_entry",0.0) or 0.0)
    current=latest_close(asset)
    invested=qty*avg
    value=qty*current if current is not None else None
    pnl=(value-invested) if value is not None else None
    pnl_pct=((current/avg)-1)*100 if current is not None and avg>0 else None
    return {
        "quantity":qty,
        "avg_entry":avg,
        "current":current,
        "invested":invested,
        "value":value,
        "pnl":pnl,
        "pnl_pct":pnl_pct,
    }

def buy_more_simulator(asset,new_qty,new_price):
    current_qty=float(asset.get("quantity",0.0) or 0.0)
    current_avg=float(asset.get("avg_entry",0.0) or 0.0)
    new_qty=float(new_qty or 0.0)
    new_price=float(new_price or 0.0)

    old_cost=current_qty*current_avg
    add_cost=new_qty*new_price
    total_qty=current_qty+new_qty
    new_avg=(old_cost+add_cost)/total_qty if total_qty>0 else 0.0

    return {
        "new_avg":new_avg,
        "new_total_qty":total_qty,
        "additional_cost":add_cost,
        "total_invested":old_cost+add_cost,
    }

def buy_more_score(market_score, risk_score, pnl_pct, position_weight_hint=None):
    """
    Separater Nachkauf-Score:
    - Markt-/Techniksignal bleibt Haupttreiber
    - hohes Risiko reduziert den Score
    - reines Minus im Depot erhöht den Score NICHT automatisch
    - starke Verluste werden leicht negativ gewichtet, um Averaging-down nicht zu belohnen
    """
    score=float(market_score)
    score -= max(0,float(risk_score)-60)*0.35

    if pnl_pct is not None:
        if pnl_pct < -20:
            score -= 8
        elif pnl_pct < -10:
            score -= 4
        elif 0 < pnl_pct < 20:
            score += 2

    return max(0,min(100,round(score)))

def buy_more_label(score):
    if score >= 82:
        return "🟢 Nachkauf attraktiv – Umsetzung prüfen"
    if score >= 70:
        return "🟢 Nachkauf beobachtenswert"
    if score >= 55:
        return "🟡 Nur bei Bestätigung durch Kurs/News"
    if score >= 40:
        return "🟠 Aktuell eher nicht nachkaufen"
    return "🔴 Kein Nachkauf-Signal"


def resolve_isin(isin):
    """
    Versucht eine ISIN über Twelve Data /symbol_search aufzulösen.
    Der ISIN-Zugriff muss bei Twelve Data als Data Add-on aktiviert sein.
    """
    isin=(isin or "").strip().upper()
    if not isin:
        return None,"Bitte eine ISIN eingeben."

    data,err=td("symbol_search",{"symbol":isin,"outputsize":10,"show_plan":"true"})
    if err:
        return None,err

    candidates=(data or {}).get("data",[])
    if not candidates:
        return None,"Keine passende Aktie gefunden."

    # Bevorzugt Common Stock / ADR / Depositary Receipt; sonst bestes Ergebnis.
    preferred_types={
        "Common Stock","American Depositary Receipt","Depositary Receipt",
        "Global Depositary Receipt","REIT","Preferred Stock"
    }
    chosen=None
    for item in candidates:
        if item.get("instrument_type") in preferred_types:
            chosen=item
            break
    if chosen is None:
        chosen=candidates[0]

    return {
        "name":chosen.get("instrument_name",""),
        "symbol":chosen.get("symbol",""),
        "exchange":chosen.get("exchange",""),
        "country":chosen.get("country",""),
        "currency":chosen.get("currency",""),
        "instrument_type":chosen.get("instrument_type",""),
    },None

def clear_stock_form():
    st.session_state["new_isin"]=""
    st.session_state["new_symbol"]=""
    st.session_state["new_exchange"]=""
    st.session_state["new_name"]=""
    st.session_state["new_status"]="Watchlist"
    st.session_state["new_quantity"]=0.0
    st.session_state["new_avg_entry"]=0.0
    st.session_state["isin_lookup_message"]=""
    st.session_state["pending_isin_lookup"]=False

def request_isin_autofill():
    """
    Callback darf keine bereits erzeugten Widget-Werte direkt verändern.
    Deshalb merken wir nur vor, dass beim nächsten Rendern aufgelöst werden soll.
    """
    st.session_state["pending_isin_lookup"]=True

def process_pending_isin_lookup():
    """
    Wird am Anfang des Aktien-Tabs ausgeführt, BEVOR die Widgets new_symbol,
    new_exchange und new_name erzeugt werden. Dadurch sind Änderungen an
    st.session_state sicher.
    """
    if not st.session_state.get("pending_isin_lookup"):
        return

    st.session_state["pending_isin_lookup"]=False
    isin=st.session_state.get("new_isin","").strip()

    if not isin:
        st.session_state["isin_lookup_message"]="Bitte zuerst eine ISIN eingeben."
        return

    result,err=resolve_isin(isin)

    if result:
        st.session_state["new_symbol"]=result.get("symbol","")
        st.session_state["new_exchange"]=result.get("exchange","")
        st.session_state["new_name"]=result.get("name","")
        st.session_state["isin_lookup_message"]=(
            f"Erkannt: {result.get('name','')} • {result.get('symbol','')} • "
            f"{result.get('exchange','')} • {result.get('currency','')}"
        )
    else:
        st.session_state["isin_lookup_message"]=(
            "Automatische ISIN-Erkennung nicht möglich: " + str(err) +
            " Du kannst Name, Ticker und Börse weiterhin manuell eintragen."
        )

def duplicate_asset(isin,symbol):
    isin=(isin or "").strip().upper()
    symbol=(symbol or "").strip().upper()
    for a in st.session_state.assets:
        if isin and (a.get("isin") or "").upper()==isin:
            return a
        if symbol and (a.get("symbol") or "").upper()==symbol:
            return a
    return None

st.title("📈 Trading Assistant")
st.caption("Version 2.9.1 • Streamlit-Formularfix + sichere ISIN-Autovervollständigung")

with st.sidebar:
    st.header("⚙️ Datenquellen")
    st.success("Twelve Data verbunden") if TD_KEY else st.error("Twelve Data fehlt")
    st.success("Marketaux verbunden") if MA_KEY else st.warning("Marketaux fehlt")
    _sb = supabase_client()
    if _sb:
        st.success("Supabase-Datenbank verbunden")
    else:
        st.info("Supabase noch nicht eingerichtet – App läuft weiter, Änderungen sind aber nicht dauerhaft gespeichert.")
    st.success("OpenAI verbunden") if OPENAI_KEY else st.warning("OpenAI-Key fehlt")

tabs=st.tabs(["📊 Dashboard","📈 Aktien","⚡ Turbos","📰 News","🔎 Analyse","🔥 Hype Radar","🧪 Signale","🔗 Dienste & Abos","💶 KI-Kosten"])
dashboard,stocks,turbos,news_tab,analysis,radar,signals_tab,services_tab,costs=tabs

with dashboard:
    st.subheader("🧪 Gespeicherte Signale – Schnellüberblick")
    _sdf=signal_summary_dataframe()
    if _sdf.empty:
        st.caption("Noch keine Signale gespeichert. Unter 🔎 Analyse kannst du ein Signal mit einem Klick beobachten.")
    else:
        wr5,avg5=win_rate(_sdf,"5T %")
        wr10,avg10=win_rate(_sdf,"10T %")
        c1,c2,c3=st.columns(3)
        c1.metric("Gespeicherte Signale",len(_sdf))
        c2.metric("Trefferquote 5T","—" if wr5 is None else f"{wr5:.1f}%")
        c3.metric("Ø Performance 10T","—" if avg10 is None else f"{avg10:+.2f}%")
    st.divider()

    st.subheader("🔥 Hype Radar – Schnellüberblick")
    st.caption("Die drei aktuell auffälligsten Werte aus deiner Depot-/Watchlist. Hype ist kein automatisches Kaufsignal.")
    quick_rows=[]
    if MA_KEY:
        for a in st.session_state.assets:
            nd,_=news_for(a["symbol"],5,asset=a)
            count=len((nd or {}).get("data",[]))
            vals=[article_sentiment(x,a["symbol"]) for x in (nd or {}).get("data",[])]
            vals=[x for x in vals if x is not None]
            sent=sum(vals)/len(vals) if vals else None
            df,_=candles(a)
            tech=technical(df) if df is not None else None
            if tech:
                sent_score=50 if sent is None else max(0,min(100,50+sent*50))
                hype=round(.4*min(100,25+count*12)+.25*sent_score+.35*tech["short"])
                quick_rows.append({
                    "Aktie":a["name"],
                    "Hype":hype,
                    "Kurzfristig":tech["short"],
                    "Risiko":tech["risk"],
                    "News":count
                })
    if quick_rows:
        quick_df=pd.DataFrame(quick_rows).sort_values("Hype",ascending=False).head(3)
        st.dataframe(quick_df,use_container_width=True,hide_index=True)
    else:
        st.info("Der Schnellüberblick erscheint, sobald Marketaux- und Kursdaten verfügbar sind.")

    st.divider()
    st.subheader("Meine Werte")
    rows=[]
    for a in st.session_state.assets:
        q,_=quote(a)
        pm=position_metrics(a)
        rows.append({
            "Wert":a["name"],
            "ISIN":a["isin"],
            "Status":a["status"],
            "Kurs":q.get("close","—") if q else "—",
            "Heute %":q.get("percent_change","—") if q else "—",
            "Stück":pm["quantity"] if a["status"]=="Depot" else "—",
            "Ø Einstand":round(pm["avg_entry"],2) if a["status"]=="Depot" and pm["avg_entry"]>0 else "—",
            "P/L %":round(pm["pnl_pct"],2) if a["status"]=="Depot" and pm["pnl_pct"] is not None else "—"
        })
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.info("Neu: relevante englische News können per KI vollständig auf Deutsch aufbereitet werden.")
    st.warning("Algorithmische Testsignale – keine Anlageberatung.")
    st.caption(f"Speicherung: **{persistence_mode()}**")

    st.divider()
    st.subheader("🔗 Meine App-Dienste & Abos")
    st.caption("Überblick über externe Dienste, Kosten und offizielle Verwaltungslinks.")

    service_rows=[]
    total_cost=0.0
    for service_name,cfg in SERVICE_CATALOG.items():
        entry=services.get(service_name,{})
        cost=float(entry.get("monthly_cost",0.0) or 0.0)
        total_cost+=cost
        service_rows.append({
            "Dienst":service_name,
            "Zweck":cfg["zweck"],
            "Status":entry.get("status","—"),
            "Monatskosten (€)":round(cost,2),
            "Nächste Verlängerung":entry.get("next_renewal","") or "—",
        })

    st.dataframe(pd.DataFrame(service_rows),use_container_width=True,hide_index=True)
    st.metric("Erfasste externe Monatskosten",f"{total_cost:.2f} €")

    for service_name,cfg in SERVICE_CATALOG.items():
        with st.expander(f"{service_name} verwalten"):
            st.write(f"**Verwendung:** {cfg['zweck']}")
            c1,c2=st.columns(2)
            with c1:
                st.link_button("⚙️ Offizielle Verwaltung / Kündigung",cfg["verwaltung"],use_container_width=True)
            with c2:
                st.link_button("🔄 Tarif / Reaktivierung",cfg["preise"],use_container_width=True)
            st.caption("Die App führt dich nur zur offiziellen Seite. Kündigung oder Reaktivierung bestätigst du dort selbst.")

    st.divider()
    st.subheader("🇩🇪 Kostenlose deutschsprachige Recherche")
    for item in GERMAN_RESEARCH:
        c1,c2=st.columns([4,1])
        with c1:
            st.markdown(f"**{item['name']}**")
            st.write(item["focus"])
            st.caption(item["cost"])
        with c2:
            st.link_button("Öffnen",item["url"],use_container_width=True)

with stocks:
    st.subheader("Aktien verwalten")
    st.caption("ISIN eingeben: Wenn Twelve Data die ISIN-Suche für deinen Zugang erlaubt, werden Name, Ticker und Börse automatisch ergänzt.")

    if "new_isin" not in st.session_state:
        clear_stock_form()

    # Reset erst in einem frischen Run, bevor Widgets erzeugt werden.
    if st.session_state.get("clear_stock_form_next_run"):
        st.session_state["clear_stock_form_next_run"]=False
        clear_stock_form()
        st.success("Aktie hinzugefügt. Eingabefelder wurden geleert.")

    # WICHTIG: vor dem Rendern der übrigen Eingabefelder ausführen.
    process_pending_isin_lookup()

    isin=st.text_input(
        "ISIN",
        key="new_isin",
        placeholder="z. B. US0231351067",
        on_change=request_isin_autofill
    )

    if st.session_state.get("isin_lookup_message"):
        msg=st.session_state["isin_lookup_message"]
        if msg.startswith("Erkannt:"):
            st.success(msg)
        else:
            st.info(msg)

    c1,c2,c3=st.columns(3)
    with c1:
        symbol=st.text_input("Ticker",key="new_symbol",placeholder="z. B. AMZN")
    with c2:
        exchange=st.text_input("Börse",key="new_exchange",placeholder="z. B. NASDAQ")
    with c3:
        status=st.selectbox("Kategorie",["Watchlist","Depot"],key="new_status")

    name=st.text_input("Name",key="new_name",placeholder="z. B. Amazon.com")

    c4,c5=st.columns(2)
    with c4:
        quantity=st.number_input(
            "Stückzahl (bei Depot)",
            min_value=0.0,
            step=1.0,
            key="new_quantity"
        )
    with c5:
        avg_entry=st.number_input(
            "Ø Einstandskurs (bei Depot)",
            min_value=0.0,
            step=1.0,
            key="new_avg_entry"
        )

    b1,b2=st.columns(2)

    with b1:
        if st.button("🔎 ISIN erneut erkennen",use_container_width=True):
            # Nur Flag setzen und sofort neu rendern. Keine Widget-Werte mehr
            # nach deren Erstellung verändern.
            st.session_state["pending_isin_lookup"]=True
            st.rerun()

    with b2:
        if st.button("➕ Aktie hinzufügen",type="primary",use_container_width=True):
            isin_val=st.session_state.get("new_isin","").strip().upper()
            symbol_val=st.session_state.get("new_symbol","").strip().upper()
            exchange_val=st.session_state.get("new_exchange","").strip().upper()
            name_val=st.session_state.get("new_name","").strip()
            status_val=st.session_state.get("new_status","Watchlist")
            qty_val=float(st.session_state.get("new_quantity",0.0) or 0.0)
            avg_val=float(st.session_state.get("new_avg_entry",0.0) or 0.0)

            if not isin_val and not symbol_val:
                st.error("Bitte mindestens ISIN oder Ticker eingeben.")
            else:
                existing=duplicate_asset(isin_val,symbol_val)
                if existing:
                    st.warning(f"{existing.get('name','Diese Aktie')} ist bereits vorhanden. Bitte unten über „Aktie bearbeiten“ korrigieren.")
                else:
                    st.session_state.assets.append({
                        "isin":isin_val,
                        "name":name_val or symbol_val or isin_val,
                        "symbol":symbol_val,
                        "exchange":exchange_val,
                        "status":status_val,
                        "quantity":qty_val if status_val=="Depot" else 0.0,
                        "avg_entry":avg_val if status_val=="Depot" else 0.0,
                    })
                    save_current_portfolio()

                    # Formularwerte NICHT hier direkt leeren, weil die Widgets in
                    # diesem Run bereits erzeugt wurden. Stattdessen Flag setzen.
                    st.session_state["clear_stock_form_next_run"]=True
                    st.rerun()

    st.divider()
    st.subheader("Bereits vorhandene Aktien")

    for i,a in list(enumerate(st.session_state.assets)):
        title=f"{a.get('name','')} ({a.get('symbol','')}) • {a.get('status','')}"
        with st.expander(title,expanded=False):
            e1,e2=st.columns(2)
            with e1:
                edit_name=st.text_input("Name",value=a.get("name",""),key=f"edit_name_{i}")
                edit_isin=st.text_input("ISIN",value=a.get("isin",""),key=f"edit_isin_{i}")
                edit_symbol=st.text_input("Ticker",value=a.get("symbol",""),key=f"edit_symbol_{i}")
            with e2:
                edit_exchange=st.text_input("Börse",value=a.get("exchange",""),key=f"edit_exchange_{i}")
                status_options=["Watchlist","Depot"]
                current_status=a.get("status","Watchlist")
                status_idx=status_options.index(current_status) if current_status in status_options else 0
                edit_status=st.selectbox("Kategorie",status_options,index=status_idx,key=f"edit_status_{i}")
                st.caption("Stückzahl und Einstand sind nur bei Kategorie „Depot“ relevant.")

            p1,p2=st.columns(2)
            with p1:
                edit_qty=st.number_input(
                    "Stückzahl",
                    min_value=0.0,
                    value=float(a.get("quantity",0.0) or 0.0),
                    step=1.0,
                    key=f"edit_qty_{i}"
                )
            with p2:
                edit_avg=st.number_input(
                    "Ø Einstandskurs",
                    min_value=0.0,
                    value=float(a.get("avg_entry",0.0) or 0.0),
                    step=1.0,
                    key=f"edit_avg_{i}"
                )

            pm=position_metrics(a)
            if a.get("status")=="Depot":
                m1,m2,m3=st.columns(3)
                m1.metric("Aktueller Kurs","—" if pm["current"] is None else f"{pm['current']:.2f}")
                m2.metric("P/L %","—" if pm["pnl_pct"] is None else f"{pm['pnl_pct']:+.2f}%")
                m3.metric("Positionswert","—" if pm["value"] is None else f"{pm['value']:.2f}")

            s1,s2=st.columns(2)
            with s1:
                if st.button("💾 Änderungen speichern",key=f"save_asset_{i}",type="primary",use_container_width=True):
                    st.session_state.assets[i]={
                        "isin":edit_isin.strip().upper(),
                        "name":edit_name.strip() or edit_symbol.strip().upper() or edit_isin.strip().upper(),
                        "symbol":edit_symbol.strip().upper(),
                        "exchange":edit_exchange.strip().upper(),
                        "status":edit_status,
                        "quantity":float(edit_qty) if edit_status=="Depot" else 0.0,
                        "avg_entry":float(edit_avg) if edit_status=="Depot" else 0.0,
                    }
                    save_current_portfolio()
                    st.success("Änderungen gespeichert.")
                    st.rerun()

            with s2:
                if st.button("🗑️ Aktie löschen",key=f"delete_asset_{i}",use_container_width=True):
                    st.session_state.assets.pop(i)
                    save_current_portfolio()
                    st.rerun()

with turbos:
    st.subheader("Turbos / Knock-outs")
    st.info("Neu in V2.5: Du kannst zu jedem Turbo den Basiswert hinterlegen. Dadurch werden deutschsprachige News zum Basiswert automatisch zugeordnet.")

    turbo_isin=st.text_input("Turbo-/Knock-out-ISIN",key="new_turbo_isin")
    turbo_underlying=st.text_input("Basiswert / Ticker (z. B. NVIDIA oder NVDA)",key="new_turbo_underlying")
    if st.button("➕ Turbo hinzufügen",type="primary") and turbo_isin:
        st.session_state.turbos.append({
            "isin":turbo_isin.strip().upper(),
            "name":"Neuer Turbo",
            "status":"Watchlist",
            "underlying":turbo_underlying.strip()
        })
        save_current_portfolio()
        st.rerun()

    st.divider()
    for i,turbo in list(enumerate(st.session_state.turbos)):
        with st.expander(f"{turbo.get('name','Turbo')} • {turbo['isin']}",expanded=False):
            underlying=st.text_input(
                "Basiswert / Ticker",
                value=turbo.get("underlying",""),
                key=f"turbo_underlying_{i}",
                placeholder="z. B. NVIDIA oder NVDA"
            )
            c1,c2=st.columns(2)
            with c1:
                if st.button("💾 Basiswert speichern",key=f"save_underlying_{i}",use_container_width=True):
                    st.session_state.turbos[i]["underlying"]=underlying.strip()
                    save_current_portfolio()
                    st.success("Basiswert gespeichert.")
            with c2:
                if st.button("🗑️ Turbo löschen",key=f"turbo_del_{i}",use_container_width=True):
                    st.session_state.turbos.pop(i)
                    save_current_portfolio()
                    st.rerun()

            if underlying.strip():
                st.markdown("#### 🇩🇪 Deutsche News zum Basiswert")
                gnews=german_news_for_turbo({**turbo,"underlying":underlying.strip()},limit=5)
                if not gnews:
                    st.caption("Aktuell keine eindeutig passenden deutschen Meldungen zum Basiswert gefunden.")
                else:
                    for item in gnews:
                        with st.expander(item["title"],expanded=False):
                            st.write(item.get("summary") or "Keine Kurzbeschreibung verfügbar.")
                            st.caption(f"{item['source']} • {item.get('published','')}")
                            if item.get("link"):
                                st.markdown(f"[Originalartikel öffnen]({item['link']})")

with news_tab:
    st.subheader("📰 Deutsches News Center")
    st.caption("V2.6.2: Strenge Zuordnung per exaktem Firmen-/Tickerbezug; zufällige Teiltreffer werden herausgefiltert.")
    st.caption(f"KI wird erst ab Relevanz {MIN_RELEVANCE_AI}/10 verwendet; ab {PUSH_RELEVANCE}/10 ist eine Meldung später Push-Kandidat.")
    scope=st.selectbox("Bereich",["Alle","Depot","Watchlist"],key="news_scope")
    assets=st.session_state.assets if scope=="Alle" else [a for a in st.session_state.assets if a["status"]==scope]
    st.markdown("### 🇩🇪 Deutsche Börsen- & Aktien-News")
    st.caption("Allgemeine Markt-News bleiben sichtbar. Aktienspezifische Zusammenfassungen erscheinen nur, wenn Überschrift und Inhalt eindeutig zusammenpassen.")

    general_news=german_market_news(limit=10)
    if general_news:
        with st.expander("🗞️ Allgemeine deutsche Börsen-News anzeigen",expanded=False):
            for item in general_news:
                st.write(f"**{item['title']}**")
                if item.get("summary"):
                    st.caption(item["summary"][:380])
                st.caption(f"{item['source']} • {item['type']} • {item.get('published','')}")
                if item.get("link"):
                    st.markdown(f"[Artikel öffnen]({item['link']})")
                st.divider()
    else:
        st.info("Aktuell konnten keine allgemeinen deutschen Börsen-News geladen werden.")

    st.markdown("### 🎯 News zu deinen Aktien")
    st.caption("Die Artikelüberschrift ist gleichzeitig der Drop-down-Titel. Erst beim Öffnen siehst du die Zusammenfassung.")

    stock_news_found=False
    for a in assets:
        gnews=german_news_for_asset(a,limit=5)
        if gnews:
            stock_news_found=True
            st.markdown(f"#### {a['name']} ({a['symbol']})")
            for item in gnews:
                with st.expander(item["title"],expanded=False):
                    st.write(item.get("summary") or "Keine Kurzbeschreibung verfügbar.")
                    st.caption(f"{item['source']} • {item['type']} • {item.get('published','')}")
                    st.success("Zuordnung geprüft: Überschrift und Inhalt passen zum Unternehmen.")
                    if item.get("link"):
                        st.markdown(f"[Originalartikel öffnen]({item['link']})")

    if not stock_news_found:
        st.info("Aktuell wurden keine eindeutig passenden deutschsprachigen Artikel zu den ausgewählten Aktien gefunden.")

    st.divider()
    st.markdown("### 🌍 Marketaux / internationale News")

    if not MA_KEY:st.warning("Marketaux-Key fehlt.")
    else:
        for a in assets:
            nd,ne=news_for(a["symbol"],4,asset=a)
            if ne:continue
            for art in (nd or {}).get("data",[]):
                rel=relevance(art,a["symbol"])
                if rel<MIN_RELEVANCE_AI:continue
                st.markdown(f"### {a['name']} • Relevanz {rel}/10")

                # Original-News bleiben immer sichtbar, damit der Nutzer sein Englisch trainieren kann.
                st.markdown("#### 🇬🇧 Original auf Englisch")
                st.write(f"**{art.get('title','Ohne Titel')}**")
                original_text=(art.get("description") or "").strip()
                if original_text:
                    st.write(original_text)
                else:
                    st.caption("Kein englischer Beschreibungstext verfügbar.")
                st.caption(f"Quelle: {art.get('source','—')} • {art.get('published_at','—')}")

                result,err,cached=ai_news(a,art,rel)
                if result:
                    st.markdown("#### 🇩🇪 Deutsche Übersetzung & Einordnung")
                    st.write(f"**{result.get('deutsche_ueberschrift',art.get('title',''))}**")
                    st.write(result.get("kurzfassung",""))
                    st.write(f"**Auswirkung:** {result.get('auswirkung','neutral')} • **Zeithorizont:** {result.get('zeithorizont','—')} • **KI-Relevanz:** {result.get('relevanz',rel)}/10")
                    st.write(f"**Einordnung:** {result.get('begruendung','')}")
                    st.write(f"**Was prüfen?** {result.get('hinweis','')}")
                    if cached:st.caption("Aus Cache – keine neuen KI-Kosten.")
                    if rel>=PUSH_RELEVANCE:st.warning("🔔 Push-Kandidat: hohe Relevanz")
                else:
                    st.info(err)

                if art.get("url"):st.markdown(f"[Originalartikel öffnen]({art['url']})")
                st.divider()

with analysis:
    st.subheader("Einzelanalyse")
    opts={f"{a['name']} ({a['symbol']})":a for a in st.session_state.assets};a=opts[st.selectbox("Wert",list(opts))]
    if st.button("🔎 Analyse starten",type="primary"):
        df,e=candles(a)
        if e:st.error(e)
        else:
            tech=technical(df);nd,_=news_for(a["symbol"],5,asset=a) if MA_KEY else (None,None)
            vals=[article_sentiment(x,a["symbol"]) for x in (nd or {}).get("data",[])];vals=[x for x in vals if x is not None]
            sent=sum(vals)/len(vals) if vals else None;score=combined(tech,sent)
            p=COMPANY_PROFILES.get(a["symbol"],{"company":a["name"],"summary":"Noch kein festes Unternehmensprofil hinterlegt.","sector":"—","drivers":[],"risk":"—"})
            st.subheader(p["company"]);st.write(p["summary"]);st.caption(f"Branche: {p['sector']} • Grundrisiko: {p['risk']}")
            c1,c2,c3,c4=st.columns(4);c1.metric("Gesamt",f"{score}/100");c2.metric("Kurzfristig",f"{tech['short']}/100");c3.metric("Mittelfristig",f"{tech['medium']}/100");c4.metric("Risiko",f"{tech['risk']}/100")
            st.markdown(f"### {action(score,tech['risk'],tech['rsi'])}")
            if a.get("status")=="Depot":
                pm=position_metrics(a)
                st.divider()
                st.subheader("📦 Deine Position")

                p1,p2,p3,p4=st.columns(4)
                p1.metric("Stückzahl",f"{pm['quantity']:.2f}")
                p2.metric("Ø Einstand",f"{pm['avg_entry']:.2f}" if pm["avg_entry"]>0 else "—")
                p3.metric("Aktueller Kurs",f"{pm['current']:.2f}" if pm["current"] is not None else "—")
                p4.metric("P/L", "—" if pm["pnl_pct"] is None else f"{pm['pnl_pct']:+.2f}%")

                bm_score=buy_more_score(score,tech["risk"],pm["pnl_pct"])
                st.markdown(f"### Nachkauf-Score: **{bm_score}/100**")
                st.write(buy_more_label(bm_score))
                st.caption("Der Nachkauf-Score belohnt einen niedrigen Einstand NICHT automatisch. Entscheidend bleiben Markt-/Techniksignal und Risiko.")

                st.markdown("#### 🧮 Nachkauf-Simulator")
                s1,s2=st.columns(2)
                with s1:
                    sim_qty=st.number_input(
                        "Geplante zusätzliche Stückzahl",
                        min_value=0.0,
                        value=0.0,
                        step=1.0,
                        key=f"sim_qty_{a['symbol']}"
                    )
                with s2:
                    default_price=float(pm["current"] or 0.0)
                    sim_price=st.number_input(
                        "Geplanter Kaufkurs",
                        min_value=0.0,
                        value=default_price,
                        step=1.0,
                        key=f"sim_price_{a['symbol']}"
                    )

                if sim_qty>0 and sim_price>0:
                    sim=buy_more_simulator(a,sim_qty,sim_price)
                    s3,s4,s5=st.columns(3)
                    s3.metric("Neuer Ø Einstand",f"{sim['new_avg']:.2f}")
                    s4.metric("Neue Stückzahl",f"{sim['new_total_qty']:.2f}")
                    s5.metric("Zusätzliches Kapital",f"{sim['additional_cost']:.2f}")
                    st.caption("Der Simulator verändert deine Depotdaten nicht. Er zeigt nur, wie sich ein möglicher Nachkauf rechnerisch auswirken würde.")

            current_action=action(score,tech["risk"],tech["rsi"])
            if st.button("💾 Dieses Signal speichern & beobachten",type="primary",key=f"save_signal_{a['symbol']}"):
                saved=store_signal(a,score,tech,sent,current_action)
                if saved.get("entry_price") is not None:
                    st.success(f"Signal gespeichert bei {saved['entry_price']:.2f}. Später vergleichen wir die Entwicklung nach 5/10/20 Handelstagen.")
                else:
                    st.success("Signal gespeichert. Ein aktueller Einstiegskurs konnte nicht ermittelt werden.")

            st.line_chart(df.set_index("datetime")[["close"]].rename(columns={"close":"Kurs"}))

with radar:
    st.subheader("🔥 Hype Radar")
    rows=[]
    if MA_KEY:
        for a in st.session_state.assets:
            nd,_=news_for(a["symbol"],5,asset=a);count=len((nd or {}).get("data",[]))
            vals=[article_sentiment(x,a["symbol"]) for x in (nd or {}).get("data",[])];vals=[x for x in vals if x is not None]
            sent=sum(vals)/len(vals) if vals else None;df,_=candles(a);tech=technical(df) if df is not None else None
            if tech:
                sent_score=50 if sent is None else max(0,min(100,50+sent*50));hype=round(.4*min(100,25+count*12)+.25*sent_score+.35*tech["short"])
                rows.append({"Aktie":a["name"],"Hype":hype,"Einstieg":combined(tech,sent),"Risiko":tech["risk"],"RSI":round(tech["rsi"],1),"News":count})
    if rows:st.dataframe(pd.DataFrame(rows).sort_values("Hype",ascending=False),use_container_width=True,hide_index=True)

with signals_tab:
    st.subheader("🧪 Signal-Historie & Beobachtung")
    st.write("Gespeicherte Signale werden nach 5, 10 und 20 Handelstagen mit dem damaligen Kurs verglichen.")

    if st.button("🔄 Performance jetzt aktualisieren",type="primary"):
        changed=refresh_signal_performance()
        st.success(f"{changed} Signal(e) aktualisiert.")
        st.rerun()

    sdf=signal_summary_dataframe()
    if sdf.empty:
        st.info("Noch keine Signale gespeichert. Unter 🔎 Analyse kannst du ein Signal speichern.")
    else:
        st.dataframe(sdf,use_container_width=True,hide_index=True)
        st.markdown("### Erfolgsübersicht")
        c1,c2,c3=st.columns(3)
        for col,label,box in [("5T %","5 Handelstage",c1),("10T %","10 Handelstage",c2),("20T %","20 Handelstage",c3)]:
            wr,avg=win_rate(sdf,col)
            with box:
                st.metric(f"Trefferquote {label}","—" if wr is None else f"{wr:.1f}%")
                st.caption("Ø Performance: "+("—" if avg is None else f"{avg:+.2f}%"))
        st.info("Für eine belastbare Bewertung brauchen wir mehrere Wochen und genügend gespeicherte Signale.")

with services_tab:
    st.subheader("🔗 Dienste & Abos verwalten")
    st.write("Pflege hier Status, Kosten und Verlängerungsdatum deiner externen Dienste.")

    status_options=["Kostenlos","Kostenpflichtig","Gekündigt","Pausiert","Nicht eingerichtet"]
    for service_name,cfg in SERVICE_CATALOG.items():
        current=services.get(service_name,{
            "status":cfg["default_status"],
            "monthly_cost":cfg["default_cost"],
            "next_renewal":"",
            "notes":""
        })

        with st.expander(service_name,expanded=True):
            st.write(f"**Zweck:** {cfg['zweck']}")
            c1,c2=st.columns(2)
            with c1:
                current_status=current.get("status","Kostenlos")
                idx=status_options.index(current_status) if current_status in status_options else 0
                new_status=st.selectbox("Status",status_options,index=idx,key=f"status_{service_name}")
                new_cost=st.number_input(
                    "Monatskosten (€)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=float(current.get("monthly_cost",0.0) or 0.0),
                    step=0.50,
                    key=f"cost_{service_name}"
                )
            with c2:
                new_renewal=st.text_input(
                    "Nächste Verlängerung (optional)",
                    value=current.get("next_renewal",""),
                    placeholder="z. B. 15.09.2026",
                    key=f"renew_{service_name}"
                )
                new_notes=st.text_input(
                    "Notiz (optional)",
                    value=current.get("notes",""),
                    key=f"notes_{service_name}"
                )

            b1,b2,b3=st.columns(3)
            with b1:
                if st.button("💾 Speichern",key=f"save_{service_name}",use_container_width=True):
                    services[service_name]={
                        "status":new_status,
                        "monthly_cost":float(new_cost),
                        "next_renewal":new_renewal.strip(),
                        "notes":new_notes.strip()
                    }
                    save_json(SERVICES_FILE,services)
                    st.success(f"{service_name} gespeichert.")
            with b2:
                st.link_button("⚙️ Kündigen / Verwalten",cfg["verwaltung"],use_container_width=True)
            with b3:
                st.link_button("🔄 Tarif / Reaktivieren",cfg["preise"],use_container_width=True)

            st.caption("Aus Sicherheitsgründen werden externe Abos nicht automatisch gekündigt oder reaktiviert.")

    st.divider()
    total=sum(float(x.get("monthly_cost",0.0) or 0.0) for x in services.values())
    st.metric("Erfasste Monatskosten aller Dienste",f"{total:.2f} €")
    st.caption("Die Summe basiert auf deinen manuellen Angaben.")

    st.subheader("🇩🇪 Kostenlose deutschsprachige Seiten")
    for item in GERMAN_RESEARCH:
        c1,c2=st.columns([4,1])
        with c1:
            st.markdown(f"**{item['name']}**")
            st.write(item["focus"])
            st.caption(item["cost"])
        with c2:
            st.link_button("Öffnen",item["url"],use_container_width=True)

with costs:
    st.subheader("💶 KI-Kostenbremse")
    u=month_usage();limit=float(settings["monthly_limit_eur"]);spent=float(u.get("estimated_eur",0))
    c1,c2,c3=st.columns(3)
    c1.metric("Geschätzte Kosten diesen Monat",f"{spent:.3f} €")
    c2.metric("Dein Monatslimit",f"{limit:.2f} €")
    c3.metric("KI-Auswertungen heute",f"{daily_calls()} / {settings['daily_ai_limit']}")
    st.progress(min(1.0,spent/limit) if limit>0 else 1.0)

    st.markdown("### Monatslimit selbst ändern")
    st.write("Du kannst das Limit jederzeit ändern – z. B. diesen Monat 3 €, nächsten Monat 5 €. Die Änderung beeinflusst nur die App-interne Kostenbremse.")
    new_limit=st.number_input("Maximale geschätzte KI-Kosten pro Monat (€)",min_value=0.0,max_value=100.0,value=limit,step=0.50)
    new_daily=st.number_input("Maximale neue KI-Auswertungen pro Tag",min_value=1,max_value=500,value=int(settings["daily_ai_limit"]),step=5)
    if st.button("💾 Kostenlimit speichern",type="primary"):
        settings["monthly_limit_eur"]=float(new_limit);settings["daily_ai_limit"]=int(new_daily);save_json(SETTINGS_FILE,settings)
        st.success("Kostenbremse gespeichert.");st.rerun()

    st.warning("Wichtig: Diese Anzeige ist eine lokale Schätzung der Modellkosten und kein Abrechnungsbeleg. Für eine harte Kontosperre solltest du zusätzlich ein Budget/Limits im OpenAI-API-Konto setzen.")
    if spent>=limit and limit>0:st.error("🛑 Monatslimit erreicht. Neue KI-Auswertungen sind gestoppt; bereits gespeicherte Zusammenfassungen bleiben verfügbar.")

st.divider()
st.caption("Trading Assistant • Version 2.9.1")
