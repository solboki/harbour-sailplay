"""Hold the first AirPlay control connection for head units that need it.

The Fiat/Marelli CARLINE_13 head unit accepts a full AirPlay session that
starts while it is still coming up, streams it and answers every feedback
request, yet never gives it the screen and does not recover. Sessions started
within about 16 s of its iAP2 link were never displayed. One started 30 s after
the link was not displayed either: the head unit's access point had only just
appeared, and the control connection followed the Wi-Fi association at once.
Every session that left 8 s or more after the association was displayed.
"""
import time


# By lower-case iAP2 manufacturer name: seconds to leave after the iAP2 link
# started, and seconds to leave after the Wi-Fi association.
SETTLE_BY_MANUFACTURER = {'marelli': (25, 10)}


SETTINGS = '/home/defaultuser/.config/sailplay/projection.ini'


def settle_disabled(path=None):
    """EXPERIMENT: `[CarPlay] skipReceiverSettle=true` connects without holding.

    Since it was paired again, the Scudo drops and reopens its Bluetooth iAP2
    link every 10 to 15 s until the phone reaches AirPlay, so the 25 s hold
    always outlasts it; a session that started during such a restart was reset.
    """
    import configparser
    settings = configparser.ConfigParser()
    try:
        settings.read(SETTINGS if path is None else path)
        return settings.getboolean('CarPlay', 'skipReceiverSettle', fallback=False)
    except (OSError, ValueError, configparser.Error):
        return False


def settle_seconds(session):
    if settle_disabled():
        return (0, 0)
    manufacturer = str(session.get('accessory_manufacturer') or '').strip().lower()
    return SETTLE_BY_MANUFACTURER.get(manufacturer, (0, 0))


def remaining(session, clock=time.monotonic, associated=None):
    """Seconds still to wait before connecting; 0 for unlisted head units.

    associated is the monotonic time of the Wi-Fi association, by default now.
    """
    after_link, after_association = settle_seconds(session)
    if not after_link and not after_association:
        return 0.0
    now = clock()
    wait = after_association - (now - (now if associated is None else associated))
    started = session.get('link_started')
    # A link time from another boot is not this monotonic clock: ignore it.
    if not isinstance(started, bool) and isinstance(started, (int, float)) and now >= started:
        wait = max(wait, after_link - (now - started))
    return min(max(0.0, wait), max(after_link, after_association))


def settle(session, log=print, sleep=time.sleep, clock=time.monotonic, associated=None):
    if settle_disabled() and SETTLE_BY_MANUFACTURER.get(str(session.get('accessory_manufacturer') or '').strip().lower()):
        log('AirPlay control connection not held: skipReceiverSettle is set')
    wait = remaining(session, clock, associated)
    if wait > 0:
        log('AirPlay control connection held for receiver start-up waitSeconds={:.1f} manufacturer={!r}'.format(
            wait, str(session.get('accessory_manufacturer'))))
        sleep(wait)
    return wait
