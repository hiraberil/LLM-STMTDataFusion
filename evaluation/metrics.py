"""
Evaluation metrics for all datasets.

Book / Movie (multi-truth): token-based Recall, Precision, F1.
Flight (single-truth): exact-match Recall, Precision, F1 per attribute.
"""

from data.loader import FLIGHT_ATTRS


def _token_match(truth_val: str, pred_val: str) -> bool:
    # Two name strings match if they have the same token set.
    t_tokens = set(truth_val.split())
    p_tokens = set(pred_val.split())
    return len(t_tokens) == len(p_tokens) and len(t_tokens - p_tokens) == 0


def compute_metrics(truth_dict: dict, pred_dict: dict) -> dict:
    # Computes overall Recall, Precision, F1 across all entities.
    tp = fn = fp = 0

    for key, truth_set in truth_dict.items():
        if key not in pred_dict:
            continue

        pred_set = pred_dict[key]
        truth_found = set()
        pred_found  = set()

        for t in truth_set:
            for p in pred_set:
                if _token_match(t, p):
                    truth_found.add(t)
                    pred_found.add(p)

        tp += len(truth_found)
        fn += len(truth_set - truth_found)
        fp += len(pred_set  - pred_found)

    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    f1        = (2 * recall * precision / (recall + precision)
                 if (recall + precision) > 0 else 0.0)

    return {
        "recall":    round(recall, 4),
        "precision": round(precision, 4),
        "f1":        round(f1, 4),
        "tp":        tp,
        "fn":        fn,
        "fp":        fp,
    }


def compute_per_key_metrics(truth_dict: dict, pred_dict: dict) -> list:
    # Computes per-entity metrics; returns a list of rows for detailed output.
    rows = []
    for key, truth_set in truth_dict.items():
        if key not in pred_dict:
            continue

        pred_set = pred_dict[key]
        truth_found = set()
        pred_found  = set()

        for t in truth_set:
            for p in pred_set:
                if _token_match(t, p):
                    truth_found.add(t)
                    pred_found.add(p)

        tp_vals = truth_found
        fn_vals = truth_set - truth_found
        fp_vals = pred_set  - pred_found

        rows.append({
            "key":       str(key),
            "truth":     "; ".join(sorted(truth_set)),
            "predicted": "; ".join(sorted(pred_set)),
            "tp":        len(tp_vals),
            "fn":        len(fn_vals),
            "fp":        len(fp_vals),
            "tp_values": "; ".join(sorted(tp_vals)),
            "fn_values": "; ".join(sorted(fn_vals)),
            "fp_values": "; ".join(sorted(fp_vals)),
        })

    return sorted(rows, key=lambda r: r["key"])


# ── Flight ────────────────────────────────────────────────────────────────────

def compute_flight_metrics(truth_dict: dict, pred_dict: dict) -> dict:
    # Computes per-attribute and overall metrics. Returns {"overall": {...}, "by_attr": {...}}.
    attr_counts = {attr: {"tp": 0, "fn": 0, "fp": 0} for attr in FLIGHT_ATTRS}

    for flight_id, truth_attrs in truth_dict.items():
        if flight_id not in pred_dict:
            for attr in truth_attrs:
                attr_counts[attr]["fn"] += 1
            continue

        pred_attrs = pred_dict[flight_id]

        for attr in FLIGHT_ATTRS:
            t_val = truth_attrs.get(attr)
            p_val = pred_attrs.get(attr)

            if t_val and p_val:
                if t_val == p_val:
                    attr_counts[attr]["tp"] += 1
                else:
                    attr_counts[attr]["fn"] += 1
                    attr_counts[attr]["fp"] += 1
            elif t_val and not p_val:
                attr_counts[attr]["fn"] += 1
            elif p_val and not t_val:
                attr_counts[attr]["fp"] += 1

    def _calc(tp, fn, fp):
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1 = (2 * recall * precision / (recall + precision)
              if (recall + precision) > 0 else 0.0)
        return {
            "recall": round(recall, 4), "precision": round(precision, 4),
            "f1": round(f1, 4), "tp": tp, "fn": fn, "fp": fp,
        }

    by_attr = {attr: _calc(**attr_counts[attr]) for attr in FLIGHT_ATTRS}

    total_tp = sum(c["tp"] for c in attr_counts.values())
    total_fn = sum(c["fn"] for c in attr_counts.values())
    total_fp = sum(c["fp"] for c in attr_counts.values())
    overall  = _calc(total_tp, total_fn, total_fp)

    return {"overall": overall, "by_attr": by_attr}
