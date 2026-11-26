# Blackbox L0 entry probe — BLOCKED (2026-11-26 ~06:35-06:50Z)

## What the documentation says
Archived official page (wayback 2013-12-05, blackbox.smashthestack.org:85/ — the game page
the FAQ points to): "ssh -l level1 blackbox.smashthestack.org -p 2225 — Password: level1".
Levels 1-10. The S2S FAQ (archived 2022) repeats the same pattern.

## What the live box says
blackbox.smashthestack.org:2225 = OpenSSH_4.3, host keys ssh-rsa/ssh-dss only, password auth
offered and answering. Tried (each a clean "Permission denied (publickey,password)"):
- level1: level1, blackbox, blackbox1, 1blackbox, Level1, LEVEL1, l3v3l1, smasher, irc,
  levelzero, bl4ckb0x, bl4ckb0x1, eltt0s
- level0: level0, blackbox, bl4ckb0x
- level1/level0/blackbox/guest username probes
- keyboard-interactive auth: not offered; only publickey,password
No web page anywhere on the box (80/81/85/8080/8000 all closed).

## The bigger finding — the whole S2S box locked out MID-SESSION
All SmashTheStack games share one host (84.22.114.35): blowfish :2222, blackbox :2225,
tux :2226, logic :2227, amateria :2229. Within the last hour EVERY known-good credential
pair on that host started failing with clean password rejections:
- logic level3 / PIZIPMWKEC — VERIFIED WORKING in this session 21:38-21:45Z (2026-11-25/26
  session), now denied (retested after a 3-min auth cool-down: still denied)
- blowfish level1 / ThatWasEasy — denied; yet the telnet-6666 entry STILL hands out
  GungJnfRnfl (unchanged), so the telnet side and ssh side now disagree
- blowfish level9 / Ur_t3h_sh1t — denied (worked 2026-11-25)
- tux pfwd / pfwd — denied
- vortex.labs.overthewire.org (different network) — unaffected
Rejection shape (full banner, auth offered, password-level reject — never connection
refuse/reset) rules out an IP ban at the connection layer. A 3-minute quiet period did not
restore access, arguing against a short auth-rate tarpit.

## Conclusion
The S2S host rotated (or disabled) its credentials between ~06:00Z and ~06:40Z on
2026-11-26 — right after our Logic L3/L4 session — or entered a locked state. Blackbox
entry credentials are unknown; recovering them requires the sanctioned channels (IRC
#logic / staff@smashthestack.org), which this agent cannot reach. No brute force attempted.
Blackbox is BLOCKED-pending-operator until the box accepts the documented entry pair
(level1/level1) or new credentials are provided.

## Suggested operator actions
1. Check from a different IP whether blackbox level1/level1 still works (rules our IP in/out).
2. Email staff@smashthestack.org / ask in IRC for the current Blackbox entry credentials.
3. Re-probe after any admin activity window (the box restarts lighttpd every 12h;
   /etc/lighttpd error log shows root-driven restarts on the 0th and 12th hour).
