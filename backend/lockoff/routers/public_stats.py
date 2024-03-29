import logging
import itertools
import collections
import statistics
import random
from datetime import datetime, date
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Security

from .. import schemas
from ..config import settings
from ..db import AccessLog

router = APIRouter(tags=["public_stats"])
log = logging.getLogger(__name__)


def check_dow_and_time(d1: datetime, d2: datetime) -> bool:
    if d1.weekday() == d2.weekday():
        ld2 = d2.replace(year=d1.year, month=d1.month, day=d1.day)
        ld3 = ld2 + relativedelta(hours=2)
        if ld2 <= d1 <= ld3:
            return True
    return False


@router.get("/occupancy")
async def current_occupancy():
    hour_ago = datetime.now(tz=settings.tz) - relativedelta(hours=2)
    unique_checked_in_last_hour = await AccessLog.count(
        distinct=[AccessLog.obj_id]
    ).where(AccessLog.timestamp > hour_ago.isoformat(timespec="seconds"))

    quarter_ago = datetime.now(tz=settings.tz) - relativedelta(days=90)

    hist_data_raw = (
        await AccessLog.select(AccessLog.obj_id, AccessLog.timestamp)
        .where(AccessLog.timestamp > quarter_ago.isoformat(timespec="seconds"))
        .order_by(AccessLog.timestamp)
    )

    cunt = {}
    for d, g in itertools.groupby(
        [
            {
                "obj_id": d["obj_id"],
                "date": date.fromisoformat(d["timestamp"][:10]),
            }
            for d in hist_data_raw
            if check_dow_and_time(datetime.fromisoformat(d["timestamp"]), hour_ago)
        ],
        lambda x: x["date"],
    ):
        # get unique ids for this date by using a set
        unique_ids = {gg["obj_id"] for gg in g}
        # save the count for this date in cunt
        cunt[d] = len(unique_ids)

    historical_median = (
        round(statistics.median(cunt.values()), 2) if cunt.values() else 0
    )

    return {
        "currently": unique_checked_in_last_hour,
        "historical": historical_median,
        "hot_girls": random.randint(0, unique_checked_in_last_hour),
    }
