"""

Combinations: <DD|DI>-<RW|CW>-<ST|MT>-<0|1>shot, across book / movie / flight.

Usage:
  python run.py --dataset book
  python run.py --dataset movie
  python run.py --dataset flight
  python run.py --dataset flight_blind   # anonymizes flight IDs before prompting
  python run.py --dataset all

"""

import os
import argparse
import datetime

import config
from data.loader import (
    load_book_claims, load_movie_claims, load_flight_claims,
    BOOK_ATTRS, MOVIE_ATTRS, FLIGHT_ATTRS,
)
from evaluation.truth_loader import load_book_truth, load_movie_truth, load_flight_truth
from evaluation.metrics import compute_metrics, compute_per_key_metrics, compute_flight_metrics
from llm.prompt_builder import (
    build_book_prompt_rw, build_book_prompt_cw,
    build_movie_prompt_rw, build_movie_prompt_cw,
    build_flight_prompt_rw, build_flight_prompt_cw,
)
from llm.client import call_llm
from llm.parser import parse_response, parse_rw_value
from llm.parser_flight import (
    parse_flight_response, parse_flight_di_response, parse_flight_cw_response, parse_time,
)

DOMAINS = ["dd_rw_st", "dd_rw_mt", "dd_cw_st", "dd_cw_mt",
           "di_rw_st", "di_rw_mt", "di_cw_st", "di_cw_mt"]

_GATE_ATTRS = {"Departure gate", "Arrival gate"}


def _normalize_truth_dates(truth_dict: dict) -> dict:
    normalized = {}
    for fid, attrs in truth_dict.items():
        norm_attrs = {}
        for attr, val in attrs.items():
            if attr in _GATE_ATTRS:
                norm_attrs[attr] = val.strip().upper()
            else:
                parsed = parse_time(val)
                norm_attrs[attr] = parsed if parsed else val
        normalized[fid] = norm_attrs
    return normalized

SHOTS = [0, 1]


def _style_tag() -> str:
    return f"{config.PROMPT_DOMAIN}_{config.PROMPT_SHOT}shot"


def _dd_or_di_layout(domain: str):
    dd_or_di, layout, _truth = domain.split("_")
    return dd_or_di, layout


def _rw_label(attrs: list, attr: str, dd_or_di: str) -> str:
    if dd_or_di == "dd":
        return attr
    return f"Attribute {attrs.index(attr) + 1}"


# ── Book / Movie save ───────────────────────────────────────────────────────────

def _escape_raw(text: str) -> str:
    return text.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")


def _save_raw(model: str, style: str, dataset: str, ts: str, raw_dict: dict):
    raw_path = os.path.join(config.OUTPUT_DIR, f"raw_{model}_{style}_{dataset}_{ts}.txt")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write("key\tattribute\traw_response\n")
        for key in sorted(raw_dict.keys(), key=str):
            value = raw_dict[key]
            if isinstance(value, dict):
                for attr, raw in value.items():
                    f.write(f"{key}\t{attr}\t{_escape_raw(raw)}\n")
            else:
                f.write(f"{key}\t\t{_escape_raw(value)}\n")
    return raw_path


def _save_book_movie(dataset: str, pred_dict: dict, metrics: dict, truth_dict: dict, raw_dict: dict):
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    ts    = datetime.datetime.now().strftime("%d%m-%H%M")
    model = config.LLM_MODEL
    style = _style_tag()

    metric_path = os.path.join(config.OUTPUT_DIR, f"metrics_{model}_{style}_{dataset}_{ts}.txt")
    with open(metric_path, "w", encoding="utf-8") as f:
        f.write("Model\tStyle\tRecall\tPrecision\tF1\n")
        f.write(f"LLM ({config.LLM_PROVIDER}/{config.LLM_MODEL})\t{style}\t"
                f"{metrics['recall']}\t{metrics['precision']}\t{metrics['f1']}\n")

    per_key = compute_per_key_metrics(truth_dict, pred_dict)
    detail_path = os.path.join(config.OUTPUT_DIR, f"detail_{model}_{style}_{dataset}_{ts}.csv")
    with open(detail_path, "w", encoding="utf-8") as f:
        f.write("key,truth,predicted,TP,FN,FP,TP_values,FN_values,FP_values\n")
        for row in per_key:
            f.write(f'"{row["key"]}","{row["truth"]}","{row["predicted"]}",'
                    f'{row["tp"]},{row["fn"]},{row["fp"]},'
                    f'"{row["tp_values"]}","{row["fn_values"]}","{row["fp_values"]}"\n')

    _save_raw(model, style, dataset, ts, raw_dict)


# ── Book ──────────────────────────────────────────────────────────────────────

def run_book(domains: list, shots: list):
    claims  = load_book_claims(config.BOOK_CLAIMS_PATH)
    truth   = load_book_truth(config.BOOK_TRUTH_PATH)
    targets = sorted(set(claims.keys()) & set(truth.keys()))
    print(f"  {len(targets)} books")

    for shot in shots:
        for domain in domains:
            config.PROMPT_DOMAIN = domain
            config.PROMPT_SHOT   = shot
            dd_or_di, layout = _dd_or_di_layout(domain)
            label = _rw_label(BOOK_ATTRS, "Author", dd_or_di)
            print(f"  [book] {_style_tag()}")

            pred_dict = {}
            raw_dict  = {}
            for i, isbn in enumerate(targets):
                if layout == "rw":
                    raw   = call_llm(build_book_prompt_rw(isbn, claims[isbn]))
                    value = parse_rw_value(raw, label)
                else:
                    raw   = call_llm(build_book_prompt_cw(isbn, "Author", claims[isbn].get("Author", [])))
                    value = raw
                pred_dict[isbn] = parse_response(value)
                raw_dict[isbn]  = raw
                if (i + 1) % 50 == 0:
                    print(f"    {i+1}/{len(targets)} processed...")

            metrics = compute_metrics(truth, pred_dict)
            print(f"    Recall={metrics['recall']:.4f}  Precision={metrics['precision']:.4f}  F1={metrics['f1']:.4f}")
            _save_book_movie("book", pred_dict, metrics, truth, raw_dict)


# ── Movie ─────────────────────────────────────────────────────────────────────

def run_movie(domains: list, shots: list):
    claims  = load_movie_claims(config.MOVIE_CLAIMS_PATH)
    truth   = load_movie_truth(config.MOVIE_TRUTH_PATH)
    targets = sorted(set(claims.keys()) & set(truth.keys()))
    print(f"  {len(targets)} movies")

    for shot in shots:
        for domain in domains:
            config.PROMPT_DOMAIN = domain
            config.PROMPT_SHOT   = shot
            dd_or_di, layout = _dd_or_di_layout(domain)
            label = _rw_label(MOVIE_ATTRS, "Director", dd_or_di)
            print(f"  [movie] {_style_tag()}")

            pred_dict = {}
            raw_dict  = {}
            for i, (title, year) in enumerate(targets):
                if layout == "rw":
                    raw   = call_llm(build_movie_prompt_rw(title, year, claims[(title, year)]))
                    value = parse_rw_value(raw, label)
                else:
                    raw   = call_llm(build_movie_prompt_cw(title, year, "Director", claims[(title, year)].get("Director", [])))
                    value = raw
                pred_dict[(title, year)] = parse_response(value)
                raw_dict[(title, year)]  = raw
                if (i + 1) % 50 == 0:
                    print(f"    {i+1}/{len(targets)} processed...")

            metrics = compute_metrics(truth, pred_dict)
            print(f"    Recall={metrics['recall']:.4f}  Precision={metrics['precision']:.4f}  F1={metrics['f1']:.4f}")
            _save_book_movie("movie", pred_dict, metrics, truth, raw_dict)


# ── Flight ────────────────────────────────────────────────────────────────────

def _print_metrics_flight(metrics: dict):
    o = metrics["overall"]
    print(f"    [OVERALL] Recall={o['recall']:.4f}  Precision={o['precision']:.4f}"
          f"  F1={o['f1']:.4f}  (TP={o['tp']}, FN={o['fn']}, FP={o['fp']})")
    for attr, m in metrics["by_attr"].items():
        print(f"      {attr:<25} R={m['recall']:.4f}  P={m['precision']:.4f}  F1={m['f1']:.4f}")


def _save_flight(style_tag: str, pred_dict: dict, metrics: dict, truth_dict: dict, raw_dict: dict):
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    ts    = datetime.datetime.now().strftime("%d%m-%H%M")
    model = config.LLM_MODEL

    metric_path = os.path.join(config.OUTPUT_DIR, f"metrics_{model}_{style_tag}_flight_{ts}.txt")
    with open(metric_path, "w", encoding="utf-8") as f:
        o = metrics["overall"]
        f.write("Model\tStyle\tDataset\tRecall\tPrecision\tF1\n")
        f.write(f"LLM ({config.LLM_PROVIDER}/{model})\t{style_tag}\tflight\t"
                f"{o['recall']}\t{o['precision']}\t{o['f1']}\n\n")
        f.write("Attribute\tRecall\tPrecision\tF1\tTP\tFN\tFP\n")
        for attr, m in metrics["by_attr"].items():
            f.write(f"{attr}\t{m['recall']}\t{m['precision']}\t{m['f1']}\t"
                    f"{m['tp']}\t{m['fn']}\t{m['fp']}\n")

    detail_path = os.path.join(config.OUTPUT_DIR, f"detail_{model}_{style_tag}_flight_{ts}.txt")
    with open(detail_path, "w", encoding="utf-8") as f:
        f.write("flight_id\tattribute\ttruth\tpredicted\tTP\tFN\tFP\tTP_value\tFN_value\tFP_value\n")
        for fid in sorted(pred_dict.keys()):
            truth_attrs = truth_dict.get(fid, {})
            pred_attrs  = pred_dict[fid]
            for attr in FLIGHT_ATTRS:
                t = truth_attrs.get(attr, "")
                p = pred_attrs.get(attr, "")
                if t and p and t == p:
                    tp, fn, fp = 1, 0, 0
                    tp_val, fn_val, fp_val = t, "", ""
                elif t and p:
                    tp, fn, fp = 0, 1, 1
                    tp_val, fn_val, fp_val = "", t, p
                elif t:
                    tp, fn, fp = 0, 1, 0
                    tp_val, fn_val, fp_val = "", t, ""
                elif p:
                    tp, fn, fp = 0, 0, 1
                    tp_val, fn_val, fp_val = "", "", p
                else:
                    tp, fn, fp = 0, 0, 0
                    tp_val, fn_val, fp_val = "", "", ""
                f.write(f"{fid}\t{attr}\t{t}\t{p}\t{tp}\t{fn}\t{fp}\t{tp_val}\t{fn_val}\t{fp_val}\n")

    _save_raw(model, style_tag, "flight", ts, raw_dict)


def run_flight(domains: list, shots: list, claims_path: str, truth_path: str, blind: bool = False):
    claims  = load_flight_claims(claims_path)
    truth   = _normalize_truth_dates(load_flight_truth(truth_path))
    targets = sorted(set(claims.keys()) & set(truth.keys()))

    anon_ids: dict = {}
    if blind:
        anon_ids = {fid: f"FLIGHT-{i+1:03d}" for i, fid in enumerate(targets)}
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        date_tag     = os.path.basename(claims_path).replace("-data.txt", "")
        mapping_path = os.path.join(config.OUTPUT_DIR, f"flight_id_mapping_{date_tag}.txt")
        with open(mapping_path, "w", encoding="utf-8") as f:
            f.write("anon_id\treal_id\n")
            for fid, anon in sorted(anon_ids.items(), key=lambda x: x[1]):
                f.write(f"{anon}\t{fid}\n")
        print(f"  {len(targets)} flights (IDs anonymized, mapping -> {mapping_path})")
    else:
        print(f"  {len(targets)} flights")

    for shot in shots:
        for domain in domains:
            config.PROMPT_DOMAIN = domain
            config.PROMPT_SHOT   = shot
            dd_or_di, layout = _dd_or_di_layout(domain)
            prefix    = "blind_" if blind else ""
            style_tag = f"{prefix}{_style_tag()}"
            print(f"\n  [{style_tag}]")

            pred_dict = {}
            raw_dict  = {}
            for j, fid in enumerate(targets):
                flight_key = anon_ids[fid] if blind else fid
                if layout == "rw":
                    raw = call_llm(build_flight_prompt_rw(flight_key, claims[fid]))
                    pred_dict[fid] = parse_flight_di_response(raw) if dd_or_di == "di" else parse_flight_response(raw)
                    raw_dict[fid]  = raw
                else:
                    attrs = {}
                    raws  = {}
                    for attr in FLIGHT_ATTRS:
                        raw   = call_llm(build_flight_prompt_cw(flight_key, attr, claims[fid].get(attr, [])))
                        value = parse_flight_cw_response(raw, attr)
                        raws[attr] = raw
                        if value:
                            attrs[attr] = value
                    pred_dict[fid] = attrs
                    raw_dict[fid]  = raws
                if (j + 1) % 20 == 0:
                    print(f"    {j+1}/{len(targets)} processed...")

            metrics = compute_flight_metrics(truth, pred_dict)
            _print_metrics_flight(metrics)
            _save_flight(style_tag, pred_dict, metrics, truth, raw_dict)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM data fusion-STMT")
    parser.add_argument("--dataset", choices=["book", "movie", "flight", "flight_blind", "all"], default="all")
    parser.add_argument("--claims", default=config.FLIGHT_CLAIMS_PATH, help="Flight claims file")
    parser.add_argument("--truth",  default=config.FLIGHT_TRUTH_PATH,  help="Flight truth file")
    args = parser.parse_args()

    print(f"=== Model: {config.LLM_MODEL} ===")

    if args.dataset in ("book", "all"):
        print("\n-> BOOK")
        run_book(DOMAINS, SHOTS)

    if args.dataset in ("movie", "all"):
        print("\n-> MOVIE")
        run_movie(DOMAINS, SHOTS)

    if args.dataset in ("flight", "all"):
        print("\n-> FLIGHT")
        run_flight(DOMAINS, SHOTS, args.claims, args.truth)

    if args.dataset == "flight_blind":
        print("\n-> FLIGHT (blind)")
        run_flight(DOMAINS, SHOTS, args.claims, args.truth, blind=True)

    print(f"\nDone. Results -> {config.OUTPUT_DIR}/")
