# Docker Optimization Playbook

## 1. Objective Prioritization

Set explicit priorities before editing:
- Minimize image size
- Minimize cold start latency
- Minimize build time in CI
- Maximize runtime security
- Maximize portability across architectures

Choose at most two primary objectives; treat others as constraints.

## 2. Base Image Strategy

- Prefer official images with clear maintenance cadence.
- Prefer slim/alpine/distroless variants only after checking native deps compatibility.
- Pin explicit version tags and update intentionally.

Quick guidance:
- Python apps: `python:<version>-slim` as safe default.
- Node apps: `node:<version>-slim` for build stage, distroless or slim runtime when possible.
- Go/Rust static binaries: distroless or scratch runtime if debugging needs are minimal.

## 3. Layer and Cache Strategy

- Put infrequently changing steps first.
- Copy lockfiles/manifests before full source copy.
- Install deps before copying volatile app files.
- Collapse package manager update/install/cleanup in one `RUN` when practical.

Pattern:
1. `COPY` dependency descriptors
2. install dependencies
3. `COPY` application source
4. runtime-only configuration

## 4. Multi-stage Build Decision

Use multi-stage when:
- build tooling is heavy;
- runtime needs only final artifacts;
- security policy requires minimal runtime surface.

Avoid unnecessary stages when the app is tiny and complexity outweighs savings.

## 5. Security Baseline

- Use non-root `USER`.
- Remove build tools from runtime image.
- Avoid embedding secrets in layers.
- Keep package set minimal.
- Add `HEALTHCHECK` for long-lived services.
- Use explicit `ENTRYPOINT`/`CMD` and predictable signal handling.

## 6. Runtime Reliability

- Ensure process receives SIGTERM and exits cleanly.
- Keep writable paths explicit.
- Use env vars with documented defaults.
- Add lightweight health endpoint checks where relevant.

## 7. Review Checklist

- Is the base image version explicit?
- Is non-root user configured?
- Is dependency caching optimized?
- Are unnecessary files excluded (`.dockerignore`)?
- Is image size reduction balanced with maintainability?
- Are monitoring and health semantics clear?
