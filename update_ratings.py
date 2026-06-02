#!/usr/bin/env python3
"""
update_ratings.py — daily pipeline step (robusto a URL com data).

A Oracle's Elixir publica o CSV com a DATA no nome do arquivo, ex.:
  .../2026_LoL_esports_match_data_from_OraclesElixir_20260601.csv
e essa data muda a cada atualizacao. Em vez de fixar/raspar, este script
TESTA as datas recentes (de hoje pra tras) e usa o primeiro arquivo que existir.

Gera ratings.json com Elo de time/jogador, forma e win-rate de campeao (walk-forward).

  pip install pandas requests
  python3 update_ratings.py            # ano atual, descoberta automatica
  OE_URL="<link>" python3 update_ratings.py   # forca uma URL especifica
"""
import sys, os, io, json, datetime as dt
import requests, numpy as np, pandas as pd
from collections import defaultdict, deque

BASE = "https://oracleselixir-downloadable-match-data.s3-us-west-2.amazonaws.com"
TIER1 = {"LCK","LPL","LEC","LTA N","LTA S","LCS","CBLOL","MSI","EWC","Worlds","WLDs","First Stand"}
ROLES = ["top","jng","mid","bot","sup"]
Kt, Kp = 24, 20

def resolve_year():
    return int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else dt.date.today().year

def find_url(year, lookback_days=21):
    """Probe dated filenames from today backwards; return first existing (HTTP 200)."""
    forced = os.environ.get("OE_URL")
    if forced:
        return forced
    today = dt.date.today()
    for d in range(lookback_days):
        day = today - dt.timedelta(days=d)
        url = f"{BASE}/{year}_LoL_esports_match_data_from_OraclesElixir_{day.strftime('%Y%m%d')}.csv"
        try:
            if requests.head(url, timeout=20).status_code == 200:
                print(f"- encontrado: {url}", file=sys.stderr); return url
        except requests.RequestException:
            pass
    return f"{BASE}/{year}_LoL_esports_match_data_from_OraclesElixir.csv"

def fetch(year):
    url = find_url(year)
    print(f"- baixando {url}", file=sys.stderr)
    r = requests.get(url, timeout=180); r.raise_for_status()
    return pd.read_csv(io.BytesIO(r.content), low_memory=False)

def build(df):
    df = df[df.league.isin(TIER1)]
    pl = df[df.position.isin(ROLES)].copy(); tm = df[df.position=="team"].copy()
    games=[]
    for gid,g in pl.groupby("gameid"):
        rec={"gameid":gid}; ok=True
        for side,pre in [("Blue","b"),("Red","r")]:
            gs=g[g.side==side]
            if len(gs)!=5: ok=False;break
            bp=gs.set_index("position")
            if set(ROLES)-set(bp.index): ok=False;break
            for rl in ROLES: rec[f"{pre}_{rl}_pl"]=bp.loc[rl,"playername"]; rec[f"{pre}_{rl}"]=bp.loc[rl,"champion"]
        if ok: games.append(rec)
    gdf=pd.DataFrame(games).set_index("gameid")
    tb=tm.set_index(["gameid","side"]); meta=[]
    for gid in gdf.index:
        try: b=tb.loc[(gid,"Blue")]; r=tb.loc[(gid,"Red")]
        except KeyError: meta.append(None); continue
        if pd.isna(b["result"]): meta.append(None); continue
        meta.append(dict(date=b["date"],blue_team=b["teamname"],red_team=r["teamname"],blue_win=int(b["result"])))
    gdf=gdf.assign(**pd.DataFrame(meta,index=gdf.index)).dropna(subset=["blue_win"])
    gdf["date"]=pd.to_datetime(gdf["date"],errors="coerce")
    gdf=gdf.dropna(subset=["date"]).sort_values("date")
    telo=defaultdict(lambda:1500.); pelo=defaultdict(lambda:1500.)
    form=defaultdict(lambda:deque(maxlen=10)); cw=defaultdict(float); cn=defaultdict(float)
    gn=defaultdict(int); last={}
    for t in gdf.itertuples():
        bt,rt,bw=t.blue_team,t.red_team,t.blue_win
        bpl=[getattr(t,f"b_{rl}_pl") for rl in ROLES]; rpl=[getattr(t,f"r_{rl}_pl") for rl in ROLES]
        teb,ter=telo[bt],telo[rt]; peb=np.mean([pelo[p] for p in bpl]); per=np.mean([pelo[p] for p in rpl])
        exp=1/(1+10**((ter-teb)/400)); telo[bt]=teb+Kt*(bw-exp); telo[rt]=ter+Kt*((1-bw)-(1-exp))
        ep=1/(1+10**((per-peb)/400))
        for p in bpl: pelo[p]+=Kp*(bw-ep)
        for p in rpl: pelo[p]+=Kp*((1-bw)-(1-ep))
        form[bt].append(bw); form[rt].append(1-bw)
        for c in [getattr(t,f"b_{rl}") for rl in ROLES]: cw[c]+=bw; cn[c]+=1
        for c in [getattr(t,f"r_{rl}") for rl in ROLES]: cw[c]+=(1-bw); cn[c]+=1
        gn[bt]+=1; gn[rt]+=1; last[bt]=str(t.date.date()); last[rt]=str(t.date.date())
    return dict(updated=dt.datetime.now(dt.timezone.utc).isoformat(), year=resolve_year(),
        n_games=int(len(gdf)), telo=dict(telo), pelo=dict(pelo),
        form={k:float(np.mean(v)) if v else .5 for k,v in form.items()},
        games_played=dict(gn), last_seen=last,
        champ_wr={c:(cw[c]+5)/(cn[c]+10) for c in cn})

if __name__=="__main__":
    year=resolve_year()
    out=build(fetch(year))
    json.dump(out, open("ratings.json","w"))
    print(f"- ratings.json escrito: {out['n_games']} jogos, {len(out['telo'])} times, "
          f"{len(out['pelo'])} jogadores", file=sys.stderr)
