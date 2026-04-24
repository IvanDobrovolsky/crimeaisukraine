#!/usr/bin/env python3
"""
Parallel C4 scan: extract ALL Crimea-mentioning documents with full text.
Uses multiprocessing to saturate all CPU cores.

Usage:
    python3 c4_sovereignty/scan_c4_parallel.py --lang en --workers 8
    python3 c4_sovereignty/scan_c4_parallel.py --lang ru --workers 8
    python3 c4_sovereignty/scan_c4_parallel.py --lang uk --workers 8
"""
import argparse, gzip, json, os, re, sys, time
from multiprocessing import Pool, cpu_count
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "pipelines" / "_shared"))

CRIMEA_TERMS_EN = [
    "crimea","crimean","simferopol","sevastopol","yalta","kerch",
    "feodosia","evpatoria","bakhchisarai","dzhankoi","alushta",
]
CRIMEA_TERMS_RU = [
    "крым","крымск","симферополь","севастополь","ялта","керчь",
    "феодосия","евпатория","бахчисарай","джанкой","алушта",
]
CRIMEA_TERMS_UK = [
    "крим","кримськ","сімферополь","севастополь","ялта","керч",
    "феодосія","євпаторія","бахчисарай","джанкой","алушта",
]

C4_CACHE = os.path.expanduser(
    "~/.cache/huggingface/hub/datasets--allenai--c4/snapshots/"
    "1588ec454efa1a09f29cd18ddd04fe05fc8653a2"
)


def get_shard_path(lang, shard_num):
    if lang == "en":
        return os.path.join(C4_CACHE, "en", f"c4-train.{shard_num:05d}-of-01024.json.gz")
    else:
        total = 4096
        return os.path.join(C4_CACHE, "multilingual",
                            f"c4-{lang}.tfrecord-{shard_num:05d}-of-{total:05d}.json.gz")


def get_crimea_terms(lang):
    if lang == "en":
        return CRIMEA_TERMS_EN
    elif lang == "ru":
        return CRIMEA_TERMS_EN + CRIMEA_TERMS_RU
    elif lang == "uk":
        return CRIMEA_TERMS_EN + CRIMEA_TERMS_UK
    return CRIMEA_TERMS_EN


def scan_shard(args):
    """Scan one shard. Called by pool workers."""
    lang, shard_num, output_dir, download_missing = args

    from sovereignty_classifier import SovereigntyClassifier
    clf = SovereigntyClassifier()
    terms = get_crimea_terms(lang)

    path = get_shard_path(lang, shard_num)
    real_path = os.path.realpath(path)

    if not os.path.exists(real_path):
        if not download_missing:
            return {"shard": shard_num, "status": "missing", "total": 0,
                    "crimea": 0, "russia": 0, "ukraine": 0}
        try:
            from huggingface_hub import hf_hub_download
            if lang == "en":
                fname = f"en/c4-train.{shard_num:05d}-of-01024.json.gz"
            else:
                fname = f"multilingual/c4-{lang}.tfrecord-{shard_num:05d}-of-04096.json.gz"
            real_path = hf_hub_download("allenai/c4", fname, repo_type="dataset")
        except Exception as e:
            return {"shard": shard_num, "status": f"download_error: {e}",
                    "total": 0, "crimea": 0, "russia": 0, "ukraine": 0}

    outfile = os.path.join(output_dir, f"shard_{shard_num:05d}.jsonl")
    total = 0
    crimea = 0
    russia = 0
    ukraine = 0

    try:
        with gzip.open(real_path, "rt", encoding="utf-8") as gz, \
             open(outfile, "w") as outf:
            for line in gz:
                total += 1
                try:
                    doc = json.loads(line)
                    text = doc.get("text", "")
                    tl = text.lower()
                    if not any(t in tl for t in terms):
                        continue
                    crimea += 1
                    result = clf.classify(text[:3000])
                    if result.label == "russia":
                        russia += 1
                    elif result.label == "ukraine":
                        ukraine += 1

                    outf.write(json.dumps({
                        "corpus": f"c4_{lang}",
                        "shard": shard_num,
                        "url": doc.get("url", ""),
                        "text": text[:3000],
                        "label": result.label,
                        "signals": [s.matched for s in result.signals],
                        "is_quoted": result.is_quoted,
                        "ru_score": result.ru_score,
                        "ua_score": result.ua_score,
                    }, ensure_ascii=False) + "\n")
                except Exception:
                    continue
    except Exception as e:
        return {"shard": shard_num, "status": f"error: {e}",
                "total": total, "crimea": crimea, "russia": russia, "ukraine": ukraine}

    return {"shard": shard_num, "status": "ok", "total": total,
            "crimea": crimea, "russia": russia, "ukraine": ukraine}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True, choices=["en", "ru", "uk"])
    parser.add_argument("--workers", type=int, default=max(1, cpu_count() - 2))
    parser.add_argument("--download", action="store_true",
                        help="Download missing shards (otherwise skip them)")
    parser.add_argument("--cached-only", action="store_true",
                        help="Only scan shards already in HF cache")
    args = parser.parse_args()

    total_shards = 1024 if args.lang == "en" else 4096
    output_dir = f"c4_sovereignty/data/c4_raw/{args.lang}"
    os.makedirs(output_dir, exist_ok=True)

    # Find cached vs missing
    cached = set()
    for shard_num in range(total_shards):
        path = get_shard_path(args.lang, shard_num)
        if os.path.exists(os.path.realpath(path)):
            cached.add(shard_num)

    missing = sorted(set(range(total_shards)) - cached)

    # Already-scanned shards (skip resume)
    done = set()
    for f in os.listdir(output_dir):
        m = re.match(r"shard_(\d+)\.jsonl", f)
        if m and os.path.getsize(os.path.join(output_dir, f)) > 0:
            done.add(int(m.group(1)))

    if args.cached_only:
        to_scan = sorted(cached - done)
        print(f"Scanning {len(to_scan)} cached shards (skipping {len(done)} done, {len(missing)} not cached)")
    else:
        to_scan = sorted((cached | (set(range(total_shards)) if args.download else set())) - done)
        print(f"Scanning {len(to_scan)} shards ({len(cached)} cached, {len(missing)} to download, {len(done)} done)")

    print(f"Language: {args.lang}, Workers: {args.workers}, Output: {output_dir}/")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")

    tasks = [(args.lang, s, output_dir, args.download) for s in to_scan]
    t0 = time.time()
    completed = 0
    total_crimea = 0
    total_russia = 0
    total_ukraine = 0
    total_docs = 0

    with Pool(args.workers) as pool:
        for result in pool.imap_unordered(scan_shard, tasks):
            completed += 1
            total_docs += result["total"]
            total_crimea += result["crimea"]
            total_russia += result["russia"]
            total_ukraine += result["ukraine"]

            if completed % 20 == 0 or completed <= 3:
                elapsed = time.time() - t0
                rate = completed / elapsed
                eta = (len(to_scan) - completed) / rate if rate > 0 else 0
                print(f"  [{completed}/{len(to_scan)}] "
                      f"Crimea={total_crimea:,} RU={total_russia:,} UA={total_ukraine:,} "
                      f"| {total_docs:,} docs | {elapsed:.0f}s | ETA {eta/60:.0f}min "
                      f"| shard {result['shard']:04d}: {result['status']}")

    elapsed = time.time() - t0

    # Merge shard files into one
    merged = f"c4_sovereignty/data/c4_raw/c4_{args.lang}_crimea_full.jsonl"
    print(f"\nMerging {completed} shard files → {merged}")
    with open(merged, "w") as out:
        for shard_num in sorted(to_scan | done):
            shard_file = os.path.join(output_dir, f"shard_{shard_num:05d}.jsonl")
            if os.path.exists(shard_file):
                with open(shard_file) as sf:
                    for line in sf:
                        out.write(line)

    merged_lines = sum(1 for _ in open(merged))

    summary = {
        "lang": args.lang,
        "shards_scanned": completed,
        "shards_total": total_shards,
        "total_docs": total_docs,
        "crimea_docs": total_crimea,
        "russia_framing": total_russia,
        "ukraine_framing": total_ukraine,
        "merged_lines": merged_lines,
        "elapsed_hours": round(elapsed / 3600, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    summary_path = merged.replace(".jsonl", "_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nCOMPLETE: {total_crimea:,} Crimea docs, "
          f"RU={total_russia:,} UA={total_ukraine:,}, "
          f"{elapsed/3600:.1f}h, {merged_lines:,} lines in {merged}")


if __name__ == "__main__":
    main()
