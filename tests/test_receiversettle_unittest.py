import unittest
from unittest.mock import Mock

from carplay_proto.receiversettle import remaining, settle, settle_seconds


class ReceiverSettleTests(unittest.TestCase):
    def session(self, started=100.0, manufacturer='Marelli'):
        return {'link_started': started, 'accessory_manufacturer': manufacturer,
                'accessory_model': 'Fiat CARLINE_13'}

    def test_only_listed_manufacturers_are_held(self):
        self.assertEqual(settle_seconds(self.session()), 25)
        self.assertEqual(settle_seconds(self.session(manufacturer=' MARELLI ')), 25)
        for manufacturer in ('HSAE', 'Honda', '', None):
            with self.subTest(manufacturer=manufacturer):
                self.assertEqual(settle_seconds(self.session(manufacturer=manufacturer)), 0)
                self.assertEqual(remaining(self.session(manufacturer=manufacturer), clock=lambda: 101), 0)
        self.assertEqual(remaining({}, clock=lambda: 101), 0)

    def test_wait_counts_from_the_iap2_link_and_ends_at_the_threshold(self):
        self.assertAlmostEqual(remaining(self.session(), clock=lambda: 103.5), 21.5)
        self.assertEqual(remaining(self.session(), clock=lambda: 125), 0)
        self.assertEqual(remaining(self.session(), clock=lambda: 400), 0)

    def test_stale_or_malformed_link_times_never_wait(self):
        for started in (500.0, None, 'soon', True):
            with self.subTest(started=started):
                self.assertEqual(remaining(self.session(started=started), clock=lambda: 110), 0)

    def test_settle_logs_and_sleeps_once_for_the_remaining_time(self):
        log, sleep = Mock(), Mock()
        self.assertAlmostEqual(settle(self.session(), log=log, sleep=sleep, clock=lambda: 110.9), 14.1)
        sleep.assert_called_once()
        self.assertAlmostEqual(sleep.call_args.args[0], 14.1)
        self.assertIn('held for receiver start-up waitSeconds=14.1', log.call_args.args[0])

    def test_retry_handover_on_an_old_link_is_not_delayed(self):
        log, sleep = Mock(), Mock()
        self.assertEqual(settle(self.session(), log=log, sleep=sleep, clock=lambda: 140), 0)
        sleep.assert_not_called()
        log.assert_not_called()


if __name__ == '__main__':
    unittest.main()
