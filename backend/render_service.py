"""FFmpeg-based video composition.

Takes a thumbnail (data URL) + voiceover (b64 mp3) and renders an MP4
with the still image, voiceover audio, and optional burnt-in subtitles.
"""
import asyncio
import base64
import os
import re
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional

RENDER_DIR = Path(os.environ.get("RENDER_DIR", "/app/backend/renders"))
RENDER_DIR.mkdir(parents=True, exist_ok=True)


def _strip_data_url(s: str) -> bytes:
    if s.startswith("data:"):
        s = s.split(",", 1)[1]
    return base64.b64decode(s)


def _to_srt(text: str, total_seconds: float) -> str:
    """Split narration into ~6-word chunks per subtitle line evenly across total_seconds."""
    words = re.findall(r"\S+", text)
    if not words:
        return ""
    chunk = 6
    chunks = [" ".join(words[i:i + chunk]) for i in range(0, len(words), chunk)]
    if not chunks:
        return ""
    per = max(0.6, total_seconds / len(chunks))
    out = []
    t = 0.0
    for i, c in enumerate(chunks, 1):
        start = t
        end = min(total_seconds, t + per)
        out.append(f"{i}\n{_fmt(start)} --> {_fmt(end)}\n{c}\n")
        t = end
    return "\n".join(out)


def _fmt(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


async def _audio_duration(path: Path) -> float:
    """Use ffprobe to get duration in seconds."""
    proc = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    out, _ = await proc.communicate()
    try:
        return float(out.decode().strip())
    except ValueError:
        return 60.0


async def render_mp4(thumbnail_data_url: str, audio_b64: str, narration: str, project_id: str) -> str:
    """Render an MP4: still image with subtle ken-burns + voiceover + burnt subtitles.
    Returns the public path (filename) of the rendered file."""
    work = Path(tempfile.mkdtemp(prefix="vf_render_"))
    try:
        img_path = work / "thumb.png"
        img_path.write_bytes(_strip_data_url(thumbnail_data_url))

        audio_path = work / "voice.mp3"
        audio_path.write_bytes(base64.b64decode(audio_b64))

        duration = await _audio_duration(audio_path)
        srt_path = work / "subs.srt"
        srt_text = _to_srt(narration or "", duration)
        srt_path.write_text(srt_text, encoding="utf-8")

        out_name = f"{project_id}_{uuid.uuid4().hex[:8]}.mp4"
        out_path = RENDER_DIR / out_name

        # Build filter: scale to 1920x1080 with letterbox, slow zoom (ken burns), then burn subs
        zoom_frames = max(1, int(duration * 25))
        # subtitles need escaped path
        srt_escaped = str(srt_path).replace(":", r"\:").replace("'", r"\'")
        vf = (
            f"scale=1920:1080:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,"
            f"zoompan=z='min(zoom+0.0008,1.15)':d={zoom_frames}:s=1920x1080:fps=25,"
            f"subtitles='{srt_escaped}':force_style='FontName=DejaVu Sans,FontSize=22,"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=1,Shadow=0,"
            f"MarginV=80'"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", "25", "-i", str(img_path),
            "-i", str(audio_path),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            str(out_path),
        ]

        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, err = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {err.decode()[-500:]}")
        return str(out_path)
    finally:
        try:
            for p in work.iterdir():
                p.unlink(missing_ok=True)
            work.rmdir()
        except Exception:
            pass


async def render_scenes_mp4(scenes: list, audio_b64: str, narration: str, project_id: str, fallback_image_data_url: str) -> str:
    """Render multi-scene MP4 with crossfade transitions.

    scenes: [{image_data_url|None, duration: int (sec)}]. Each scene image is shown for `duration`s with 0.5s crossfade.
    Audio is the full voiceover (audio drives final length). If a scene image is missing, fallback is used.
    """
    if not scenes:
        return await render_mp4(fallback_image_data_url, audio_b64, narration, project_id)

    work = Path(tempfile.mkdtemp(prefix="vf_render_"))
    try:
        # Save audio
        audio_path = work / "voice.mp3"
        audio_path.write_bytes(base64.b64decode(audio_b64))
        total_duration = await _audio_duration(audio_path)

        # Save scene images
        scene_files = []
        scene_durations = []
        # Stretch/scale per-scene durations to fit total_duration
        sum_d = sum(s.get("duration", 10) for s in scenes) or 1
        scale = total_duration / sum_d
        for i, sc in enumerate(scenes):
            dur = max(2.0, sc.get("duration", 10) * scale)
            img_data = sc.get("image_data_url") or fallback_image_data_url
            p = work / f"scene_{i}.png"
            p.write_bytes(_strip_data_url(img_data))
            scene_files.append(p)
            scene_durations.append(dur)

        # Subtitle file from full narration
        srt_path = work / "subs.srt"
        srt_path.write_text(_to_srt(narration or "", total_duration), encoding="utf-8")

        # Build a long ffmpeg command with xfade transitions
        # For N inputs, do (((s0 xfade s1) xfade s2) ... xfade sN)
        out_name = f"{project_id}_{uuid.uuid4().hex[:8]}.mp4"
        out_path = RENDER_DIR / out_name

        # Each input is a "loop image for duration" decoded to 1920x1080 25fps yuv420p
        cmd = ["ffmpeg", "-y"]
        for sf, dur in zip(scene_files, scene_durations):
            cmd += ["-loop", "1", "-t", f"{dur:.3f}", "-i", str(sf)]
        cmd += ["-i", str(audio_path)]

        # Build filter graph
        n = len(scene_files)
        filter_parts = []
        # Scale + format each video
        for i in range(n):
            filter_parts.append(
                f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=increase,"
                f"crop=1920:1080,setsar=1,fps=25,format=yuv420p[v{i}]"
            )
        # Chain xfade
        xf = 0.5
        if n == 1:
            chain_label = "v0"
        else:
            offset = scene_durations[0] - xf
            filter_parts.append(f"[v0][v1]xfade=transition=fade:duration={xf}:offset={offset:.3f}[x1]")
            for i in range(2, n):
                offset += scene_durations[i - 1] - xf
                filter_parts.append(f"[x{i-1}][v{i}]xfade=transition=fade:duration={xf}:offset={offset:.3f}[x{i}]")
            chain_label = f"x{n-1}"
        # Burn subtitles on the chained output
        srt_escaped = str(srt_path).replace(":", r"\:").replace("'", r"\'")
        filter_parts.append(
            f"[{chain_label}]subtitles='{srt_escaped}':force_style='FontName=DejaVu Sans,FontSize=24,"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=80'[vout]"
        )
        filter_complex = ";".join(filter_parts)
        cmd += [
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", f"{n}:a",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            str(out_path),
        ]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, err = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg multiscene failed: {err.decode()[-800:]}")
        return str(out_path)
    finally:
        try:
            for p in work.iterdir():
                p.unlink(missing_ok=True)
            work.rmdir()
        except Exception:
            pass
