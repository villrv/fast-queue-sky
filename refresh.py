"""Rebuild the FAST Queue Sky page from the live Google Sheet.

Usage: python3 refresh.py            -> writes fast-queue-sky.html next to this file
Light curves: reuses lc_cache.json (YSE-PZ pulls from a signed-in browser session);
targets missing from the cache get Orcus photometry, which is then cached too.
Orcus token is read from ~/Dropbox/Observing/bulk_report_at/.env (SKYPORTAL_TOKEN).
"""
import csv, io, json, os, re, datetime, urllib.request
HERE=os.path.dirname(os.path.abspath(__file__))
SHEET="https://docs.google.com/spreadsheets/d/1pItVtBbhYYViD32obqGGXkDmgcKALeJRitSXebR8nY4/export?format=csv"
ORCUS="https://orcusgate.org"

def env_token():
    p=os.path.expanduser("~/Dropbox/Observing/bulk_report_at/.env")
    for line in open(p):
        line=line.strip()
        if line.startswith(("SKYPORTAL_TOKEN","export SKYPORTAL_TOKEN")) and "=" in line:
            return line.split("=",1)[1].strip().strip('"').strip("'")
def orcus_lc(name,tok):
    req=urllib.request.Request(f"{ORCUS}/api/sources/{name}/photometry",headers={"Authorization":f"token {tok}"})
    try: data=json.load(urllib.request.urlopen(req,timeout=60)).get("data",[])
    except Exception as e: print("orcus fail",name,e); return []
    ins=lambda i:"Z" if "ZTF" in str(i) else "R" if "LSST" in str(i) else "A" if "ATLAS" in str(i) else "G" if "GOTO" in str(i) else "P" if "GPC" in str(i) else "O"
    pts=[[round(p["mjd"]-61000,2),re.sub(r"^(ztf|lsst|sdss|ps1)","",str(p["filter"])),round(p["mag"],2),round(p.get("magerr") or 0,2),ins(p.get("instrument_name"))]
         for p in data if p.get("mag") is not None and (p.get("magerr") or 0)<1]
    return sorted(pts)

rows=list(csv.DictReader(io.StringIO(urllib.request.urlopen(SHEET,timeout=60).read().decode("utf-8"))))
sheet_title="FAST Root Sheet (first tab)"
cache_p=os.path.join(HERE,"lc_cache.json"); cache=json.load(open(cache_p)) if os.path.exists(cache_p) else {}
tok=None; out=[]
for r in rows:
    n=(r.get("Target Name") or "").strip()
    try: ra=float(r.get("RA") or ""); dec=float(r.get("DEC") or "")
    except ValueError: continue
    if not n: continue
    mg=r.get("r-mag (approx)",""); m=re.match(r"\s*([\d.]+)",mg); band=re.search(r"\(([^)]*)\)",mg)
    pr=(r.get("Priority") or "").strip()
    t={"n":n,"ra":round(ra,5),"dec":round(dec,5),"p":int(float(pr)) if re.match(r"^\d+(\.\d+)?$",pr) else 9,"m":float(m.group(1)) if m else None,
       "mb":band.group(1) if band else "","mag":mg,"t":r.get("SN type (if available)",""),"no":r.get("Notes",""),"ob":r.get("Observed?",""),
       "o":r.get("Orcus Link",""),"y":r.get("YSEPZ Link",""),"tns":r.get("TNS?",""),"rq":r.get("Requested by:",""),"nx":r.get("Next step?","")}
    k=re.sub(r"^(AT|SN)\s?","",n)
    if k not in cache or not cache[k].get("lc"):
        tok=tok or env_token(); pts=orcus_lc(k,tok)
        if pts: cache[k]={"lc":[p for p in pts if p[0]>=230],"lcs":"Orcus"}
    if k in cache and cache[k].get("lc"): t["lc"]=cache[k]["lc"]; t["lcs"]=cache[k]["lcs"]
    out.append(t)
json.dump(cache,open(cache_p,"w"),separators=(",",":"))
data={"asof":datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"),"sheet":sheet_title,"targets":out}
tpl=open(os.path.join(HERE,"template.html")).read()
html=tpl.replace("/*__DATA__*/null",json.dumps(data,separators=(",",":")).replace("</","<\\/"))
open(os.path.join(HERE,"fast-queue-sky.html"),"w").write(html)
# GitHub Pages serves index.html: a full document, so add the skeleton the Claude artifact host normally provides
open(os.path.join(HERE,"index.html"),"w").write('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>'+html+"</body></html>")
print(f"targets: {len(out)} | with light curves: {sum(1 for t in out if t.get('lc'))} | wrote fast-queue-sky.html and index.html")
