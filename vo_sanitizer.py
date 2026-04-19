"""
vo_sanitizer.py — Voiceover text cleanup for TTS
=================================================
Call sanitize_voiceover(text) before passing any string to Edge TTS.

Fixes:
  **word**  → word          (bold markdown → read aloud as "asterisk asterisk")
  *word*    → word          (italic markdown)
  `code`    → code          (backtick code)
  b_n       → b sub n       (underscore subscripts)
  x_i       → x sub i
  a_0       → a sub 0
  #Heading  → Heading       (hash headers)
  ---       → (silence/pause)
  [link](url) → link
  \\n       → space
"""

import re


def sanitize_voiceover(text: str) -> str:
    """
    Clean a voiceover script so TTS reads it naturally.
    Removes markdown formatting that gets read aloud literally.
    """
    if not text:
        return text

    # 1. Remove markdown bold: **word** → word
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)

    # 2. Remove markdown italic: *word* → word  (but not multiplication *)
    text = re.sub(r'\*([^\*\n]+?)\*', r'\1', text)

    # 3. Remove inline code backticks: `code` → code
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # 4. Convert subscript underscores: x_n → x sub n, b_n → b sub n
    #    Match single letter/digit subscripts: a_0, b_n, x_i, F_g etc.
    text = re.sub(r'([A-Za-z])_([A-Za-z0-9])\b', r'\1 sub \2', text)
    #    Multi-char subscripts: x_{max} → x sub max
    text = re.sub(r'([A-Za-z])_\{([^}]+)\}', r'\1 sub \2', text)

    # 5. Convert superscript carets: x^2 → x squared, x^n → x to the n
    text = re.sub(r'([A-Za-z0-9])\^2\b', r'\1 squared', text)
    text = re.sub(r'([A-Za-z0-9])\^3\b', r'\1 cubed', text)
    text = re.sub(r'([A-Za-z0-9])\^\{([^}]+)\}', r'\1 to the power of \2', text)
    text = re.sub(r'([A-Za-z0-9])\^([A-Za-z0-9]+)', r'\1 to the \2', text)

    # 6. Remove markdown headers: ## Title → Title
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # 7. Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # 8. Remove markdown links: [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # 9. Remove bare URLs
    text = re.sub(r'https?://\S+', '', text)

    # 10. Remove blockquote markers
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

    # 11. Remove bullet/list markers at start of lines
    text = re.sub(r'^\s*[-•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # 12. Collapse multiple newlines to a single space
    text = re.sub(r'\n+', ' ', text)

    # 13. Collapse multiple spaces
    text = re.sub(r' {2,}', ' ', text)

    return text.strip()


if __name__ == "__main__":
    # Quick test
    samples = [
        "**Fourier Series** is an expansion of a *periodic* function f(x).",
        "The coefficient b_n is computed by integrating over one period.",
        "Using x^2 + y^2 = r^2 we get the circle equation.",
        "## Introduction\nThis lecture covers the **key** concepts.",
        "The formula `f(x) = sin(x)` is fundamental.",
        "See [this link](https://example.com) for more.",
        "b_0, b_n, a_i, F_g, x_{max}, omega_{0}",
    ]
    for s in samples:
        print(f"IN:  {s}")
        print(f"OUT: {sanitize_voiceover(s)}")
        print()
