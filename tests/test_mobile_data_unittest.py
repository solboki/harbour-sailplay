import unittest
from unittest.mock import Mock, patch

from carplay_proto.mobiledata import MobileDataKeeper, RETRY_SECONDS


CELL = '/net/connman/service/cellular_1_context1'
WIFI = '/net/connman/service/wifi_hu_managed_psk'


class ConnmanError(Exception):
    def __init__(self, name):
        self.name = name

    def get_dbus_name(self):
        return self.name


class MobileDataTests(unittest.TestCase):
    def setUp(self):
        self.keeper = MobileDataKeeper(log=Mock())
        self.keeper.system, self.keeper.manager = Mock(), Mock()
        self.cell = {'Type': 'cellular', 'State': 'online', 'AutoConnect': True}
        self.wifi = {'Type': 'wifi', 'State': 'ready', 'AutoConnect': True}
        self.keeper.manager.GetServices.side_effect = lambda: [(WIFI, self.wifi), (CELL, self.cell)]
        self.service = Mock()
        self.now = 500
        patches = [patch('carplay_proto.mobiledata.network_object', return_value=self.service),
                   patch('carplay_proto.mobiledata.network_interface', side_effect=lambda obj, name: obj),
                   patch('carplay_proto.mobiledata.time.monotonic', side_effect=lambda: self.now)]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def logged(self):
        return [call.args[0] for call in self.keeper.log.call_args_list]

    def test_connected_mobile_data_and_wifi_are_left_alone(self):
        self.keeper.poll()
        self.wifi['State'] = 'idle'
        self.keeper.poll()
        self.service.Connect.assert_not_called()

    def test_mobile_data_dropped_during_the_projection_is_requested_again(self):
        self.keeper.poll()
        self.cell['State'] = 'idle'
        self.keeper.poll()
        self.service.Connect.assert_called_once_with(timeout=RETRY_SECONDS)
        self.keeper.poll()
        self.service.Connect.assert_called_once()
        self.now += RETRY_SECONDS
        self.keeper.poll()
        self.assertEqual(self.service.Connect.call_count, 2)
        self.cell['State'] = 'ready'
        self.keeper.poll()
        self.assertIn('Mobile data restored service={} state=ready'.format(CELL), self.logged())
        self.now += RETRY_SECONDS
        self.keeper.poll()
        self.assertEqual(self.service.Connect.call_count, 2)

    def test_mobile_data_already_down_when_the_projection_starts_is_connected(self):
        self.cell['State'] = 'idle'
        self.keeper.poll()
        self.service.Connect.assert_called_once_with(timeout=RETRY_SECONDS)
        self.cell['State'] = 'ready'
        self.keeper.poll()
        self.assertIn('Mobile data restored service={} state=ready'.format(CELL), self.logged())

    def test_mobile_data_switched_off_before_the_projection_is_never_connected(self):
        self.cell.update(State='idle', AutoConnect=False)
        for _ in range(3):
            self.keeper.poll()
            self.now += RETRY_SECONDS
        self.service.Connect.assert_not_called()

    def test_mobile_data_switched_off_by_the_user_stays_off(self):
        self.keeper.poll()
        self.cell.update(State='idle', AutoConnect=False)
        self.keeper.poll()
        self.now += RETRY_SECONDS
        self.keeper.poll()
        self.service.Connect.assert_not_called()

    def test_a_connection_in_progress_is_not_interrupted_and_errors_are_reported(self):
        self.keeper.poll()
        self.cell['State'] = 'association'
        self.keeper.poll()
        self.service.Connect.assert_not_called()
        self.cell['State'] = 'failure'
        self.service.Connect.side_effect = ConnmanError('net.connman.Error.PermissionDenied')
        self.keeper.poll()
        self.assertIn('Mobile data reconnection service={} error=net.connman.Error.PermissionDenied'.format(CELL),
                      self.logged())


if __name__ == '__main__':
    unittest.main()


class LeadWithMobileDataTests(unittest.TestCase):
    HOME = '/net/connman/service/wifi_home'
    CAR = '/net/connman/service/wifi_car'
    CELL = '/net/connman/service/cellular_1'

    def scene(self, cellular='ready', home='online', after='online', autoconnect=True, rejoin=False):
        from carplay_proto.mobiledata import lead_with_mobile_data
        test = self
        state = {'cellular': cellular, 'home': home, 'now': 0.0}
        calls = []

        class Manager:
            def GetServices(self):
                return [(test.HOME, {'Type': 'wifi', 'State': state['home']}),
                        (test.CELL, {'Type': 'cellular', 'State': state['cellular'], 'AutoConnect': autoconnect}),
                        (test.CAR, {'Type': 'wifi', 'State': 'idle'})]

        class Service:
            def __init__(self, path):
                self.path = path

            def Disconnect(self):
                calls.append(self.path)
                state['home'] = 'idle'
                state['after'] = state['now'] + 2

        def sleep(seconds):
            state['now'] += seconds
            if rejoin and state['now'] >= state.get('after', 1e9) - 1:
                state['home'] = 'ready'
            elif after and state['now'] >= state.get('after', 1e9):
                state['cellular'] = after

        log = []
        result = lead_with_mobile_data(Manager(), Service, self.HOME, self.CAR, log=log.append,
                                       clock=lambda: state['now'], sleep=sleep)
        return result, calls, log

    def test_other_wifi_is_left_until_mobile_data_is_online(self):
        result, calls, log = self.scene()
        self.assertTrue(result)
        self.assertEqual(calls, [self.HOME])
        self.assertIn('Mobile data leads', log[0])

    def test_wait_ends_when_the_other_wifi_reconnects_on_its_own(self):
        result, calls, log = self.scene(rejoin=True)
        self.assertFalse(result)
        self.assertEqual(calls, [self.HOME])
        self.assertIn('another Wi-Fi reconnected elapsedMs=1000', log[0])

    def test_idle_mobile_data_is_given_time_to_connect(self):
        result, calls, _ = self.scene(cellular='idle')
        self.assertTrue(result)
        self.assertEqual(calls, [self.HOME])

    def test_mobile_data_already_leading_keeps_the_wifi(self):
        result, calls, log = self.scene(cellular='online', home='ready')
        self.assertTrue(result)
        self.assertEqual((calls, log), ([], []))

    def test_mobile_data_switched_off_keeps_the_wifi(self):
        result, calls, _ = self.scene(autoconnect=False)
        self.assertFalse(result)
        self.assertEqual(calls, [])

    def test_no_connected_wifi_changes_nothing(self):
        result, calls, _ = self.scene(home='idle')
        self.assertFalse(result)
        self.assertEqual(calls, [])

    def test_handover_goes_on_when_mobile_data_stays_down(self):
        result, calls, log = self.scene(cellular='idle', after=None)
        self.assertFalse(result)
        self.assertEqual(calls, [self.HOME])
        self.assertIn('joining the head unit Wi-Fi anyway', log[0])
