import logging
import itertools
import collections
import statistics
from datetime import datetime, date
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Security

from .. import schemas
from ..db import AccessLog

router = APIRouter(tags=["public_stats"])
log = logging.getLogger(__name__)


def check_dow_and_time(d1: datetime, d2) -> bool:
    if (d1.hour == d2.hour) and (d1.weekday() == d2.weekday()):
        return True
    return False


@router.get("/current-occupancy")
async def current_occupancy():
    hour_ago = datetime.now(tz=settings.tz) - relativedelta(hours=1)
    unique_checked_in_last_hour = await AccessLog.count(
        distinct=[AccessLog.obj_id]
    ).where(AccessLog.timestamp > hour_ago.isoformat(timespec="seconds"))

    quarter_ago = datetime.now(tz=settings.tz) - relativedelta(days=180)

    hist_data_raw = (
        await AccessLog.select(AccessLog.obj_id, AccessLog.timestamp)
        .where(AccessLog.timestamp > quarter_ago.isoformat(timespec="seconds"))
        .order_by(AccessLog.timestamp)
    )

    cunt = collections.Counter()
    for d in [
        {
            "obj_id": d["obj_id"],
            "date": date.fromisoformat(d["timestamp"][:10]),
        }
        for d in hist_data_raw
        if check_dow_and_time(datetime.fromisoformat(d["timestamp"]), hour_ago)
    ]:
        cunt[d["date"]] += 1

    historical_median = round(statistics.median(cunt.values()), 2)

    return {
        "currently": unique_checked_in_last_hour,
        "historical": historical_median,
    }
