import logging
import os
import unittest

import pytest
from redis import Redis

from rq.utils import get_version


def find_empty_redis_database(ssl=False):
    """Tries to connect to a random Redis database (starting from 4), and
    will use/connect it when no keys are in there.
    """
    for dbnum in range(4, 17):
        connection_kwargs = {'db': dbnum}
        if ssl:
            connection_kwargs['port'] = 9736
            connection_kwargs['ssl'] = True
            # disable certificate validation
            connection_kwargs['ssl_cert_reqs'] = None  # type: ignore
        testconn = Redis(**connection_kwargs)  # type: ignore
        empty = testconn.dbsize() == 0
        if empty:
            return testconn
        testconn.close()
    assert False, 'No empty Redis database found to run tests in.'


def min_redis_version(ver: tuple[int, ...]):
    ver_str = '.'.join(map(str, ver))
    with Redis() as conn:
        redis_version = get_version(conn)

    return unittest.skipIf(redis_version < ver, f'Skip if Redis server < {ver_str}')


def slow(f):
    f = pytest.mark.slow(f)
    return unittest.skipUnless(os.environ.get('RUN_SLOW_TESTS_TOO'), 'Slow tests disabled')(f)


def ssl_test(f):
    f = pytest.mark.ssl_test(f)
    return unittest.skipUnless(os.environ.get('RUN_SSL_TESTS'), 'SSL tests disabled')(f)


class RQTestCase(unittest.TestCase):
    """Base class to inherit test cases from for RQ.

    It sets up the Redis connection (available via self.connection), turns off
    logging to the terminal and flushes the Redis database before and after
    running each test.
    """

    @classmethod
    def setUpClass(cls):
        # Set up connection to Redis
        cls.connection = find_empty_redis_database()

        # Shut up logging
        logging.disable(logging.ERROR)

    def setUp(self):
        # Flush beforewards (we like our hygiene)
        self.connection.flushdb()

    def tearDown(self):
        # Flush afterwards
        self.connection.flushdb()

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)
        cls.connection.close()
