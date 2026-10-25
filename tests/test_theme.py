"""Calculate real CSS token contrast; not a claim of complete accessibility compliance."""

from pathlib import Path
import re


def test_theme_contrast():
    css = Path("static/styles.css").read_text(encoding="utf-8")
    tokens = dict(re.findall(r"(--[\w-]+):\s*(#[a-f\d]{6});", css, re.I))

    def luminance(name):
        channels = [int(tokens[name][index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return sum(c * weight for c, weight in zip(linear, [0.2126, 0.7152, 0.0722]))

    def ratio(first, second):
        a, b = sorted([luminance(first), luminance(second)])
        return (b + 0.05) / (a + 0.05)

    for foreground, background in [
        ("--text", "--background"),
        ("--text", "--surface"),
        ("--muted", "--surface"),
        ("--muted", "--surface-soft"),
        ("--sidebar-text", "--sidebar"),
        ("--sidebar-muted", "--sidebar-hover"),
        ("--on-accent", "--accent"),
        ("--on-accent", "--accent-hover"),
        ("--accent", "--surface"),
        ("--success-text", "--success-bg"),
        ("--warning-text", "--warning-bg"),
        ("--error-text", "--error-bg"),
    ]:
        assert ratio(foreground, background) >= 4.5, (foreground, background)
    for foreground, background in [
        ("--focus", "--surface"),
        ("--focus-dark", "--sidebar"),
        ("--input-border", "--input"),
    ]:
        assert ratio(foreground, background) >= 3, (foreground, background)
