#!/usr/bin/env python3
"""Generate review output with Gemini via local gateway, Google API, or GpuGeek.

Usage:
  python skills/review/scripts/gemini_review.py --input-file input.txt

Environment variables:
  GEMINI_MODE           auto | openai_compat | google_api | gpugeek (default: auto)
  GEMINI_BASE_URL       OpenAI-compatible base URL (default: http://127.0.0.1:8000/v1)
  GEMINI_MODEL          Model name (default: gemini-2.5-pro)
  GEMINI_API_KEY        API key for local gateway or Google API
  GPU_GEEK_API_KEY      API key for GpuGeek
  GPU_GEEK_URL          GpuGeek API URL (default: https://api.gpugeek.com/predictions)
  GPU_GEEK_MODEL        GpuGeek model (default: Vendor2/Gemini-3-flash)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

GPU_GEEK_URL = "https://api.gpugeek.com/predictions"
GPU_GEEK_MODEL = "Vendor2/Gemini-3-flash"


SYSTEM_PROMPT = """You are a science communicator writing expert-insight X replies.

Output only the final answer. No preface, no explanation, no markdown quote blocks.
Return exactly this structure:
[内容分析]
- ...
- ...
- 可以理解为...
- 可能和...有关
- 关于这个话题，人们关心的点在于...

[评论方案]
Comment 1（<style>）:
<EN <= 280>
CN:
<中文翻译>

Comment 2（<style>）:
<EN <= 280>
CN:
<中文翻译>

Comment 3（<style>）:
<EN <= 280>
CN:
<中文翻译>

... up to Comment 5

Sources:
- <url>
- <url>

Rules:
- Keep each English comment <= 280 chars.
- Make each comment sound like a real human reply on X.
- Keep sentences short and punchy. Prefer one core point per sentence.
- Keep most comments around 1-2 concise sentences.
- Keep the voice conversational and grounded, like a thoughtful practitioner reply.
- Allow light natural connectors like honestly, to be fair, in practice when useful.
- Prefer concrete phrasing over academic prose.
- Avoid dense abstract phrasing and avoid research-paper tone.
- Prioritize practical implications, risk boundaries, and what people should care about next.
- Blend facts into opinions naturally. Do not sound like a strict fact-check report.
- Keep 1-2 relevant technical terms in each comment to preserve professional depth.
- Explain terms in plain language when needed, avoid dense jargon stacking.
- Prefer a mechanism-first pattern seen in strong samples.
- Use concise causal chains like dependency coupling latency retrieval failover control-plane.
- Prefer sharp but grounded contrast patterns such as it does not mean X but it signals Y.
- Use concrete nouns and operational verbs. Avoid abstract management wording.
- Avoid textbook phrasing and avoid lecture tone.
- Do not over-explain obvious context.
- Keep claims specific and falsifiable rather than broad vibe statements.
- Be neutral-professional with depth, not extreme.
- Stay neutral and objective. Avoid fan tone, attack tone, or absolute verdicts.
- Prefer calibrated wording such as likely may suggest rather than certainty inflation.
- Avoid rhetorical questions and sarcasm in English comments.
- Point out the problem and provide nuance in the same comment.
- Build light emotional resonance through concrete pain points, not slogans.
- Zero self-promotion. Pure value delivery.
- Avoid overblown words, marketing hype, or decorative metaphors.
- No quotation marks in generated comments.
- No colons in generated comments.
- Reduce AI-like style markers in all sections.
- Minimize quotation marks and minimize colons in body text.
- Do not use quote-plus-metaphor patterns.
- Forbidden style examples include quoted labels or quoted metaphors like
  model is a lobotomy
  launch honeymoon
  magic intelligence
- Prefer literal wording over decorative figurative language.
- Do not evaluate writing style or post formatting.
- Do not judge the poster as a person.
- Focus on event-level facts, uncertainty, implications, and practical context.
- Keep tone calm, grounded, concise, and native.
- Keep opening patterns diverse across the generated comments.
- Generate 3 to 5 comments depending on content richness.
- Do not force all styles if the post does not need them.
- If the post has no clear misinformation risk, skip 事实核查版.
- Use post-specific short style labels, not fixed canned labels.
- Avoid default label sets repeated across runs.
- Make each comment target a different user concern, not the same angle reworded.
- Across comments, vary sentence rhythm and avoid parallel skeletons.
- If 科普版 is included, it must open with a mechanism outcome sentence, not a term list.
- For 科普版, do not start with two nouns joined by and.
- For 科普版, avoid naming terms first and explaining later.
- Prefer this order for 科普版
  mechanism consequence first
  then 1-2 terms naturally embedded in that sentence
- Comment 4 should sound like insider field talk with realistic pain points, not generic advice.
- If a claim is plausible but unproven, mark it as hypothesis-level clearly.
- Do not open with verification/meta phrases unrelated to substance.
- Comment 1 is contextual framing, not truth policing.
- Do not use judge-like wording such as true false verified unverified fact-check.
- Forbidden openings include but are not limited to
  The timeline is real
  Fact check
  Strictly speaking
  It is true that
  According to verification
  From a fact-check perspective
- Style anti-template constraints
- Do not start Comment 2 with phrase patterns like
  key terms are
  X and Y are the key terms
  in simple terms
  this means
- Do not use the same opening pattern across comments.
- At most 2 comments may use a Not A but B frame.
- Do not repeat reusable template starters such as
  Big jump in
  What changed is
  In practice
  The key is
  This means
  The post is directionally
- Avoid consulting tone phrases such as
  directionally reasonable
  maturity is uneven
  enterprise outcomes
  execution shift
- Prefer field language over framework language.
- Each comment should include at least one concrete operational detail such as retries timeout context window dependency chain tool call permission layer or token budget.
"""

STRICT_OUTPUT_APPEND = """

Final check before output:
- You must include both [内容分析] and [评论方案].
- You must include 3 to 5 comments with CN translations.
- Number comments sequentially from Comment 1.
- You must include Sources with at least 2 URLs.
- Output nothing except the final formatted result.
"""


def build_prompt(user_prompt: str) -> str:
    return f"{user_prompt.rstrip()}\n{STRICT_OUTPUT_APPEND}"


def is_structured_review(text: str) -> bool:
    required = [
        "[内容分析]",
        "[评论方案]",
        "Sources:",
        "\nCN:\n",
    ]
    if not all(marker in text for marker in required):
        return False
    headers = re.findall(r"Comment\s+([1-5])（([^）]+)）:", text)
    if not (3 <= len(headers) <= 5):
        return False
    nums = [int(n) for n, _ in headers]
    if nums != list(range(1, len(nums) + 1)):
        return False
    styles = [s.strip() for _, s in headers]
    if len(set(styles)) < min(3, len(styles)):
        return False
    return True


def normalize_review_output(text: str) -> str:
    """Normalize near-miss outputs into the expected review template shape."""
    s = text.replace("\r\n", "\n").strip()

    # Keep content from [内容分析] onward if the model adds a preface.
    idx = s.find("[内容分析]")
    if idx != -1:
        s = s[idx:]

    # Normalize common comment header variants.
    fallback_styles = {
        "1": "机制洞察版",
        "2": "科普版",
        "3": "内容评价版",
        "4": "生活落地版",
        "5": "幽默有梗版",
    }
    for i in ["1", "2", "3", "4", "5"]:
        s = re.sub(
            rf"(?im)^Comment\s*{i}\s*$",
            f"Comment {i}（{fallback_styles[i]}）:",
            s,
        )
        s = re.sub(
            rf"(?im)^Comment\s*{i}\s*[:：]\s*$",
            f"Comment {i}（{fallback_styles[i]}）:",
            s,
        )
        s = re.sub(
            rf"(?im)^Comment\s*{i}\s*[:：]\s*(.+)$",
            f"Comment {i}（{fallback_styles[i]}）:\n\\1",
            s,
        )
        s = re.sub(
            rf"(?im)^Comment\s*{i}\s*[-–—]\s*.*$",
            f"Comment {i}（{fallback_styles[i]}）:",
            s,
        )

    # Normalize translation labels.
    s = re.sub(r"(?im)^中文翻译\s*[:：]\s*$", "CN:", s)
    s = re.sub(r"(?im)^Chinese\s*[:：]\s*$", "CN:", s)
    s = re.sub(r"(?im)^(?:翻译|中文翻译)\s*[:：]\s*(.+)$", "CN:\n\\1", s)
    s = re.sub(r"(?im)^CN:\s*(.+)$", "CN:\n\\1", s)

    # Remove narrative lines under [评论方案] before Comment 1.
    if "[评论方案]" in s and "Comment 1" in s:
        head, rest = s.split("[评论方案]", 1)
        c1 = rest.find("Comment 1")
        if c1 != -1:
            rest = "\n" + rest[c1:]
        s = head + "[评论方案]" + rest

    return s.strip()


def strip_quotes(text: str) -> str:
    """Remove quote characters to reduce AI-styled quoted metaphors."""
    quote_chars = ['"', "'", "“", "”", "‘", "’", "「", "」", "『", "』", "《", "》"]
    out = text
    for ch in quote_chars:
        out = out.replace(ch, "")
    return out


def build_repair_prompt(user_prompt: str, draft_output: str) -> str:
    return f"""Reformat the draft into the exact required structure.
Do not add or remove factual claims unless they violate format.
Fix style to sound natural and aligned with the role.
Match this target voice:
- mechanism first
- sharp but restrained
- short, concrete sentences
- not X but Y contrast when useful
- no lecture tone
- no verification-first framing
- no meta opener like The timeline is real
- keep 1-2 technical terms per comment with plain wording
- keep neutral objective stance and avoid absolute conclusions
- no quote-plus-metaphor style
- avoid decorative figurative wording
- no key terms are opener
- no repeated sentence skeleton across comments
- no consulting tone wording
- less academic tone, more natural comment voice
- shorter and more conversational wording
- Generate 3 to 5 comments only.
- Keep only the most suitable styles for this post.
- Skip 事实核查版 when there is no clear misinformation risk.
- If 科普版 is included, its first line must describe a concrete mechanism outcome.
- If 科普版 is included, it must not open with term pairing like A and B.
- no sensational words, no horror framing, no sarcasm.
- no rhetorical question sentences.
Keep each English comment <= 280 chars.
Use CN: on its own line before each Chinese translation.
Do not use quotation marks in any generated comment body.
Do not use colons in any generated comment body.
Only keep colons in section headers and label lines.

Original task context:
{user_prompt}

Draft to repair:
{draft_output}
"""


STYLE_BANNED_SUBSTRINGS = [
    "key terms are",
    "are the key terms",
    "in simple terms",
    "this means",
    "the timeline is real",
    "fact check",
    "directionally reasonable",
    "maturity is uneven",
    "enterprise outcomes",
    "execution shift",
    "big jump in",
    "what changed is",
    "the key is",
    "the post is directionally",
    "in practice",
    "the hard part is",
]

SENSATIONAL_BANNED_SUBSTRINGS = [
    "sci-fi",
    "horror movie",
    "terrifying",
    "nightmare",
    "gaslighting",
    "psychologically manipulate",
    "bully the others",
    "officially a research discovery now",
]


COMMENT2_BANNED_STARTS = [
    "key terms are",
    "the key terms are",
    "the core mechanics",
    "core mechanics",
    "x and y are",
    "prompt injection and",
    "latency and",
    "security and",
    "reliability and",
]


def extract_comment_english(text: str, idx: int) -> str:
    m = re.search(
        rf"Comment\s+{idx}（[^）]+）:\n(.*?)\nCN:\n",
        text,
        flags=re.DOTALL,
    )
    if not m:
        return ""
    return m.group(1).strip()


def extract_comment_style(text: str, idx: int) -> str:
    m = re.search(rf"Comment\s+{idx}（([^）]+)）:", text)
    if not m:
        return ""
    return m.group(1).strip()


def comment2_has_term_listing_opening(text: str) -> bool:
    style = extract_comment_style(text, 2)
    if style and "科普" not in style:
        return False
    c2 = extract_comment_english(text, 2)
    if not c2:
        return False
    first_line = c2.splitlines()[0].strip().lower()
    for p in COMMENT2_BANNED_STARTS:
        if first_line.startswith(p):
            return True
    # Catch "A and B ..." template-like openings.
    if re.match(r"^[a-z0-9\-\s]{1,24}\s+and\s+[a-z0-9\-\s]{1,24}\s+(are|drive|define|shape)\b", first_line):
        return True
    return False


def has_style_issues(text: str) -> bool:
    t = text.lower()
    for s in STYLE_BANNED_SUBSTRINGS:
        if s in t:
            return True

    # Avoid overusing the same rhetorical frame.
    not_but_count = len(re.findall(r"\bnot\b.{0,40}\bbut\b", t))
    if not_but_count > 2:
        return True

    for s in SENSATIONAL_BANNED_SUBSTRINGS:
        if s in t:
            return True

    # Avoid rhetorical questions in comment text.
    if "?\nCN:\n" in text or "?\r\nCN:\r\n" in text:
        return True

    # Ensure 3-5 comments and sequential numbering.
    headers = re.findall(r"Comment\s+([1-5])（([^）]+)）:", text)
    if not (3 <= len(headers) <= 5):
        return True
    nums = [int(n) for n, _ in headers]
    if nums != list(range(1, len(nums) + 1)):
        return True

    # Encourage distinct openings across comments.
    openings = []
    comment_texts = []
    for i in nums:
        c = extract_comment_english(text, i)
        if not c:
            continue
        comment_texts.append(c.lower())
        first_line = c.splitlines()[0].strip().lower()
        words = re.findall(r"[a-z0-9]+", first_line)[:3]
        openings.append(" ".join(words))
    if openings and len(set(openings)) < max(2, len(openings) - 1):
        return True

    # Reduce cross-comment template similarity.
    for i in range(len(comment_texts)):
        for j in range(i + 1, len(comment_texts)):
            a = set(re.findall(r"[a-z0-9]{3,}", comment_texts[i]))
            b = set(re.findall(r"[a-z0-9]{3,}", comment_texts[j]))
            if not a or not b:
                continue
            jaccard = len(a & b) / len(a | b)
            if jaccard > 0.62:
                return True

    if comment2_has_term_listing_opening(text):
        return True
    return False


def generate_with_mode(
    mode: str,
    prompt: str,
    *,
    base_url: str,
    model: str,
    api_key: str | None,
    gpugeek_url: str,
    gpugeek_model: str,
    timeout: int,
) -> str:
    if mode == "gpugeek":
        if not api_key:
            raise RuntimeError("GPU_GEEK_API_KEY or --api-key is required for gpugeek mode.")
        return call_gpugeek_api(
            prompt=prompt,
            model=gpugeek_model,
            api_key=api_key,
            endpoint=gpugeek_url,
            timeout=timeout,
        )
    if mode == "google_api":
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is required for google_api mode.")
        return call_google_api(
            prompt=prompt,
            model=model,
            api_key=api_key,
            timeout=timeout,
        )
    return call_openai_compat(
        prompt=prompt,
        base_url=base_url,
        model=model,
        api_key=api_key,
        timeout=timeout,
    )


def call_openai_compat(
    prompt: str,
    base_url: str,
    model: str,
    api_key: str | None,
    timeout: int,
) -> str:
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(prompt)},
        ],
        "temperature": 0.3,
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI-compatible API HTTP {e.code}: {detail}") from e
    except Exception as e:
        raise RuntimeError(f"OpenAI-compatible request failed: {e}") from e

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError("OpenAI-compatible API returned non-JSON response.") from e

    return data["choices"][0]["message"]["content"].strip()


def call_google_api(prompt: str, model: str, api_key: str, timeout: int) -> str:
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{urllib.parse.quote(model)}:generateContent?key={urllib.parse.quote(api_key)}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": build_prompt(prompt)}]}],
        "generationConfig": {"temperature": 0.3, "responseModalities": ["TEXT"]},
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API HTTP {e.code}: {detail}") from e
    except Exception as e:
        raise RuntimeError(f"Gemini request failed: {e}") from e

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError("Gemini API returned non-JSON response.") from e

    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Google Gemini response missing candidates: {data}")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise RuntimeError(f"Google Gemini response missing text: {data}")
    return text


def extract_text_from_gpugeek(payload: Any) -> str:
    """Best-effort text extraction from common GpuGeek response shapes."""
    if isinstance(payload, str):
        return payload.strip()
    if isinstance(payload, list):
        items = [extract_text_from_gpugeek(x) for x in payload]
        return "\n".join(x for x in items if x).strip()
    if not isinstance(payload, dict):
        return ""

    out = payload.get("output")
    if out:
        text = extract_text_from_gpugeek(out)
        if text:
            return text

    candidates = payload.get("candidates")
    if candidates:
        text = extract_text_from_gpugeek({"output": candidates})
        if text:
            return text

    content = payload.get("content")
    if isinstance(content, dict):
        parts = content.get("parts", [])
        if isinstance(parts, list):
            texts = [p.get("text", "").strip() for p in parts if isinstance(p, dict)]
            merged = "\n".join(t for t in texts if t).strip()
            if merged:
                return merged

    if "text" in payload and isinstance(payload["text"], str):
        return payload["text"].strip()
    if "response" in payload and isinstance(payload["response"], str):
        return payload["response"].strip()
    return ""


def call_gpugeek_api(
    prompt: str,
    model: str,
    api_key: str,
    endpoint: str,
    timeout: int,
) -> str:
    payload = {
        "model": model,
        "input": {
            "system_prompt": SYSTEM_PROMPT,
            "prompt": build_prompt(prompt),
        },
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GpuGeek API HTTP {e.code}: {detail}") from e
    except Exception as e:
        raise RuntimeError(f"GpuGeek request failed: {e}") from e

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError("GpuGeek API returned non-JSON response.") from e

    text = extract_text_from_gpugeek(data)
    if not text:
        raise RuntimeError(f"GpuGeek response missing text: {data}")
    return text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate review output with Gemini local API."
    )
    parser.add_argument(
        "--input-file",
        help="Path to UTF-8 text input. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--output-file",
        help="Optional path to write output text. Prints to stdout if omitted.",
    )
    parser.add_argument(
        "--mode",
        default=os.getenv("GEMINI_MODE", "auto"),
        choices=["auto", "openai_compat", "google_api", "gpugeek"],
        help="Provider mode.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("GEMINI_BASE_URL", "http://127.0.0.1:8000/v1"),
        help="OpenAI-compatible base URL for local Gemini gateway.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("GEMINI_MODEL", "gemini-2.5-pro"),
        help="Gemini model name.",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("GEMINI_API_KEY"),
        help="API key for local gateway or Google API. Also used by GpuGeek if GPU_GEEK_API_KEY is not set.",
    )
    parser.add_argument(
        "--gpugeek-url",
        default=os.getenv("GPU_GEEK_URL", GPU_GEEK_URL),
        help="GpuGeek endpoint URL.",
    )
    parser.add_argument(
        "--gpugeek-model",
        default=os.getenv("GPU_GEEK_MODEL", GPU_GEEK_MODEL),
        help="GpuGeek model ID.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="HTTP timeout in seconds.",
    )
    return parser.parse_args()


def read_input(path: str | None) -> str:
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return sys.stdin.read().strip()


def write_output(path: str | None, content: str) -> None:
    if path:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content.rstrip() + "\n")
        return
    print(content)


def main() -> int:
    args = parse_args()
    user_input = read_input(args.input_file)
    if not user_input:
        print("Input is empty. Provide --input-file or stdin content.", file=sys.stderr)
        return 2

    mode = args.mode
    if mode == "auto":
        if os.getenv("GPU_GEEK_API_KEY"):
            mode = "gpugeek"
        else:
            mode = "openai_compat" if os.getenv("GEMINI_BASE_URL") else "google_api"

    provider_key = (
        (os.getenv("GPU_GEEK_API_KEY") or args.api_key)
        if mode == "gpugeek"
        else args.api_key
    )

    try:
        out = generate_with_mode(
            mode,
            user_input,
            base_url=args.base_url,
            model=args.model,
            api_key=provider_key,
            gpugeek_url=args.gpugeek_url,
            gpugeek_model=args.gpugeek_model,
            timeout=args.timeout,
        )
    except Exception as exc:
        print(f"Gemini request failed: {exc}", file=sys.stderr)
        return 1

    out = strip_quotes(normalize_review_output(out))
    if not is_structured_review(out) or has_style_issues(out):
        print("Warning: first pass not in expected structure, retrying repair pass.", file=sys.stderr)
        try:
            out = generate_with_mode(
                mode,
                build_repair_prompt(user_input, out),
                base_url=args.base_url,
                model=args.model,
                api_key=provider_key,
                gpugeek_url=args.gpugeek_url,
                gpugeek_model=args.gpugeek_model,
                timeout=args.timeout,
            )
        except Exception as exc:
            print(f"Repair pass failed: {exc}", file=sys.stderr)
        out = strip_quotes(normalize_review_output(out))

    if not is_structured_review(out) or has_style_issues(out):
        print("Warning: final output still not fully structured.", file=sys.stderr)

    write_output(args.output_file, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
