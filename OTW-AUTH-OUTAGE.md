# Network-wide authentication outage (2026-11-26, discovered ~07:15Z)

## Scope
EVERY wargame login on BOTH networks now returns "Permission denied (publickey,password)"
with clean password-level rejections (TCP connects, banners arrive, auth methods offered):

| account | password | last verified working | now |
|---|---|---|---|
| vortex13 (2228) | 6iyARs3cY | 06:30Z today (L13 attempt 7) | DENIED |
| maze1 (2225) | Sp5VmLGFC0 | today (L0 solve) | DENIED |
| maze2 (2225) | jJF6jn9qW6 | 2026-11-23 | DENIED |
| bandit0 (2220) | bandit0 | canonical entry, never rotated | DENIED |
| narnia0 (2226) | narnia0 | canonical entry, never rotated | DENIED |
| drifter0 (2230) | yttCfzKiorcOz... | 2026-11-23 | DENIED |
| all S2S (84.22.114.35) | all known pairs | earlier today | DENIED (10d1173) |

## Analysis
- bandit0/bandit0 and narnia0/narnia0 are the canonical OTW entry pairs that have NEVER
  been rotated in the games' history - their rejection cannot be credential rotation.
- Rejection shape: full banners, "Authentications that can continue: publickey,password",
  password packet sent and rejected - NOT connection-level bans (TCP + auth transport fine).
- Timeline: vortex13 worked at 06:30Z, denied by ~07:15Z; S2S logins died between ~06:00Z
  and ~06:40Z (10d1173). The two networks went out within the same hour.
- Conclusion: coordinated auth outage (PAM/sshd backends) or a deliberate global credential
  reset across OTW labs + S2S. An agent-side IP ban cannot explain canonical-entry failures
  arriving at cleanly functioning auth daemons on both networks at once.

## Consequence
No live level can be solved, verified, recorded, or replayed until the labs accept logins
again. All live-work queues are BLOCKED-external. Local work that remains valid: JSON
rebuilds for levels whose casts already exist (maze L1-L8 stubs have casts), audits,
narration re-keying - but per the replay rule every rebuild must be REPLAYED live before
commit, which is impossible during the outage; hence only already-verified material ships.

## Suggested operator actions
1. Check status pages / IRC (#wargames, #otw) for an outage notice.
2. Retry the canonical bandit0/bandit0 from another IP (rules our container IP in/out).
3. When auth returns: re-verify one canonical pair first, then resume the queues.
