#!/usr/bin/env python3
"""
Subscriber program that listens to the Zenoh key used by
`object_detector.py` and prints any JSON payload it receives.

Usage:
    python3 detector/subscribe_detections.py [--connect ENDPOINT] [--key KEY]

Defaults:
    key = tb/detections
    connect = multicast (i.e. empty string)
"""

import argparse
import json
import time

import zenoh


def main():
    parser = argparse.ArgumentParser(description="Print JSON detections from Zenoh")
    parser.add_argument(
        "--connect", "-e", type=str, default="",
        help="Zenoh endpoint to connect to (empty = multicast)"
    )
    parser.add_argument(
        "--key", "-k", type=str, default="tb/detections",
        help="Zenoh key to subscribe to"
    )
    args = parser.parse_args()

    conf = zenoh.Config()
    if args.connect:
        conf.insert_json5("connect/endpoints", json.dumps([args.connect]))

    session = zenoh.open(conf)

    def callback(sample):
        try:
            payload = bytes(sample.payload).decode("utf-8")
            try:
                obj = json.loads(payload)
                print(json.dumps(obj, indent=2))
            except Exception:
                print(payload)
        except Exception as e:
            print(f"Error decoding payload: {e}")

    sub = session.declare_subscriber(args.key, callback)
    print(f"Subscribed to: {args.key} (press Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        sub.undeclare()
        session.close()


if __name__ == "__main__":
    main()
