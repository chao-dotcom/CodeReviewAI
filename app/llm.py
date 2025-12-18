from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.config import settings


class LLMClient:
    def __init__(self) -> None:
        self.backend = settings.llm_backend
        self.model_name = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
        self._pipeline = None

    def _load_local(self):
        if self._pipeline is not None:
            return
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self._pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=self.max_tokens,
            temperature=self.temperature,
        )

    def generate(self, prompt: str) -> str:
        if self.backend != "local":
            return ""
        self._load_local()
        result = self._pipeline(prompt, num_return_sequences=1)
        if not result:
            return ""
        return result[0].get("generated_text", "")


def parse_json_block(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def parse_findings(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = payload.get("findings")
    if not isinstance(findings, list):
        return []
    return [item for item in findings if isinstance(item, dict)]
