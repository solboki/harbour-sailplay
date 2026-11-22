"""Hold the first AirPlay control connection for head units that need it.

The Fiat/Marelli CARLINE_13 head unit accepts a full AirPlay session that
starts within about 16 s of its iAP2 link, streams it and answers every
feedback request, yet never gives it the screen and does not recover. Sessions
whose control connection came 25 s or more after the link were all displayed.
"""
import time


# Seconds after the iAP2 link started, by lower-case iAP2 manufacturer name.
SETTLE_BY_MANUFACTURER = {'marelli': 25}


def settle_seconds(session):
    manufacturer = str(session.get('accessory_manufacturer') or '').strip().lower()
    return SETTLE_BY_MANUFACTURER.get(manufacturer, 0)


def remaining(session, clock=time.monotonic):
    """Seconds still to wait before connecting; 0 for unlisted head units."""
    required = settle_seconds(session)
    started = session.get('link_started')
    if not required or isinstance(started, bool) or not isinstance(started, (int, float)):
        return 0.0
    age = clock() - started
    if age < 0:
        # Not this boot's monotonic clock; never wait on a stale session file.
        return 0.0
    return max(0.0, required - age)


def settle(session, log=print, sleep=time.sleep, clock=time.monotonic):
    wait = remaining(session, clock)
    if wait > 0:
        log('AirPlay control connection held for receiver start-up waitSeconds={:.1f} manufacturer={!r}'.format(
            wait, str(session.get('accessory_manufacturer'))))
        sleep(wait)
    return wait
