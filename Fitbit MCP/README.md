# fitbit-mcp

Read-only MCP server for your Fitbit (Fitbit Air included) data via the [Google Health API](https://developers.google.com/health/about).

## 1. Google Cloud setup (once)

1. Create or pick a project at https://console.cloud.google.com.
2. Enable **Google Health API** (`health.googleapis.com`) under APIs & Services → Library.
3. Google Auth Platform → **Audience**: user type **External**, publishing status **Testing**, add your own Google account under **Test users**.
4. Google Auth Platform → **Data Access** → Add or remove scopes → filter by "Google Health API" and add these `.readonly` scopes: `activity_and_fitness`, `health_metrics_and_measurements`, `sleep`, `nutrition`, `ecg`, `irn`, `settings`.
5. Google Auth Platform → **Clients** → Create client → type **Desktop app**. Download the JSON.

## 2. Sign in

```bash
cd "/Users/whoishmk/Fitbit MCP"
FITBIT_MCP_CLIENT_SECRETS=/path/to/client_secret.json uv run fitbit-mcp auth
```

A browser opens for Google consent. The token is saved to `~/.config/fitbit-mcp/token.json`.

In Testing mode Google expires refresh tokens after 7 days. When a tool replies "Sign-in expired", run the command above again. No restart is needed.

## 3. Register with Claude Code

```bash
claude mcp add fitbit -- uv --directory "/Users/whoishmk/Fitbit MCP" run fitbit-mcp
```

## Tools

Generic (any data type from `list_data_types`):

- `list_data_types`
- `list_data_points(data_type, start, end)`
- `reconcile_data_points(data_type, start, end, source)`
- `roll_up(data_type, start, end, window_seconds)`
- `daily_roll_up(data_type, start_date, end_date)`
- `list_paired_devices`

Metric tools, each taking `start_date` and `end_date` (inclusive, `YYYY-MM-DD`):

`get_steps`, `get_distance`, `get_calories`, `get_active_zone_minutes`, `get_heart_rate`, `get_resting_heart_rate`, `get_hrv`, `get_spo2`, `get_respiratory_rate`, `get_skin_temperature`, `get_vo2_max`, `get_sleep`, `get_workouts`.

Roll-ups of `heart-rate`, `total-calories`, `active-minutes` and `calories-in-heart-rate-zone` are limited by Google to 14 days per call; other roll-ups to 90 days.

## Tests

```bash
uv run pytest
```
