"""
app_changes.py  ─  Drop-in replacements for the three patched sections in app.py
=================================================================================

HOW TO APPLY
─────────────
1.  Copy vo_sanitizer.py to the same folder as app.py.

2.  In app.py, find the line:
        from diagrams import (
    and add ONE line ABOVE it:
        from vo_sanitizer import sanitize_voiceover

3.  Replace the _gen_one_vo function with the version below (PATCH A).

4.  Inside _enrich_voiceovers → _call_batch, replace the `prompt = f"""..."""`
    with the version below (PATCH B).

5.  In diagrams.py, replace the entire file with the new diagrams.py provided.
    The key fix is _render_definition_box which now wraps text into lines
    that stay inside the rounded box.
"""

# ══════════════════════════════════════════════════════════════════
# PATCH A  ─  Replace _gen_one_vo in app.py
# ══════════════════════════════════════════════════════════════════

PATCH_A = '''
def _gen_one_vo(args) -> Tuple[int, Dict]:
    idx, slide, work_dir = args
    try:
        time.sleep(idx * 0.07)

        # Get raw voiceover text
        text = slide.get("voiceover", "").strip()
        if not text:
            text = " ".join(slide.get("bullets", [])) or slide.get("title", f"Slide {idx+1}")

        # ── Sanitize: strip markdown that TTS reads literally ──────
        text = sanitize_voiceover(text)
        # ──────────────────────────────────────────────────────────

        path = os.path.join(work_dir, f"audio_{idx}.mp3")

        async def _synth():
            communicate = edge_tts.Communicate(text, EDGE_TTS_VOICE)
            await communicate.save(path)

        asyncio.run(_synth())
        dur = _duration(path)
        logger.info(f"Slide {idx+1}: audio {dur:.1f}s  [{EDGE_TTS_VOICE}]")
        return idx, {"path": path, "duration": dur}
    except Exception as e:
        logger.error(f"Slide {idx+1} audio failed: {e}")
        return idx, {"path": "", "duration": 8.0}
'''


# ══════════════════════════════════════════════════════════════════
# PATCH B  ─  Replace the prompt inside _call_batch in app.py
#             (inside _enrich_voiceovers)
# Find:   prompt = f"""You are a university lecturer recording...
# Replace the entire f-string with this one:
# ══════════════════════════════════════════════════════════════════

PATCH_B = '''
        prompt = f"""You are a university lecturer recording spoken audio narration for a lecture video.

{source_instruction}

SOURCE MATERIAL:
{source_block}

SLIDES TO NARRATE ({len(batch_slides)} slides):
{slides_block}

STRICT REQUIREMENTS:
1. Write narration for EVERY slide above, in EXACT ORDER (position 1, 2, 3...).
2. CONTENT / TECHNICAL slides: 120-180 words of fluent, engaging spoken narration.
   - EXPLAIN the concept in depth: what it is, why it matters, how it works.
   - INCORPORATE specific facts, terms, examples from the slide\'s key points.
   - Add ONE concrete real-world example or analogy.
   - Do NOT just read out bullet points. Do NOT produce placeholder text.
   - Do NOT start with "In this slide..." or "Today we will see...".
3. TITLE / INTRO / AGENDA / THANK-YOU slides: 15-30 words only.
4. Natural flowing spoken English. Conversational but authoritative.
5. TTS FORMATTING — ABSOLUTELY CRITICAL:
   - NO markdown whatsoever: no **bold**, no *italic*, no `backticks`, no ## headers.
   - NO bullet points or numbered lists in the voiceover text.
   - NO underscores for subscripts — write "b sub n" not "b_n", "x sub i" not "x_i".
   - NO carets for superscripts — write "x squared" not "x^2", "e to the x" not "e^x".
   - Spell out ALL math symbols in plain English: "the integral from zero to infinity",
     "alpha sub zero", "partial derivative of f with respect to x".
   - This text goes DIRECTLY to a text-to-speech voice engine. Plain English only.
6. Return STRICT JSON only — no markdown fences, no preamble, no trailing text.

JSON FORMAT (exactly {len(batch_slides)} objects, in order):
{{
  "slides": [
    {{"position": 1, "voiceover": "full narration for slide 1 here"}},
    {{"position": 2, "voiceover": "full narration for slide 2 here"}}
  ]
}}"""
'''


# ══════════════════════════════════════════════════════════════════
# PATCH C  ─  Also update _single_fallback prompt in app.py
#             Find:   prompt = f"""You are a university lecturer. Record 120-160 words...
#             Replace with:
# ══════════════════════════════════════════════════════════════════

PATCH_C = '''
        prompt = f"""You are a university lecturer. Record 120-160 words of spoken audio narration
for the following lecture slide.

{source_instruction}

SOURCE MATERIAL:
{source_block}

SLIDE:
{ctx}

Requirements:
- Explain the concept in depth: define it, explain why it matters, give a concrete example.
- Natural spoken English. Do NOT start with "In this slide..." or just restate the title.
- TTS FORMATTING — CRITICAL: No markdown (**bold**, *italic*, `code`, ## headers).
  No underscores (write "b sub n" not "b_n"). No carets (write "x squared" not "x^2").
  Plain spoken English only — this goes directly to a text-to-speech engine.
- Return ONLY the narration text. No JSON, no quotes, no preamble.
"""
'''


if __name__ == "__main__":
    print("Patches defined. Apply manually to app.py as described in the docstring above.")
    print()
    print("Summary of changes:")
    print("  PATCH A: _gen_one_vo — sanitize text before TTS")
    print("  PATCH B: _call_batch prompt — instruct Gemini to avoid TTS-breaking markdown")
    print("  PATCH C: _single_fallback prompt — same TTS formatting rules")
    print("  diagrams.py: _render_definition_box — wrap text into multiple lines inside box")
    print("  vo_sanitizer.py: new file — sanitize_voiceover() function")
