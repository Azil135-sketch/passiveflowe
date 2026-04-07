"""
PassiveFlow - Base Agent
========================
All agents inherit from this. Handles logging, retries, Claude API calls.
"""

import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import google.generativeai as genai


class BaseAgent:
    """Base class for all PassiveFlow agents."""

    MODEL = "gemini-1.5-flash"  # FREE tier — 1500 requests/day, zero cost
    MAX_TOKENS = 4096
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds

    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.logger = self._setup_logger()
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.results = []

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)

        # File handler
        fh = logging.FileHandler(self.log_dir / f"{self.name}.log")
        fh.setLevel(logging.INFO)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        if not logger.handlers:
            logger.addHandler(fh)
            logger.addHandler(ch)

        return logger

    def call_claude(self, system_prompt: str, user_prompt: str,
                    max_tokens: int = None, json_mode: bool = False) -> str:
        """
        Call Gemini API (FREE tier) with retry logic.
        Returns the text response.
        """
        if json_mode:
            system_prompt += "\n\nRESPOND ONLY WITH VALID JSON. No markdown fences, no preamble."

        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                self.logger.info(f"Gemini API call (attempt {attempt}/{self.MAX_RETRIES})")
                model = genai.GenerativeModel(self.MODEL)
                response = model.generate_content(full_prompt)
                text = response.text.strip()
                self.logger.info(f"API call success.")
                return text

            except Exception as e:
                self.logger.error(f"API error on attempt {attempt}: {e}")
                if attempt == self.MAX_RETRIES:
                    raise
                time.sleep(self.RETRY_DELAY * attempt)

        raise RuntimeError(f"{self.name}: Failed after {self.MAX_RETRIES} attempts")

    def call_claude_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Call Gemini and parse JSON response."""
        raw = self.call_claude(system_prompt, user_prompt, json_mode=True)
        try:
            cleaned = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parse error: {e}\nRaw: {raw[:200]}")
            raise

    def log_result(self, result: dict):
        """Log a result to the agent's result list and to file."""
        result["timestamp"] = datetime.now().isoformat()
        result["agent"] = self.name
        self.results.append(result)

    def save_results(self):
        """Persist results to logs/agent_name_results.json."""
        path = self.log_dir / f"{self.name}_results.json"
        existing = []
        if path.exists():
            with open(path) as f:
                existing = json.load(f)
        existing.extend(self.results)
        with open(path, "w") as f:
            json.dump(existing, f, indent=2)
        self.logger.info(f"Saved {len(self.results)} results to {path}")

    def run(self):
        """Override in subclass."""
        raise NotImplementedError(f"{self.name}.run() not implemented")
