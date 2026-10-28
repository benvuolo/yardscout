/* Scan watchdog (hourly Cloudflare cron). GitHub's own schedule drops runs
 * under load — on 2026-10-28 it skipped the 20:00 scan AND every hourly run
 * of the GitHub-side watchdog — so the backup lives here, on Cloudflare's
 * cron, which has been reliable for the Monday digest.
 *
 * If no scan is queued/running and the last SUCCESSFUL scan started >= 5 h
 * ago, dispatch scan.yml. Needs SCAN_DISPATCH_TOKEN: a fine-grained GitHub
 * token for benvuolo/yardscout with "Actions: Read and write". Without it
 * this is a silent no-op. */
const REPO = 'benvuolo/yardscout';
const MAX_AGE_MS = 5 * 3600_000;

export async function runScanWatchdog(env, { now = Date.now() } = {}) {
  const token = env.SCAN_DISPATCH_TOKEN;
  if (!token) return { action: 'skipped', reason: 'no token' };
  const gh = (path, init = {}) => fetch(`https://api.github.com/repos/${REPO}${path}`, {
    ...init,
    headers: {
      authorization: `Bearer ${token}`,
      accept: 'application/vnd.github+json',
      'x-github-api-version': '2022-11-28',
      'user-agent': 'yardscout-scan-watchdog',
      ...(init.body ? { 'content-type': 'application/json' } : {}),
    },
  });
  const runs = await gh('/actions/workflows/scan.yml/runs?per_page=20');
  if (!runs.ok) return { action: 'error', status: runs.status };
  const active = ((await runs.json()).workflow_runs || [])
    .filter((r) => ['queued', 'in_progress', 'waiting', 'pending', 'requested'].includes(r.status));
  if (active.length) return { action: 'none', reason: 'scan active' };
  const ok = await gh('/actions/workflows/scan.yml/runs?status=success&per_page=1');
  if (!ok.ok) return { action: 'error', status: ok.status };
  const last = ((await ok.json()).workflow_runs || [])[0];
  const startedAt = last ? Date.parse(last.run_started_at || last.created_at) : 0;
  const ageMs = now - startedAt;
  if (ageMs < MAX_AGE_MS) return { action: 'none', reason: 'fresh', ageHours: +(ageMs / 3600_000).toFixed(1) };
  const d = await gh('/actions/workflows/scan.yml/dispatches', { method: 'POST', body: JSON.stringify({ ref: 'main' }) });
  return { action: d.status === 204 ? 'dispatched' : 'error', status: d.status, ageHours: +(ageMs / 3600_000).toFixed(1) };
}
