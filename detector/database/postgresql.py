import psycopg2
from psycopg2 import DatabaseError
from datetime import datetime, timezone
import math
import json as json_module

def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # Connection parameters
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5433
        }
        
        # Connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        
        # Create a cursor object for executing SQL queries
        cur = conn.cursor()
        
        # Execute a simple query
        cur.execute('SELECT version()')
        
        # Fetch the result
        db_version = cur.fetchone()
        print(f'PostgreSQL database version: {db_version}')
        
        # Close the cursor and connection
        cur.close()
        
    except DatabaseError as e:
        print(f'An error occurred: {e}')
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')



def quaternion_to_yaw(qx, qy, qz, qw):
    """Convert quaternion to yaw angle (in radians)."""
    sinr_cosp = 2 * (qw * qx + qy * qz)
    cosr_cosp = 1 - 2 * (qx * qx + qy * qy)
    return math.atan2(sinr_cosp, cosr_cosp)


def insert_detection_event(event_json):
    """Insert a maze.detection.v1 event into detection_events and detections tables.

    Args:
        event_json: dict with schema maze.detection.v1 containing:
          - event_id, run_id, robot_id, sequence
          - image: {stamp: {sec, nanosec}, frame_id, width, height, encoding, ...}
          - odometry: {x, y, z, qx, qy, qz, qw, vx, vy, vz, wz, ...}
          - tf: {base_frame, camera_frame, t_base_camera, tf_ok}
          - detections: [{det_id, class_id, class_name, confidence, bbox_xyxy}, ...]

    Returns:
        bool: True if inserted successfully, False otherwise
    """
    conn = None
    try:
        # Connection parameters
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5433
        }

        conn = psycopg2.connect(**params)
        cur = conn.cursor()

        # Extract event-level data
        event_id = event_json.get("event_id")
        run_id = event_json.get("run_id")
        robot_id = event_json.get("robot_id")
        sequence = event_json.get("sequence")

        # Extract image data
        image = event_json.get("image") or {}
        image_frame_id = image.get("frame_id")
        image_sha256 = image.get("sha256")
        width = image.get("width")
        height = image.get("height")
        encoding = image.get("encoding")

        # Build timestamp from image stamp (sec, nanosec)
        stamp_dict = image.get("stamp", {})
        sec = stamp_dict.get("sec", 0)
        nanosec = stamp_dict.get("nanosec", 0)
        stamp = datetime.fromtimestamp(sec + nanosec / 1e9, tz=timezone.utc)

        # Extract odometry data
        odom = event_json.get("odometry") or {}
        x = odom.get("x")
        y = odom.get("y")
        # Calculate yaw from quaternion
        qx = odom.get("qx", 0.0)
        qy = odom.get("qy", 0.0)
        qz = odom.get("qz", 0.0)
        qw = odom.get("qw", 1.0)
        yaw = quaternion_to_yaw(qx, qy, qz, qw)
        vx = odom.get("vx")
        vy = odom.get("vy")
        wz = odom.get("wz")

        # Extract TF data
        tf = event_json.get("tf") or {}
        tf_ok = tf.get("tf_ok", False)
        t_base_camera = tf.get("t_base_camera", [])

        # Insert into detection_events table
        insert_event_query = """
        INSERT INTO detection_events (
            event_id, run_id, robot_id, sequence, stamp,
            image_frame_id, image_sha256, width, height, encoding,
            x, y, yaw, vx, vy, wz,
            tf_ok, t_base_camera,
            raw_event
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (run_id, robot_id, sequence) DO NOTHING
        """

        raw_event_str = json_module.dumps(event_json)

        cur.execute(
            insert_event_query,
            (
                event_id, run_id, robot_id, sequence, stamp,
                image_frame_id, image_sha256, width, height, encoding,
                x, y, yaw, vx, vy, wz,
                tf_ok, t_base_camera,
                raw_event_str
            )
        )

        # Insert detections
        detections = event_json.get("detections", [])
        insert_det_query = """
        INSERT INTO detections (
            event_id, det_id, class_id, class_name, confidence,
            x1, y1, x2, y2
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id, det_id) DO NOTHING
        """

        for det in detections:
            bbox = det.get("bbox_xyxy", [None, None, None, None])
            cur.execute(
                insert_det_query,
                (
                    event_id,
                    det.get("det_id"),
                    det.get("class_id"),
                    det.get("class_name"),
                    det.get("confidence"),
                    bbox[0],  # x1
                    bbox[1],  # y1
                    bbox[2],  # x2
                    bbox[3],  # y2
                ),
            )

        conn.commit()
        print(f"Event {event_id}: inserted successfully ({len(detections)} detections)")
        return True

    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error inserting event: {e}")
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

def view_items_in_table(table_name):
    conn = None
    cursor = None
    try:
        # 1. Establish a connection
        # Replace 'your_database', 'your_user', 'your_password', 'your_host', and 'your_port' with your actual details
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5433
        }
        conn = psycopg2.connect(**params)
        # Optional: set autocommit to True if you don't need explicit transaction control
        # conn.autocommit = True 

        # 2. Create a cursor object
        cursor = conn.cursor()

        # 3. Define and execute the SELECT query
        # Using %s as a placeholder for the table name is not directly supported in psycopg2 
        # for identifiers (like table names), so we format the string carefully.
        # Be cautious with string formatting to avoid SQL injection in real applications.
        sql_query = f"SELECT * FROM {table_name}"
        cursor.execute(sql_query)

        # 4. Fetch all the results
        # fetchall() returns a list of tuples, where each tuple is a row
        records = cursor.fetchall()

        # 5. Process and display the results
        print(f"Items in the table '{table_name}':")
        for row in records:
            print(row)

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    finally:
        # 6. Close the cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("Database connection closed.")



if __name__ == '__main__':
    connect()# Example usage:
    view_items_in_table("detection_events")