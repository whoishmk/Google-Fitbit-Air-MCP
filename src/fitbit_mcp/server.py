import sys
from typing import Literal

from mcp.server.mcpserver import MCPServer

from fitbit_mcp.auth import authorized_session, sign_in
from fitbit_mcp.catalog import CATALOG
from fitbit_mcp.client import HealthClient, next_day

server = MCPServer("fitbit")


def client():
    return HealthClient(authorized_session())


@server.tool()
def list_data_types() -> dict:
    """Readable Google Health data types with their record kind and supported operations (list, reconcile, rollUp, dailyRollUp)."""
    return CATALOG


@server.tool()
def list_data_points(data_type: str, start: str, end: str) -> list[dict]:
    """Raw data points of one data type. start and end are local civil time, YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS; end is exclusive. Use for intraday detail, e.g. heart-rate samples."""
    return client().list_data_points(data_type, start, end)


@server.tool()
def reconcile_data_points(
    data_type: str,
    start: str,
    end: str,
    source: Literal[
        "all-sources", "google-wearables", "google-sources"
    ] = "all-sources",
) -> list[dict]:
    """Data points with overlapping sources deduplicated, matching what the Google Health app shows. start and end as in list_data_points."""
    return client().reconcile_data_points(data_type, start, end, source)


@server.tool()
def roll_up(data_type: str, start: str, end: str, window_seconds: int) -> list[dict]:
    """Aggregates over fixed windows of window_seconds. start and end are UTC, YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS; end is exclusive."""
    return client().roll_up(data_type, start, end, window_seconds)


@server.tool()
def daily_roll_up(data_type: str, start_date: str, end_date: str) -> list[dict]:
    """Per-day aggregates by local calendar day. start_date and end_date are YYYY-MM-DD, both inclusive."""
    return client().daily_roll_up(data_type, start_date, end_date)


@server.tool()
def list_paired_devices() -> list[dict]:
    """Paired Fitbit and Pixel devices with battery level and last sync time."""
    return client().paired_devices()


METRICS = {
    "get_steps": ("steps", "Daily step totals."),
    "get_distance": ("distance", "Daily distance totals."),
    "get_calories": ("total-calories", "Daily total calories burned."),
    "get_active_zone_minutes": ("active-zone-minutes", "Daily Active Zone Minutes."),
    "get_heart_rate": (
        "heart-rate",
        "Daily heart rate aggregates. Max 14 days per call.",
    ),
    "get_resting_heart_rate": ("daily-resting-heart-rate", "Daily resting heart rate."),
    "get_hrv": ("daily-heart-rate-variability", "Daily heart rate variability."),
    "get_spo2": ("daily-oxygen-saturation", "Daily blood oxygen saturation (SpO2)."),
    "get_respiratory_rate": ("daily-respiratory-rate", "Daily respiratory rate."),
    "get_skin_temperature": (
        "daily-sleep-temperature-derivations",
        "Nightly skin temperature variation.",
    ),
    "get_vo2_max": ("daily-vo2-max", "Daily VO2 max (cardio fitness)."),
    "get_sleep": (
        "sleep",
        "Sleep sessions with stages, for nights ending on the given dates.",
    ),
    "get_workouts": ("exercise", "Exercise sessions."),
}


def metric_tool(data_type):
    if "rollUp" in CATALOG[data_type]["operations"]:

        def tool(start_date: str, end_date: str) -> list[dict]:
            return client().daily_roll_up(data_type, start_date, end_date)

    else:

        def tool(start_date: str, end_date: str) -> list[dict]:
            return client().list_data_points(data_type, start_date, next_day(end_date))

    return tool


for name, (data_type, summary) in METRICS.items():
    server.add_tool(
        metric_tool(data_type),
        name=name,
        description=f"{summary} start_date and end_date are YYYY-MM-DD, both inclusive.",
    )


def main():
    if sys.argv[1:] == ["auth"]:
        sign_in()
    else:
        server.run()
