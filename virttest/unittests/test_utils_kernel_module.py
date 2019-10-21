import unittest

try:
    from unittest import mock
except ImportError:
    import mock

from virttest import utils_kernel_module

# Test values
some_module_name = 'skvm'
some_module_param = 'force_emulation_prefix'
some_module_val = 'N'
some_module_config = {some_module_param: some_module_val,
                      'halt_poll_ns_shrink': '0'}
some_module_params = "%s=%s" % (some_module_param, some_module_val)

# Mocks
getstatusoutput_ok = mock.Mock(return_value=(0, ""))
system_ok = mock.Mock(return_value=0)

@mock.patch.object(utils_kernel_module.os, 'listdir', return_value=[some_module_param])
@mock.patch.object(utils_kernel_module, 'open', mock.mock_open(read_data=some_module_val + '\n'))
@mock.patch.object(utils_kernel_module.process, 'getstatusoutput', getstatusoutput_ok)
class TestLoadModule(unittest.TestCase):
    """
    Tests the load_module method

    precondition                    TC1     TC2     TC3     TC4     TC5     TC6
    -------------------------------
    module loaded                   N       N       Y       Y       Y       Y
    requested params already loaded *       *       Y       N       Y       N
    force load                      Y       N       Y       Y       N       N
    -------------------------------
    result
    -------------------------------
    load module w/ requested params Y       N       Y       Y       N       Y
    """

    def tearDown(self):
        getstatusoutput_ok.reset_mock()

    def assertLoadedWith(self, params):
        self.assertTrue(getstatusoutput_ok.called)
        cmd = getstatusoutput_ok.call_args[0][0]
        if params != "":
         self.assertTrue(params in cmd)
        else:
         self.assertTrue(cmd.endswith(some_module_name))

    def assertNotLoaded(self):
        getstatusoutput_ok.assert_not_called()

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=False)
    def test_tc1(self, *mocks):
        self.handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        self.handler.load_module(force=True, params=some_module_params)
        self.assertLoadedWith(some_module_params)

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=False)
    def test_tc2(self, *mocks):
        self.handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        self.handler.load_module(force=False, params=some_module_params)
        self.assertNotLoaded()

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=True)
    def test_tc3(self, *mocks):
        self.handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        self.handler.load_module(force=True, params=some_module_params)
        self.assertLoadedWith(some_module_params)

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=True)
    def test_tc3_empty(self, *mocks):
        self.handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        self.handler.load_module(force=True, params="")
        self.assertLoadedWith("")

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=True)
    def test_tc4(self, *mocks):
        self.handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        self.handler.load_module(force=True, params="key=value")
        self.assertLoadedWith("key=value")

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=True)
    def test_tc5(self, *mocks):
        self.handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        self.handler.load_module(force=False, params=some_module_params)
        self.assertNotLoaded()

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=True)
    def test_tc5_empty(self, *mocks):
        self.handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        self.handler.load_module(force=False, params="")
        self.assertNotLoaded()

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=True)
    def test_tc6(self, *mocks):
        self.handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        self.handler.load_module(force=False, params="key=value")
        self.assertLoadedWith("key=value")

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=True)
    def test_tc6_partial(self, *mocks):
        self.handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        self.assertEqual(some_module_params, self.handler.get_config_backup())
        self.handler.load_module(force=False, params=some_module_params + " key=value")
        self.assertLoadedWith("key=value")


@mock.patch.object(utils_kernel_module.process, 'getstatusoutput', getstatusoutput_ok)
@mock.patch.object(utils_kernel_module.os, 'listdir', return_value=[some_module_param])
@mock.patch.object(utils_kernel_module, 'open', mock.mock_open(read_data=some_module_val + '\n'))
class TestInit(unittest.TestCase):
    """
    Tests if module status is backed up correctly
    """

    def tearDown(self):
        getstatusoutput_ok.reset_mock()

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=True)
    def test_loaded(self, *mocks):
        handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        self.assertTrue(handler.get_was_loaded())
        self.assertEqual(some_module_params, handler.get_config_backup())

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=False)
    def test_not_loaded(self, *mocks):
        handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        self.assertFalse(handler.get_was_loaded())
        self.assertIsNone(handler.get_config_backup())


@mock.patch.object(utils_kernel_module.os, 'listdir', return_value=[some_module_param])
@mock.patch.object(utils_kernel_module, 'open', mock.mock_open(read_data=some_module_val + '\n'))
@mock.patch.object(utils_kernel_module.process, 'getstatusoutput', getstatusoutput_ok)
@mock.patch.object(utils_kernel_module.process, 'system', system_ok)
class TestRestore(unittest.TestCase):
    """
    Tests the restore method

    precondition                    TC1     TC2     TC3     TC4
    -------------------------------
    module loaded                   Y       Y       N       N
    loaded w/ requested params      Y       N       Y       N
    -------------------------------
    result
    -------------------------------
    restore                         Y       N       Y       N
    """

    def tearDown(self):
        system_ok.reset_mock()
        getstatusoutput_ok.reset_mock()

    def assertRestored(self, params):
        self.assertTrue(system_ok.called)
        cmd = system_ok.call_args[0][0]
        self.assertTrue(params in cmd)

    def assertNoRestore(self):
        self.assertFalse(system_ok.called)

    def assertUnloaded(self):
        self.assertTrue(system_ok.called)
        cmd = system_ok.call_args[0][0]
        self.assertFalse("modprobe" in cmd)

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=True)
    def test_tc1(self, *mocks):
        self.handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        orig_config = self.handler.get_config_backup()
        self.handler.load_module(True, "key=value")
        self.handler.restore()
        self.assertRestored(orig_config) 

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=True)
    def test_tc1_load_twice(self, *mocks):
        self.handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        orig_config = self.handler.get_config_backup()
        self.handler.load_module(True, "key=value")
        self.handler.load_module(True, "key1=value1")
        self.handler.restore()
        self.assertRestored(orig_config) 

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=True)
    def test_tc2(self, *mocks):
        self.handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        orig_config = self.handler.get_config_backup()
        self.handler.restore()
        self.assertNoRestore()

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=False)
    def test_tc3(self, *mocks):
        self.handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        self.assertFalse(self.handler._was_loaded)
        self.handler.load_module(True, "key=value")
        self.handler.restore()
        self.assertUnloaded()

    @mock.patch.object(utils_kernel_module.os.path, 'exists', return_value=False)
    def test_tc4(self, *mocks):
        self.handler = utils_kernel_module.KernelModuleHandler(some_module_name)
        self.handler.restore()
        self.assertNoRestore()


@mock.patch.object(utils_kernel_module.KernelModuleHandler, '__init__', return_value=None)
@mock.patch.object(utils_kernel_module.KernelModuleHandler, 'load_module', return_value=None)
class TestLoad(unittest.TestCase):
    """
    Tests the module global load method
    """

    def test_empty_params_1(self, *mocks):
        self.assertIsNone(utils_kernel_module.load(some_module_name, force=False, params=""))

    def test_empty_params_2(self, *mocks):
        self.assertIsNotNone(utils_kernel_module.load(some_module_name, force=True, params=""))

    def test_non_empty_params_1(self, *mocks):
        self.assertIsNotNone(utils_kernel_module.load(some_module_name, force=False, params=some_module_params))

    def test_non_empty_params_2(self, *mocks):
        self.assertIsNotNone(utils_kernel_module.load(some_module_name, force=True, params=some_module_params))


if __name__ == '__main__':
    unittest.main()
