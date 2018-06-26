#!/usr/bin/env python3

import socket

from flask import Flask, render_template, send_from_directory

from flask_env import MetaFlaskEnv

from flask_redis_sentinel import SentinelExtension

from healthcheck import HealthCheck

from prometheus_client import multiprocess
from prometheus_client.core import CollectorRegistry

from prometheus_flask_exporter import PrometheusMetrics


class Configuration(metaclass=MetaFlaskEnv):
    DEBUG = False
    PORT = 5000


app = Flask(__name__)
app.config.from_object(Configuration)

registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry, path='/tmp')
metrics = PrometheusMetrics(app, registry=registry)
healthcheck = HealthCheck(app, "/health")

redis_sentinel = SentinelExtension()
redis = redis_sentinel.default_connection
redis_sentinel.init_app(app)

hostname = socket.gethostname()


def redis_available():
    redis.info()
    return True, "redis ok"


healthcheck.add_check(redis_available)


@app.errorhandler(500)
def error(e):
    return render_template('error.html',
                           hostname=hostname, error=e), 500


@app.route("/")
def index():
    redis.zincrby("counters", hostname)
    counters = redis.zrevrange("counters", 0, -1, withscores=True)
    counters = [(s.decode(), int(i)) for (s, i) in counters]
    thiscount = int(redis.zscore("counters", hostname))
    totalcount = sum(i for (s, i) in counters)
    return render_template("index.html",
                           hostname=hostname, counters=counters,
                           thiscount=thiscount, totalcount=totalcount)


@app.route("/assets/<path:path>")
def assets(path):
    return send_from_directory("assets", path)


if __name__ == "__main__":
    app.run()

#  vim: set et fenc=utf-8 ft=python sts=4 sw=4 ts=4 tw=79 :
