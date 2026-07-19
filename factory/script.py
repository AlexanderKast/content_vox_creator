"""Script model and validation.

The script is 80% of the result. A beautiful video with a weak script is
useless; a strong script with mediocre animation still works. So the structure
is enforced in code, not left to vibes.

Two shapes, because the two modes are genuinely different products:
  VIDEO    — the edit sets the pace. Continuous narration, one timeline.
  CARRUSEL — the user's thumb sets the pace. Each slide is autonomous.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .formulas import FORMULAS, Formula
from .gating import GatingSpec, is_personalized
from .router import Asset
from .timing import UNDERLINE_DELAY_FRAMES, asset_entrance_frame


class Mode(str, Enum):
    VIDEO = "video"
    CARRUSEL = "carrusel"


# Format per mode. These are not preferences — 9:16 uploaded to a carousel gets
# cropped to 3:4 by Instagram, which eats the frame.
DIMENSIONS: dict[Mode, tuple[int, int]] = {
    Mode.VIDEO: (1080, 1920),   # 9:16 — Reels, TikTok
    Mode.CARRUSEL: (1080, 1350),  # 4:5 — Instagram feed
}

FPS = 30

# Carousel safe area, centered. Instagram's UI covers 80px top / 200px bottom.
CAROUSEL_SAFE_AREA = (1000, 1070)

# How many variants each SFX family has. MUST match the keys defined in
# factory.pipeline.SFX_PROMPTS (pop-a..pop-c, whoosh-a.., etc.). sfx_cues
# rotates the variant by beat so the same sound isn't fired every time.
SFX_FAMILY_VARIANTS: dict[str, int] = {"pop": 3, "whoosh": 3, "impact": 3, "marker": 2}


@dataclass(frozen=True)
class SfxCue:
    name: str
    frame_offset: int  # frames from the start of the beat's own Sequence


@dataclass(frozen=True)
class PanoramaGroup:
    """2-3 consecutive carrusel beats sharing ONE wide backdrop image, sliced
    into per-beat strips (factory.pipeline._produce_panorama) instead of each
    beat paying for its own independent backdrop. `beats` are indices into
    Script.beats (contiguous, ascending — see validate()). `description` is
    the same kind of prompt as Beat.scene: English, no visible text, the
    template supplies the look."""

    beats: tuple[int, ...]
    description: str


@dataclass
class Beat:
    """One scene (VIDEO) or one slide (CARRUSEL)."""

    index: int
    text: str                  # on-screen TITLE — ALWAYS a complete sentence
                                # (the hook/atencion, not a 2-5 word label),
                                # mandatory in carrusel, sound is off.
    subtitle: str = ""         # on-screen description under the title — the
                                # why/for-what (interes+deseo), NOT a repeat
                                # of the title in smaller words.
    # AIDA phase this beat plays in a carrusel's arc: "atencion" | "interes" |
    # "deseo" | "accion". Empty = not declared (old scripts, or VIDEO — AIDA is
    # a carrusel structure, not enforced there). Once ANY beat in a script
    # declares it, validate() holds the whole carrusel to the pattern: beat 1
    # is "atencion" (the disruptive hook), the last beat is "accion" (the CTA,
    # its own slide — never folded into a title+subtitle beat).
    aida: str = ""
    kicker: str = ""           # small black top label ("ULTIMA HORA", section)
    badge: str = ""            # orange sticker callout ("$$$", "-50%", "RECORD")
    scene: str = ""            # full-frame themed background illustration (bakery,
                                # map, stadium...) — the beat's "world", full-bleed
    stat: str = ""             # giant colored number ("7 PAISES", "18,078 KM")
    search: str = ""           # CTA search-bar mockup: the word to type out
    narration: str = ""        # spoken line (VIDEO); empty means silent beat
    seconds: float = 3.0
    assets: list[Asset] = field(default_factory=list)
    sfx: str | None = None     # explicit SFX name, overrides the whole automatic
                                # cue set (see Script.sfx_cues) with one cue at frame 0


@dataclass
class Script:
    mode: Mode
    brand: str
    topic: str
    hook: str
    beats: list[Beat]
    cta: str
    music_prompt: str = (
        "high-energy modern trap beat, hard-hitting 808 drums, fast crisp hi-hats, "
        "driving bassline, punchy and motivational, cinematic hype, no vocals"
    )

    # Formula system (factory.formulas). None means "legacy / no formula
    # declared" — only the generic structural rules above apply. Declaring a
    # formula switches on the research-backed rules in `validate_formula()`.
    formula: Formula | None = None

    # F5 SERIE only: which part of the series this is, and which formula
    # (F1 or F2) runs inside it.
    series_part: int | None = None
    series_total: int | None = None
    series_formula: Formula | None = None

    # Gating CTA (factory.gating). F1 requires this to be set — "CTA triple"
    # IS the gating flow: follow, then share, then personalized comment.
    gating: GatingSpec | None = None

    # Mode VIDEO only. Not every closer supports a seamless wrap — opt-in per
    # script. See BoxVideo.tsx for how the loop-fade actually disguises the seam.
    loop: bool = False

    # Persistent series tag shown at the top of every frame ("100% AUTOMATIZADO"
    # in the reference). Empty = no series kicker.
    series_kicker: str = ""

    # --- Brand profile, injected from brand.json by cli.load_script ---------
    # These used to be Alexander-specific constants hardcoded in this module,
    # which meant the validators rejected anyone else's scripts. They're now
    # per-brand config so the project is shareable. Empty defaults mean the
    # corresponding rule is SKIPPED (you can't enforce a credential/proof/name
    # a brand never declared) — never a false rejection.
    credentials: tuple[str, ...] = ()   # exact allowed experience claims
    proof: tuple[str, ...] = ()         # own brands/clients that count as proof
    founder_name: str | None = None     # for F1 auto-dialogo ("Pero <name>, ...?")
    hashtags: tuple[str, ...] = ()      # brand hashtags for the caption
    signature: str | None = None        # caption sign-off line

    # Visual template (factory.router.TEMPLATE_NAMES) — e.g. "dark-luxury-gold".
    # None means "use the brand's default from brand.json, or the global
    # default" — resolved in Factory.build, not here (this class doesn't read
    # brand.json).
    template: str | None = None

    # Number of narrative chapters this VIDEO covers (content-vox-news: a
    # coherent multi-part story, ~30s per chapter, up to 4). 1 (default) means
    # "no chapter concept" and leaves the generic 45-90s duration bound
    # (validate()) untouched — only chapters > 1 switches to the per-chapter
    # bound. There's no dedicated field for it: a chapter boundary is just a
    # beat whose `kicker` reads e.g. "CAPÍTULO 2 DE 3" (Beat.kicker already
    # exists for this).
    chapters: int = 1

    # CARRUSEL only: groups of 2-3 consecutive beats that share one wide
    # backdrop, sliced per-beat (see PanoramaGroup, factory.pipeline
    # ._produce_panorama). Empty tuple = no panoramas, every beat with a
    # `scene` gets its own independent backdrop as before.
    panoramas: tuple[PanoramaGroup, ...] = ()

    @property
    def narration_text(self) -> str:
        return " ".join(beat.narration.strip() for beat in self.beats if beat.narration).strip()

    @property
    def character_count(self) -> int:
        return len(self.narration_text)

    @property
    def all_assets(self) -> list[Asset]:
        return [asset for beat in self.beats for asset in beat.assets]

    @property
    def duration_seconds(self) -> float:
        return round(sum(beat.seconds for beat in self.beats), 2)

    @property
    def full_text(self) -> str:
        """Every word a viewer or reader will see or hear. The transversal
        content rules (numbers, no guaranteed profit, exact credentials,
        proof, objection-handling) scan this, not any single field, because a
        claim can legitimately live in the hook, a beat, or the CTA."""
        parts = [self.hook, self.cta, self.topic]
        for beat in self.beats:
            parts.append(beat.text)
            parts.append(beat.narration)
        return " \n".join(p for p in parts if p)

    def sfx_cues(self, beat: Beat) -> list[SfxCue]:
        """Every SFX this beat triggers, by entry type — one sound per thing
        that visibly happens (a cutout entering -> pop, a cut -> whoosh, the
        underline -> marker, the remate/hook/number -> impact).

        Each family has variants (pop-a/pop-b/...) and the variant rotates by
        beat, so consecutive beats don't all fire the identical sound — it
        stops feeling repetitive. An explicit beat.sfx overrides everything
        with a single cue at frame 0."""
        if beat.sfx:
            return [SfxCue(beat.sfx, 0)]

        idx = self.beats.index(beat)

        def variant(family: str) -> str:
            count = SFX_FAMILY_VARIANTS.get(family, 1)
            return f"{family}-{chr(ord('a') + idx % count)}"

        cues = [SfxCue(variant("whoosh"), 0)]
        beat_duration_frames = round(beat.seconds * FPS)
        for i, _asset in enumerate(beat.assets):
            frame = asset_entrance_frame(i, len(beat.assets), beat_duration_frames)
            cues.append(SfxCue(variant("pop"), frame))
        cues.append(SfxCue(variant("marker"), UNDERLINE_DELAY_FRAMES))
        # Impact hit on the open (epic hook), the close (remate), and any beat
        # that leans on a number.
        if beat is self.beats[0] or beat is self.beats[-1] or any(ch.isdigit() for ch in beat.text):
            cues.append(SfxCue(variant("impact"), 0))
        return cues

    def all_sfx_names(self) -> set[str]:
        """Every unique SFX name this script needs — what gets priced and
        produced, once each, regardless of how many beats/cues use it."""
        return {cue.name for beat in self.beats for cue in self.sfx_cues(beat)}


class ScriptError(ValueError):
    """Raised when a script violates a rule we already know breaks the output."""


# -- content-rule patterns -------------------------------------------------
# These are keyword/regex heuristics, not NLP. Each is deliberately tied to
# a concrete, checkable signal instead of a vibe — see the docstring on each
# validator for what it actually looks for and why.

_LOSS_HOOK_PATTERN = re.compile(
    r"\b(no|nunca|dejaste?|pierdes?|perdiendo|sin darte cuenta|te est[aá] costando)\b",
    re.IGNORECASE,
)
_INCLUSIVE_PATTERN = re.compile(r"\b(tu|tus|te|ti)\b", re.IGNORECASE)

_INCOME_PATTERN = re.compile(
    r"\b(cobrar(le|selo)?|cobras|ingreso|factura|te pagan|paga(n|r)?|\$)\b",
    re.IGNORECASE,
)

_GUARANTEE_PATTERN = re.compile(
    r"\b(vas a ganar|garantizad[oa]|seguro ganas)\b", re.IGNORECASE
)

# "cliente real" / "un cliente de" are generic proof phrasings that count for
# any brand; a brand's OWN proof names (its companies/clients) come from
# script.proof (brand.json), so this project isn't wired to one person's brands.
_GENERIC_PROOF_PATTERN = re.compile(r"\b(cliente real|un cliente de)\b", re.IGNORECASE)

_NUMBERED_ITEM_PATTERN = re.compile(r"^\s*\d+[\.\)]\s")

_YEARS_CLAIM_PATTERN = re.compile(r"\b\d+\s*\+?\s*a[nñ]os?\b", re.IGNORECASE)


def _has_digit(text: str) -> bool:
    return any(ch.isdigit() for ch in text)


def _fold_accents(text: str) -> str:
    """Strip diacritics so "años" and "anos" compare equal. On-screen captions
    routinely drop accents (examples write "musculos", "SENAL"), so comparing a
    credential claim against its accented form would false-positive-reject a
    perfectly compliant, just unaccented, script."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _proof_matches(script: Script) -> bool:
    """Proof = a generic proof phrase, OR any of this brand's own declared
    proof names (script.proof from brand.json)."""
    text = script.full_text
    if _GENERIC_PROOF_PATTERN.search(text):
        return True
    folded = _fold_accents(text.lower())
    return any(_fold_accents(p.lower()) in folded for p in script.proof)


def _numbered_beats(script: Script) -> list[Beat]:
    return [b for b in script.beats if _NUMBERED_ITEM_PATTERN.match(b.text)]


def _beats_in_window(script: Script, start: float, end: float) -> list[Beat]:
    """Beats whose [cumulative-start, cumulative-end) overlaps [start, end)."""
    cursor = 0.0
    hits = []
    for beat in script.beats:
        beat_start, beat_end = cursor, cursor + beat.seconds
        if beat_start < end and beat_end > start:
            hits.append(beat)
        cursor = beat_end
    return hits


def validate_transversal(script: Script) -> list[str]:
    """Rules that apply to every formula-declaring script, regardless of
    which formula it is. Each one exists because a specific failure mode was
    observed, not as generic hygiene:
      - a number is what makes a claim feel researched instead of vibes
        ("ahorra 63%" lands, "ahorra mucho" doesn't)
      - a guaranteed-profit claim is a legal and brand-trust liability
      - a credential that isn't the exact validated one is a lie by rounding
    """
    errors: list[str] = []
    text = script.full_text

    if not _has_digit(text):
        errors.append(
            "Sin numero hiperespecifico. \"Ahorra mucho\" no convence; "
            "\"ahorra 63%\" si — la especificidad es la credibilidad."
        )

    if _GUARANTEE_PATTERN.search(text):
        errors.append(
            "Promesa de ganancia garantizada detectada (\"vas a ganar\" / "
            "\"garantizado\" / \"seguro ganas\"). Riesgo legal y de marca — "
            "usa \"se lo puedes cobrar\" o \"puedes llegar a\"."
        )

    # Credential check only bites when the brand DECLARED its exact credentials
    # (script.credentials from brand.json). No declared credentials → nothing to
    # enforce against, so a years claim passes rather than getting falsely
    # rejected. A brand that sets credentials gets the "no rounding up" guard.
    years_claim = _YEARS_CLAIM_PATTERN.search(text)
    folded_text = _fold_accents(text.lower())
    if script.credentials and years_claim and not any(
        _fold_accents(cred.lower()) in folded_text for cred in script.credentials
    ):
        errors.append(
            f"Credencial de anos no exacta (\"{years_claim.group(0)}\"). "
            f"Solo se permite exactamente: {' o '.join(script.credentials)}. "
            "Innegociable."
        )

    return errors


def _validate_f1(script: Script) -> list[str]:
    errors: list[str] = []

    if not (_LOSS_HOOK_PATTERN.search(script.hook) and _INCLUSIVE_PATTERN.search(script.hook)):
        errors.append(
            "F1: hook no es inclusivo-perdida. Necesita un pronombre inclusivo "
            "(tu/tus) y un marco de perdida (no/nunca/pierdes/...)."
        )

    agitation_beats = _beats_in_window(script, 4.0, 15.0)
    if not any(b.narration.strip() and b.assets for b in agitation_beats):
        errors.append(
            "F1: falta agitacion con escena vivida entre 4-15s (un beat con "
            "narracion y un asset visual en esa ventana)."
        )

    if not (3 <= len(_numbered_beats(script)) <= 6):
        errors.append(
            f"F1: cuerpo debe ser una lista numerada de 3-6 items "
            f"(encontrados: {len(_numbered_beats(script))})."
        )

    # Proof rule only bites when the brand declared its own proof names, or
    # the script uses a generic proof phrase. A brand with no proof configured
    # (a fresh setup) isn't blocked — see _proof_matches.
    if (script.proof or _GENERIC_PROOF_PATTERN.search(script.full_text)) and not _proof_matches(script):
        own = " / ".join(script.proof) if script.proof else "tus marcas/clientes"
        errors.append(
            f"F1: falta prueba propia ({own} / \"cliente real\" referenciado)."
        )

    if script.gating is None:
        errors.append(
            "F1: CTA triple ausente — F1 requiere gating (seguir -> compartir "
            "-> comentario personalizado). Declara script.gating."
        )

    # Auto-dialogo objection only enforced when the brand set a founder name to
    # look for ("Pero <name>, ...?"). No name configured → rule skipped.
    if script.founder_name:
        pattern = re.compile(rf"\bpero,?\s+{re.escape(script.founder_name)}\b", re.IGNORECASE)
        if not pattern.search(script.full_text):
            errors.append(
                "F1: falta auto-dialogo — una objecion del avatar respondida "
                f"(\"Pero {script.founder_name}, ...?\" -> respuesta)."
            )

    return errors


def _validate_f2(script: Script) -> list[str]:
    if not _INCOME_PATTERN.search(script.full_text):
        return [
            "F2: falta promesa de INGRESO (\"se lo puedes cobrar a un cliente "
            "por $X\"). F2 no puede prometer solo ahorro."
        ]
    return []


def _validate_f3(script: Script) -> list[str]:
    return [FORMULAS[Formula.F3].rejection_message]


def _validate_f4(script: Script) -> list[str]:
    if not any(len(b.text.strip()) > 40 for b in script.beats):
        return [
            "F4: falta el prompt literal en pantalla — algun beat.text debe "
            "contener el prompt real usado, no una descripcion de el."
        ]
    return []


def _validate_f5(script: Script) -> list[str]:
    errors: list[str] = []
    if script.series_part is None or script.series_total is None:
        errors.append("F5: falta declarar series_part y series_total (\"parte N de M\").")
    elif not (1 <= script.series_part <= script.series_total):
        errors.append(
            f"F5: series_part ({script.series_part}) debe estar entre 1 y "
            f"series_total ({script.series_total})."
        )
    if script.series_formula not in (Formula.F1, Formula.F2):
        errors.append("F5: series_formula debe ser F1 o F2 — la serie usa una de esas por dentro.")
    elif script.series_formula is Formula.F1:
        errors.extend(f"F5/F1: {e}" for e in _validate_f1(script))
    elif script.series_formula is Formula.F2:
        errors.extend(f"F5/F2: {e}" for e in _validate_f2(script))
    return errors


_FORMULA_VALIDATORS = {
    Formula.F1: _validate_f1,
    Formula.F2: _validate_f2,
    Formula.F3: _validate_f3,
    Formula.F4: _validate_f4,
    Formula.F5: _validate_f5,
}


def validate_formula(script: Script) -> list[str]:
    """Structural rules for the declared formula. Video-only: a carrusel is a
    muted, thumb-paced slideshow, and F1/F2/F4's phase structure (narrated
    hook window, spoken objection-handling, timed agitation beat) doesn't
    apply to it. A carrusel may still declare a formula for tracking/
    correlation purposes (factory.feedback, phase 5) without being held to
    the video-timing rules."""
    if script.formula is None:
        return []

    spec = FORMULAS[script.formula]
    errors: list[str] = []

    if script.mode is Mode.VIDEO and spec.min_seconds is not None:
        if not spec.min_seconds <= script.duration_seconds <= spec.max_seconds:
            errors.append(
                f"{script.formula.value} ({spec.name}) dura {script.duration_seconds}s; "
                f"rango valido {spec.min_seconds}-{spec.max_seconds}s."
            )

    if script.mode is Mode.VIDEO:
        errors.extend(_FORMULA_VALIDATORS[script.formula](script))
    elif script.formula is Formula.F3:
        # The F3 refusal applies regardless of mode — it isn't a duration or
        # phase rule, it's "this factory does not shoot selfies."
        errors.append(FORMULAS[Formula.F3].rejection_message)

    return errors


def validate_gating(script: Script) -> list[str]:
    """The build fails, it does not warn, if a gating CTA promises a lead
    magnet that isn't on disk — see factory.gating for why."""
    if script.gating is None:
        return []
    errors: list[str] = []
    if not is_personalized(script.gating.gating_question):
        errors.append(
            f"Gating question \"{script.gating.gating_question}\" no esta "
            "personalizada — usa algo como \"comenta QUE VENDES\", no "
            "\"comenta INFO\"."
        )
    if not Path(script.gating.lead_magnet_path).exists():
        errors.append(
            f"Gating promete un lead magnet que no existe en disco: "
            f"{script.gating.lead_magnet_path}. Prometer un entregable que no "
            "existe rompe la confianza — el build falla, no advierte."
        )
    return errors


_AIDA_PHASES = {"atencion", "interes", "deseo", "accion"}


def _validate_carrusel_aida(script: Script) -> list[str]:
    """Every carrusel is an AIDA arc: slide 1 grabs attention with a
    disruptive hook, the last slide is the call to action — everything
    between builds interest and desire. This only bites once a script opts
    in by declaring `aida` on at least one beat (old scripts, and any beat
    that skips it, are silently exempt) — but once one beat declares it,
    every beat must, and the two structural anchors are non-negotiable."""
    declared = [b for b in script.beats if b.aida.strip()]
    if not declared:
        return []

    errors: list[str] = []
    for beat in script.beats:
        phase = beat.aida.strip()
        if not phase:
            errors.append(
                f"Slide {beat.index} no declara \"aida\" pero otros slides de este "
                "carrusel si — o todos lo declaran o ninguno."
            )
        elif phase not in _AIDA_PHASES:
            errors.append(
                f"Slide {beat.index}: aida=\"{phase}\" invalido. Usa uno de: "
                f"{', '.join(sorted(_AIDA_PHASES))}."
            )

    if script.beats and script.beats[0].aida.strip() not in ("", "atencion"):
        errors.append(
            f"Slide 1 debe ser aida=\"atencion\" (el hook disruptivo) — es "
            f"\"{script.beats[0].aida}\"."
        )
    if script.beats and script.beats[-1].aida.strip() not in ("", "accion"):
        errors.append(
            f"El ultimo slide debe ser aida=\"accion\" (el CTA) — es "
            f"\"{script.beats[-1].aida}\"."
        )
    return errors


def _validate_panoramas(script: Script) -> list[str]:
    """A panorama group is 2-3 consecutive, ascending beat indices sharing
    one wide backdrop (see PanoramaGroup) — never overlapping another group,
    never reusing a beat, and never on a beat that ALSO declares its own
    `scene` (the group replaces that role for its beats, it doesn't add to
    it). Capped at 3, not 4: the image API only accepts a fixed enum of
    aspect ratios (factory.providers.images_wavespeed.VALID_ASPECT_RATIOS)
    and the widest one, 21:9, already fits 3 slides snugly — a 4th would
    need a wider ratio that doesn't exist, forcing a stretched, distorted
    crop instead of a clean one."""
    if not script.panoramas:
        return []

    errors: list[str] = []
    beat_by_index = {b.index: b for b in script.beats}
    seen_beats: set[int] = set()

    for group in script.panoramas:
        if not (2 <= len(group.beats) <= 3):
            errors.append(
                f"Grupo panoramico {list(group.beats)}: usa 2-3 beats, no "
                f"{len(group.beats)}."
            )
        if list(group.beats) != sorted(group.beats) or len(set(group.beats)) != len(group.beats):
            errors.append(f"Grupo panoramico {list(group.beats)}: los beats deben ser ascendentes y sin repetir.")
        elif list(group.beats) != list(range(group.beats[0], group.beats[0] + len(group.beats))):
            errors.append(f"Grupo panoramico {list(group.beats)}: los beats deben ser consecutivos.")

        for idx in group.beats:
            if idx in seen_beats:
                errors.append(f"Beat {idx} esta en mas de un grupo panoramico — cada beat va en uno solo.")
            seen_beats.add(idx)
            beat = beat_by_index.get(idx)
            if beat is None:
                errors.append(f"Grupo panoramico {list(group.beats)}: no existe el beat {idx}.")
            elif beat.scene.strip():
                errors.append(
                    f"Beat {idx} esta en un grupo panoramico Y tiene su propio \"scene\" — "
                    "el grupo ya cubre el fondo de ese beat, sacale el scene individual."
                )
    return errors


def validate(script: Script) -> list[str]:
    """Return blocking errors. Empty list means the script may proceed."""
    errors: list[str] = []

    if not script.hook.strip():
        errors.append("Missing hook. The first 3 seconds are the whole video.")

    if script.mode is Mode.CARRUSEL:
        if not 6 <= len(script.beats) <= 10:
            errors.append(
                f"Carrusel has {len(script.beats)} slides. Use 6-10 — the technical "
                "limit is 20, but nobody finishes 20."
            )
        for beat in script.beats:
            if not beat.text.strip():
                errors.append(
                    f"Slide {beat.index} has no on-screen text. Carousels are consumed "
                    "muted; a slide that needs audio to be understood is a broken slide."
                )
            if not 4.0 <= beat.seconds <= 12.0:
                errors.append(
                    f"Slide {beat.index} is {beat.seconds}s. Use 4-12s per slide "
                    "(con voz, ~10s permite una frase completa por slide)."
                )
        errors.extend(_validate_carrusel_aida(script))
        errors.extend(_validate_panoramas(script))
    else:
        if script.panoramas:
            errors.append("panoramas solo aplica a mode=carrusel.")
        # Generic duration bound applies ONLY to formula-less scripts. When a
        # formula is declared, ITS range governs (see validate_formula) and this
        # generic rule must NOT stack on top — otherwise a valid F1 (75-100s per
        # formulas.py) gets killed by the narrower generic bound. The formula
        # owns its own timing; this is the fallback for scripts without one.
        if script.formula is None:
            if script.chapters > 1:
                # content-vox-news multi-chapter: ~30s/chapter, ±5s slack.
                lo, hi = 25 * script.chapters, 35 * script.chapters
            else:
                lo, hi = 45, 90
            if not lo <= script.duration_seconds <= hi:
                errors.append(
                    f"Video dura {script.duration_seconds}s. Debe estar entre "
                    f"{lo} y {hi}s"
                    + (f" ({script.chapters} capitulos x ~30s)." if script.chapters > 1 else " (ideal 60-75).")
                )
        for beat in script.beats:
            if beat.seconds > 1.2 and not beat.assets and not beat.scene:
                errors.append(
                    f"Beat {beat.index} holds {beat.seconds}s with no visual. "
                    "Nothing stays static past ~1.2s (give it an asset or a scene)."
                )

    if not script.cta.strip():
        errors.append("Missing CTA.")

    for asset in script.all_assets:
        if asset.is_public_figure and not asset.is_real_entity:
            errors.append(
                f"Asset '{asset.id}' es is_public_figure sin is_real_entity. Una "
                "figura publica SIEMPRE es una foto real (Tier.PHOTO), nunca "
                "generada — declara is_real_entity=true tambien."
            )

    errors.extend(validate_formula(script))
    if script.formula is not None:
        errors.extend(validate_transversal(script))
    errors.extend(validate_gating(script))

    return errors


def assert_valid(script: Script) -> None:
    errors = validate(script)
    if errors:
        raise ScriptError("Script rejected:\n  - " + "\n  - ".join(errors))
