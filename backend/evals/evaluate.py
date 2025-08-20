import argparse
import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Question:
    id: str
    category: str
    type: str
    prompt: str
    reference_answer: Optional[str] = None
    language: Optional[str] = None
    entry_point: Optional[str] = None
    tests: Optional[List[Dict[str, Any]]] = None


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    with file_path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def to_question(obj: Dict[str, Any]) -> Question:
    return Question(
        id=obj.get("id"),
        category=obj.get("category"),
        type=obj.get("type"),
        prompt=obj.get("prompt"),
        reference_answer=obj.get("reference_answer"),
        language=obj.get("language"),
        entry_point=obj.get("entry_point"),
        tests=obj.get("tests"),
    )


def parse_number_or_fraction(text: str) -> Tuple[Optional[Fraction], Optional[float]]:
    text = text.strip()
    if "/" in text:
        try:
            return Fraction(text), None
        except Exception:
            pass
    # decimal number
    try:
        return None, float(text.replace(",", "."))
    except Exception:
        return None, None


def compare_numeric(reference: str, candidate: str, tol: float = 1e-2) -> bool:
    ref_frac, ref_float = parse_number_or_fraction(reference)
    cand_frac, cand_float = parse_number_or_fraction(candidate)

    if ref_frac is not None and cand_frac is not None:
        return ref_frac == cand_frac
    if ref_frac is not None and cand_float is not None:
        return abs(float(ref_frac) - cand_float) <= tol
    if ref_float is not None and cand_frac is not None:
        return abs(ref_float - float(cand_frac)) <= tol
    if ref_float is not None and cand_float is not None:
        return abs(ref_float - cand_float) <= tol
    # fallback strict string compare (normalized)
    return reference.strip() == candidate.strip()


def compare_text(reference: str, candidate: str) -> bool:
    return reference.replace(" ", "").strip().lower() == candidate.replace(" ", "").strip().lower()


def compare_mcq(reference: str, candidate: str) -> bool:
    ref = (reference or "").strip().upper()[:1]
    cand = (candidate or "").strip().upper()[:1]
    return ref == cand and ref in {"A", "B", "C", "D"}


def run_python_tests(code: str, entry_point: str, tests: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    # Safe-ish builtins
    safe_builtins = {
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "enumerate": enumerate,
        "filter": filter,
        "float": float,
        "int": int,
        "len": len,
        "list": list,
        "dict": dict,
        "str": str,
        "set": set,
        "tuple": tuple,
        "max": max,
        "min": min,
        "map": map,
        "range": range,
        "reversed": reversed,
        "sorted": sorted,
        "sum": sum,
        "zip": zip,
    }
    # Very restricted import allowing only whitelisted modules
    allowed_modules = {"collections"}
    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.split(".")[0] in allowed_modules:
            return __import__(name, globals, locals, fromlist, level)
        raise ImportError("__import__ not found")

    globals_dict: Dict[str, Any] = {"__builtins__": safe_builtins, "__import__": safe_import}
    locals_dict: Dict[str, Any] = {}
    messages: List[str] = []
    try:
        exec(code, globals_dict, locals_dict)
    except Exception as e:
        return False, [f"Kod çalıştırma hatası: {e}"]

    func = locals_dict.get(entry_point) or globals_dict.get(entry_point)
    if func is None or not callable(func):
        return False, [f"Fonksiyon bulunamadı: {entry_point}"]

    all_ok = True
    for idx, test in enumerate(tests):
        args = test.get("args", [])
        kwargs = test.get("kwargs", {})
        expected = test.get("output")
        try:
            result = func(*args, **kwargs)
            # Normalize tuple/list equality for convenience
            if isinstance(expected, list) and isinstance(result, tuple):
                result_cmp = list(result)
            else:
                result_cmp = result
            ok = result_cmp == expected
        except Exception as e:
            ok = False
            result = f"Exception: {e}"
        if not ok:
            all_ok = False
            messages.append(f"Test {idx+1} başarısız. args={args} kwargs={kwargs} beklenen={expected} alınan={result}")
    return all_ok, messages


def evaluate(questions_path: Path, responses_path: Path) -> Dict[str, Any]:
    questions = [to_question(q) for q in load_jsonl(questions_path)]
    responses_raw = load_jsonl(responses_path)
    responses: Dict[str, Dict[str, Any]] = {r["id"]: r for r in responses_raw if "id" in r}

    totals = {"math": 0, "turkish": 0, "coding": 0}
    detailed: List[Dict[str, Any]] = []

    for q in questions:
        r = responses.get(q.id, {})
        item: Dict[str, Any] = {"id": q.id, "category": q.category}
        correct = False
        detail_msg: List[str] = []

        if q.category == "math":
            cand = (r.get("answer") or "").strip()
            correct = compare_numeric(q.reference_answer or "", cand) if q.type == "numeric" else compare_text(q.reference_answer or "", cand)
            item["expected"] = q.reference_answer
            item["got"] = cand
        elif q.category == "turkish":
            cand = (r.get("answer") or "").strip()
            correct = compare_mcq(q.reference_answer or "", cand)
            item["expected"] = q.reference_answer
            item["got"] = cand
        elif q.category == "coding":
            code = r.get("code") or ""
            if (q.language == "python") and q.entry_point and q.tests:
                correct, detail_msg = run_python_tests(code, q.entry_point, q.tests)
            else:
                detail_msg = ["Desteklenmeyen kodlama sorusu türü"]
                correct = False
            item["messages"] = detail_msg
        else:
            detail_msg = ["Bilinmeyen kategori"]
            correct = False

        if correct:
            totals[q.category] += 1
        item["correct"] = bool(correct)
        detailed.append(item)

    return {"totals": totals, "details": detailed}


def main() -> None:
    parser = argparse.ArgumentParser(description="JSONL tabanlı LLM değerlendirme aracı")
    parser.add_argument("--questions", type=Path, required=True, help="Sorular JSONL yolu")
    parser.add_argument("--responses", type=Path, required=True, help="Cevaplar JSONL yolu")
    parser.add_argument("--report", type=Path, default=None, help="İsteğe bağlı rapor JSON çıktısı")
    args = parser.parse_args()

    result = evaluate(args.questions, args.responses)

    print("Sonuçlar:")
    print(json.dumps(result["totals"], ensure_ascii=False, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Rapor kaydedildi: {args.report}")


if __name__ == "__main__":
    main()

