import os
import tempfile
import unittest

from carplay_proto.videodemo import keep_bluetooth


class KeepBluetoothTests(unittest.TestCase):
    def setting(self, text):
        handle, path = tempfile.mkstemp(suffix='.ini')
        self.addCleanup(os.unlink, path)
        with os.fdopen(handle, 'w') as output:
            output.write(text)
        return path

    def test_handoff_is_requested_by_default(self):
        for text in ('', '[CarPlay]\niosVersion=17\n', '[CarPlay]\nkeepBluetooth=false\n',
                     '[CarPlay]\nkeepBluetooth=perhaps\n', 'not an ini file'):
            with self.subTest(text=text):
                self.assertFalse(keep_bluetooth({'model': 'Fiat CARLINE_13'}, self.setting(text)))
        self.assertFalse(keep_bluetooth({'model': 'Fiat CARLINE_13'}, '/nonexistent/projection.ini'))

    def test_setting_keeps_bluetooth_for_any_head_unit(self):
        path = self.setting('[CarPlay]\niosVersion=17\nkeepBluetooth=true\n\n[Projection]\nprotocol=carplay\n')
        self.assertTrue(keep_bluetooth({'model': 'Fiat CARLINE_13'}, path))
        self.assertTrue(keep_bluetooth({}, path))

    def test_honda_keeps_bluetooth_without_the_setting(self):
        self.assertTrue(keep_bluetooth({'model': 'Honda Display Audio'}, '/nonexistent/projection.ini'))


if __name__ == '__main__':
    unittest.main()
