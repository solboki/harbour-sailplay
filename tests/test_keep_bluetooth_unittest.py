import os
import tempfile
import unittest

from unittest.mock import MagicMock, patch

from carplay_proto.videodemo import carplay_flag, drop_bluetooth_link, keep_bluetooth


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


    def test_flags_are_independent_and_off_by_default(self):
        path = self.setting('[CarPlay]\ndropBluetoothAtHandoff=true\n')
        self.assertTrue(carplay_flag('dropBluetoothAtHandoff', path))
        self.assertFalse(carplay_flag('keepBluetooth', path))
        self.assertFalse(keep_bluetooth({'model': 'Fiat CARLINE_13'}, path))
        self.assertFalse(carplay_flag('dropBluetoothAtHandoff', '/nonexistent/projection.ini'))

    def test_dropping_the_link_disconnects_only_that_device_and_never_raises(self):
        dbus = MagicMock()
        with patch.dict('sys.modules', {'dbus': dbus}), patch('builtins.print') as output:
            drop_bluetooth_link('/org/bluez/hci0/dev_fixture')
        dbus.SystemBus.return_value.get_object.assert_called_once_with(
            'org.bluez', '/org/bluez/hci0/dev_fixture', introspect=False)
        dbus.Interface.return_value.Disconnect.assert_called_once_with(timeout=3)
        dbus.SystemBus.return_value.close.assert_called_once_with()
        self.assertIn('dropped by the phone', output.call_args.args[0])
        dbus.Interface.return_value.Disconnect.side_effect = RuntimeError('fixture')
        with patch.dict('sys.modules', {'dbus': dbus}), patch('builtins.print') as output:
            drop_bluetooth_link('/org/bluez/hci0/dev_fixture')
        self.assertIn('drop at handoff failed', output.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
