from __future__ import annotations

from typing import Literal, NotRequired, TypedDict

FrameWorkerDecoderHardware = Literal[
    "auto",
    "cpu",
    "cuda",
    "vaapi",
    "qsv",
    "videotoolbox",
    "d3d11va",
    "d3d12va",
    "dxva2",
    "vulkan",
    "opencl",
    "drm",
    "rkmpp",
]
"""Hardware backend for the detection decoder. `auto` probes the platform order, `cpu` forces software decoding."""


class FrameWorkerDecoderSettings(TypedDict):
    """Decoder hardware selection for the frame worker."""

    hardware: FrameWorkerDecoderHardware
    """Hardware backend to decode with."""
    device: NotRequired[str]
    """Device the backend opens (GPU index like `0`, or a path like `/dev/dri/renderD128`). Backend default when omitted."""


class CameraFrameWorkerSettings(TypedDict):
    """Frame worker (decoder) settings."""

    mainStreamAnalysis: NotRequired[bool]
    """Analyse the main stream while something is detected, instead of the detection stream."""
    decoder: NotRequired[FrameWorkerDecoderSettings]
    """Decoder hardware selection. Applies on the machine that decodes this camera (master or assigned worker); an unusable selection falls back to auto."""
    workerDecoder: NotRequired[FrameWorkerDecoderSettings]
    """Decoder hardware selection used instead of `decoder` while this camera decodes on its assigned worker. Falls back to `decoder` when omitted."""


SnapshotRefreshMode = Literal["interval", "onView", "onDemand"]
"""When a camera takes a new snapshot. `interval` runs a timer, `onView` fetches for a viewer once the stored picture is older than `maxAge`, `onDemand` only on an explicit request (automations, the refresh button, the API)."""


class SnapshotSettings(TypedDict):
    """Snapshot settings for a camera."""

    mode: SnapshotRefreshMode
    """When a new picture is taken."""
    interval: int
    """Timer interval in seconds for `interval` mode (10 to 3600)."""
    maxAge: int
    """Age in seconds after which a viewer gets a new picture in `onView` mode (10 to 3600)."""
