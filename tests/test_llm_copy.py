"""Unit tests for the opt-in LLM-written hooks/caption path. No real network
calls — a fake TextLLM stands in. Confirms: (1) the LLM path is used when it
succeeds, (2) any failure falls back to the free template silently, (3) the
cost estimate only shows the copy line when explicitly enabled.

Run with:
    python -m unittest tests.test_llm_copy
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from factory import caption, config, hooks, pipeline  # noqa: E402
from factory.router import Asset  # noqa: E402
from factory.script import Beat, Mode, Script  # noqa: E402


class FakeLLM:
    name = "fake"

    def __init__(self, response: str | None = None, raise_error: bool = False):
        self._response = response
        self._raise_error = raise_error
        self.calls = 0

    def generate(self, prompt: str, *, system: str | None = None, max_tokens: int = 400) -> str:
        self.calls += 1
        if self._raise_error:
            raise RuntimeError("simulated LLM failure")
        return self._response


def _script() -> Script:
    return Script(
        mode=Mode.VIDEO,
        brand="alexander",
        topic="Como automatizar tu primer proceso con IA",
        hook="Tus resultados no crecen aunque trabajes mas duro.",
        beats=[
            Beat(index=1, text="EMPEZAMOS", narration="", seconds=3,
                 assets=[Asset(id="a", description="d")]),
        ],
        cta="Sigue la cuenta.",
    )


class CaptionLlmTest(unittest.TestCase):
    def test_uses_llm_summary_and_questions_on_success(self):
        llm = FakeLLM(response="Linea uno del resumen LLM.\nLinea dos.\n\n"
                                "¿Pregunta uno real?\n¿Pregunta dos real?\n¿Pregunta tres real?")
        result = caption.generate_caption(_script(), llm)
        self.assertIn("Linea uno del resumen LLM.", result)
        self.assertIn("¿Pregunta uno real?", result)
        self.assertEqual(llm.calls, 2)  # summary + questions

    def test_falls_back_to_template_on_llm_error(self):
        llm = FakeLLM(raise_error=True)
        script = _script()
        result = caption.generate_caption(script, llm)
        template_only = caption.generate_caption(script, None)
        self.assertEqual(result, template_only)

    def test_no_llm_uses_template(self):
        script = _script()
        result = caption.generate_caption(script)
        self.assertIn(script.hook, result)


class HooksLlmTest(unittest.TestCase):
    def test_uses_llm_variants_on_success(self):
        llm = FakeLLM(response="Variante uno\nVariante dos\nVariante tres\nVariante cuatro")
        script = _script()
        result = hooks.generate_hooks(script, llm)
        self.assertEqual(result[0], script.hook.strip())  # original hook never rewritten
        self.assertIn("Variante uno", result)
        self.assertEqual(len(result), 5)

    def test_falls_back_to_template_when_llm_returns_too_few_lines(self):
        llm = FakeLLM(response="Solo una linea")
        script = _script()
        result = hooks.generate_hooks(script, llm)
        template_only = hooks.generate_hooks(script, None)
        self.assertEqual(result, template_only)

    def test_falls_back_to_template_on_llm_error(self):
        llm = FakeLLM(raise_error=True)
        script = _script()
        result = hooks.generate_hooks(script, llm)
        template_only = hooks.generate_hooks(script, None)
        self.assertEqual(result, template_only)


def _config(use_llm_copy: bool, mistral_key: str | None) -> config.Config:
    return config.Config(
        wavespeed_key=None, kie_key=None, fal_key=None, magnific_key=None,
        apify_token=None, apify_image_actor="x", elevenlabs_key=None,
        max_spend_per_run=10.0, render_concurrency=1, whisper_model_size="medium",
        mistral_key=mistral_key, use_llm_copy=use_llm_copy,
    )


class EstimateLlmCostTest(unittest.TestCase):
    def test_no_copy_line_when_disabled(self):
        est = pipeline.estimate(_script(), _config(use_llm_copy=False, mistral_key="k"))
        self.assertFalse(any("copy" in line.label for line in est.lines))

    def test_no_copy_line_when_enabled_but_no_key(self):
        est = pipeline.estimate(_script(), _config(use_llm_copy=True, mistral_key=None))
        self.assertFalse(any("copy" in line.label for line in est.lines))

    def test_copy_line_when_enabled_with_key(self):
        est = pipeline.estimate(_script(), _config(use_llm_copy=True, mistral_key="k"))
        self.assertTrue(any("copy" in line.label for line in est.lines))

    def test_no_cfg_means_no_copy_line(self):
        est = pipeline.estimate(_script())
        self.assertFalse(any("copy" in line.label for line in est.lines))


if __name__ == "__main__":
    unittest.main()
