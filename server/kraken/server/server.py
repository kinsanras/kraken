#!/usr/bin/env python3

# Copyright 2020-2021 The Kraken Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import logging

import connexion
from connexion.resolver import Resolver
from flask import request

from . import logs
from . import models
from . import backend
from . import consts
from . import srvcheck
from . import webhooks
from . import agentblob
from . import storage
from . import job_log
from . import badge
from .. import version

log = logging.getLogger('server')


class MyResolver(Resolver):
    def resolve_operation_id(self, operation):
        operation_id = operation.operation_id
        tags = operation._operation['tags']  # pylint: disable=protected-access
        name = 'kraken.server.{}.{}'.format(tags[0].lower(), operation_id)
        return name


def _set_log_ctx():
    if request.path.startswith('/api'):
        name = 'api'
    elif request.path.startswith('/backend'):
        name = 'backend'
    elif request.path.startswith('/install'):
        name = 'install'
    elif request.path.startswith('/artifacts'):
        name = 'artifacts'
    elif request.path.startswith('/job_log'):
        name = 'job-log'
    elif request.path.startswith('/branch-badge'):
        name = 'badge'
    elif request.path.startswith('/webhooks'):
        name = 'webhooks'
    else:
        name = 'other'

    try:
        log.set_ctx(tool=name)
    except Exception:
        pass


def _clear_log_ctx(a):  # pylint: disable=unused-argument
    try:
        log.set_ctx(tool=None)
    except Exception:
        pass


def create_app():
    # addresses
    db_url = os.environ.get('KRAKEN_DB_URL', consts.DEFAULT_DB_URL)
    redis_addr = os.environ.get('KRAKEN_REDIS_ADDR', consts.DEFAULT_REDIS_ADDR)
    clickhouse_url = os.environ.get('KRAKEN_CLICKHOUSE_URL', consts.DEFAULT_CLICKHOUSE_URL)
    planner_url = os.environ.get('KRAKEN_PLANNER_URL', consts.DEFAULT_PLANNER_URL)
    server_addr = os.environ.get('KRAKEN_SERVER_ADDR', consts.DEFAULT_SERVER_ADDR)

    srvcheck.check_postgresql(db_url)
    srvcheck.check_tcp_service('redis', redis_addr, 6379)
    srvcheck.check_url('clickhouse', clickhouse_url, 8123)
    srvcheck.check_url('planner', planner_url, 7997)

    logs.setup_logging('server')
    log.info('Kraken Server started, version %s', version.version)

    # Create the connexion application instance
    basedir = os.path.abspath(os.path.dirname(__file__))
    _, server_port = server_addr.split(':')
    connex_app = connexion.App('Kraken Server', port=int(server_port), specification_dir=basedir)

    # Get the underlying Flask app instance
    app = connex_app.app

    # Configure the SqlAlchemy part of the app instance
    app.config["SQLALCHEMY_ECHO"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url + '?application_name=server'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # initialize SqlAlchemy
    models.db.init_app(app)

    # setup sentry
    with app.app_context():
        sentry_url = models.get_setting('monitoring', 'sentry_dsn')
        logs.setup_sentry(sentry_url)

    # Read the swagger.yml file to configure the endpoints
    connex_app.add_api("swagger.yml", resolver=MyResolver())

    # backend for serving agents
    connex_app.add_url_rule("/backend", view_func=backend.serve_agent_request, methods=['POST'])

    # serve agent files for agent update
    connex_app.add_url_rule("/install/<blob>", view_func=agentblob.serve_agent_blob, methods=['GET'])

    # serve build artifacts
    connex_app.add_url_rule("/artifacts/<store_type>/f/<flow_id>/<path:path>", view_func=storage.serve_flow_artifact, methods=['GET'])
    connex_app.add_url_rule("/artifacts/<store_type>/r/<run_id>/<path:path>", view_func=storage.serve_run_artifact, methods=['GET'])

    # serve job log
    connex_app.add_url_rule("/job_log/<job_id>", view_func=job_log.serve_job_log, methods=['GET'])

    # install webhooks
    webhooks_bp = webhooks.create_blueprint()
    app.register_blueprint(webhooks_bp, url_prefix='/webhooks')

    # branch status badge
    app.add_url_rule("/branch-badge/<branch_id>", view_func=badge.get_branch_badge, methods=['GET'], defaults={'what': None})
    app.add_url_rule("/branch-badge/<branch_id>/<what>", view_func=badge.get_branch_badge, methods=['GET'])

    app.before_request(_set_log_ctx)
    app.teardown_request(_clear_log_ctx)

    return connex_app


def main():
    app = create_app()
    app.run(debug=True)


if __name__ == "__main__":
    main()
