"""Proof that the formula rules bite. No network calls, no API keys required.

Run with:
    python -m unittest tests.test_formulas
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from factory.formulas import Formula  # noqa: E402
from factory.gating import GatingSpec  # noqa: E402
from factory.router import Asset  # noqa: E402
from factory.script import Beat, Mode, Script, validate  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
EXISTING_LEAD_MAGNET = str(FIXTURES_DIR / "lead-magnet.md")
MISSING_LEAD_MAGNET = str(FIXTURES_DIR / "does-not-exist.md")


def _asset(id_: str = "a") -> Asset:
    return Asset(id=id_, description="a cutout illustration")


def _valid_f1_script() -> Script:
    """A script that satisfies every F1 rule — used both as a positive test
    and as a base other tests mutate to break one rule at a time."""
    beats = [
        Beat(index=1, text="EMPEZAMOS", narration="", seconds=4, assets=[_asset("1")]),
        Beat(
            index=2, text="LA CALLE ENSEÑA OTRA COSA",
            narration="En Bogota, un vendedor gana 40 mil pesos con suerte en el dia.",
            seconds=6, assets=[_asset("2")],
        ),
        Beat(index=3, text="1. AUTOMATIZA LO REPETITIVO", narration="", seconds=5, assets=[_asset("3")]),
        Beat(index=4, text="2. COBRA POR RESULTADOS", narration="", seconds=5, assets=[_asset("4")]),
        Beat(index=5, text="3. DOCUMENTA TODO", narration="", seconds=5, assets=[_asset("5")]),
        Beat(index=6, text="4. MIDE EL SEGUIMIENTO", narration="", seconds=5, assets=[_asset("6")]),
        Beat(
            index=7, text="ASI LO HICIMOS EN KREOON",
            narration="Con KREOON ya generamos mas de cien piezas en un mes para clientes reales.",
            seconds=6, assets=[_asset("7")],
        ),
        Beat(
            index=8, text="PERO ALEXANDER...",
            narration="Pero Alexander, ¿y si no se nada de codigo? Tranquilo, no necesitas saber programar.",
            seconds=8, assets=[_asset("8")],
        ),
        Beat(
            index=9, text="EL 63% YA LO ESTA HACIENDO",
            narration="El 63% de quienes automatizan esto ganan mas en tres meses.",
            seconds=6, assets=[_asset("9")],
        ),
        Beat(index=10, text="SIGUE PARA LA PARTE 2", narration="", seconds=8, assets=[_asset("10")]),
        Beat(index=11, text="CIERRE", narration="", seconds=8, assets=[_asset("11")]),
        Beat(index=12, text="CIERRE 2", narration="", seconds=10, assets=[_asset("12")]),
    ]
    return Script(
        mode=Mode.VIDEO,
        brand="alexander",
        topic="Como automatizar tu primer proceso con IA",
        hook="Tus resultados no crecen aunque trabajes mas duro.",
        beats=beats,
        cta="Sigue, comparte y comenta QUE VENDES para el link.",
        formula=Formula.F1,
        gating=GatingSpec(
            gating_question="comenta QUE VENDES",
            lead_magnet_path=EXISTING_LEAD_MAGNET,
        ),
        # Brand profile: with these set, the proof / objection / credential
        # rules actually bite in these tests (they're skipped when unset).
        proof=("KREOON", "UGC Colombia", "LiveCake"),
        founder_name="Alexander",
        credentials=("8 años en negocios digitales", "6 años en pauta"),
    )


class ValidF1ScriptPasses(unittest.TestCase):
    def test_passes_with_no_errors(self):
        errors = validate(_valid_f1_script())
        self.assertEqual(errors, [], f"expected a clean F1 script, got: {errors}")


class F3IsRejected(unittest.TestCase):
    def test_f3_rejected_with_record_it_yourself_message(self):
        script = _valid_f1_script()
        script.formula = Formula.F3
        script.gating = None
        errors = validate(script)
        self.assertTrue(
            any("grabalo tu" in e.lower() or "grábalo tú" in e.lower() for e in errors),
            f"expected the F3 refusal message, got: {errors}",
        )


class F1WithoutProofIsRejected(unittest.TestCase):
    def test_missing_kreoon_reference_rejected(self):
        script = _valid_f1_script()
        for beat in script.beats:
            if "KREOON" in beat.narration or "KREOON" in beat.text:
                beat.text = "ASI LO HICIMOS NOSOTROS"
                beat.narration = "Ya lo hemos probado con varios equipos internos."
        errors = validate(script)
        self.assertTrue(
            any("prueba propia" in e for e in errors),
            f"expected a missing-proof error, got: {errors}",
        )


class NoSpecificNumberIsRejected(unittest.TestCase):
    def test_no_digits_anywhere_rejected(self):
        script = Script(
            mode=Mode.VIDEO,
            brand="alexander",
            topic="Como cobrar mejor tus servicios",
            hook="Tus precios no suben aunque mejores.",
            beats=[
                Beat(index=1, text="COBRA MAS", narration="Puedes cobrarle a un cliente por el resultado.",
                     seconds=40, assets=[_asset()]),
            ],
            cta="Sigue la cuenta.",
            formula=Formula.F2,
        )
        errors = validate(script)
        self.assertTrue(
            any("numero hiperespecifico" in e.lower() for e in errors),
            f"expected a missing-number error, got: {errors}",
        )


class GuaranteedProfitIsRejected(unittest.TestCase):
    def test_vas_a_ganar_garantizado_rejected(self):
        script = Script(
            mode=Mode.VIDEO,
            brand="alexander",
            topic="Como vender mas con IA",
            hook="Tus ventas no suben aunque publiques mas.",
            beats=[
                Beat(index=1, text="GARANTIZADO",
                     narration="Con esto vas a ganar garantizado 500 dolares al mes.",
                     seconds=40, assets=[_asset()]),
            ],
            cta="Sigue la cuenta.",
            formula=Formula.F2,
        )
        errors = validate(script)
        self.assertTrue(
            any("garantizada" in e.lower() for e in errors),
            f"expected a guaranteed-profit error, got: {errors}",
        )


class GatingWithoutLeadMagnetIsRejected(unittest.TestCase):
    def test_missing_lead_magnet_on_disk_rejected(self):
        script = _valid_f1_script()
        script.gating = GatingSpec(
            gating_question="comenta QUE VENDES",
            lead_magnet_path=MISSING_LEAD_MAGNET,
        )
        errors = validate(script)
        self.assertTrue(
            any("no existe en disco" in e for e in errors),
            f"expected a missing-lead-magnet error, got: {errors}",
        )

    def test_generic_gating_question_rejected(self):
        script = _valid_f1_script()
        script.gating = GatingSpec(
            gating_question="comenta INFO",
            lead_magnet_path=EXISTING_LEAD_MAGNET,
        )
        errors = validate(script)
        self.assertTrue(
            any("no esta personalizada" in e.lower() or "no está personalizada" in e.lower() for e in errors),
            f"expected a generic-question error, got: {errors}",
        )


# Credentials are per-brand now (script.credentials from brand.json). The rule
# only bites when a brand declared its exact credentials — these tests pass
# them explicitly to exercise it.
_CREDS = ("8 años en negocios digitales", "6 años en pauta")


class ExactCredentialsAreEnforced(unittest.TestCase):
    def test_ten_plus_years_rejected(self):
        script = Script(
            mode=Mode.VIDEO,
            brand="alexander",
            topic="Lo que aprendi en 10+ años en el mercado",
            hook="Tus resultados no crecen sin experiencia real.",
            beats=[
                Beat(index=1, text="10+ AÑOS",
                     narration="Llevo 10+ años ayudando a negocios a crecer, un 40% mas rapido.",
                     seconds=40, assets=[_asset()]),
            ],
            cta="Sigue la cuenta.",
            formula=Formula.F2,
            credentials=_CREDS,
        )
        errors = validate(script)
        self.assertTrue(
            any("credencial de anos no exacta" in e.lower() for e in errors),
            f"expected an exact-credentials error, got: {errors}",
        )

    def test_exact_allowed_credential_passes_that_rule(self):
        script = Script(
            mode=Mode.VIDEO,
            brand="alexander",
            topic="Lo que aprendi en el mercado",
            hook="Tus resultados no crecen sin experiencia real.",
            beats=[
                Beat(index=1, text="8 AÑOS",
                     narration="Llevo 8 años en negocios digitales, y esto lo puedes cobrar hoy mismo, un 40% mas rapido.",
                     seconds=40, assets=[_asset()]),
            ],
            cta="Sigue la cuenta.",
            formula=Formula.F2,
            credentials=_CREDS,
        )
        errors = validate(script)
        self.assertFalse(
            any("credencial de anos no exacta" in e.lower() for e in errors),
            f"exact allowed credential should not be rejected, got: {errors}",
        )

    def test_exact_credential_without_tilde_still_passes(self):
        # On-screen captions routinely drop accents — an unaccented "anos" must
        # still count as the exact allowed credential.
        script = Script(
            mode=Mode.VIDEO,
            brand="alexander",
            topic="Lo que aprendi en el mercado",
            hook="Tus resultados no crecen sin experiencia real.",
            beats=[
                Beat(index=1, text="8 ANOS",
                     narration="Llevo 8 anos en negocios digitales, y esto lo puedes cobrar hoy mismo, un 40% mas rapido.",
                     seconds=40, assets=[_asset()]),
            ],
            cta="Sigue la cuenta.",
            formula=Formula.F2,
            credentials=_CREDS,
        )
        errors = validate(script)
        self.assertFalse(
            any("credencial de anos no exacta" in e.lower() for e in errors),
            f"unaccented exact credential should not be rejected, got: {errors}",
        )

    def test_no_credentials_configured_skips_the_rule(self):
        # A fresh brand that never declared credentials must NOT get its
        # scripts rejected for mentioning years — the rule is skipped.
        script = Script(
            mode=Mode.VIDEO,
            brand="nuevo",
            topic="Lo que aprendi en 10 años",
            hook="Tus resultados no crecen sin experiencia real.",
            beats=[
                Beat(index=1, text="10 AÑOS",
                     narration="Llevo 10 años en esto y lo puedes cobrar, un 40% mas rapido.",
                     seconds=40, assets=[_asset()]),
            ],
            cta="Sigue la cuenta.",
            formula=Formula.F2,
        )
        errors = validate(script)
        self.assertFalse(
            any("credencial de anos no exacta" in e.lower() for e in errors),
            f"a brand with no credentials configured must not be rejected, got: {errors}",
        )


if __name__ == "__main__":
    unittest.main()
