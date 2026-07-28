# GitHub Repo Audit Tracker

Agentic audit of Cfomodz (and related org) repositories: each audited repo gets a
deep-read of its actual code — bugs, security issues, broken packaging, doc gaps —
recorded in `audits/<repo>.md` with a TODO list.

Legend: ✅ audited · 🔄 in progress · ⬜ queued

## Audited

| Repo | Date | Notes |
|---|---|---|
| ✅ [github-use](audits/github-use.md) | 2026-07-28 | `--include-forks` broken; fails own license/tests checks |
| ✅ [StreamDrop](audits/StreamDrop.md) | 2026-07-28 | deadlock on update/delete; auto-recovery can't restart; unauthenticated API leaks stream keys |
| ✅ [spam-baiter](audits/spam-baiter.md) | 2026-07-28 | missing soundboard files crash live calls; phantom bluetooth bridge; deps can't install |
| ✅ [browser-osint](audits/browser-osint.md) | 2026-07-28 | CWD-relative templates kill detection; broken Google reverse-search; stale docs |
| ✅ [audible-to-yoto](audits/audible-to-yoto.md) | 2026-07-28 | ffmpeg loop skips books after first; `set -e` defeats error handling; placeholder badges |
| ✅ [Brother-QL-710W_Incrementing-Label-Creator](audits/Brother-QL-710W_Incrementing-Label-Creator.md) | 2026-07-28 | won't start (missing template modules); no deps manifest; counter race |
| ✅ [dmarket_bot](audits/dmarket_bot.md) | 2026-07-28 | buy loop crashes every cycle (str/float compare); zip misalignment = wrong-price orders |
| ✅ [Inbox-Sorter](audits/Inbox-Sorter.md) | 2026-07-28 | stored XSS via From: header; unauthenticated cache routes |
| ✅ [steam_user_stats](audits/steam_user_stats.md) | 2026-07-28 | debug=True on 0.0.0.0 (RCE); API key over plain HTTP; DOM XSS |

## Queue (own, non-fork, most recently active first)

- ⬜ its_listed (private)
- ⬜ adversarial-risk-group (private)
- ⬜ its_listed_kickstarter (private)
- ⬜ coin-poc-orchestrator (private)
- ⬜ ebay-sourcing (private)
- ⬜ auto-browse-screen-recording-video-for-voiceover
- ⬜ Zoom-Video-Auto-Editor-for-vertical-video-participants
- ⬜ if-a-user-account-is-found
- ⬜ career-ops (private)
- ⬜ cue-voice-sales-agent-helper (private)
- ⬜ Impossible-Invoice
- ⬜ Deduplicate-and-Meta-Tag-Photos
- ⬜ FDG-ZUI
- ⬜ passcode-pattern-recognition
- ⬜ price-of-war
- ⬜ accessibility-board
- ⬜ Dual-Tone-Multi-Frequency-DTMF-tone-cleaner
- ⬜ walk-n-meters-to-the-car-wash
- ⬜ my.remarkable
- ⬜ Plane-Eisenhower-Matrix-Desktop-Wallpaper-for-KDE-Plasma
- ⬜ Open-edX-Accessibility-Reader
- ⬜ Walgreen-Photo-Library-Downloader
- ⬜ Open-Demand-Letter
- ⬜ vidashby.static
- ⬜ pinewood-derby-linux
- ⬜ multi-view / FFAIPeg / free-right-now / deep-task / Sales-Goal-Thermometer / Speak-Now-Driver / easemail
- ⬜ phone-number-mnemonic
- ⬜ ai-clicker / Qwen3-TTS-Web-GUI
- ⬜ community-use / tech-now / parallax-studio-pro
- ⬜ remote-python-agent-admin-tool / MITM-Audio-Capture-Tool
- ⬜ Press-Pass / object-scanning-frontend
- ⬜ PCGS-slab-picture-to-listing-tool
- ⬜ unitranslate / Object-Scanning-Listing-Tool-Core-Backend- / AI-Video-Production-Toolkit
- ⬜ etsy-inventory-export-tool / obs-input-checker / what-bot / centered-div
- ⬜ Cfomodz (profile README)
- ⬜ QES-WJ01 org: l2l suite (l2l, l2l-punch-list-automatic-selection, m2m, qms, dashboards…)
- ⬜ Patch-Code-Prosperity org: Chrome-WebSocket-Proxy-for-OBS, Tornado-Invest-API, Stock-Corporate-Action-Data, Schwab-API-Sandbox, alerts-server…
- ⬜ remaining private repos (tmp, Pen, security-matrix-course, store-credits, skool-*, cfomodz.com, vidashby.com, …)

Forks and archived repos are excluded unless requested.
