import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "src" / "slideshow_engine" / "generate_campaign.py"
RENDER = ROOT / "src" / "slideshow_engine" / "render_slides.py"
BG = ROOT / "tests" / "fixtures" / "test_bg.jpg"


def test_generate_cherry_campaign():
    result = subprocess.run(["python3", str(GEN), "--app", "cherry", "--iterations", "25", "--seed", "1"], cwd=ROOT, text=True, capture_output=True, check=True)
    data = json.loads(result.stdout)
    assert data["app"] == "cherry"
    assert data["winners"] > 0
    campaign = ROOT / "campaigns" / "cherry" / "latest_campaign.md"
    assert campaign.exists()
    text = campaign.read_text()
    assert "Try Cherry on Google Play" in text


def test_generate_held_campaign_general_purpose():
    result = subprocess.run(["python3", str(GEN), "--app", "held", "--iterations", "25", "--seed", "2"], cwd=ROOT, text=True, capture_output=True, check=True)
    data = json.loads(result.stdout)
    assert data["app"] == "held"
    campaign = ROOT / "campaigns" / "held" / "latest_campaign.md"
    assert campaign.exists()
    text = campaign.read_text()
    assert "Held" in text
    assert "Cherry" not in text


def test_postiz_payloads_require_attachment_and_safe_settings():
    subprocess.run(["python3", str(GEN), "--app", "cherry", "--iterations", "25"], cwd=ROOT, text=True, capture_output=True, check=True)
    payloads = json.loads((ROOT / "postiz" / "cherry_postiz_drafts.json").read_text())
    assert payloads
    first = payloads[0]
    assert first["attachment_needed"] is True
    assert first["settings"]["content_posting_method"] == "UPLOAD"
    assert first["settings"]["comment"] is True
    assert first["settings"]["video_made_with_ai"] is True


def test_render_creates_multiple_slide_images(tmp_path):
    pytest_cmd = [
        "uv", "run", "--with", "pillow", "python", str(RENDER),
        "--app", "cherry", "--post-index", "0", "--background", str(BG), "--out-dir", str(tmp_path)
    ]
    subprocess.run(pytest_cmd, cwd=ROOT, text=True, capture_output=True, check=True)
    slides = sorted(tmp_path.glob("slide_*.jpg"))
    assert len(slides) >= 4
    assert len(slides) <= 7
    assert (tmp_path / "manifest.json").exists()
