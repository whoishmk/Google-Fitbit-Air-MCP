import pytest
from google.auth.exceptions import RefreshError
from mcp.server.mcpserver.exceptions import ToolError

from fitbit_mcp import server
from fitbit_mcp.client import HealthClient, time_filter


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, *payloads):
        self.payloads = list(payloads)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        payload = self.payloads.pop(0)
        if isinstance(payload, Exception):
            raise payload
        return payload if isinstance(payload, FakeResponse) else FakeResponse(payload)


BASE = "https://health.googleapis.com/v4/users/me"


def test_list_follows_pages_with_interval_filter():
    session = FakeSession(
        {"dataPoints": [{"n": 1}], "nextPageToken": "abc"},
        {"dataPoints": [{"n": 2}], "nextPageToken": ""},
    )
    points = HealthClient(session).list_data_points("steps", "2026-10-01", "2026-10-02")

    assert points == [{"n": 1}, {"n": 2}]
    first, second = session.calls
    assert first[1] == f"{BASE}/dataTypes/steps/dataPoints"
    assert first[2]["params"] == {
        "pageSize": 10000,
        "filter": 'steps.interval.civil_start_time >= "2026-10-01" AND steps.interval.civil_start_time < "2026-10-02"',
    }
    assert second[2]["params"]["pageToken"] == "abc"


@pytest.mark.parametrize(
    "data_type, start, end, expected",
    [
        (
            "daily-resting-heart-rate",
            "2026-10-01T08:00:00",
            "2026-10-03",
            'daily_resting_heart_rate.date >= "2026-10-01" AND daily_resting_heart_rate.date < "2026-10-03"',
        ),
        (
            "heart-rate",
            "2026-10-01T08:00:00",
            "2026-10-01T09:00:00",
            'heart_rate.sample_time.civil_time >= "2026-10-01T08:00:00" AND heart_rate.sample_time.civil_time < "2026-10-01T09:00:00"',
        ),
        (
            "sleep",
            "2026-10-01",
            "2026-10-02",
            'sleep.interval.civil_end_time >= "2026-10-01" AND sleep.interval.civil_end_time < "2026-10-02"',
        ),
        (
            "exercise",
            "2026-10-01",
            "2026-10-02",
            'exercise.interval.civil_start_time >= "2026-10-01" AND exercise.interval.civil_start_time < "2026-10-02"',
        ),
        (
            "electrocardiogram",
            "2026-10-01",
            "2026-10-02",
            'electrocardiogram.interval.start_time >= "2026-10-01T00:00:00Z"',
        ),
        ("food", "2026-10-01", "2026-10-02", None),
    ],
)
def test_time_filter(data_type, start, end, expected):
    assert time_filter(data_type, start, end) == expected


def test_sleep_uses_small_pages_and_food_has_no_filter():
    session = FakeSession({"dataPoints": []}, {"dataPoints": []})
    client = HealthClient(session)
    client.list_data_points("sleep", "2026-10-01", "2026-10-02")
    client.list_data_points("food", "2026-10-01", "2026-10-02")

    assert session.calls[0][2]["params"]["pageSize"] == 25
    assert session.calls[1][2]["params"] == {"pageSize": 10000}


def test_reconcile_sends_source_family():
    session = FakeSession({"dataPoints": [{"n": 1}]})
    HealthClient(session).reconcile_data_points(
        "steps", "2026-10-01", "2026-10-02", "google-wearables"
    )

    method, url, kwargs = session.calls[0]
    assert url == f"{BASE}/dataTypes/steps/dataPoints:reconcile"
    assert (
        kwargs["params"]["dataSourceFamily"]
        == "users/me/dataSourceFamilies/google-wearables"
    )


def test_daily_roll_up_end_is_inclusive_and_pages_through_body():
    session = FakeSession(
        {"rollupDataPoints": [{"d": 1}], "nextPageToken": "next"},
        {"rollupDataPoints": [{"d": 2}]},
    )
    points = HealthClient(session).daily_roll_up("steps", "2026-10-01", "2026-10-31")

    assert points == [{"d": 1}, {"d": 2}]
    method, url, kwargs = session.calls[0]
    assert (method, url) == ("POST", f"{BASE}/dataTypes/steps/dataPoints:dailyRollUp")
    assert kwargs["json"]["range"]["start"]["date"] == {
        "year": 2026,
        "month": 10,
        "day": 1,
    }
    assert kwargs["json"]["range"]["end"]["date"] == {
        "year": 2026,
        "month": 11,
        "day": 1,
    }
    assert kwargs["json"]["windowSizeDays"] == 1
    assert session.calls[1][2]["json"]["pageToken"] == "next"


def test_roll_up_body():
    session = FakeSession({"rollupDataPoints": []})
    HealthClient(session).roll_up(
        "heart-rate", "2026-10-01", "2026-10-01T06:00:00", 3600
    )

    assert session.calls[0][2]["json"] == {
        "range": {
            "startTime": "2026-10-01T00:00:00Z",
            "endTime": "2026-10-01T06:00:00Z",
        },
        "windowSize": "3600s",
    }


def test_api_error_raises_with_status_and_body():
    session = FakeSession(FakeResponse({"error": "bad filter"}, status_code=400))

    with pytest.raises(ToolError, match="400"):
        HealthClient(session).list_data_points("steps", "2026-10-01", "2026-10-02")


def test_expired_refresh_token_tells_user_to_sign_in():
    session = FakeSession(RefreshError("invalid_grant"))

    with pytest.raises(ToolError, match="fitbit-mcp auth"):
        HealthClient(session).paired_devices()


def test_metric_tools_route_to_roll_up_or_inclusive_list(monkeypatch):
    session = FakeSession({"rollupDataPoints": []}, {"dataPoints": []})
    monkeypatch.setattr(server, "client", lambda: HealthClient(session))

    server.metric_tool("steps")("2026-10-01", "2026-10-07")
    server.metric_tool("daily-resting-heart-rate")("2026-10-01", "2026-10-07")

    assert session.calls[0][1].endswith("steps/dataPoints:dailyRollUp")
    assert session.calls[1][2]["params"]["filter"].endswith('date < "2026-10-08"')


def test_all_metric_tools_use_catalog_types():
    assert all(data_type in server.CATALOG for data_type, _ in server.METRICS.values())
