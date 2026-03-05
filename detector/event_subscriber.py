#!/usr/bin/env python3

import argparse
import hashlib
import json
import sys
import time
import uuid

import rclpy
from rclpy.serialization import deserialize_message
from rclpy.node import Node
from sensor_msgs.msg import Image
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from database.postgresql import insert_detection_event
import json

import zenoh


def parse_args():
    p = argparse.ArgumentParser(description="Zenoh+ROS2 event composer (maze.detection.v1)")
    p.add_argument("--run-id", type=str, default=str(uuid.uuid4()),
                   help="Identifier for this run/session")
    p.add_argument("--robot-id", type=str, default="tb3_sim",
                   help="Logical robot identifier")
    p.add_argument("--sequence-start", type=int, default=0,
                   help="Initial sequence number")
    p.add_argument("--image-topic", type=str, default="/camera/image_raw",
                   help="ROS 2 topic for camera images")
    p.add_argument("--odom-topic", type=str, default="/odom",
                   help="ROS 2 topic for odometry")
    p.add_argument("--tf-topic", type=str, default="/tf",
                   help="ROS 2 topic for TF data")
    p.add_argument("--detect-key", type=str, default="tb/detections",
                   help="Zenoh key carrying detection lists")
    p.add_argument("-e", "--zenoh-endpoint", type=str, default="",
                   help="Zenoh endpoint for detection subscription")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="Print debug info when data arrives")
    return p.parse_args()


class EventComposer(Node):
    """ROS 2 node that listens to image/odom/tf and emits events on detection."""

    def __init__(self, args):
        super().__init__("event_subscriber")
        self.args = args
        self.state = {
            "image": None,
            "odometry": None,
            "tf": None,
        }
        self.sequence = args.sequence_start
        self.verbose = args.verbose

        # ROS 2 subscriptions
        self.image_sub = self.create_subscription(
            Image, args.image_topic, self.image_callback, 10
        )
        self.odom_sub = self.create_subscription(
            Odometry, args.odom_topic, self.odom_callback, 10
        )
        self.tf_sub = self.create_subscription(
            TransformStamped, args.tf_topic, self.tf_callback, 10
        )

        # Zenoh session for detections (separate from ROS 2 DDS)
        self.zenoh_session = None
        self.zenoh_sub = None

    def image_callback(self, msg: Image):
        """Store latest image metadata."""
        self.state["image"] = {
            "topic": self.args.image_topic,
            "stamp": {"sec": msg.header.stamp.sec, "nanosec": msg.header.stamp.nanosec},
            "frame_id": msg.header.frame_id,
            "width": msg.width,
            "height": msg.height,
            "encoding": msg.encoding,
        }
        # if self.verbose:
            # print(f"[DEBUG] {self.args.image_topic}: updated", file=sys.stderr)

    def tf_callback(self, msg: TransformStamped):
        # print(msg)
        """Store latest TF data."""
        # raw_data = msg.payload.to_bytes()
        # # Deserialize the message
        # data = deserialize_message(raw_data, TransformStamped)

        # # Print
        # print("after parse", data)
        self.state["tf"] = {
            "base_frame": "base_footprint",
            "camera_frame": "camera_link",
            "t_base_camera": [40],
            "tf_ok": True
        }
        if self.verbose:
            print(f"[DEBUG] {self.args.tf_topic}: updated", file=sys.stderr)


    def odom_callback(self, msg: Odometry):
        """Store latest odometry data."""
        pose = msg.pose.pose
        twist = msg.twist.twist
        self.state["odometry"] = {
            "topic": self.args.odom_topic,
            "frame_id": msg.header.frame_id,
            "x": float(pose.position.x),
            "y": float(pose.position.y),
            "z": float(pose.position.z),
            # orientation in quaternion
            "qx": float(pose.orientation.x),
            "qy": float(pose.orientation.y),
            "qz": float(pose.orientation.z),
            "qw": float(pose.orientation.w),
            "vx": float(twist.linear.x),
            "vy": float(twist.linear.y),
            "vz": float(twist.linear.z),
            "wx": float(twist.angular.x),
            "wy": float(twist.angular.y),
            "wz": float(twist.angular.z),
        }
        # if self.verbose:
            # print(f"[DEBUG] {self.args.odom_topic}: updated", file=sys.stderr)

    def make_event(self, detections: list) -> dict:
        """Build a maze.detection.v1 event."""
        self.sequence += 1
        event = {
            "schema": "maze.detection.v1",
            "event_id": str(uuid.uuid4()),
            "run_id": self.args.run_id,
            "robot_id": self.args.robot_id,
            "sequence": self.sequence,
            "image": self.state["image"],
            "odometry": self.state["odometry"],
            "tf": self.state["tf"],
            "detections": [],
        }

        for det in detections:
            event_det = {
                "det_id": str(uuid.uuid4()),
                "class_id": det.get("class_id", 0),
                "class_name": det.get("class") or det.get("class_name", ""),
                "confidence": det.get("confidence"),
                "bbox_xyxy": det.get("bbox") or det.get("bbox_xyxy", []),
            }
            event["detections"].append(event_det)

        return event

    def setup_zenoh(self):
        """Initialize Zenoh subscription for detections."""
        conf = zenoh.Config()
        if self.args.zenoh_endpoint:
            conf.insert_json5("connect/endpoints", json.dumps([self.args.zenoh_endpoint]))
        self.zenoh_session = zenoh.open(conf)

        detect_key = self.args.detect_key.strip("/")
        self.zenoh_sub = self.zenoh_session.declare_subscriber(
            detect_key, self.detection_callback
        )

        if self.verbose:
            print(f"[DEBUG] Zenoh session opened, subscribed to {detect_key}", file=sys.stderr)

    def detection_callback(self, sample):
        """Handle incoming detection list; emit event if non-empty."""
        raw = bytes(sample.payload)
        try:
            detections = json.loads(raw.decode("utf-8"))
        except Exception as e:
            print(f"ignoring non-json detection payload: {e}", file=sys.stderr)
            return

        if not isinstance(detections, list):
            print("detection payload is not a list, skipping", file=sys.stderr)
            return

        if len(detections) == 0:
            if self.verbose:
                print(f"[DEBUG] empty detection list, skipping event", file=sys.stderr)
            return

        event = self.make_event(detections)
        if self.verbose:
            print(f"[DEBUG] emitting event with {len(detections)} detection(s)", file=sys.stderr)
        print(json.dumps(event))
        insert_detection_event(event)

    def cleanup(self):
        """Clean up resources."""
        if self.zenoh_sub:
            self.zenoh_sub.undeclare()
        if self.zenoh_session:
            self.zenoh_session.close()


def main():
    args = parse_args()

    rclpy.init()
    node = EventComposer(args)

    if args.verbose:
        print(f"[DEBUG] ROS 2 Node initialized", file=sys.stderr)
        print(f"[DEBUG] Subscribed to ROS 2 topics:", file=sys.stderr)
        # print(f"  Image:    {args.image_topic}", file=sys.stderr)
        print(f"  Odometry: {args.odom_topic}", file=sys.stderr)
        print(f"  TF:       {args.tf_topic}", file=sys.stderr)

    node.setup_zenoh()

    print("Event subscriber running (Ctrl+C to exit)", file=sys.stderr)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cleanup()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
