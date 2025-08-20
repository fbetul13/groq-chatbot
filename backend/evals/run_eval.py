import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List

from groq import Groq

# Yerel evaluate modülünü kullan
from evaluate import evaluate as evaluate_results


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def save_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def sanitize_model_name(model: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", model)


def build_messages_for_question(q: Dict[str, Any]) -> List[Dict[str, str]]:
    category = q.get("category")
    qtype = q.get("type")
    prompt = q.get("prompt")

    if category == "math":
        if qtype == "numeric":
            system = (
                "You are a strict math solver. Output only the final numeric answer.\n"
                "- If result is a rational number, return simplest fraction a/b.\n"
                "- Otherwise return decimal using dot.\n"
                "- No units, no explanation, no extra text."
            )
        else:
            system = (
                "You are a strict math solver. Output only the requested values.\n"
                "- For multiple values, separate with a single comma and no spaces.\n"
                "- No explanation, no extra text."
            )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

    if category == "turkish":
        system = (
            "Türkçe dil bilgisi sorularında sadece şık harfini ver.\n"
            "- Yalnızca A, B, C ya da D harfi.\n"
            "- Açıklama, cümle, noktalama ekleme."
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

    if category == "coding":
        entry = q.get("entry_point")
        lang = q.get("language", "python")
        system = (
            f"Return only the {lang} function implementation for `{entry}`.\n"
            "- Do NOT include backticks or any prose.\n"
            "- Use standard library only.\n"
            "- Keep it simple and correct.\n"
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

    # Fallback
    return [
        {"role": "system", "content": "Answer concisely with only the required value."},
        {"role": "user", "content": prompt},
    ]


def postprocess_coding_output(text: str, entry_point: str) -> str:
    """Model çıktısından fonksiyon gövdesini çıkarıp temizlemeye çalış."""
    # Kod bloklarını temizle
    text = text.strip()
    if text.startswith("```"):
        # ```python ... ``` veya ``` ... ```
        text = re.sub(r"^```(?:[a-zA-Z]+)?\n", "", text)
        text = re.sub(r"\n```$", "", text)
        text = text.strip()

    # entry_point fonksiyonunu yakala
    pattern = rf"def\s+{re.escape(entry_point)}\s*\("
    match = re.search(pattern, text)
    if match:
        return text[text.find("def", match.start()) :].strip()
    return text


def run_for_model(client: Groq, model: str, questions_path: Path, out_dir: Path) -> Dict[str, Any]:
    questions = load_jsonl(questions_path)
    responses: List[Dict[str, Any]] = []
    timings: List[Dict[str, Any]] = []

    for q in questions:
        messages = build_messages_for_question(q)
        start = time.time()
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            top_p=1,
            max_tokens=1024,
        )
        elapsed = time.time() - start
        content = resp.choices[0].message.content or ""

        if q.get("category") == "coding":
            entry = q.get("entry_point")
            content = postprocess_coding_output(content, entry)
            responses.append({"id": q["id"], "code": content})
        else:
            responses.append({"id": q["id"], "answer": content.strip()})

        timings.append({
            "id": q["id"],
            "category": q.get("category"),
            "latency_sec": elapsed,
        })

    # Kaydet
    model_safe = sanitize_model_name(model)
    out_dir.mkdir(parents=True, exist_ok=True)
    resp_file = out_dir / f"{model_safe}_responses.jsonl"
    save_jsonl(resp_file, responses)

    # Skorla
    report = evaluate_results(questions_path, resp_file)
    report["model"] = model
    report["timings"] = timings
    report_file = out_dir / f"{model_safe}_report.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # Özet metrikler
    summary = {
        "model": model,
        "totals": report.get("totals", {}),
        "avg_latency_sec": round(sum(t["latency_sec"] for t in timings) / max(1, len(timings)), 3),
    }
    return {
        "responses_path": str(resp_file),
        "report_path": str(report_file),
        "summary": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM eval runner (Groq)")
    parser.add_argument("--models", required=True, help="Virgülle ayrılmış model listesi (örn: llama-3.1-8b-instant,llama-3.3-70b-versatile)")
    parser.add_argument("--questions", type=Path, required=True, help="Sorular JSONL yolu")
    parser.add_argument("--out", type=Path, required=True, help="Çıktı klasörü")
    args = parser.parse_args()

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("GROQ_API_KEY environment variable is required")

    client = Groq(api_key=api_key)
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    all_summaries: List[Dict[str, Any]] = []
    for model in models:
        print(f"Running eval for model: {model} ...")
        result = run_for_model(client, model, args.questions, args.out)
        print(json.dumps(result["summary"], ensure_ascii=False))
        all_summaries.append(result["summary"])

    # Tüm modeller için kısa özet
    overview_path = args.out / "overview.json"
    overview = {"models": all_summaries}
    overview_path.write_text(json.dumps(overview, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Overview saved to: {overview_path}")


if __name__ == "__main__":
    main()

