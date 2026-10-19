# Fitbit MCP — design

Read-only MCP server (Python, uv, stdio) exposing Google Health API v4 data from a Fitbit Air.

## API facts used
- Base: `https://health.googleapis.com/v4/users/me/...`
- `GET dataTypes/{t}/dataPoints` (list), `GET dataTypes/{t}/dataPoints:reconcile`, `POST dataTypes/{t}/dataPoints:rollUp`, `POST dataTypes/{t}/dataPoints:dailyRollUp`, `GET pairedDevices`, `GET identity`.
- Pagination: `pageSize` / `pageToken` → `nextPageToken` (empty = last page). Max page 10000, 25 for `sleep` and `exercise`.
- List filter fields (AIP-160, `>=` and `<`, joined by `AND`):
  - interval: `{t}.interval.civil_start_time`
  - sample: `{t}.sample_time.civil_time`
  - daily: `{t}.date`
  - session: `{t}.interval.civil_start_time`; sleep: `sleep.interval.civil_end_time`; ECG: `electrocardiogram.interval.start_time >=` only (RFC 3339)
  - `{t}` is the snake_case data type name.
- rollUp body: `range.startTime/endTime` (UTC RFC 3339), `windowSize` (`"Ns"`). dailyRollUp body: `range.start/end` as CivilDateTime, `windowSizeDays`. Both closed-open.
- Rollup range limit: 14 days for heart-rate, total-calories, active-minutes, calories-in-heart-rate-zone; 90 days otherwise. Errors pass through.
- Testing-mode refresh tokens expire after 7 days.

## Auth
- `uv run fitbit-mcp auth`: InstalledAppFlow loopback against a Desktop OAuth client whose JSON path is in `FITBIT_MCP_CLIENT_SECRETS`. Token saved to `~/.config/fitbit-mcp/token.json` (0600).
- Scopes (readonly): activity_and_fitness, health_metrics_and_measurements, sleep, nutrition, ecg, irn, settings (settings is required by pairedDevices).
- Server loads the token and uses `AuthorizedSession` (auto refresh). Missing token or `RefreshError` → tool error telling the user to run `fitbit-mcp auth`.

## Tools
Generic: `list_data_types`, `list_data_points(data_type, start, end)`, `reconcile_data_points(data_type, start, end, source?)`, `roll_up(data_type, start, end, window_seconds)`, `daily_roll_up(data_type, start_date, end_date)`, `list_paired_devices`.
`list`/`reconcile` `start`/`end` are local civil `YYYY-MM-DD[THH:MM:SS]`, end exclusive; `roll_up` takes UTC. `daily_roll_up` dates are inclusive. `source` (reconcile only, the only list-style call that accepts it) ∈ `all-sources`, `google-wearables`, `google-sources`.
Errors are raised as MCP `ToolError` so Google's message and the sign-in hint reach the model (mcp 2.x masks other exceptions).

Metric tools take `start_date`, `end_date` (inclusive):

| Tool | Data type | Op |
|---|---|---|
| get_steps | steps | dailyRollUp |
| get_distance | distance | dailyRollUp |
| get_calories | total-calories | dailyRollUp |
| get_active_zone_minutes | active-zone-minutes | dailyRollUp |
| get_heart_rate | heart-rate | dailyRollUp |
| get_resting_heart_rate | daily-resting-heart-rate | list |
| get_hrv | daily-heart-rate-variability | list |
| get_spo2 | daily-oxygen-saturation | list |
| get_respiratory_rate | daily-respiratory-rate | list |
| get_skin_temperature | daily-sleep-temperature-derivations | list |
| get_vo2_max | daily-vo2-max | list |
| get_sleep | sleep | list |
| get_workouts | exercise | list |

## Files
- `src/fitbit_mcp/catalog.py`: readable data types → kind, ops.
- `src/fitbit_mcp/auth.py`: sign-in flow, token load.
- `src/fitbit_mcp/client.py`: `HealthClient` over a requests-style session.
- `src/fitbit_mcp/server.py`: FastMCP tools + `main` entry point.
- `tests/`: fake-session unit tests for filters, paging, bodies.

## Open check
- Daily filter field casing: the reference example uses `dailyHeartRateVariability.date`; we use snake_case and confirm in the live smoke test.
