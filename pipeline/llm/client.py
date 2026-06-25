"""Cliente DeepSeek (OpenAI-compatible): batching, concurrencia, retry/backoff.

La API key se lee SOLO de la env var DEEPSEEK_API_KEY. Nunca se hardcodea ni
se loguea. El prefijo (system) es estable para aprovechar el prompt-cache.
"""
from __future__ import annotations

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from tqdm import tqdm

from . import schema
from .cache import Cache, text_key
from .vocab import Vocab

BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEFAULT_TIMEOUT = 60  # segundos


class EmptyContentError(RuntimeError):
    """DeepSeek a veces devuelve content vacío; reintentable."""


class TimeoutError(RuntimeError):
    """Timeout en la llamada a la API."""


@dataclass
class Stats:
    requests: int = 0
    errors: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    total_time: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def add(self, usage) -> None:
        with self._lock:
            self.requests += 1
            if usage:
                self.prompt_tokens += getattr(usage, "prompt_tokens", 0) or 0
                self.completion_tokens += getattr(usage, "completion_tokens", 0) or 0
                details = getattr(usage, "prompt_tokens_details", None)
                if details:
                    self.cached_tokens += getattr(details, "cached_tokens", 0) or 0

    def add_time(self, seconds: float) -> None:
        with self._lock:
            self.total_time += seconds


class DeepSeekClient:
    def __init__(self, vocab: Vocab, model: str = None, batch_size: int = 5,
                 workers: int = 2, max_tokens: int = 2048, timeout: int = DEFAULT_TIMEOUT):
        self.model = model or DEFAULT_MODEL

        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise SystemExit(
                "❌ Falta DEEPSEEK_API_KEY en el entorno.\n"
                "   Exporta tu clave: export DEEPSEEK_API_KEY='tu-clave'"
            )

        from openai import OpenAI

        self.client = OpenAI(
            api_key=api_key,
            base_url=BASE_URL,
            timeout=timeout,
        )
        self.batch_size = batch_size
        self.workers = workers
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.system = schema.build_system_prompt(vocab)
        self.stats = Stats()

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((EmptyContentError, TimeoutError, ConnectionError))
    )
    def _call(self, batch: list[tuple[int, str]]) -> str:
        start_time = time.time()

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": self.system},
                    {"role": "user", "content": schema.build_user_message(batch)},
                ],
                timeout=self.timeout,
            )
        except Exception as e:
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                raise TimeoutError(f"Timeout en llamada a API: {e}")
            raise

        elapsed = time.time() - start_time
        self.stats.add_time(elapsed)
        self.stats.add(getattr(resp, "usage", None))

        content = resp.choices[0].message.content
        if not content or not content.strip():
            raise EmptyContentError("content vacío")

        return content

    def run(self, pairs: list[tuple[str, str]], cache: Cache,
            on_batch=None) -> None:
        if not pairs:
            print("  ℹ️ No hay textos para procesar")
            return

        batches: list[list[tuple[int, str]]] = []
        keymaps: list[dict[int, str]] = []

        for start in range(0, len(pairs), self.batch_size):
            chunk = pairs[start:start + self.batch_size]
            batches.append([(i, desc) for i, (_, desc) in enumerate(chunk)])
            keymaps.append({i: k for i, (k, _) in enumerate(chunk)})

        print(f"  📦 {len(batches)} lotes de tamaño {self.batch_size}")
        print(f"  🔧 {self.workers} workers concurrentes")

        def work(idx: int):
            try:
                content = self._call(batches[idx])
                return idx, content, None
            except Exception as e:
                return idx, None, str(e)

        pbar = tqdm(
            total=len(batches),
            desc=f"  🚀 LLM ({self.model})",
            unit="lote",
            ncols=100,
        )

        if self.workers == 1:
            for i in range(len(batches)):
                try:
                    idx, content, error = work(i)
                    if error:
                        self.stats.errors += 1
                        print(f"\n  ⚠️ Error en lote {i+1}: {error[:100]}")
                    elif on_batch and content:
                        on_batch(content, batches[idx], keymaps[idx], cache)
                except Exception as e:
                    self.stats.errors += 1
                    print(f"\n  ⚠️ Error en lote {i+1}: {e}")
                finally:
                    pbar.update(1)
        else:
            with ThreadPoolExecutor(max_workers=self.workers) as ex:
                futures = {ex.submit(work, i): i for i in range(len(batches))}

                for future in as_completed(futures):
                    try:
                        idx, content, error = future.result()

                        if error:
                            self.stats.errors += 1
                            print(f"\n  ⚠️ Error en lote {idx+1}: {error[:100]}")
                        elif on_batch and content:
                            on_batch(content, batches[idx], keymaps[idx], cache)
                    except Exception as e:
                        self.stats.errors += 1
                        print(f"\n  ⚠️ Error inesperado: {e}")
                    finally:
                        pbar.update(1)

        pbar.close()
        print(f"\n  📊 Total: {len(pairs)} textos | {self.stats.requests} requests")
        if self.stats.errors > 0:
            print(f"  ⚠️ Errores: {self.stats.errors}")
