import asyncio
import logging
import time
from typing import Optional

from ..utils.rollups import run_hourly_rollups, run_daily_rollups
from ..utils.alerts import periodic_anomaly_check

logger = logging.getLogger("scheduler")


class Scheduler:
    """
    Simple background scheduler that triggers hourly and daily rollups and anomaly checks.
    """
    _loop_task: Optional[asyncio.Task] = None
    _running: bool = False

    @classmethod
    def start(cls):
        if cls._running:
            return
        cls._running = True
        cls._loop_task = asyncio.create_task(cls._loop())
        logger.info("Scheduler started.")

    @classmethod
    def stop(cls):
        if cls._loop_task:
            cls._loop_task.cancel()
            cls._loop_task = None
        cls._running = False
        logger.info("Scheduler stopped.")

    @classmethod
    async def _loop(cls):
        last_hour = None
        last_day = None
        while True:
            try:
                now = time.gmtime()
                # Hourly at minute 0
                hour_key = (now.tm_year, now.tm_yday, now.tm_hour)
                if hour_key != last_hour and now.tm_min == 0:
                    await run_hourly_rollups()
                    last_hour = hour_key

                # Daily at 00:05
                day_key = (now.tm_year, now.tm_yday)
                if day_key != last_day and now.tm_hour == 0 and now.tm_min == 5:
                    await run_daily_rollups()
                    last_day = day_key

                # Anomaly checks every 5 minutes
                if now.tm_min % 5 == 0 and now.tm_sec < 5:
                    await periodic_anomaly_check()

                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Scheduler loop error: %s", e)
                await asyncio.sleep(10)
