"""Basic regression checks for the purely decorative visual atmosphere."""
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "public" / "index.html"
SVG = ROOT / "public" / "visuals" / "question-atlas.svg"


class TagCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def test_atmosphere_is_decorative_and_keeps_question_form():
    source = HTML.read_text(encoding="utf-8")
    doc = TagCollector()
    doc.feed(source)

    assert any(tag == "div" and attrs.get("class") == "qr-world"
               and attrs.get("aria-hidden") == "true" for tag, attrs in doc.tags)
    assert all(any(attrs.get("id") == target for _, attrs in doc.tags)
               for target in ("form", "question", "submit", "result", "cards"))
    assert "fetch('/api/question'" in source
    assert "Una pregunta<br>" not in source
    assert "No busques una respuesta rápida." not in source


def test_atmosphere_uses_local_svg_and_reduced_motion():
    source = HTML.read_text(encoding="utf-8")
    assert "url('/visuals/question-atlas.svg')" in source
    assert "prefers-reduced-motion:reduce" in source
    assert "pointer-events:none" in source
    assert "qrCardEnter" in source
    assert "qrPanelEnter" in source
    # The decorative asset is safe, bundled and has no external requests or scripts.
    tree = ElementTree.parse(SVG)
    assert tree.getroot().tag.endswith("svg")
    assert "http" not in SVG.read_text(encoding="utf-8").replace(
        'xmlns="http://www.w3.org/2000/svg"', ""
    )
