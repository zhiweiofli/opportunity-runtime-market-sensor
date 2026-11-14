# OR Judge · Google Drive → GitHub → Pages

## Source of truth

- Google Drive Research/Judge files remain the authoritative source. GitHub stores a version-controlled private mirror; a Drive success is not a GitHub success.
- `or-archive/research/`: original Research Google Docs exported as UTF-8 Markdown; `or-archive/judge/`: complete archived Judge reports.
- `or-archive/manifest.json`: source Drive IDs, modified timestamps, mirror paths, and sync statuses. Keep distinct IDs; never overwrite a different source with the same name.
- `site/data/latest.json`: curated **sanitized decision projection**; `site/index.html`: read-only viewer. Do not expose the unredacted private documents on Pages.

## Recurring contract

Every `judge@0.2.2` run (every three days from 2026-11-15 19:00 Asia/Taipei):
1. Re-list and read last 7 days' Research plus still viable historical Judge candidates and confirmed human decisions; use Source Signal/Research version to dedupe.
2. Preserve all judgment and human approval rules. Archive to the Drive Judge folder and verify by reread and folder listing.
3. Sync all new or updated eligible Research and the completed Judge to GitHub private archive; reconcile by Google Doc ID and modified time, and verify file readbacks. Never classify a demo/PILOT as a real candidate.
4. Build an anonymized `site/data/latest.json` with 3–5 business-oriented opportunities, statuses, human decisions and audit freshness; use explicit unknowns and preserve Research stage/status.
5. Publish only the `site/` folder with GitHub Actions Pages workflow. If Pages isn't enabled or deployment is unverified, say so. GitHub failures don't invalidate a verified Google Drive archive.

## Deployment and privacy

GitHub Pages websites are normally publicly reachable even when the source repository is private. Private folder contents in `or-archive/` are **not** deployed because the workflow uploads only `./site`. Do not include secrets, full private Research or personal decision notes in `site/`.

Enable GitHub Pages in repository Settings → Pages → Build and deployment → GitHub Actions. Verify actual deployment before claiming a working public URL. Private repository Pages eligibility depends on the account plan.

## Current sync

The first mirrored sync is incremental. `manifest.json` identifies completed exports and any `backfill_pending` records. An initial document inventory is not a claim that all documents were mirrored. Original Market Sensor workflows and behavior remain unchanged.
