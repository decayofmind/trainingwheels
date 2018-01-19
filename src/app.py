#!/usr/bin/env python

from flask import Flask, Response, send_from_directory, render_template
import os
import redis
import socket
import prometheus_client

from metrics import setup_metrics


CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')

app = Flask(__name__)
setup_metrics(app)

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


@app.route('/metrics')
def metrics():
    return Response(prometheus_client.generate_latest(),
                    mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run()

#  vim: set et fenc=utf-8 ft=python sts=4 sw=4 ts=4 tw=79 :
