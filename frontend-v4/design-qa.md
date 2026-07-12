# Design QA

- Source visual truth: `assets/references/studio-command.png`
- Intended implementation capture: `assets/screenshots/guide-panel-v4.png`
- Viewport: 1440 x 1024
- State: guide console preview, room 839201, 8 visitors, 2 private requests
- Full-view comparison evidence: source opened successfully; implementation screenshot unavailable because the managed Windows sandbox rejected the user-approved Playwright Chrome child process with `spawn EPERM`.
- Focused region comparison evidence: blocked for the same reason.

**Findings**

- [P1] Rendered visual comparison unavailable
  Location: guide console and all responsive views.
  Evidence: the local server returned every V4 route successfully and the enhancement script passed syntax validation, but Chromium could not be launched by Playwright inside the managed sandbox.
  Impact: typography metrics, final overflow, and pixel-level layout fidelity cannot be certified from a rendered capture.
  Fix: run the Playwright capture in an environment that permits browser child processes, then compare it with `assets/references/studio-command.png` at 1440 x 1024.

**Static Fidelity Review**

- Fonts and typography: Noto/Source Han serif and Inter/Noto Sans stacks are mapped to editorial headings and operational text.
- Spacing and layout rhythm: 236px sidebar, 72px command header, 32px workspace gutters, 12px controlled radii, and thin dividers match the selected direction.
- Colors and visual tokens: ink `#172126`, ivory `#fbfaf6`, clay `#df7032`, sage `#4e8c63`, and warm gray borders are centralized in CSS variables.
- Image quality and assets: the selected visual target is preserved as a project reference; no required content imagery was replaced with CSS drawings.
- Copy and content: existing page content, IDs, API scripts, and control labels are preserved; preview fixtures mirror the selected guide-console state.

**Patches Made**

- Added a shared Studio Command design layer across all six product surfaces.
- Added the guide-console navigation rail, live room card, attention queue, and responsive fallback.
- Added a query-scoped preview state without changing the production authentication flow.
- Replaced quick-action emoji with Material Symbols and removed decorative gradients.

**Implementation Checklist**

- Capture guide console at 1440 x 1024.
- Check 390px mobile layouts for landing and assistant.
- Exercise start, pause, skip, spot selection, request shortcut, upload, search, and assistant send controls.
- Resolve any P0/P1/P2 visual mismatch and update this report.

final result: blocked
