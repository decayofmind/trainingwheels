#!/usr/bin/env python

from flask import Flask, Response, send_from_directory, render_template
from healthcheck import HealthCheck
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import multiprocess
from prometheus_client.core import CollectorRegistry

import os
import redis
import socket


app = Flask(__name__)

registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry, path='/tmp')

metrics = PrometheusMetrics(app, registry=registry)
healthcheck = HealthCheck(app, "/health")

hostname = socket.gethostname()
redis = redis.Redis(os.getenv("REDIS_HOST", "redis"))


if "DEBUG" in os.environ:
    app.debug = True


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
    app.run(port=os.getenv("APP_PORT", 5000))

#  vim: set et fenc=utf-8 ft=python sts=4 sw=4 ts=4 tw=79 :
