import requests
import time
import json
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm

# ---------- CONFIG ----------
LEAGUE_CODE = "per.1"   # "per.1" Liga 1 (Perú)
START_DATE = "2010-01-01"   # YYYY-MM-DD
END_DATE   = "2025-09-28"
OUT_JSONL = f"espn_{LEAGUE_CODE}_{START_DATE}_to_{END_DATE}.jsonl"
OUT_CSV   = f"espn_{LEAGUE_CODE}_{START_DATE}_to_{END_DATE}.csv"

# Timing / politeness
SCOREBOARD_SLEEP = 0.2
SUMMARY_SLEEP = 0.6
RETRY_SLEEP = 2.0
MAX_RETRIES = 3
TIMEOUT = 12
# ----------------------------

# map human league label fallback
LEAGUE_LABELS = {
    "eng.1": "Premier League",
    "esp.1": "LaLiga (España)",
    "fra.1": "Ligue 1",
    "per.1": "Liga 1 (Perú)"
}

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.espn.com/"
})
# If you need proxy, set here:
# session.proxies.update({"http":"http://proxy:port","https":"http://proxy:port"})

def daterange(start_date, end_date):
    s = datetime.strptime(start_date, "%Y-%m-%d").date()
    e = datetime.strptime(end_date, "%Y-%m-%d").date()
    d = s
    while d <= e:
        yield d
        d += timedelta(days=1)

def safe_get(url, params=None, max_retries=MAX_RETRIES, timeout=TIMEOUT):
    for attempt in range(1, max_retries+1):
        try:
            r = session.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r
            else:
                print(f"HTTP {r.status_code} for {r.url}")
        except requests.exceptions.RequestException as e:
            print(f"Request error (attempt {attempt}) for {url}: {e}")
        time.sleep(RETRY_SLEEP * attempt)
    return None

def normalize_num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return v
    s = str(v).strip()
    if s.endswith('%'):
        s = s.replace('%', '').strip()
        try:
            return float(s)
        except:
            return s
    s = s.replace(',', '')
    try:
        if '.' in s:
            return float(s)
        return int(s)
    except:
        return s

def extract_stats_from_summary_json(summary_json):
    out = {
        "posesion_local": None, "posesion_visitante": None,
        "tiros_totales_local": None, "tiros_totales_visitante": None,
        "tiros_a_puerta_local": None, "tiros_a_puerta_visitante": None,
        "corners_local": None, "corners_visitante": None,
        "tarjetas_amarillas_local": None, "tarjetas_amarillas_visitante": None,
        "tarjetas_rojas_local": None, "tarjetas_rojas_visitante": None
    }
    try:
        box = summary_json.get("boxscore") or {}
        teams = box.get("teams") or []
        for team in teams:
            is_home = team.get("homeAway") == "home"
            stats_list = team.get("statistics") or []
            for s in stats_list:
                name = (s.get("name") or s.get("id") or s.get("label") or s.get("stat") or s.get("type") or "").lower()
                val = s.get("displayValue") if s.get("displayValue") is not None else s.get("value")
                if val is None:
                    continue
                if "possession" in name:
                    if is_home: out["posesion_local"] = normalize_num(val)
                    else: out["posesion_visitante"] = normalize_num(val)
                elif "total" in name and "shot" in name:
                    if is_home: out["tiros_totales_local"] = normalize_num(val)
                    else: out["tiros_totales_visitante"] = normalize_num(val)
                elif "on target" in name:
                    if is_home: out["tiros_a_puerta_local"] = normalize_num(val)
                    else: out["tiros_a_puerta_visitante"] = normalize_num(val)
                elif "corner" in name:
                    if is_home: out["corners_local"] = normalize_num(val)
                    else: out["corners_visitante"] = normalize_num(val)
                elif "yellow" in name:
                    if is_home: out["tarjetas_amarillas_local"] = normalize_num(val)
                    else: out["tarjetas_amarillas_visitante"] = normalize_num(val)
                elif "red" in name:
                    if is_home: out["tarjetas_rojas_local"] = normalize_num(val)
                    else: out["tarjetas_rojas_visitante"] = normalize_num(val)
        return out
    except Exception as e:
        print("Error extrayendo stats:", e)
        return out

def parse_event_basic(event):
    rec = {
        "match_id": None,
        "fecha": None,
        "liga": LEAGUE_LABELS.get(LEAGUE_CODE, LEAGUE_CODE),
        "equipo_local": None,
        "equipo_visitante": None,
        "goles_local": None,
        "goles_visitante": None,
    }
    try:
        rec["match_id"] = str(event.get("id") or event.get("uid") or "")
        rec["fecha"] = event.get("date") or event.get("gameDate") or ""
        if rec["fecha"] and isinstance(rec["fecha"], str) and "T" in rec["fecha"]:
            rec["fecha"] = rec["fecha"].split("T")[0]
        comps = event.get("competitions") or []
        if comps:
            comp = comps[0]
            for team in comp.get("competitors", []):
                is_home = team.get("homeAway", "") == "home"
                tname = team.get("team", {}).get("displayName")
                score = team.get("score")
                rec_name = "equipo_local" if is_home else "equipo_visitante"
                rec_score = "goles_local" if is_home else "goles_visitante"
                rec[rec_name] = tname
                try:
                    rec[rec_score] = int(score) if score not in [None, ""] else None
                except:
                    rec[rec_score] = score
        return rec
    except Exception as e:
        print("Error parse_event_basic:", e)
        return rec

def scrape_range(start_date, end_date, league_code):
    processed = set()
    records = []
    for d in tqdm(list(daterange(start_date, end_date)), desc="Fechas"):
        datestr = d.strftime("%Y%m%d")
        scoreboard_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard"
        params = {"dates": datestr}
        resp = safe_get(scoreboard_url, params=params)
        time.sleep(SCOREBOARD_SLEEP)
        if not resp:
            continue
        try:
            data = resp.json()
        except Exception as e:
            print("JSON decode error scoreboard:", e)
            continue
        events = data.get("events") or []
        if not events and data.get("leagues"):
            for lg in data.get("leagues", []):
                evs = lg.get("events") or []
                events.extend(evs)
        if not events:
            continue
        for event in events:
            basic = parse_event_basic(event)
            mid = basic["match_id"]
            if not mid or mid in processed:
                continue
            processed.add(mid)
            summary_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/summary"
            sresp = safe_get(summary_url, params={"event": mid})
            time.sleep(SUMMARY_SLEEP)
            summary_json = {}
            if sresp:
                try:
                    summary_json = sresp.json()
                except:
                    summary_json = {}
            stats = extract_stats_from_summary_json(summary_json)
            rec = {**basic, **stats}
            rec["liga"] = LEAGUE_LABELS.get(league_code, league_code)
            try:
                if rec["fecha"] and isinstance(rec["fecha"], str) and len(rec["fecha"]) == 8 and rec["fecha"].isdigit():
                    rec["fecha"] = f"{rec['fecha'][:4]}-{rec['fecha'][4:6]}-{rec['fecha'][6:]}"
            except:
                pass
            records.append(rec)
            with open(OUT_JSONL, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return records

def main():
    print(" Scraping ESPN API")
    print(f"Liga: {LEAGUE_LABELS.get(LEAGUE_CODE, LEAGUE_CODE)}")
    print(f"Rango: {START_DATE} -> {END_DATE}")
    start = time.time()
    recs = scrape_range(START_DATE, END_DATE, LEAGUE_CODE)
    end = time.time()
    total = len(recs)
    print(f"\n Proceso finalizado. Partidos extraídos: {total}")
    print(f"Tiempo: {end - start:.1f}s")
    if total == 0:
        print("No se extrajeron partidos. Posibles causas: ESPN no tiene cobertura para esos años de Liga 1, o errores de conexión.")
    if recs:
        df = pd.DataFrame(recs)
        cols = ["match_id","fecha","liga","equipo_local","equipo_visitante",
                "goles_local","goles_visitante",
                "posesion_local","posesion_visitante",
                "tiros_totales_local","tiros_totales_visitante",
                "tiros_a_puerta_local","tiros_a_puerta_visitante",
                "corners_local","corners_visitante",
                "tarjetas_amarillas_local","tarjetas_amarillas_visitante",
                "tarjetas_rojas_local","tarjetas_rojas_visitante"]
        for c in cols:
            if c not in df.columns:
                df[c] = None
        df = df[cols]
        df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
        print(f" Guardado CSV: {OUT_CSV}")
        print(f" Guardado JSONL: {OUT_JSONL}")
    else:
        open(OUT_JSONL, "a", encoding="utf-8").close()
        print(f" Archivo JSONL vacío creado: {OUT_JSONL}")

if __name__ == "__main__":
    main()
