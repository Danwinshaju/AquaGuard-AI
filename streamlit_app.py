"""Free cloud portfolio demo for AquaGuard AI.

This intentionally small app reuses the project's core idea without MongoDB or the
local React/FastAPI stack. Uploaded media is processed in temporary files and removed
before the Streamlit run finishes.
"""

from __future__ import annotations

import math
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np
import streamlit as st
from ultralytics import YOLO

MAX_UPLOAD_BYTES = 150 * 1024 * 1024
MAX_DURATION_SECONDS = 60.0

MODES = {
    "Fast (recommended for free hosting)": {"imgsz": 320, "stride": 2},
    "Balanced": {"imgsz": 416, "stride": 1},
    "Accurate (slow on free CPU)": {"imgsz": 512, "stride": 1},
}


@dataclass
class TrackState:
    centroid: tuple[float, float]
    inactivity_seconds: float = 0.0
    maximum_inactivity_seconds: float = 0.0
    risk: int = 0


def load_detector() -> YOLO:
    """Create isolated tracking state; Ultralytics downloads the small model if needed."""

    return YOLO("yolo11n.pt")


def risk_label(risk: int) -> tuple[str, tuple[int, int, int]]:
    if risk >= 70:
        return "POSSIBLE DANGER", (30, 30, 230)
    if risk >= 40:
        return "WARNING", (0, 170, 255)
    return "SAFE", (70, 190, 70)


def draw_overlay(
    frame: np.ndarray,
    observations: list[tuple[int, tuple[int, int, int, int], float, int]],
) -> np.ndarray:
    highest_risk = max((item[3] for item in observations), default=0)
    overall_label, banner_color = risk_label(highest_risk)
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 54), banner_color, -1)
    cv2.putText(
        frame,
        f"AquaGuard AI | {overall_label} | Human verification required",
        (16, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    for track_id, (x1, y1, x2, y2), confidence, risk in observations:
        label, color = risk_label(risk)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
        text = f"Person {track_id} | {label} {risk}% | {confidence:.0%}"
        text_width = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)[0][0]
        text_top = max(55, y1 - 27)
        text_right = min(frame.shape[1], x1 + text_width + 12)
        cv2.rectangle(frame, (x1, text_top), (text_right, text_top + 27), color, -1)
        cv2.putText(
            frame,
            text,
            (x1 + 5, text_top + 19),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
    return frame


def update_tracks(
    result: object,
    states: dict[int, TrackState],
    frame_size: tuple[int, int],
    elapsed_seconds: float,
) -> list[tuple[int, tuple[int, int, int, int], float, int]]:
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return []

    coordinates = boxes.xyxy.int().cpu().tolist()
    confidences = boxes.conf.cpu().tolist()
    identifiers = (
        boxes.id.int().cpu().tolist()
        if boxes.id is not None
        else list(range(1, len(coordinates) + 1))
    )
    diagonal = max(1.0, math.hypot(*frame_size))
    observations: list[tuple[int, tuple[int, int, int, int], float, int]] = []

    for track_id, coordinates_for_track, confidence in zip(
        identifiers, coordinates, confidences, strict=True
    ):
        x1, y1, x2, y2 = (int(value) for value in coordinates_for_track)
        centroid = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
        previous = states.get(track_id)
        if previous is None:
            state = TrackState(centroid=centroid)
            states[track_id] = state
        else:
            displacement = math.dist(previous.centroid, centroid) / diagonal
            if displacement < 0.008:
                previous.inactivity_seconds += elapsed_seconds
            else:
                previous.inactivity_seconds = max(
                    0.0, previous.inactivity_seconds - elapsed_seconds * 1.5
                )
            previous.centroid = centroid
            state = previous

        state.maximum_inactivity_seconds = max(
            state.maximum_inactivity_seconds, state.inactivity_seconds
        )
        state.risk = min(100, round(state.inactivity_seconds / 5.0 * 85))
        observations.append((track_id, (x1, y1, x2, y2), float(confidence), state.risk))

    return observations


def analyse_video(
    source_path: Path,
    mode_name: str,
    progress_callback: Callable[[float, str], None],
) -> dict[str, object]:
    mode = MODES[mode_name]
    detector = load_detector()
    capture = cv2.VideoCapture(str(source_path))
    if not capture.isOpened():
        raise ValueError("The uploaded video could not be opened.")

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 25.0)
    if not math.isfinite(fps) or fps <= 0:
        fps = 25.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if width <= 0 or height <= 0 or total_frames <= 0:
        capture.release()
        raise ValueError("The video has invalid dimensions or no readable frames.")
    duration = total_frames / fps
    if duration > MAX_DURATION_SECONDS:
        capture.release()
        raise ValueError(
            f"The free demo accepts videos up to {MAX_DURATION_SECONDS:.0f} seconds. "
            "Trim this video and try again."
        )
    width -= width % 2
    height -= height % 2

    temporary_output = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    output_path = Path(temporary_output.name)
    temporary_output.close()
    frame_index = 0
    analyzed_frames = 0
    states: dict[int, TrackState] = {}
    last_observations: list[tuple[int, tuple[int, int, int, int], float, int]] = []
    highest_risk = 0
    evidence_jpeg: bytes | None = None
    writer = None
    completed = False

    try:
        writer = imageio_ffmpeg.write_frames(
            str(output_path),
            (width, height),
            fps=fps,
            codec="libx264",
            pix_fmt_in="rgb24",
            pix_fmt_out="yuv420p",
            output_params=["-preset", "veryfast", "-movflags", "+faststart"],
        )
        writer.send(None)
        while True:
            success, frame = capture.read()
            if not success:
                break
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
            if frame_index % int(mode["stride"]) == 0:
                results = detector.track(
                    frame,
                    persist=True,
                    tracker="bytetrack.yaml",
                    classes=[0],
                    conf=0.35,
                    imgsz=int(mode["imgsz"]),
                    device="cpu",
                    verbose=False,
                )
                analyzed_frames += 1
                if results:
                    elapsed = int(mode["stride"]) / fps
                    last_observations = update_tracks(
                        results[0], states, (width, height), elapsed
                    )

            annotated = draw_overlay(frame.copy(), last_observations)
            frame_risk = max((item[3] for item in last_observations), default=0)
            if frame_risk > highest_risk:
                highest_risk = frame_risk
                if frame_risk >= 40:
                    encoded, buffer = cv2.imencode(".jpg", annotated)
                    if encoded:
                        evidence_jpeg = buffer.tobytes()

            writer.send(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))
            frame_index += 1
            if frame_index == 1 or frame_index % max(1, round(fps)) == 0:
                progress_callback(
                    min(1.0, frame_index / total_frames),
                    f"Processing frame {frame_index:,} of {total_frames:,}",
                )
        completed = True
    finally:
        capture.release()
        if writer is not None:
            writer.close()
        if not completed:
            output_path.unlink(missing_ok=True)

    if frame_index == 0:
        output_path.unlink(missing_ok=True)
        raise ValueError("No frames could be decoded from this video.")

    video_bytes = output_path.read_bytes()
    output_path.unlink(missing_ok=True)
    progress_callback(1.0, "Analysis complete")
    return {
        "video": video_bytes,
        "evidence": evidence_jpeg,
        "people": len(states),
        "frames": frame_index,
        "analyzed_frames": analyzed_frames,
        "highest_risk": highest_risk,
        "longest_inactivity": max(
            (state.maximum_inactivity_seconds for state in states.values()), default=0.0
        ),
    }


def save_upload(data: bytes, suffix: str) -> Path:
    temporary = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        temporary.write(data)
        return Path(temporary.name)
    finally:
        temporary.close()


st.set_page_config(
    page_title="AquaGuard AI Live Demo",
    page_icon="🌊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1180px; padding-top: 2rem;}
    .hero {padding: 1.8rem; border-radius: 1.5rem; color: white;
      background: linear-gradient(135deg, #082f49, #0369a1 55%, #0891b2);}
    .hero h1 {margin: 0; font-size: 2.6rem;}
    .hero p {margin: .65rem 0 0; color: #cffafe; font-size: 1.05rem;}
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="hero">
      <h1>AquaGuard AI — Online Demo</h1>
      <p>Upload a short pool video to see YOLO person detection, ByteTrack identities,
      movement-based risk labels, and an annotated result.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.warning(
    "Educational demonstration only. This app cannot determine whether somebody is safe "
    "or drowning and must never replace a lifeguard, direct supervision, or emergency action."
)

with st.sidebar:
    st.header("How to demonstrate")
    st.markdown(
        "1. Choose a short MP4, AVI, or MOV.\n"
        "2. Keep **Fast** mode selected.\n"
        "3. Select **Analyze video**.\n"
        "4. Review boxes and possible-risk labels.\n"
        "5. Download the labelled result if required."
    )
    st.divider()
    st.markdown("**Cloud limits**")
    st.caption(
        "Maximum 150 MB and 60 seconds. The first run downloads the small YOLO model."
    )
    st.divider()
    st.markdown("**Danwin Shaju**")
    st.link_button("GitHub source", "https://github.com/Danwinshaju/AquaGuard-AI")
    st.link_button("LinkedIn", "https://www.linkedin.com/in/danwin-shaju/")

left, right = st.columns([0.88, 1.12], gap="large")
with left:
    st.subheader("1. Choose a video")
    selected_mode = st.selectbox("Performance", list(MODES), index=0)
    uploaded_file = st.file_uploader(
        "MP4, AVI, or MOV — up to 150 MB and 60 seconds",
        type=["mp4", "avi", "mov"],
    )
    analyze_clicked = st.button(
        "Analyze video",
        type="primary",
        use_container_width=True,
        disabled=uploaded_file is None,
    )
    st.info(
        "Privacy: the online demo uses temporary server files only during processing. "
        "It has no login or database and removes those files when processing finishes."
    )

if analyze_clicked and uploaded_file is not None:
    upload_bytes = uploaded_file.getvalue()
    if len(upload_bytes) > MAX_UPLOAD_BYTES:
        st.error(
            "This file is larger than 150 MB. Choose a shorter or compressed video."
        )
    else:
        source_path = save_upload(upload_bytes, Path(uploaded_file.name).suffix.lower())
        progress = right.progress(0.0)
        status = right.empty()

        def report_progress(value: float, message: str) -> None:
            progress.progress(value)
            status.caption(message)

        try:
            with st.spinner("Running YOLO tracking on the free CPU..."):
                st.session_state["aquaguard_result"] = analyse_video(
                    source_path, selected_mode, report_progress
                )
        except (
            Exception
        ) as error:  # Streamlit must show cloud/model/codec failures clearly.
            st.session_state.pop("aquaguard_result", None)
            right.error(f"Analysis failed: {error}")
        finally:
            source_path.unlink(missing_ok=True)

result = st.session_state.get("aquaguard_result")
with right:
    st.subheader("2. Review the labelled result")
    if result:
        label, _ = risk_label(int(result["highest_risk"]))
        st.success("Analysis complete. The result starts automatically and repeats.")
        st.video(
            result["video"],
            format="video/mp4",
            autoplay=True,
            loop=True,
            muted=True,
        )
        metric_columns = st.columns(4)
        metric_columns[0].metric("People tracked", int(result["people"]))
        metric_columns[1].metric("Frames", int(result["frames"]))
        metric_columns[2].metric("Highest risk", f"{int(result['highest_risk'])}%")
        metric_columns[3].metric("Result", label)
        st.caption(
            f"AI checks: {int(result['analyzed_frames']):,} • "
            f"Longest measured inactivity: {float(result['longest_inactivity']):.1f}s"
        )
        st.download_button(
            "Download labelled MP4",
            data=result["video"],
            file_name="aquaguard-streamlit-result.mp4",
            mime="video/mp4",
            use_container_width=True,
        )
        if result["evidence"]:
            st.subheader("Possible-risk evidence frame")
            st.image(result["evidence"], caption="Human verification is required.")
    else:
        st.info("Your processed video will appear here.")

st.divider()
st.caption(
    "AquaGuard AI portfolio demonstration by Danwin Shaju • "
    "The movement heuristic is illustrative and is not a validated drowning classifier."
)
