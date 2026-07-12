from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend-v4"

PAGES = {
    "landing": "landing",
    "user-portal": "user-portal",
    "recommend": "recommend",
    "vision": "vision",
    "ai-assistant": "ai-assistant",
    "knowledge-base": "knowledge-base",
    "dashboard": "dashboard",
    "guide-panel": "guide-panel",
    "avatar-studio": "avatar-studio",
}

EXTRA_IDS = {
    "user-portal": {
        "avatar-container", "avatar-status-label", "room-join-overlay", "room-code-input",
        "room-join-btn", "room-join-error", "member-list-container", "menu-toggle", "menu-close",
        "function-overlay", "fn-knowledge", "fn-audio", "fn-map", "fn-ai", "avatar-mode",
        "text-mode", "btn-switch-text", "btn-switch-avatar", "public-chat-area",
        "public-chat-input", "public-chat-send", "narration-text", "btn-voice", "spot-chip",
        "spot-chip-name", "tts-player", "page-body", "route-progress-bar", "route-progress-fill",
        "route-progress-text", "route-spots-pills", "spot-info-card", "spot-info-name",
        "spot-info-desc", "fn-result-modal", "fn-result-title", "fn-result-body",
    },
    "guide-panel": {
        "room-id-display", "route-name-display", "member-count", "member-status-dot",
        "current-spot-display", "scenic-area-display", "progress-display", "pending-requests-row",
        "pending-requests-text", "btn-start", "btn-skip", "btn-collect", "btn-pause",
        "btn-copy-room", "btn-share", "btn-view-requests", "btn-view-requests2",
        "requests-badge", "spot-selector-btn", "spot-selector-label", "spot-dropdown",
        "member-list", "member-list-title", "tab-all", "tab-requests", "route-modal",
        "route-list", "route-cancel", "route-confirm",
    },
}

DYNAMIC_IDS = {"typing-indicator", "requests-close", "help-card"}

failures = []
for page, script in PAGES.items():
    html_path = FRONTEND / "pages" / page / "index.html"
    js_path = FRONTEND / "assets" / "js" / "pages" / f"{script}.js"
    if not html_path.exists():
        failures.append(f"{page}: missing HTML")
        continue
    if not js_path.exists():
        failures.append(f"{page}: missing JS")
        continue
    html = html_path.read_text(encoding="utf-8")
    js = js_path.read_text(encoding="utf-8")
    required = (set(re.findall(r"getElementById\(['\"]([^'\"]+)", js)) - DYNAMIC_IDS) | EXTRA_IDS.get(page, set())
    ids = set(re.findall(r'\bid=["\']([^"\']+)', html))
    missing = sorted(required - ids)
    if missing:
        failures.append(f"{page}: missing DOM ids: {', '.join(missing)}")

if failures:
    raise SystemExit("\n".join(failures))
print(f"Frontend DOM contracts passed for {len(PAGES)} pages")
