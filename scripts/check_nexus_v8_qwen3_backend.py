from __future__ import annotations
import argparse, hashlib, json, urllib.request
from pathlib import Path

EXPECTED_14B_SHA256="500a8806e85ee9c83f3ae08420295592451379b4f8cf2d0f41c15dffeb6b81f0"

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(8<<20),b""): h.update(block)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model")
    p.add_argument("--base-url",default="http://127.0.0.1:8080/v1")
    a=p.parse_args()
    out={"model_file":None,"server":None}
    if a.model:
        path=Path(a.model)
        digest=sha256(path) if path.is_file() else None
        out["model_file"]={"exists":path.is_file(),"bytes":path.stat().st_size if path.is_file() else 0,"sha256":digest,"checksum_ok":digest==EXPECTED_14B_SHA256}
    try:
        with urllib.request.urlopen(a.base_url.rstrip("/")+"/models",timeout=10) as r:
            body=json.loads(r.read().decode())
        ids=[str(x.get("id")) for x in body.get("data",[])]
        out["server"]={"reachable":True,"models":ids,"qwen3_14b_present":"Qwen3-14B-Q4_K_M" in ids}
    except Exception as e:
        out["server"]={"reachable":False,"error":f"{type(e).__name__}: {e}"}
    print(json.dumps(out,ensure_ascii=False,indent=2))
    if a.model and not out["model_file"]["checksum_ok"]: raise SystemExit(2)

if __name__=="__main__": main()
