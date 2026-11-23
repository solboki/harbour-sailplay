import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from carplay_proto.receiversettle import remaining, settle, settle_seconds


class ReceiverSettleTests(unittest.TestCase):
    def setUp(self):
        # Never read the phone's own settings.
        settings = patch('carplay_proto.receiversettle.SETTINGS', '/nonexistent/projection.ini')
        settings.start()
        self.addCleanup(settings.stop)

    def test_experimental_setting_removes_the_hold(self):
        from carplay_proto import receiversettle
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'projection.ini')
            for text, expected in (('[CarPlay]\nskipReceiverSettle=true\n', True), ('[CarPlay]\niosVersion=27\n', False),
                                   ('[CarPlay]\nskipReceiverSettle=maybe\n', False), ('not an ini file', False)):
                with open(path, 'w') as output:
                    output.write(text)
                self.assertEqual(receiversettle.settle_disabled(path), expected)
            with open(path, 'w') as output:
                output.write('[CarPlay]\nskipReceiverSettle=true\n')
            with patch('carplay_proto.receiversettle.SETTINGS', path):
                log, sleep = Mock(), Mock()
                session = {'accessory_manufacturer': 'Marelli', 'link_started': 100.0}
                self.assertEqual(settle(session, log, sleep, clock=lambda: 101.0), 0.0)
                sleep.assert_not_called()
                log.assert_called_once_with('AirPlay control connection not held: skipReceiverSettle is set')
                self.assertEqual(settle({'accessory_manufacturer': 'Honda'}, log, sleep, clock=lambda: 101.0), 0.0)
                log.assert_called_once()

    def session(self, started=100.0, manufacturer='Marelli'):
        return {'link_started': started, 'accessory_manufacturer': manufacturer,
                'accessory_model': 'Fiat CARLINE_13'}

    def test_only_listed_manufacturers_are_held(self):
        self.assertEqual(settle_seconds(self.session()), (25, 10))
        self.assertEqual(settle_seconds(self.session(manufacturer=' MARELLI ')), (25, 10))
        for manufacturer in ('HSAE', 'Honda', '', None):
            with self.subTest(manufacturer=manufacturer):
                self.assertEqual(settle_seconds(self.session(manufacturer=manufacturer)), (0, 0))
                self.assertEqual(remaining(self.session(manufacturer=manufacturer), clock=lambda: 101), 0)
        self.assertEqual(remaining({}, clock=lambda: 101), 0)

    def test_fast_wifi_waits_for_the_link_to_be_old_enough(self):
        # Associated 3.5 s after the link started: the link rule dominates.
        self.assertAlmostEqual(remaining(self.session(), clock=lambda: 103.5), 21.5)
        self.assertAlmostEqual(remaining(self.session(), clock=lambda: 112, associated=103.5), 13)

    def test_slow_wifi_still_leaves_time_after_the_association(self):
        # 22 Nov 18:28: associated 28.8 s after the link, connected at once, never displayed.
        self.assertAlmostEqual(remaining(self.session(), clock=lambda: 128.8), 10)
        self.assertAlmostEqual(remaining(self.session(), clock=lambda: 133.8, associated=128.8), 5)
        self.assertEqual(remaining(self.session(), clock=lambda: 138.8, associated=128.8), 0)
        # Between the two rules the longer one applies.
        self.assertAlmostEqual(remaining(self.session(), clock=lambda: 118), 10)
        self.assertAlmostEqual(remaining(self.session(), clock=lambda: 110), 15)

    def test_stale_or_malformed_link_times_only_wait_for_the_association(self):
        for started in (500.0, None, 'soon', True):
            with self.subTest(started=started):
                self.assertAlmostEqual(remaining(self.session(started=started), clock=lambda: 110), 10)
                self.assertEqual(remaining(self.session(started=started), clock=lambda: 110, associated=95), 0)

    def test_wait_is_bounded(self):
        self.assertLessEqual(remaining(self.session(), clock=lambda: 100, associated=10 ** 9), 25)

    def test_settle_logs_and_sleeps_once_for_the_remaining_time(self):
        log, sleep = Mock(), Mock()
        self.assertAlmostEqual(settle(self.session(), log=log, sleep=sleep, clock=lambda: 110.9), 14.1)
        sleep.assert_called_once()
        self.assertAlmostEqual(sleep.call_args.args[0], 14.1)
        self.assertIn('held for receiver start-up waitSeconds=14.1', log.call_args.args[0])

    def test_nothing_is_logged_when_no_wait_is_left(self):
        log, sleep = Mock(), Mock()
        self.assertEqual(settle(self.session(), log=log, sleep=sleep, clock=lambda: 140, associated=120), 0)
        sleep.assert_not_called()
        log.assert_not_called()


if __name__ == '__main__':
    unittest.main()
