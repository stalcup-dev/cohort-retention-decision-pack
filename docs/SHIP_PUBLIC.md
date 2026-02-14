# Public Ship Checklist

Use this checklist before each public push.

## Content Integrity
- [ ] No unresolved placeholders remain (`TODO`, `TBD`, `<...>`, instructional blanks).
- [ ] Public docs use business-first language and avoid tutorial/training tone.
- [ ] Decision framing is explicit (targets, guardrails, non-causal scope).

## README 90-Second Test
- [ ] One-sentence value proposition is visible at top.
- [ ] ICP is explicit.
- [ ] Outputs and artifact links are explicit and clickable.
- [ ] Minimal run commands are copy-paste ready.
- [ ] Proof and trust signals are explicit.
- [ ] Public vs private scope is explicit.
- [ ] Roadmap and known limitations are present.

## Link + Artifact Validity
- [ ] All README links resolve to repo-relative existing files.
- [ ] `exports/public_release_latest.zip` exists and is up to date.
- [ ] Story screenshots render in README.
- [ ] Public release includes memo, story, and summary artifacts.

## Reproducibility + Trust Signals
- [ ] `py -3 -m pytest -q` passes.
- [ ] `py -3 scripts/public_audit.py` passes.
- [ ] `py -3 scripts/build_public_zip.py` passes.
- [ ] CI workflow files remain in `.github/workflows/` and are green.

## Security + Redaction
- [ ] No private/internal folders are tracked unintentionally.
- [ ] No machine paths, proxy variables, or local env hints appear in public docs.
- [ ] Publish from `exports/public_release_latest.zip`, not from ad hoc file selection.

## Release Receipt
- Date:
- Commit SHA:
- `pytest -q`:
- `public_audit.py`:
- `build_public_zip.py`:
- Release bundle: `exports/public_release_latest.zip`
