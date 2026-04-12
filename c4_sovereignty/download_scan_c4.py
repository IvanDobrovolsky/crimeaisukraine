#!/usr/bin/env python3
"""Download each C4 EN shard to disk, scan locally, delete. 16 parallel workers."""
import argparse, json, re, gzip, time, os, sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "pipelines" / "_shared"))
from sovereignty_classifier import SovereigntyClassifier

CRIMEA_TERMS = ["crimea","crimean","simferopol","sevastopol","yalta","kerch","feodosia","evpatoria","bakhchisarai","dzhankoi","alushta"]

def has_crimea(t):
    tl=t.lower(); return any(x in tl for x in CRIMEA_TERMS)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--file-start",type=int,required=True)
    p.add_argument("--file-end",type=int,required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()

    from huggingface_hub import hf_hub_download
    clf = SovereigntyClassifier()

    print(f"[{datetime.now(timezone.utc).isoformat()}] C4 EN files {a.file_start}-{a.file_end}",flush=True)
    total=0;crimea=0;ru_c=0;ua_c=0;t0=time.time()

    with open(a.output,"w") as outf:
        for fi in range(a.file_start, a.file_end+1):
            fname = f"en/c4-train.{fi:05d}-of-01024.json.gz"
            sc=0
            try:
                local = hf_hub_download("allenai/c4", fname, repo_type="dataset")
                with gzip.open(local,"rt",encoding="utf-8") as gz:
                    for line in gz:
                        try:
                            total+=1
                            doc=json.loads(line)
                            text=doc.get("text","")
                            if not has_crimea(text): continue
                            crimea+=1; sc+=1
                            ms=[text.lower().find(x) for x in CRIMEA_TERMS if x in text.lower()]
                            idx=min(ms) if ms else 0; w=text[max(0,idx-500):idx+1500]
                            result=clf.classify(w)
                            if result.label=="russia": ru_c+=1
                            elif result.label=="ukraine": ua_c+=1
                            outf.write(json.dumps({"corpus":"c4_en","label":result.label,"url":doc.get("url",""),"text":text[:3000],"signals":[s.matched for s in result.signals]},ensure_ascii=False)+"\n")
                            outf.flush()
                        except Exception: continue
            except Exception as e:
                print(f"  File {fi}: ERROR {e}",flush=True); continue
            el=time.time()-t0
            print(f"  File {fi:04d}: {sc} Crimea (tot:{crimea} RU={ru_c} UA={ua_c} {total:,}docs {el:.0f}s)",flush=True)

    el=time.time()-t0
    with open(a.output.replace(".jsonl","_summary.json"),"w") as f:
        json.dump({"files":f"{a.file_start}-{a.file_end}","total_docs":total,"crimea_docs":crimea,"russia":ru_c,"ukraine":ua_c,"elapsed_hours":round(el/3600,2)},f,indent=2)
    print(f"COMPLETE: {crimea} Crimea, RU={ru_c} UA={ua_c}, {el/3600:.1f}h",flush=True)

if __name__=="__main__": main()
