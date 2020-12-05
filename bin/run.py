#!/usr/bin/env python3

import argparse
import logging
import os
import sys

from apscheduler.schedulers.background import BackgroundScheduler

from piplant.app import create_app
import piplant.scheduler


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for running PiPlant server")
    parser.add_argument("--host", default="0.0.0.0", help="(default: %(default)s)")
    parser.add_argument("--port", default=5000, help="(default: %(default)s)")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--disable-scheduler", action="store_true", help="Disable the scheduler from running")
    args = parser.parse_args()

    if os.getenv('FLASK_ENV') is None:
        logging.error("Environment variable FLASK_ENV is not set. Please set it to either 'production' or 'development'.")
        sys.exit(-1)

    app = create_app()

    # Scheduler for running background tasks
    if not args.disable_scheduler:
        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(piplant.scheduler.Scheduler(app=app).update, "interval", seconds=10)
        scheduler.start()

    app.run(host=args.host, port=args.port, debug=args.debug, use_reloader=bool(args.disable_scheduler))
