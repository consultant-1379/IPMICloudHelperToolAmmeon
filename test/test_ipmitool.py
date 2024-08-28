from unittest import TestCase
from ipmitool import IPMICloudAdapter
import ipmitool
from mock import Mock, patch, NonCallableMock

class TestIPMICloudAdapter(TestCase):
    def setUp(self):
        pass


    @patch('ipmitool.urllib2.Request')
    @patch('ipmitool.urllib2.urlopen')
    def test_set_poweroff(self, mock_urlopen, mock_request):
        self.adapter = IPMICloudAdapter('1.1.1.42')

        return_code = self.adapter.set_poweroff()
        mock_request.assert_called_once_with('https://10.42.34.79/Vms/poweroff_api/vm_name:ms-1.xml')
        self.assertEquals(0, return_code)

    @patch('ipmitool.urllib2.Request')
    @patch('ipmitool.urllib2.urlopen')
    def test_set_poweron(self, mock_urlopen, mock_request):
        self.adapter = IPMICloudAdapter('1.1.1.42')
        mocked_sleep = patch('ipmitool.time.sleep')
        mocked_sleep.return_value = 0
        mocked_sleep.start()

        return_code = self.adapter.set_poweron()
        mock_request.has_calls(['https://10.42.34.79/Vms/poweron_api/vm_name:ms-1.xml','https://10.42.34.79/Vms/boot_devices:hd/vm_name:ms-1.xml'])
        mocked_sleep.stop()
        self.assertEquals(0, return_code)

    @patch('ipmitool.urllib2.Request')
    @patch('ipmitool.urllib2.urlopen')
    def test_set_bootdev_pxe(self, mock_urlopen, mock_request):
        self.adapter = IPMICloudAdapter('1.1.1.42')

        return_code = self.adapter.set_bootdev_pxe()
        mock_request.assert_called_once_with('https://10.42.34.79/Vms/set_boot_device_api/boot_devices:net/vm_name:ms-1.xml')
        self.assertEquals(0, return_code)

    @patch('ipmitool.urllib2.Request')
    @patch('ipmitool.urllib2.urlopen')
    def test_set_bootdev_hd(self, mock_urlopen, mock_request):
        self.adapter = IPMICloudAdapter('1.1.1.42')

        return_code = self.adapter.set_bootdev_hd()
        mock_request.assert_called_once_with('https://10.42.34.79/Vms/set_boot_device_api/boot_devices:hd/vm_name:ms-1.xml')
        self.assertEquals(0, return_code)

    @patch('ipmitool.urllib2.Request')
    @patch('ipmitool.urllib2.urlopen')
    def test_http_error(self, mock_urlopen, mock_request):
        class mock_httperror(Exception):
            def __init__(self):
                self.code = 404
                self.read = lambda: 'foo'

        mock_exception = mock_httperror
        mock_urlopen.side_effect = mock_exception
        try:
            actual_httperror = ipmitool.urllib2.HTTPError
            ipmitool.urllib2.HTTPError = mock_exception

            self.adapter = IPMICloudAdapter('1.1.1.42')
            return_code = self.adapter.set_bootdev_hd()
            self.assertEquals(1, return_code)
        finally:
            ipmitool.urllib2.HTTPError = actual_httperror
            pass

    @patch('ipmitool.urllib2.Request')
    @patch('ipmitool.urllib2.urlopen')
    def test_url_error(self, mock_urlopen, mock_request):
        class mock_urlerror(Exception):
            def __init__(self):
                # Yes, in URLError args == reason
                self.reason = self.args = '[Errno 110] Connection timed out'

        mock_exception = mock_urlerror
        mock_urlopen.side_effect = mock_exception
        try:
            actual_urlerror = ipmitool.urllib2.URLError
            ipmitool.urllib2.URLError = mock_exception

            self.adapter = IPMICloudAdapter('1.1.1.42')
            return_code = self.adapter.set_bootdev_hd()
            self.assertEquals(1, return_code)
        finally:
            ipmitool.urllib2.URLError = actual_urlerror
            pass

    def test_bad_vapp_node_address(self):
        bad_addresses = ['foo', 'sada:sad', '0.0.0.0', '1.2.f.3']
        for bad_address in bad_addresses:
            self.assertRaises(ValueError, IPMICloudAdapter, bad_address)

    def test_invalid_vapp_node_address(self):
        self.assertRaises(ValueError, IPMICloudAdapter, '15.16.17.18')

    @patch('ipmitool.IPMICloudAdapter.set_bootdev_pxe')
    def test_run_cmd_bootdev_pxe(self, mock_method):
        mock_args = Mock(command='chassis', subcmd='bootdev', arg='pxe')
        mock_method.return_value = 0
        self.adapter = IPMICloudAdapter('15.16.17.43')
        self.assertEquals(0, self.adapter.run_cmd(mock_args))
        self.assertTrue(mock_method.called_once_with())

    @patch('ipmitool.IPMICloudAdapter.set_bootdev_hd')
    def test_run_cmd_bootdev_disk(self, mock_method):
        mock_args = Mock(command='chassis', subcmd='bootdev', arg='disk')
        mock_method.return_value = 0
        self.adapter = IPMICloudAdapter('15.16.17.43')
        self.assertEquals(0, self.adapter.run_cmd(mock_args))
        self.assertTrue(mock_method.called_once_with())

    @patch('__builtin__.print')
    @patch('ipmitool.IPMICloudAdapter.set_poweroff')
    def test_run_cmd_poweroff(self, mock_method, mock_print):
        mock_args = Mock(command='chassis', subcmd='power', arg='off')
        mock_method.return_value = 0
        self.adapter = IPMICloudAdapter('15.16.17.43')
        self.assertEquals(0, self.adapter.run_cmd(mock_args))
        self.assertTrue(mock_method.called_once_with())
        mock_print.has_calls("Chassis Power Control: Down/Off")

    @patch('__builtin__.print')
    @patch('ipmitool.IPMICloudAdapter.set_poweron')
    def test_run_cmd_poweron(self, mock_method, mock_print):
        mock_args = Mock(command='chassis', subcmd='power', arg='on')
        mock_method.return_value = 0
        self.adapter = IPMICloudAdapter('15.16.17.43')
        self.assertEquals(0, self.adapter.run_cmd(mock_args))
        self.assertTrue(mock_method.called_once_with())
        mock_print.has_calls("Chassis Power Control: Up/On")

    def test_run_cmd_power_bad_arg(self):
        mock_args = Mock(command='chassis', subcmd='power', arg='foo')
        self.adapter = IPMICloudAdapter('15.16.17.43')
        self.assertEquals(1, self.adapter.run_cmd(mock_args))

    def test_run_cmd_bootdev_bad_dev(self):
        mock_args = Mock(command='chassis', subcmd='bootdev', arg='foo')
        self.adapter = IPMICloudAdapter('15.16.17.43')
        self.assertEquals(1, self.adapter.run_cmd(mock_args))

    def test_run_cmd_bad_subcmd(self):
        mock_args = Mock(command='chassis', subcmd='foo', arg='bar')
        self.adapter = IPMICloudAdapter('15.16.17.43')
        self.assertEquals(1, self.adapter.run_cmd(mock_args))

    @patch('ipmitool.IPMICloudAdapter')
    @patch('ipmitool.sys.exit')
    def test_main_function(self, mock_exit, mock_adapter):
        try:
            actual_argv = ipmitool.sys.argv
            ipmitool.sys.argv = ('ipmitool', '-H', '192.168.42.42', '-I', 'lanplus', '-U', 'root', 'chassis', 'power', 'on')

            ipmitool.run_ipmitool()
            mock_adapter.assert_called_once_with('192.168.42.42')
        finally:
            ipmitool.sys.argv = actual_argv
