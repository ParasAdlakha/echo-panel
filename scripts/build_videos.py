"""Narrated videos.

  python scripts/build_videos.py pitch   -> docs/video/EchoPanel-pitch.mp4  (slides + speaker-note narration)
  python scripts/build_videos.py demo    -> docs/video/EchoPanel-demo.mp4   (panel replay viewer + narration)

Narration uses OpenAI text-to-speech (gpt-4o-mini-tts); video assembly uses ffmpeg.
Adapted from the authors' earlier sprint project (pre-existing code).
"""
import json
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import echo.llm  # noqa: E402,F401  (loads .env)

VID = ROOT / "docs" / "video"
TMP = VID / "_build"
TEMPO = 1.12  # keeps the pitch under 5 minutes
VOICE, INSTR = "coral", "Calm, clear, friendly research presenter. Moderate pace."


def tts(text: str, out: Path):
    if out.exists():
        return
    client = OpenAI()
    with client.audio.speech.with_streaming_response.create(model="gpt-4o-mini-tts", voice=VOICE, input=text,
                                                            instructions=INSTR, response_format="mp3") as r:
        r.stream_to_file(out)


def dur(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], check=True)


def concat(parts, out):
    lst = TMP / (out.stem + "_list.txt")
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts))
    ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out)
    print(out, f"{dur(out):.1f}s")


def pitch():
    notes = json.loads((ROOT / "docs" / "slides" / "notes.json").read_text(encoding="utf-8"))
    parts = []
    for sid, text in notes.items():
        a = TMP / f"pitch_{sid}.mp3"
        tts(text, a)
        seg = TMP / f"pitch_{sid}.mp4"
        d = dur(a) / TEMPO + 0.8
        ff("-loop", "1", "-i", ROOT / "docs" / "slides" / f"{sid}.png", "-i", a, "-t", f"{d:.2f}",
           "-vf", "scale=1920:1080,format=yuv420p", "-c:v", "libx264", "-r", "30", "-tune", "stillimage",
           "-c:a", "aac", "-b:a", "160k", "-af", f"atempo={TEMPO},apad", "-shortest", seg)
        parts.append(seg)
    concat(parts, VID / "EchoPanel-pitch.mp4")


DEMO = [  # (viewer query string, narration)
    ("q=0", "This is the panel replay from our project, The Echo Panel. Each question here really happened and has "
            "already resolved. The grey line is what the prediction market said; the models never saw it. Each row "
            "is a different way to build a panel of five AI advisors."),
    ("q=33&autoplay=1&step=3200",
     "Take this one: will Chris Stigall win the Republican nomination for Missouri's sixth district? The market said "
     "sixty-nine percent, and he won. One model asked five times says about three percent, five times over. Five personas "
     "of the same model: the same. Five different models are more spread out. Now watch the bottom row: after one "
     "round of discussion, the spread collapses and all five agree, on the wrong answer."),
    ("filter=unanwrong&q=85&autoplay=1&step=2600",
     "The filter finds every question where discussion left the panel unanimous and wrong. Read as five independent "
     "witnesses, this one says NO with nearly nine in ten confidence, and the answer was YES. Across all 190 questions, unanimity rose from 56 to 84 percent "
     "after discussion, while accuracy stayed flat."),
    ("q=0", "That is the core finding. Five voices carry little more than one opinion, and talking makes them agree "
            "without making them right. The report, the code and every logged answer are linked on the project page."),
]


def demo():
    from playwright.sync_api import sync_playwright
    parts = []
    for k, (query, text) in enumerate(DEMO):
        a = TMP / f"demo_{k}.mp3"
        tts(text, a)
        d = dur(a) + 0.8
        raw_dir = TMP / f"demo_raw_{k}"
        raw_dir.mkdir(parents=True, exist_ok=True)
        for old in raw_dir.glob("*.webm"):
            old.unlink()
        url = (ROOT / "docs" / "viewer.html").as_uri() + "?" + query
        with sync_playwright() as p:
            try:
                b = p.chromium.launch()
            except Exception:
                b = p.chromium.launch(channel="msedge")
            ctx = b.new_context(viewport={"width": 1280, "height": 720}, device_scale_factor=1,
                                record_video_dir=str(raw_dir), record_video_size={"width": 1280, "height": 720})
            pg = ctx.new_page()
            pg.goto(url)
            pg.wait_for_timeout(int(d * 1000) + 600)
            ctx.close(); b.close()
        webm = sorted(raw_dir.glob("*.webm"))[-1]
        seg = TMP / f"demo_{k}.mp4"
        ff("-ss", "0.5", "-i", webm, "-i", a, "-t", f"{d:.2f}", "-vf", "scale=1920:1080,format=yuv420p,fps=30",
           "-c:v", "libx264", "-c:a", "aac", "-b:a", "160k", "-af", "apad", "-shortest", seg)
        parts.append(seg)
    concat(parts, VID / "EchoPanel-demo.mp4")


if __name__ == "__main__":
    TMP.mkdir(parents=True, exist_ok=True)
    {"pitch": pitch, "demo": demo}[sys.argv[1]]()
