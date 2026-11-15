"""Model clients with an on-disk cache.

The client code (providers, retries, semaphores) is adapted from our earlier
Planted Post project (pre-existing code, marked as such in the README). The
cache is new: every call is keyed by (model, messages, seed) so reruns are free
and every number in the report can be reproduced from results/cache/.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results" / "cache"


def _load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()

NVIDIA_PREFIXES = ("google/", "deepseek-ai/", "nvidia/", "mistralai/", "moonshotai/", "openai/gpt-oss", "meta/", "qwen/")


def provider(model: str) -> str:
    if model.startswith("adaption/"):
        return "adaption"
    return "nvidia" if model.startswith(NVIDIA_PREFIXES) else "openai"


_clients: dict[str, OpenAI] = {}
_sems = {"openai": threading.Semaphore(int(os.environ.get("OPENAI_CONCURRENCY", "24"))),
         "nvidia": threading.Semaphore(int(os.environ.get("NVIDIA_CONCURRENCY", "6"))),
         "adaption": threading.Semaphore(int(os.environ.get("ADAPTION_CONCURRENCY", "6")))}
_adaption = None
_usage_lock = threading.Lock()
USAGE: dict[str, dict[str, int]] = {}


def _client(prov: str) -> OpenAI:
    if prov not in _clients:
        if prov == "nvidia":
            _clients[prov] = OpenAI(api_key=os.environ["NVIDIA_API_KEY"], base_url="https://integrate.api.nvidia.com/v1",
                                    timeout=120, max_retries=0)
        else:
            _clients[prov] = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=120, max_retries=0)
    return _clients[prov]


def _adaption_chat(name: str, messages: list[dict]) -> tuple[str, dict]:
    global _adaption
    if _adaption is None:
        from adaption import Adaption
        _adaption = Adaption(timeout=120, max_retries=0)
    r = _adaption.responses.create(model=name, input=messages, temperature=1.0)
    u = getattr(r, "usage", None)
    return r.output_text or "", {"in": getattr(u, "input_tokens", 0) or 0, "out": getattr(u, "output_tokens", 0) or 0}


def _raw_chat(model: str, messages: list[dict], json_mode: bool) -> tuple[str, dict]:
    prov = provider(model)
    kw: dict = {"model": model, "messages": messages}
    if prov == "openai":
        if model.startswith("gpt-5"):
            kw["reasoning_effort"] = "low"
            kw["max_completion_tokens"] = 4000
        else:
            kw["temperature"] = 1.0
            kw["max_tokens"] = 600
        if json_mode:
            kw["response_format"] = {"type": "json_object"}
    else:
        kw["temperature"] = 1.0
        kw["max_tokens"] = 2500
    delay = 2.0
    for attempt in range(8):
        try:
            with _sems[prov]:
                if prov == "adaption":
                    return _adaption_chat(model.split("/", 1)[1], messages)
                r = _client(prov).chat.completions.create(**kw)
            u = r.usage
            return r.choices[0].message.content or "", {"in": getattr(u, "prompt_tokens", 0) or 0,
                                                        "out": getattr(u, "completion_tokens", 0) or 0}
        except Exception as e:  # rate limits, timeouts, transient 5xx
            msg = str(e)
            if any(s in msg for s in ("invalid_api_key", "expired", "does not exist", "model_not_found", "404", "410")):
                raise
            if attempt >= 2:
                print(f"[retry {attempt}] {model}: {msg[:160]}", flush=True)
            if "rate limit" in msg.lower() or "429" in msg:
                delay = max(delay, 30.0)
            time.sleep(delay)
            delay = min(delay * 2, 60)
    raise RuntimeError(f"{model}: gave up after retries")


def chat(model: str, messages: list[dict], seed: int = 0, json_mode: bool = True) -> str:
    """Cached chat call. `seed` only distinguishes repeated samples in the cache key."""
    key = hashlib.sha256(json.dumps([model, messages, seed, json_mode], sort_keys=True).encode()).hexdigest()
    path = CACHE / key[:2] / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))["text"]
    text, usage = _raw_chat(model, messages, json_mode)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"model": model, "messages": messages, "seed": seed, "text": text, "usage": usage}),
                    encoding="utf-8")
    with _usage_lock:
        u = USAGE.setdefault(model, {"calls": 0, "in": 0, "out": 0})
        u["calls"] += 1
        u["in"] += usage["in"]
        u["out"] += usage["out"]
    return text


_JSON = re.compile(r"\{.*\}", re.S)


def parse_json(text: str) -> dict | None:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    m = _JSON.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
