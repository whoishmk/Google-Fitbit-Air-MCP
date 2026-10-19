from datetime import date, timedelta

from google.auth.exceptions import RefreshError
from mcp.server.mcpserver.exceptions import ToolError

from fitbit_mcp.auth import SIGN_IN_HINT
from fitbit_mcp.catalog import CATALOG, SMALL_PAGE_TYPES

BASE_URL = "https://health.googleapis.com/v4/users/me"


def next_day(day):
    return (date.fromisoformat(day) + timedelta(days=1)).isoformat()


def utc(value):
    if len(value) == 10:
        value += "T00:00:00"
    return value if value.endswith("Z") else value + "Z"


def civil_date(day):
    parsed = date.fromisoformat(day)
    return {
        "date": {"year": parsed.year, "month": parsed.month, "day": parsed.day},
        "time": {"hours": 0, "minutes": 0, "seconds": 0, "nanos": 0},
    }


def time_filter(data_type, start, end):
    kind = CATALOG[data_type]["kind"]
    name = data_type.replace("-", "_")
    if kind == "food":
        return None
    if data_type == "electrocardiogram":
        return f'electrocardiogram.interval.start_time >= "{utc(start)}"'
    if kind == "daily":
        field, start, end = f"{name}.date", start[:10], end[:10]
    elif data_type == "sleep":
        field = "sleep.interval.civil_end_time"
    elif kind == "sample":
        field = f"{name}.sample_time.civil_time"
    else:
        field = f"{name}.interval.civil_start_time"
    return f'{field} >= "{start}" AND {field} < "{end}"'


class HealthClient:
    def __init__(self, session):
        self.session = session

    def _request(self, method, path, **kwargs):
        try:
            response = self.session.request(method, f"{BASE_URL}/{path}", **kwargs)
        except RefreshError as error:
            raise ToolError(f"Sign-in expired. {SIGN_IN_HINT}") from error
        if response.status_code >= 400:
            raise ToolError(
                f"Google Health API {response.status_code}: {response.text}"
            )
        return response.json()

    def _collect(self, key, fetch):
        items, token = [], ""
        while True:
            page = fetch(token)
            items += page.get(key, [])
            token = page.get("nextPageToken", "")
            if not token:
                return items

    def _get_pages(self, path, params):
        return self._collect(
            "dataPoints",
            lambda token: self._request(
                "GET", path, params=params | ({"pageToken": token} if token else {})
            ),
        )

    def _post_pages(self, path, body):
        return self._collect(
            "rollupDataPoints",
            lambda token: self._request(
                "POST", path, json=body | ({"pageToken": token} if token else {})
            ),
        )

    def _list_params(self, data_type, start, end):
        params = {"pageSize": 25 if data_type in SMALL_PAGE_TYPES else 10000}
        query = time_filter(data_type, start, end)
        if query:
            params["filter"] = query
        return params

    def paired_devices(self):
        return self._request("GET", "pairedDevices").get("pairedDevices", [])

    def list_data_points(self, data_type, start, end):
        return self._get_pages(
            f"dataTypes/{data_type}/dataPoints",
            self._list_params(data_type, start, end),
        )

    def reconcile_data_points(self, data_type, start, end, source):
        params = self._list_params(data_type, start, end)
        params["dataSourceFamily"] = f"users/me/dataSourceFamilies/{source}"
        return self._get_pages(f"dataTypes/{data_type}/dataPoints:reconcile", params)

    def roll_up(self, data_type, start, end, window_seconds):
        body = {
            "range": {"startTime": utc(start), "endTime": utc(end)},
            "windowSize": f"{window_seconds}s",
        }
        return self._post_pages(f"dataTypes/{data_type}/dataPoints:rollUp", body)

    def daily_roll_up(self, data_type, start_date, end_date):
        body = {
            "range": {
                "start": civil_date(start_date),
                "end": civil_date(next_day(end_date)),
            },
            "windowSizeDays": 1,
        }
        return self._post_pages(f"dataTypes/{data_type}/dataPoints:dailyRollUp", body)
