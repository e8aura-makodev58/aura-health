# Review 2 of catch-up + calendar UI and browser suite — Gemini, 2026-10-15

Scope: `aura_ui/catchup.js` and `tests/browser/catchup_calendar.cjs` at `origin/main` `ab1dd09`
(code read plus one suite run; see Verified in the handover). Recommendations only; no code changed.
Severity: **M** = fix before relying on it, **L** = low, **T** = test gap.

## Findings in `catchup.js`

1. **M — Keyboard focus is lost on every day tap.** The `.med-day` click handler calls `showPreview()`,
   which does `preview.replaceChildren()` and rebuilds every button, so the focused button is destroyed.
   Keyboard and screen-reader users return to the top of the dialog after each toggle (and get no
   announcement of the new status). Fix: after re-render, refocus the button with the same `data-date`,
   and add an `aria-live="polite"` region (or update `med-update-message`) with the new status.
2. **M — Failed window load leaves the dialog half-usable.** In `openUpdate`, if `update-window` fails
   the dialog opens with an error, but `Tap days instead` / `Read this` stay enabled. With `state.window`
   null, `showPreview()` throws (`state.window.days`), an uncaught `pageerror`. Fix: disable the controls
   (or return early in `showPreview` when `state.window` is null) and offer Close/retry.
3. **L — "Update this day's medication" ignores the day.** `openUpdate(date)` only passes `onlyDate`
   as a boolean; the preview shows all 14 days and does not highlight or focus the chosen one. Pass the
   date through and focus/scroll that cell.
4. **L — Welcome-back is not dismissible and refetches too often.** `renderWelcomeBack` runs on every
   `renderCompanion` and calls `/coverage` each time; the banner persists until a record changes
   (the dose card dismissal uses `sessionStorage`, this one does not). Also `box.textContent` is set
   even while hidden. Consider a dismiss control and reusing `coverage` when `coverageFor` matches.
5. **L — Error after save leaves a stale Save state.** In the catch branch the result message is shown
   but `updateSave()` can re-enable Save for a request whose first attempt may have succeeded; this is
   safe because `state.requestId` is reused (idempotent), but the message for non-conflict errors should
   say "try again" so the patient knows retry is safe.
6. **L — Interpret failure when `state.window` is stale.** `result.window || state.window` keeps old
   locks if the server omits `window`; the save path then relies on the server's 409. Acceptable, just
   noting the dependency.
7. **L — Prompt dismissal outlives its cause.** `aura-med-update-dismissed:<patient>` lasts for the
   session even if many more days become unresolved. Fine for a demo; clear the key when the unresolved
   count increases if you want it to re-prompt.
8. **L — Calendar day buttons give no focus/selection cue after load.** `aria-pressed` is set only after
   a day loads, and `loadDay` scrolls smoothly even under reduced motion. Respect
   `prefers-reduced-motion` (`behavior: "auto"`).

No safety bypass found: the prompt is gated on `safety_normal`, `BLOCKED` closes the dialog and refreshes,
and nothing is saved before the Save press. Text is set via `textContent` everywhere (no HTML injection).

## Test-suite gaps (`catchup_calendar.cjs`)

- **T — Hard-coded fixture dates.** CU6 mocks `/coverage` with `today:'2026-03-11'` and fixed dates; it
  silently depends on the demo fixture's latest record day. Derive from the real `/coverage` response.
- **T — Order and fixture coupling.** CU2 uses `days.nth(11)` and `nth(12)` assuming those are unlocked;
  CU5's regex `2 of the last 14` depends on CU2 having saved exactly two days. Assert preconditions or read
  the date list from `/medication/update-window`.
- **T — Not covered:** `UPDATE_CONFLICT` message; `SAFETY_ACTIVE`/`BLOCKED` path closing the dialog;
  out-of-window note; the "Yes" branch (dashed styling becomes explicit); "Not now" dismissal; the
  calendar's disabled future/before-record cells; `calendar-update-day` button; clinician detail never shows
  the update button; keyboard operation and focus retention (finding 1); status cycling through
  Not sure and back to blank; the window-load failure (finding 2).
- **T — Sharing state not restored on failure.** CU5 restores sharing only on the success path. Wrap in
  `try/finally`.
- **T — Layout checks are page-level only.** `noScroll` checks the document width, not the dialog or the
  7-column grid at 390 px (a clipped cell would pass). Check `calendar-grid` and dialog `scrollWidth`
  against `clientWidth`, and day detail after opening it.
- **T — Visual styling untested.** "From most days" is checked through `data-basis` only; the dashed
  border and ring come from CSS and would pass even if the CSS broke. Assert a computed style.

## Suite run

`catchup_calendar.cjs` on `ab1dd09`, hosted, port 8056: all 12 checks PASS (CU1–CU6, phone 390 and laptop 1280). Needed `NODE_PATH` (playwright) and `LD_LIBRARY_PATH` (user-space libgbm) because this worktree has neither.

## Verdict

No blocking safety finding. Fix findings 1 and 2 (small, local changes) before the demo; the rest are
polish. The suite is a good happy-path smoke test but would not catch the failure paths above.
