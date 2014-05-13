from IPython.parallel import Client, RemoteError, interactive

from dalek.parallel.launcher import BaseLauncher
import pytest

try:
    remote_clients = Client()
except IOError:
    ipcluster_available = False
else:
    ipcluster_available = True

pytestmark = pytest.mark.skipif(not ipcluster_available,
                                reason='There is no ipython cluster running. '
                                       'Please start one with ipcluster start -n'
                                       ' <number of engines>')


default_config = {'a':{'b':{'param1':0, 'param2':1, 'param3':2}}}

@interactive
def simple_worker_test(config_dict, atom_data=None):
    import sys
    import logging
    import time

    logger = logging.getLogger(__name__)

    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    start_time = time.time()

    #testing if run_tardis is defined
    type(run_tardis)

    #testing if default_atom_data is defined
    type(default_atom_data)

    action = config_dict.get('action', 'run')
    if action == 'raise':
        raise ValueError('raising a test exception')
    elif action == 'run':
        pass


    sleep_time = config_dict.get('runtime', 20)
    logger.info('going to sleep')
    for i in xrange(sleep_time):
        time.sleep(1)
        logger.info("zzzz ({0} s)".format(i))
        sys.stdout.flush()
    logger.warning("waking up after a {0} second nap".format(sleep_time))

    return time.time() - start_time



class TestSimpleInstantiation():

    def setup(self):
        self.launcher = BaseLauncher(remote_clients, worker=simple_worker_test)

    def test_simple_add(self):
        result = self.launcher.queue_parameter_set({'action':'run'})
        result.get()

    def test_simple_error(self):
        result = self.launcher.queue_multiple_parameter_sets({'action':'raise'})
        with pytest.raises(RemoteError):
            result.get()

