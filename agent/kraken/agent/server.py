import os
import json
import time
import logging
import datetime
import urllib.request
from urllib.parse import urljoin, urlparse

from . import config
from . import sysutils

log = logging.getLogger(__name__)


def _send_http_request(url, data):
    url = urljoin(url, 'backend')
    data = json.dumps(data)
    data = data.encode('utf-8')
    req = urllib.request.Request(url=url, data=data, headers={'content-type': 'application/json'})
    resp = None

    # Codes description:
    #     -2 - 'Name or service not known'
    #     32 - 'Broken pipe'
    #     100 - 'Network is down'
    #     101 - 'Network is unreachable'
    #     110 - 'Connection timed out'
    #     111 - 'Connection refused'
    #     112 - 'Host is down'
    #     113 - 'No route to host'
    #     10053 - 'An established connection was aborted by the software in your host machine'
    #     10054 - An existing connection was forcibly closed by the remote host
    #     10060 - 'Connection timed out'
    #     10061 - 'No connection could be made because the target machine actively refused it'
    connection_errors = [-2, 32, 100, 101, 110, 111, 112, 113, 10053, 10054, 10060, 10061]

    while resp is None:
        try:
            with urllib.request.urlopen(req) as f:
                resp = f.read().decode('utf-8')
        except KeyboardInterrupt:
            raise
        # except socket.error as e:
        #     if e.errno in connection_errors:
        #         # TODO: just warn and sleep for a moment
        except urllib.error.URLError as e:
            if e.__context__ and e.__context__.errno in connection_errors:
                log.warning('connection problem to %s: %s, trying one more time in 5s', url, str(e))
                time.sleep(5)
            else:
                raise
        except ConnectionError as e:
            log.warning('connection problem to %s: %s, trying one more time in 5s', url, str(e))
            time.sleep(5)
        except:
            log.exception('some problem with connecting to server to %s', url)
            log.info('trying one more time in 5s')
            time.sleep(5)

    resp = json.loads(resp)
    return resp


class Server():
    def __init__(self):
        self.srv_addr = config.get('server')
        self.checks_num = 0
        self.last_check = datetime.datetime.now()
        slot = os.environ.get('KRAKEN_AGENT_SLOT', None)
        builtin = os.environ.get('KRAKEN_AGENT_BUILTIN', None)
        if slot is not None:
            self.my_addr = 'agent.%s' % slot
        elif builtin is not None:
            self.my_addr = 'server'
        else:
            srv_ip_addr = urlparse(self.srv_addr).hostname
            self.my_addr = sysutils.get_my_ip(srv_ip_addr)

    def check_server(self):
        current_addr = self.srv_addr
        self.checks_num += 1
        if self.checks_num > 15 or (datetime.datetime.now() - self.last_check > datetime.timedelta(seconds=60 * 5)):
            self.srv_addr = None
            self.checks_num = 0

        if self.srv_addr is None:
            # srv_addr = self._get_srv_addr()  # TODO
            pass
        else:
            srv_addr = None

        if srv_addr is not None and srv_addr != current_addr:
            self.srv_addr = srv_addr

        return self.srv_addr

    def _get_srv_addr(self):
        # TODO
        return None

    def _ensure_srv_address(self):
        if self.srv_addr is None:
            self._establish_connection()

    def _establish_connection(self):
        raise NotImplementedError

    def report_sys_info(self, sys_info):
        self._ensure_srv_address()

        request = {'address': self.my_addr,
                   'msg': 'sys-info',
                   'info': sys_info}

        response = _send_http_request(self.srv_addr, request)

        return response

    def get_job(self):
        self._ensure_srv_address()

        request = {'address': self.my_addr, 'msg': 'get-job'}

        response = _send_http_request(self.srv_addr, request)

        cfg_changes = {}
        if 'cfg' in response:
            cfg_changes = config.merge(response['cfg'])

        version = None
        if 'version' in response:
            version = response['version']

        if 'job' in response:
            return response['job'], cfg_changes, version

        return {}, cfg_changes, version

    def report_step_result(self, job_id, step_idx, result):
        request = {'address': self.my_addr,
                   'msg': 'step-result',
                   'job_id': job_id,
                   'step_idx': step_idx,
                   'result': result}

        response = _send_http_request(self.srv_addr, request)

        if 'cfg' in response:
            config.merge(response['cfg'])

        return {}

    def in_progres(self):
        pass

    def dispatch_tests(self, job_id, step_idx, tests):
        request = {'address': self.my_addr,
                   'msg': 'dispatch-tests',
                   'job_id': job_id,
                   'step_idx': step_idx,
                   'tests': tests}

        response = _send_http_request(self.srv_addr, request)

        if 'cfg' in response:
            config.merge(response['cfg'])

        return response
