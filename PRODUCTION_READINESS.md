# Hex Face ERP Production Readiness Plan

This document summarizes key updates needed to make this biometric attendance app production-ready for ERP deployment.

## 1) Critical security and data protection (do first)

1. **Require authentication for attendance APIs**
   - `recognized_faces` and `post_attendance_via_method` are currently exposed with `allow_guest=True`.
   - Move to authenticated calls and role checks (kiosk user + signed requests).

2. **Remove hardcoded infrastructure paths and URLs**
   - Replace hardcoded `SITE_URL`, training/output/validation paths, and YOLO model path with configurable settings/env vars.
   - This is mandatory for multi-site and cloud deployments.

3. **Stop storing biometric snapshots in repo/app folders**
   - Validation snapshots are currently saved inside app paths.
   - Move to site-private storage (`sites/<site>/private/files/...`) and add retention policy + cleanup job.

4. **Harden secret management**
   - Never depend on static tokens embedded into process globals.
   - Rotate credentials, use short-lived service credentials when possible, and audit all auth usage.

5. **Input and payload hardening**
   - Validate base64 image size, MIME type, max frames, and office_id format before decode/process.
   - Reject malformed or oversized payloads early.

## 2) Correctness and reliability

1. **Fix attendance identity mismatch**
   - Recognition returns a person name, but attendance posting uses `office_id` from client input.
   - Use a trusted server-side mapping between recognized employee and Employee record before check-in.

2. **Make recognition deterministic and auditable**
   - Persist confidence thresholds in settings (face distance + anti-spoof confidence).
   - Store decision metadata per attempt (without persisting raw biometrics longer than policy allows).

3. **Improve anti-spoof strategy**
   - Current YOLO person-detection is not equivalent to liveness.
   - Introduce face liveness model inference (challenge/response or blink/head movement + model score) and tune with real-world data.

4. **Fix training pipeline behavior**
   - `sync_employee_images` retrains during each loop iteration and may duplicate data.
   - Sync all images first, then trigger a single training job.
   - Add versioned model artifacts and rollback support.

5. **Error handling and observability**
   - Replace `print` debugging with structured logs.
   - Standardize API responses and error codes.
   - Add retry/backoff for downstream attendance posting failures.

## 3) Performance and scalability

1. **Load models once with startup checks**
   - Validate model files and encoding artifacts at startup.
   - Fail fast with clear diagnostics if dependencies/models are missing.

2. **Move heavy jobs off request path**
   - Training and model refresh should run asynchronously via background jobs.

3. **Tune for kiosk throughput**
   - Add per-device rate limits and request timeout budgets.
   - Cache encodings in memory with safe reload hooks.

## 4) ERP integration hardening

1. **Device trust model**
   - Register kiosk devices and sign payloads with per-device credentials.

2. **Idempotent attendance writes**
   - Prevent duplicate check-ins when client retries.

3. **Time and timezone correctness**
   - Use server timezone-aware timestamps and include device/server clock skew checks.

4. **Configurable policy controls**
   - Admin settings for confidence thresholds, required shots, liveness mode, geo requirements, and auto-attendance toggle.

## 5) Front-end and UX quality

1. **Fix typo/endpoint consistency**
   - Ensure all client scripts call the same correct backend method name.

2. **Add clear failure reasons and recovery guidance**
   - Differentiate camera denied, no face, spoof suspected, unknown person, and network failure.

3. **Accessibility and kiosk resilience**
   - Add fullscreen kiosk mode support, reconnect handling, and camera stream cleanup on navigation.

## 6) DevEx, testing, and release readiness

1. **Tests to add before go-live**
   - Unit tests: encoding, recognition decision logic, input validation.
   - Integration tests: Employee mapping -> check-in write.
   - Security tests: unauthorized access, payload abuse, replay attempts.

2. **CI gates**
   - Enforce lint + tests + dependency audit + basic SAST on every PR.

3. **Operational runbooks**
   - Incident playbooks for camera outages, model drift, and false acceptance spikes.
   - Define SLOs (recognition success %, latency, spoof detection metrics).

## Suggested rollout plan

- **Phase 1 (1-2 weeks):** Security/auth hardening, path/config cleanup, deterministic employee mapping.
- **Phase 2 (1-2 weeks):** Async training pipeline, logging/metrics, idempotent attendance APIs.
- **Phase 3 (2-4 weeks):** Liveness upgrade, threshold tuning with pilot data, full test coverage and staged rollout.

