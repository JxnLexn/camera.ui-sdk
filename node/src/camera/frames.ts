/**
 * Hardware backend for the detection decoder.
 * `auto` probes the platform order, `cpu` forces software decoding.
 */
export type FrameWorkerDecoderHardware =
  'auto' | 'cpu' | 'cuda' | 'vaapi' | 'qsv' | 'videotoolbox' | 'd3d11va' | 'd3d12va' | 'dxva2' | 'vulkan' | 'opencl' | 'drm' | 'rkmpp';

/** Decoder hardware selection for the frame worker. */
export interface FrameWorkerDecoderSettings {
  /** Hardware backend to decode with. */
  hardware: FrameWorkerDecoderHardware;
  /** Device the backend opens (GPU index like `0`, or a path like `/dev/dri/renderD128`). Backend default when omitted. */
  device?: string;
}

/** Frame worker (decoder) settings. */
export interface CameraFrameWorkerSettings {
  /** Analyse the main stream while something is detected, instead of the detection stream. */
  mainStreamAnalysis?: boolean;
  /** Decoder hardware selection. Applies on the machine that decodes this camera (master or assigned worker); an unusable selection falls back to auto. */
  decoder?: FrameWorkerDecoderSettings;
  /** Decoder hardware selection used instead of `decoder` while this camera decodes on its assigned worker. Falls back to `decoder` when omitted. */
  workerDecoder?: FrameWorkerDecoderSettings;
}

/**
 * When a camera takes a new snapshot.
 * `interval` runs a timer, `onView` fetches for a viewer once the stored picture is older than `maxAge`,
 * `onDemand` only on an explicit request (automations, the refresh button, the API).
 */
export type SnapshotRefreshMode = 'interval' | 'onView' | 'onDemand';

/** Snapshot settings for a camera. */
export interface SnapshotSettings {
  /** When a new picture is taken. */
  mode: SnapshotRefreshMode;
  /** Timer interval in seconds for `interval` mode (10 to 3600). */
  interval: number;
  /** Age in seconds after which a viewer gets a new picture in `onView` mode (10 to 3600). */
  maxAge: number;
}
