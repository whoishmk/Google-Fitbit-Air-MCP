LIST = "list"
RECONCILE = "reconcile"
ROLL_UP = "rollUp"
DAILY_ROLL_UP = "dailyRollUp"

ALL = [LIST, RECONCILE, ROLL_UP, DAILY_ROLL_UP]
READ = [LIST, RECONCILE]
ROLL_UPS = [ROLL_UP, DAILY_ROLL_UP]

CATALOG = {
    "active-energy-burned": {"kind": "interval", "operations": ALL},
    "active-minutes": {"kind": "interval", "operations": ALL},
    "active-zone-minutes": {"kind": "interval", "operations": ALL},
    "activity-level": {"kind": "interval", "operations": READ},
    "altitude": {"kind": "interval", "operations": ALL},
    "blood-glucose": {"kind": "sample", "operations": ALL},
    "body-fat": {"kind": "sample", "operations": ALL},
    "calories-in-heart-rate-zone": {"kind": "interval", "operations": ROLL_UPS},
    "core-body-temperature": {"kind": "sample", "operations": ALL},
    "daily-heart-rate-variability": {"kind": "daily", "operations": READ},
    "daily-heart-rate-zones": {"kind": "daily", "operations": READ},
    "daily-oxygen-saturation": {"kind": "daily", "operations": READ},
    "daily-respiratory-rate": {"kind": "daily", "operations": READ},
    "daily-resting-heart-rate": {"kind": "daily", "operations": READ},
    "daily-sleep-temperature-derivations": {"kind": "daily", "operations": READ},
    "daily-vo2-max": {"kind": "daily", "operations": READ},
    "distance": {"kind": "interval", "operations": ALL},
    "electrocardiogram": {"kind": "session", "operations": [LIST]},
    "exercise": {"kind": "session", "operations": READ},
    "floors": {"kind": "interval", "operations": [RECONCILE, *ROLL_UPS]},
    "food": {"kind": "food", "operations": [LIST]},
    "food-measurement-unit": {"kind": "food", "operations": [LIST]},
    "heart-rate": {"kind": "sample", "operations": ALL},
    "heart-rate-variability": {"kind": "sample", "operations": READ},
    "height": {"kind": "sample", "operations": READ},
    "hydration-log": {"kind": "session", "operations": ALL},
    "irregular-rhythm-notification": {"kind": "session", "operations": [LIST]},
    "nutrition-log": {"kind": "session", "operations": ALL},
    "oxygen-saturation": {"kind": "sample", "operations": READ},
    "respiratory-rate-sleep-summary": {"kind": "sample", "operations": READ},
    "run-vo2-max": {"kind": "sample", "operations": ALL},
    "sedentary-period": {"kind": "interval", "operations": ALL},
    "sleep": {"kind": "session", "operations": READ},
    "steps": {"kind": "interval", "operations": ALL},
    "swim-lengths-data": {"kind": "interval", "operations": ALL},
    "time-in-heart-rate-zone": {"kind": "interval", "operations": ALL},
    "total-calories": {"kind": "interval", "operations": ROLL_UPS},
    "vo2-max": {"kind": "sample", "operations": READ},
    "weight": {"kind": "sample", "operations": ALL},
}

SMALL_PAGE_TYPES = {"sleep", "exercise"}
