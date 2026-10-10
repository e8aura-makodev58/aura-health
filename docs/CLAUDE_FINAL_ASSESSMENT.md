# Claude assessment before design lock

2026-10-10. Claude (reviewer). Docs only; no code changed. Based on the live site
(https://aura-health.makodev58.com, DeepSeek `deepseek-flash` per `/system/status`) at
`cde6d43`: clinician and patient views at 1280 px, patient at 390 px, and one simulator run
("Simulate: flu 3 days", Case B). Not verified: all five agent roles live, other simulator
events, the three-minute story buttons, the clinician view on a phone, accessibility,
latency under load. I read Codex's brainstorm in `HANDOVER.md` (2026-10-10) and agree with
its direction; this adds what I saw on screen.

## 1. What is clearly better than a week ago
- Cards with rounded values ("about 2.5 h later", "about 1,900 steps a day fewer"), a
  span bar, "Why?" and "See on chart"; a finding-dates strip; callouts on the charts.
- Patient home has icon cards in plain wording, "Not sent" visit note, no charts (§43),
  and the phone layout is clean.
- The simulator works end to end: "flu 3 days" added 46 events in about 25 s and the
  charts show it (resting HR up, HRV down, respiratory rate up, skin temperature up,
  thermometer 38).

## 2. What still undercuts it (ranked by effect on the first impression)
1. **The flu is in the charts but not in the assessment.** After the simulated flu the
   assessment still lists only sleep and activity. Nothing says "heart rate and
   temperature rose this week". That is the cause-and-effect moment the demo exists for,
   and it fails. Likely cause: the engine only evaluates the four original channels, and
   the new channels are display/research tier, so the agent gets no facts about them.
2. **The AI text is inconsistent and the fallback has a defect.** The first load showed
   "AI-written · sources checked"; later loads (and the patient screen every time I
   looked) showed "Offline extraction". The fallback produced two Sleep timing cards
   with different spans (23 Feb–11 Mar and 21 Feb–22 Feb). Codex already noted live
   drafts being rejected; that means most viewers may see the non-AI path.
3. **Raw prose survives.** The AI-written version still printed "Sleep duration was
   recorded from 2026-03-04 through 2026-03-11 (7.9611 to 8.0647 hours)…" with four
   decimals and ISO dates, and the headline says "versus anchored references".
4. **No synthesis.** Nothing connects later sleep, lower activity and a week of Rough
   check-ins, and the check-ins are not a clinician card. "Worth asking" is the same three
   generic questions in every state.
5. **Patient hierarchy and tone.** The headline "A little less to carry." sits above two
   "shifted" cards and a "Rough" check-in. "steady · reports" beside "Rough" is
   confusing. The cards have labels but no plain sentence (§43 asked for a short recap).
   The dark primary button is "I want to mention something"; the real benefit, the visit
   note, is a muted row. "Why? / Sources" repeats on every card.
6. **The page is long.** After the simulator it shows ten charts; the display-only
   intermittent ones (BP, thermometer, SpO2) show two or three dots and look empty.
7. Minor: three empty-looking accordions (Evidence, Context, Details); the Demo guide
   panel is dense.

## 3. Proposed lock scope (smallest set; then fixes only, no new features)
- **L1 Flu shows up.** Give the agent descriptive, server-computed window comparisons
  for every enabled channel (last 7 days versus the prior baseline window, with source
  IDs), shown as cards. This is the approved "descriptive analysis tools" decision
  (§39 item 5) and does not need engine decisions. **User decision:** descriptive only, or
  also let the engine raise drift on the new channels.
- **L2 Make the AI path reliable.** Investigate why live drafts are rejected without
  loosening validation; dedupe findings per channel (one latest card per channel); show
  the "Offline extraction" label only when it applies.
- **L3 One synthesis line** under the headline, built from verified co-occurring
  findings including the check-ins, plus a check-ins card; "Worth asking" varies with
  the findings.
- **L4 Patient screen:** one plain sentence of recap above the cards, "Prepare for my
  appointment" as the primary action, drop "steady" beside check-ins, one "Why?" per
  card.
- **L5 Tidy:** remove the leftover raw sentence and "anchored references", group charts
  as the four core plus an "Also moved" group, hide empty accordions.
- Order: L1, L2, L3, L4, L5. Walk the three-minute story and the other simulator events
  afterwards and record what happens.

## 4. For the user
Lock only after L1 and L2: until then the main demo moment does not work and the AI is
often not on the screen. The rest is polish. Codex should confirm this scope with the user
before building (HIL rule in `HANDOVER.md`).
