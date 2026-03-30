import ast
import collections
import matplotlib.pyplot as plt
import numpy as np
import psycopg2
from psycopg2 import DatabaseError
from datetime import datetime, timezone
import json
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# AGE Graph attributes:
# Run	run_id, started_at (run id will increment for each new run, this will be determined by the first keyframe in the run)
# Keyframe	run_id, keyframe_id, timestamp (this will be populated from detection_events table and will point to pose, observation, and place assumption at that keyframe)
# Pose	map_x, map_y, map_yaw (this is populated from detection_events table and will point to the observations that were made at that pose)
# Observation	det_id, class_name, confidence (specific detection id coming from detections will link to the object)
# Object	object_id, class_name, mean_x, mean_y, obs_count (this comes from merged_landmarks and will link to the place which will be found by dbscan bucketing)
# Place	place_id, centroid_x, centroid_y, keyframe_count (the mapping will come from clustering the merged_landmarks with DBSCAN, and the keyframe count will be the number of keyframes that have an observation linked to an object linked to that place)

# compute cosine similarity sim = dot(e, mean_embedding)
def cosine_similarity_diff(a, b):
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return np.dot(a, b) / (a_norm * b_norm)

# filter existing landmarks so that they are only compared to other landmarks of the same class, for every class
# return a dictionary where the keys are class names and the values are lists of landmarks of that class
def filter_landmarks_by_class(landmarks):
    binned_landmarks = collections.defaultdict(list)
    for lm in landmarks:
        binned_landmarks[lm['class']].append(lm)
    return binned_landmarks

# REN NOTE: update this function so that it instead takes a single landmark and inserts into graph based on whether it matches to an existing object or not, 
# and then returns the object id that it is linked to (either existing or new)
# landmarks is an object with keys 'class', 'x', 'y', 'embedding''
# later, the graph will point an observation with an embedding to one of these objects
# def merge_landmarks(landmarks):
#     # Step 1: Bin all landmarks by class so that objects of each class are only compared to other objects of the same class, for every class
#     binned_landmarks = filter_landmarks_by_class(landmarks)
#     binned_objects_all = []

#     # do following steps for each class in the binned landmarks
#     # we are trying to build merged landmarks by creating a new object for the first candidate, then comparing the next candidate to the existing merged landmark 
#     # and either merging it or creating a new merged landmark, and so on for all candidates of that class
#     for c, candidates in binned_landmarks.items():
#         passes_filters = True
#         # a clip embedding is a multidimensional vector of floats
#         # for first candidate, we want the mean_embedding to be the embedding of that candidate, and then for subsequent candidates, we want to update the mean_embedding to be the average of the embeddings of all candidates that have been merged so far
#         mean_embedding = None
#         binned_objects = []
#         # For each candidate, compute cosine similarity sim = dot(e, mean_embedding) (primary filter, threshold 0.7)
#         # this means we need to know the mean embedding, and also e is equivalent to my embedding key in the landmarks object
#         for candidate in candidates:
#             if len(binned_objects) == 0:
#                 # binned object has class, x, y, embedding, count
#                 binned_objects.append({
#                     'class': c,
#                     'x': candidate['x'],
#                     'y': candidate['y'],
#                     'embedding': candidate['embedding'],
#                     'count': 1
#                 })
#                 mean_embedding = candidate['embedding']
#                 continue
#             for obj in binned_objects:
#                 passes_filters = True
#                 sim = cosine_similarity(candidate['embedding'], mean_embedding)
#                 if sim < 0.7:
#                     passes_filters = False

#                 # For candidates passing similarity, compute spatial distance (secondary filter, threshold 3.0 m)
#                 dist = np.sqrt((candidate['x'] - obj['x'])**2 + (candidate['y'] - obj['y'])**2)
#                 if dist >= 3.0:
#                     passes_filters = False
                
#                 # if passes filters, merge (update running averages of position, embedding, count) and go to next candidate
#                 if passes_filters:
#                     count = obj['count']
#                     obj['x'] = (obj['x'] * count + candidate['x']) / (count + 1)
#                     obj['y'] = (obj['y'] * count + candidate['y']) / (count + 1)
#                     obj['embedding'] = (obj['embedding'] * count + candidate['embedding']) / (count + 1)
#                     obj['count'] += 1
#                     mean_embedding = obj['embedding']
#                     break
#                 # if does not pass filters, check next object in binned objects, and if no objects in binned objects pass filters, create new binned object
#             if not passes_filters:
#                 binned_objects.append({
#                     'class': c,
#                     'x': candidate['x'],
#                     'y': candidate['y'],
#                     'embedding': candidate['embedding'],
#                     'count': 1
#                 })
#                 mean_embedding = candidate['embedding']
#         binned_objects_all.extend(binned_objects)
#     return binned_objects_all

def fetch_detection_info(detection_embedding):
    # given an embedding from postgresql.py, we want to fetch the corresponding detection information from the detections table, 
    # and then also the corresponding event information from the detection_events table, and return all of that information in a dictionary
    conn = None
    try:
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5433
        }

        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        # first fetch the detection information from the detections table using the det_pk foreign key in the detection_embeddings table
        cur.execute("SELECT det_id, class_name, confidence, x1, y1, x2, y2 FROM detections WHERE det_pk = %s", (detection_embedding['det_pk'],))
        det_info = cur.fetchone()
        if det_info is None:
            print(f"No detection found for det_pk {detection_embedding['det_pk']}")
            return None
        det_id, class_name, confidence, x1, y1, x2, y2 = det_info

        # then fetch the event information from the detection_events table using the event_id foreign key in the detections table
        cur.execute("SELECT run_id, robot_id, sequence, stamp, x, y, yaw FROM detection_events WHERE event_id = (SELECT event_id FROM detections WHERE det_pk = %s)", (detection_embedding['det_pk'],))
        event_info = cur.fetchone()
        if event_info is None:
            print(f"No event found for det_pk {detection_embedding['det_pk']}")
            return None
        run_id, robot_id, sequence, stamp, x, y, yaw = event_info

        return {
            'det_id': det_id,
            'class_name': class_name,
            'confidence': confidence,
            'bbox': (x1, y1, x2, y2),
            'run_id': run_id,
            'robot_id': robot_id,
            'sequence': sequence,
            'stamp': stamp,
            'x': x,
            'y': y,
            'yaw': yaw
        }
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error fetching event: {e}")
        return False
    finally:
        if conn:
            cur.close()
            conn.close()


def fetch_embedding(det_pk):
    conn = None
    try:
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5433
        }

        conn = psycopg2.connect(**params)
        cur = conn.cursor()

        cur.execute("SELECT embedding FROM detection_embeddings WHERE det_pk = %s", (det_pk,))
        embedding = cur.fetchone()
        if embedding is None:
            print(f"No embedding found for det_pk {det_pk}")
            return None
        return embedding[0]
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error fetching embedding: {e}")
        return None
    finally:        
        if conn:
            cur.close()
            conn.close()


def build_graph(detection_embedding):
    detection_info = fetch_detection_info(detection_embedding)
    if detection_info is None:
        print(f"Could not fetch info for detection embedding with det_pk {detection_embedding['det_pk']}")
        return None
    # using the detection info, we can build the graph
    # example node query:
    # SELECT * FROM cypher('graph_name', $$
    # CREATE (:Person {name: 'John'}), 
    #        (:Person {name: 'Jack'}), 
    #        (:Location {name: 'New York'})
    # $$) AS (v agtype);
    # example edge query:
    # SELECT * FROM cypher('graph_name', $$
    #     MATCH (a:Person {name: 'John'}), (b:Location {name: 'New York'})
    #     CREATE (a)-[e:VISITED]->(b)
    #     RETURN e
    # $$) AS (e agtype);
    # node types: Run, Keyframe, Pose, Observation, Object, Place
    # edge connections: Run HAS_KEYFRAME Keyframe, Keyframe HAS_POSE Pose, Pose HAS_OBSERVATION Observation, Observation OBSERVES Object, Object LOCATED_IN Place
    # Place ADJACENT_TO Place, and Keyframe IN_PLACE Place
    
    # first, connect to age postgres graph
    print(f"Beginning graph build for detection embedding with det_pk {detection_embedding['det_pk']}")
    conn = None
    try:
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5434
        }

        conn = psycopg2.connect(**params)
        cur = conn.cursor()

        cur.execute("SET search_path = ag_catalog, \"$user\", public;")

        # then, we want to check if the Run node for this run_id already exists, and if not, create it
        cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (r:Run {run_id: %s}) RETURN r $$) AS (r agtype)", (detection_info['run_id'],))
        run_node = cur.fetchone()
        if run_node is None:
            cur.execute("SELECT * FROM cypher('detections_graph', $$ CREATE (r:Run {run_id: %s, started_at: %s}) RETURN r $$) AS (r agtype)", (detection_info['run_id'], detection_info['stamp'],))
            run_node = cur.fetchone()
        
        print(f"Run node for run_id {detection_info['run_id']}: {run_node}")
        
        # next, we want to check if the Keyframe node for this sequence already exists, and if not, create it and connect it to the Run node
        cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (k:Keyframe {sequence: %s}) RETURN k $$) AS (k agtype)", (detection_info['sequence'],))
        keyframe_node = cur.fetchone()
        if keyframe_node is None:
            cur.execute("SELECT * FROM cypher('detections_graph', $$ CREATE (k:Keyframe {run_id: %s, sequence: %s, timestamp: %s}) RETURN k $$) AS (k agtype)", (detection_info['run_id'], detection_info['sequence'], detection_info['stamp'],))
            keyframe_node = cur.fetchone()
            # connect keyframe to run
            cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (r:Run {run_id: %s}), (k:Keyframe {sequence: %s}) CREATE (r)-[:HAS_KEYFRAME]->(k) RETURN r, k $$) AS (r agtype, k agtype)", (detection_info['run_id'], detection_info['sequence'],))
        
        print(f"Keyframe node for sequence {detection_info['sequence']}: {keyframe_node}")

        # next, we want to check if the Pose node for this keyframe already exists, and if not, create it and connect it to the Keyframe node
        cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (p:Pose {x: %s, y: %s, yaw: %s}) RETURN p $$) AS (p agtype)", (detection_info['x'], detection_info['y'], detection_info['yaw'],))
        pose_node = cur.fetchone()
        if pose_node is None:
            cur.execute("SELECT * FROM cypher('detections_graph', $$ CREATE (p:Pose {x: %s, y: %s, yaw: %s}) RETURN p $$) AS (p agtype)", (detection_info['x'], detection_info['y'], detection_info['yaw'],))
            pose_node = cur.fetchone()
            # connect pose to keyframe
            cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (k:Keyframe {sequence: %s}), (p:Pose {x: %s, y: %s, yaw: %s}) CREATE (k)-[:HAS_POSE]->(p) RETURN k, p $$) AS (k agtype, p agtype)", (detection_info['sequence'], detection_info['x'], detection_info['y'], detection_info['yaw'],))
        
        print(f"Pose node for keyframe sequence {detection_info['sequence']}: {pose_node}")
        # cur.execute("CREATE EXTENSION vector;")
        # next, we want to create an Observation node for this detection and connect it to the Pose node
        cur.execute("SELECT * FROM cypher('detections_graph', $$ CREATE (o:Observation {det_id: %s, class_name: %s, confidence: %s, det_pk: %s}) RETURN o $$) AS (o agtype)", (detection_info['det_id'], detection_info['class_name'], detection_info['confidence'], detection_embedding['det_pk']))
        observation_node = cur.fetchone()
        # connect observation to pose 
        cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (p:Pose {x: %s, y: %s, yaw: %s}), (o:Observation {det_id: %s}) CREATE (p)-[:HAS_OBSERVATION]->(o) RETURN p, o $$) AS (p agtype, o agtype)", (detection_info['x'], detection_info['y'], detection_info['yaw'], detection_info['det_id'],))

        print(f"Observation node for det_id {detection_info['det_id']}: {observation_node}")

        # need to get all of the current Object nodes of the same class as this observation, and compare the embedding of this observation to the embeddings of those Object nodes using cosine similarity, and if any of them pass the similarity threshold of 0.7 and spatial distance threshold of 3.0, then we connect this observation to that existing Object node, and if not, we create a new Object node for this observation and connect it to that
        # observation contains an embedding which is a multidimensional vector, and the Object nodes contain a mean embedding which is also a multidimensional vector, and we want to compute cosine similarity between those two vectors
        cur.execute("SELECT to_jsonb(obj) FROM cypher('detections_graph', $$ MATCH (o:Observation {class_name: %s})-[:OBSERVES]->(obj:Object) RETURN obj $$) AS (obj agtype)", (detection_info['class_name'],))
        # do the same as previous line but select list of json objects

        object_nodes = cur.fetchall()
        object_found = False
        print(f"Comparing observation embedding to {len(object_nodes)} existing object nodes of class {detection_info['class_name']} for potential matches")  # Debug print to check how many object nodes are being compared against
        for obj in object_nodes:
            # ok so we need to calculate the mean embedding for each object node, which means we need to get all of the observation nodes that are connected to that object node, 
            # and then get the embeddings for those observation nodes from the detection_embeddings table using the det_pk foreign key, 
            # and then average those embeddings to get the mean embedding for that object node, and then we can compute cosine similarity between the observation embedding 
            # and the mean embedding of the object node
            obj_node = obj[0]  # convert from agtype to json, then to dict
            print(obj_node)  # Debug print to check the object node being processed
           
           # get the observation nodes that are connected to this object node
            cur.execute("SELECT to_jsonb(o) FROM cypher('detections_graph', $$ MATCH (o:Observation)-[:OBSERVES]->(obj:Object {class_name: %s, x: %s, y: %s}) RETURN o $$) AS (o agtype)", (detection_info['class_name'], obj_node['properties']['x'], obj_node['properties']['y']))
            connected_observations = cur.fetchall()
            print(f"Object node with class {detection_info['class_name']} at position ({obj_node['properties']['x']}, {obj_node['properties']['y']}) has {len(connected_observations)} connected observations")  # Debug print to check how many observations are connected to this object node
            if len(connected_observations) == 0:
                continue
            # get the embeddings for those observation nodes from the detection_embeddings table using the det_pk foreign key
            embeddings = []
            for obs in connected_observations:
                # cur.execute("SELECT * FROM detection_embeddings WHERE det_pk = %s", (obs[0]['properties']['det_pk'],))
                embedding = json.loads(fetch_embedding(obs[0]['properties']['det_pk']))
                if embedding is not None:
                    embeddings.append(np.array(embedding, dtype=float))
            if len(embeddings) == 0:
                continue
            print(f"Calculate mean embeddings")  # Debug print to check the embeddings being compared
            mean_embedding = np.mean(embeddings, axis=0)
            # print(f"Mean embedding for object node with class {detection_info['class_name']} at position ({obj_node['properties']['x']}, {obj_node['properties']['y']}): {mean_embedding}")  # Debug print to check the mean embedding
            sim = cosine_similarity(detection_embedding['embedding'], mean_embedding)
            print(f"Cosine similarity between observation embedding and object node mean embedding: {sim}")  # Debug print to check cosine similarity
            if sim >= 0.7:
                # check spatial distance as well, for that we need to get the mean x and y of the object node, which are stored as properties of the node
                obj_x = float(obj_node['properties']['x'])
                obj_y = float(obj_node['properties']['y'])
                dist = np.sqrt((detection_info['x'] - obj_x)**2 + (detection_info['y'] - obj_y)**2)
                if dist < 3.0:
                    print(f"Found matching object node with cosine similarity {sim} and spatial distance {dist}, connecting observation to this object node")  # Debug print to confirm when a match is found
                    # connect observation to existing object node and update x, y averages
                    # cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (o:Observation {det_id: %s}), (obj:Object {class_name: %s, x: %s, y: %s}) CREATE (o)-[:OBSERVES]->(obj) RETURN o, obj $$) AS (o agtype, obj agtype)", (detection_info['det_id'], detection_info['class_name'], detection_info['x'], detection_info['y']))
                    # print(f"Observation with det_id {detection_info['det_id']} connected to existing object node with class {detection_info['class_name']} at position ({obj_node['properties']['x']}, {obj_node['properties']['y']})")  # Debug print to confirm observation connection to existing object node
                    # get the det_id of every observation node currently connected to this object node
                    cur.execute("SELECT to_jsonb(o) FROM cypher('detections_graph', $$ MATCH (o:Observation)-[:OBSERVES]->(obj:Object {class_name: %s, x: %s, y: %s}) RETURN o $$) AS (o agtype)", (detection_info['class_name'], obj_node['properties']['x'], obj_node['properties']['y']))
                    connected_observations = cur.fetchall()
                    
                    existing_count = float(obj_node['properties']['embedcnt'])
                    new_x = (obj_x * existing_count + detection_info['x']) / (existing_count + 1)
                    new_y = (obj_y * existing_count + detection_info['y']) / (existing_count + 1)
                    new_count = float(existing_count + 1)
                    # print(f"Existing object node position: ({obj_x}, {obj_y}), count: {existing_count}")  # Debug print to check existing object node position and count
                    cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (obj:Object {class_name: %s, x: %s, y: %s, embedcnt: %s}) SET obj.x = %s, obj.y = %s, obj.embedcnt = %s  RETURN obj $$) AS (obj agtype)", (detection_info['class_name'], obj_x, obj_y, existing_count, new_x, new_y, new_count,))
                    retobj = cur.fetchone()
                    print(retobj)
                    # connect observation to existing object node
                    cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (o:Observation {det_id: %s}), (obj:Object {class_name: %s, x: %s, y: %s}) CREATE (o)-[:OBSERVES]->(obj) RETURN o, obj $$) AS (o agtype, obj agtype)", (detection_info['det_id'], detection_info['class_name'], new_x, new_y,))
                    # reconnect the existing observations to the updated object node position
                    # for obs in connected_observations:
                    #     cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (o:Observation {det_id: %s}), (obj:Object {class_name: %s, x: %s, y: %s}) CREATE (o)-[:OBSERVES]->(obj) RETURN o, obj $$) AS (o agtype, obj agtype)", (obs[0]['properties']['det_id'], detection_info['class_name'], new_x, new_y,))
                    print(f"Observation with det_id {detection_info['det_id']} connected to existing object node with class {detection_info['class_name']} at updated position ({new_x}, {new_y}) with updated count {new_count}")  # Debug print to confirm observation connection to existing object node and updated position and count
                    
                    object_found = True
                    break
        if not object_found:
            print(f"No matching object node found, creating new object node for this observation")  # Debug print to confirm when no match is found and a new object node is being created
            # create new object node and connect observation to it
            count = float(1)
            cur.execute("SELECT * FROM cypher('detections_graph', $$ CREATE (obj:Object {class_name: %s, x: %s, y: %s, embedcnt: %s}) RETURN obj $$) AS (obj agtype)", (detection_info['class_name'], detection_info['x'], detection_info['y'], count,))
            new_object_node = cur.fetchone()
            print(f"New object node created with class {detection_info['class_name']} at position ({detection_info['x']}, {detection_info['y']})")  # Debug print to confirm new object node creation
            cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (o:Observation {det_id: %s}), (obj:Object {class_name: %s, x: %s, y: %s}) CREATE (o)-[:OBSERVES]->(obj) RETURN o, obj $$) AS (o agtype, obj agtype)", (detection_info['det_id'], detection_info['class_name'], detection_info['x'], detection_info['y'],))
            print(f"Object node connection complete for observation with det_id {detection_info['det_id']}")  # Debug print to confirm object node connection
        # we want to assign these places as well, but those are best done offline
        # connect keyframe to place as well
        # verify that the observation is connected to an object
        cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (o:Observation {det_id: %s})-[:OBSERVES]->(obj:Object) RETURN o, obj $$) AS (o agtype, obj agtype)", (detection_info['det_id'],))
        observation_object_connection = cur.fetchone()
        if not observation_object_connection:
            print(f"Error: Observation with det_id {detection_info['det_id']} is not connected to any object node")
            return False

        conn.commit()
        print(f"Graph updated with detection embedding for det_id {detection_info['det_id']}")

        return True
    
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error building graph: {e}")
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

# the previous function constructs places based on object, but we actually need to do it based on the poses tied to each keyframe, and then connect the objects to the places based on the observations tied to each pose, so we need to update the construct_places function to do that instead, and then we can use the object-based clustering as a fallback for any objects that are not connected to any places after the initial place construction
def construct_places():
    # this function will go through all of the Keyframe nodes in the graph, cluster them based on the x and y positions of their connected Pose nodes using DBSCAN, 
    # and then create Place nodes for each cluster and connect the Keyframe nodes to their corresponding Place nodes, along with the object nodes that are connected to those keyframes through observations
    conn = None
    try:
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5434
        }

        conn = psycopg2.connect(**params)
        cur = conn.cursor()

        cur.execute("SET search_path = ag_catalog, \"$user\", public;")
        # first delete and disconnect any existing Place nodes so that we can reconstruct them from scratch based on the current Keyframe and Pose nodes
        cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (k:Keyframe)-[:IN_PLACE]->(p:Place) DETACH DELETE p $$) AS (p agtype)")

        cur.execute("SELECT to_jsonb(k), to_jsonb(p) FROM cypher('detections_graph', $$ MATCH (k:Keyframe)-[:HAS_POSE]->(p:Pose) RETURN k, p $$) AS (k agtype, p agtype)")
        keyframe_pose_pairs = cur.fetchall()
        keyframe_positions = []
        for pair in keyframe_pose_pairs:
            keyframe_node = pair[0]
            pose_node = pair[1]
            pose_x = pose_node['properties']['x']
            pose_y = pose_node['properties']['y']
            keyframe_positions.append((pose_x, pose_y))
        # cluster keyframe positions using DBSCAN
        if len(keyframe_positions) == 0:
            print("No keyframe nodes with poses found in graph, skipping place construction")
            return True
        from sklearn.cluster import DBSCAN
        clustering = DBSCAN(eps=0.25, min_samples=3).fit(keyframe_positions)
        labels = clustering.labels_
        unique_labels = set(labels)
        print("about to cluster")
        place_id = 0  # Initialize place_id counter
        for label in unique_labels:
            cluster_indices = [i for i, l in enumerate(labels) if l == label]
            cluster_keyframe_pose_pairs = [keyframe_pose_pairs[i] for i in cluster_indices]
            # print(cluster_keyframe_pose_pairs, len(cluster_keyframe_pose_pairs))
            # create place node for this cluster
            cluster_x = np.mean([pair[1]['properties']['x'] for pair in cluster_keyframe_pose_pairs])
            cluster_y = np.mean([pair[1]['properties']['y'] for pair in cluster_keyframe_pose_pairs])
            # cur.execute("SELECT * FROM cypher('detections_graph', $$ CREATE (place:Place {centroid_x: %s, centroid_y: %s, keyframe_count: %s}) RETURN place $$) AS (place agtype)", (cluster_x, cluster_y, len(cluster_keyframe_pose_pairs),))
            # do same as previous but include an incrementing place_id 
            cur.execute("SELECT * FROM cypher('detections_graph', $$ CREATE (place:Place {centroid_x: %s, centroid_y: %s, place_id: %s}) RETURN place $$) AS (place agtype)", (cluster_x, cluster_y, place_id,))
            place_node = cur.fetchone()
            print("connect keyframe nodes in this cluster to the place node")
            # connect keyframe nodes in this cluster to the place node
            for pair in cluster_keyframe_pose_pairs:
                keyframe_node = pair[0]
                cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (k:Keyframe {sequence: %s}), (place:Place {centroid_x: %s, centroid_y: %s}) CREATE (k)-[:IN_PLACE]->(place) RETURN k, place $$) AS (k agtype, place agtype)", (keyframe_node['properties']['sequence'], cluster_x, cluster_y,))
                # also connect object nodes that have observations linked to these keyframes to the place node
                cur.execute("SELECT to_jsonb(obj) FROM cypher('detections_graph', $$ MATCH (obj:Object)<-[:OBSERVES]-(:Observation)<-[:HAS_OBSERVATION]-(:Pose)<-[:HAS_POSE]-(k:Keyframe {sequence: %s}) RETURN DISTINCT obj $$) AS (obj agtype)", (keyframe_node['properties']['sequence'],))
                object_nodes = cur.fetchall()
                for obj_node in object_nodes:  
                    cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (obj:Object {class_name: %s, x: %s, y: %s})-[:LOCATED_IN]->(place:Place {centroid_x: %s, centroid_y: %s}) RETURN obj, place $$) AS (obj agtype, place agtype)", (obj_node[0]['properties']['class_name'], obj_node[0]['properties']['x'], obj_node[0]['properties']['y'], cluster_x, cluster_y,))
                    if cur.fetchone() is None:
                        cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (obj:Object {class_name: %s, x: %s, y: %s}), (place:Place {centroid_x: %s, centroid_y: %s}) CREATE (obj)-[:LOCATED_IN]->(place) RETURN obj, place $$) AS (obj agtype, place agtype)", (obj_node[0]['properties']['class_name'], obj_node[0]['properties']['x'], obj_node[0]['properties']['y'], cluster_x, cluster_y,))
        conn.commit()
        print("Place construction complete")
        return True
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error constructing places: {e}")
        return False
    finally:
        if conn:
            cur.close()
            conn.close()


def create_graph():
    print("Creating graph from detection embeddings...")
    conn = None
    try:
        print("Connecting to graph database...")
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5434
        }
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        # cur.execute("LOAD 'age';")
        cur.execute("SET search_path = ag_catalog, \"$user\", public;")
        # cur.execute("CREATE EXTENSION age;")
        cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (n) RETURN n $$) as (v agtype);")
        conn.commit()
        return True
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error creating graph: {e}")
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

def delete_object_nodes():
    conn = None
    try:
        print("Connecting to graph database...")
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5434
        }
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SET search_path = ag_catalog, \"$user\", public;")
        cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (obj:Object) DETACH DELETE obj $$) as (v agtype);")
        conn.commit()
        print("Object nodes deleted successfully")
        return True
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error deleting object nodes: {e}")
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

def get_keyframe_count():
    conn = None
    try:
        print("Connecting to graph database...")
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5434
        }
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SET search_path = ag_catalog, \"$user\", public;")
        cur.execute("SELECT COUNT(*) FROM cypher('detections_graph', $$ MATCH (k:Keyframe) RETURN k $$) as (k agtype);")
        count = cur.fetchone()[0]
        print(f"Total keyframe count: {count}")
        return count
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error getting keyframe count: {e}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

def get_observation_count():
    conn = None
    try:
        print("Connecting to graph database...")
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5434
        }
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SET search_path = ag_catalog, \"$user\", public;")
        cur.execute("SELECT COUNT(*) FROM cypher('detections_graph', $$ MATCH (o:Observation) RETURN o $$) as (o agtype);")
        count = cur.fetchone()[0]
        print(f"Total observation count: {count}")
        return count
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error getting observation count: {e}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

def get_object_count():
    conn = None
    try:
        print("Connecting to graph database...")
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5434
        }
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SET search_path = ag_catalog, \"$user\", public;")
        cur.execute("SELECT COUNT(*) FROM cypher('detections_graph', $$ MATCH (obj:Object) RETURN obj $$) as (obj agtype);")
        count = cur.fetchone()[0]
        print(f"Total object count: {count}")
        return count
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error getting object count: {e}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

def get_place_count():
    conn = None
    try:
        print("Connecting to graph database...")
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5434
        }

        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SET search_path = ag_catalog, \"$user\", public;")
        cur.execute("SELECT COUNT(*) FROM cypher('detections_graph', $$ MATCH (place:Place) RETURN place $$) as (place agtype);")
        count = cur.fetchone()[0]
        print(f"Total place count: {count}")
        return count
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error getting place count: {e}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

# Provide working scripts for:
# Get the two most recent detection embeddings from detection_embeddings, pretending we have no other information
def get_recent_detections():
    conn = None
    try:
        print("Connecting to database...")
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5433
        }
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SELECT det_pk, embedding FROM detection_embeddings ORDER BY det_pk DESC LIMIT 2;")
        recent_detections = cur.fetchall()
        recent_embeddings = [json.loads(detection[1]) for detection in recent_detections]
        # also get x,y coordinates for these recent detections from the detections table using the det_pk foreign key
        # first need to get the event_id for each det_pk from the detections table, and then get the x,y coordinates for each event_id from the detection_events table
        for i, detection in enumerate(recent_detections):
            det_pk = detection[0]
            cur.execute("SELECT event_id, class_name FROM detections WHERE det_pk = %s;", (det_pk,))
            event_id = cur.fetchone()[0]
            cur.execute("SELECT x, y FROM detection_events WHERE event_id = %s;", (event_id,))
            coords = cur.fetchone()
            recent_embeddings[i] = {
                "embedding": recent_embeddings[i],
                "x": coords[0],
                "y": coords[1]
            }
        print(f"Most recent embeddings: {recent_embeddings}")
        # print classnames as well
        cur.execute("SELECT det_pk, class_name FROM detections WHERE det_pk IN (%s, %s);", (recent_detections[0][0], recent_detections[1][0],))
        class_names = cur.fetchall()
        for i, class_name in enumerate(class_names):
            recent_embeddings[i]["class_name"] = class_name[1]
        return recent_embeddings
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error fetching recent detections: {e}")
        return None
    finally:        
        if conn:
            cur.close()
            conn.close()

# Vector
# Top-k visually similar detections for a query crop.
# Compute CLIP embeddings for query crops and find the top-k most visually similar stored detections:
# SELECT det_id, embedding <=> $query_vec AS distance
# FROM detection_embeddings
# ORDER BY distance
# LIMIT 10;
def get_similar_detections(query_embedding, k=10):
    conn = None
    try:
        print("Connecting to database...")
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5433
        }
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        # cur.execute("SELECT det_pk, embedding <=> %s AS distance FROM detection_embeddings ORDER BY distance LIMIT %s;", (json.dumps(query_embedding), k,))
        # use the embedding to find the det_pks of the top k most similar detections where det_pk also exists in the detections graph
        # because the detection graph uses a different port, we need to first get the det_pks of the top k most similar detections from this database, and then use those det_pks to query the detections graph database to get the corresponding det_ids
        cur.execute("SELECT det_pk, embedding <=> %s AS distance FROM detection_embeddings ORDER BY distance LIMIT %s;", (json.dumps(query_embedding), k,))
        similar_detections = cur.fetchall()
        # get all the det_ids of the similar detections and return them as a list
        det_pks = [detection[0] for detection in similar_detections]
        print(f"Top {k} similar detection pks: {det_pks}")
        embeddings = [detection[1] for detection in similar_detections]
            # print("similarity score: ", cosine_similarity(query_embedding, json.loads(embed)))
            # print("siilarity score: ", sklearn.metrics.pairwise.cosine_similarity(query_embedding, embed))
        # print(f"Top {k} similar detection pks: {det_pks}")
        # use det_pks to get the corresponding det_ids from the detections table
        return det_pks
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error fetching similar detections: {e}")
        return None
    finally:        
        if conn:
            cur.close()
            conn.close()

# Graph
# Reachable places within N hops containing an object class.
# For each matched det_id, traverse the graph to find which Place the object is in:
# SELECT * FROM cypher('semantic_map', $$
#   MATCH (obs:Observation {det_id: id})
#         -[:OBSERVES]->(obj:Object)
#         -[:LOCATED_IN]->(p:Place)
#   RETURN p.place_id, p.centroid_x, p.centroid_y, obj.class_name
# $$) AS (place_id agtype, cx agtype, cy agtype, class agtype);
def get_places_for_detection(det_pk):
    conn = None
    try:
        print("Connecting to graph database...")
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5434
        }
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SET search_path = ag_catalog, \"$user\", public;")
        print(f"Fetching place information for detection with det_pk {det_pk} from graph database...")
        cur.execute("SELECT to_jsonb(p) FROM cypher('detections_graph', $$ MATCH (obs:Observation {det_pk: %s})-[:OBSERVES]->(obj:Object)-[:LOCATED_IN]->(p:Place) RETURN p $$) AS (p agtype);", (det_pk,))
        places = cur.fetchall()
        # print(f"Places found for detection with det_pk {det_pk}: {places}")
        # get class_name of associated observation as well
        cur.execute("SELECT to_jsonb(obj) FROM cypher('detections_graph', $$ MATCH (obs:Observation {det_pk: %s})-[:OBSERVES]->(obj:Object) RETURN obj $$) AS (obj agtype);", (det_pk,))
        obj = cur.fetchone()
        print(f"Object found for detection with det_pk {det_pk}: {obj}")
        print(f"Object has class_name: {obj[0]['properties']['class_name'] if obj else 'unknown'}")  # Debug print to check class name of associated object
        class_name = obj[0]['properties']['class_name'] if obj else 'unknown'
        place_info = []
        for place in places:
            # only append if it is not already in the list to avoid duplicates in case there are multiple observations of the same object connected to the same place
            if (place[0]['properties']['place_id']) not in place_info:
                 place_info.append((place[0]['properties']['centroid_x'], place[0]['properties']['centroid_y'], place[0]['properties']['place_id']))
            # place_info.append((place[0]['properties']['centroid_x'], place[0]['properties']['centroid_y'], place[0]['properties']['place_id'], class_name))
        # print(f"Places for detection with det_pk {det_pk}: {place_info}")
        return place_info
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error fetching places for detection: {e}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

# Re-localization
# Top-3 candidate places from query crops.
# Group results by Place, sum similarity scores, rank top-3. The winning Place’s centroid is the pose hypothesis.
# print all results
def get_candidate_places_for_embedding(real_embedding, places, k=3):
    # get embedding for det_id
    conn = None
    try:
        print("Connecting to database...")
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5434
        }
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SET search_path = ag_catalog, \"$user\", public;")
        # for each place, we want to compute the similarity score between the embedding and the mean embedding of the objects located in that place, and then sum those similarity scores for each place, and then rank the places by their total similarity score, and return the top k places as candidate places for re-localization
        place_scores = []
        for place in places:
            # place_id = place[0]
            centroid_x = place[0]
            centroid_y = place[1]
            place_id = place[2]
            # class_name = place[3]
            # class_name = place[3]
            # get all object nodes located in this place with this class name
            # cur.execute("SELECT to_jsonb(obj) FROM cypher('detections_graph', $$ MATCH (obj:Object {class_name: %s})-[:LOCATED_IN]->(place:Place {place_id: %s}) RETURN obj $$) AS (obj agtype)", (class_name, place_id,))
            # get all object nodes located in this place
            cur.execute("SELECT to_jsonb(obj) FROM cypher('detections_graph', $$ MATCH (obj:Object)-[:LOCATED_IN]->(place:Place {place_id: %s}) RETURN obj $$) AS (obj agtype)", (place_id,))
            # same as previous but match on centroid_x and centroid_y instead of place_id since we don't have place_id in the current graph schema
            # cur.execute("SELECT to_jsonb(obj) FROM cypher('detections_graph', $$ MATCH (obj:Object {class_name: %s})-[:LOCATED_IN]->(place:Place {centroid_x: %s, centroid_y: %s}) RETURN obj $$) AS (obj agtype)", (class_name, centroid_x, centroid_y,))
            object_nodes = cur.fetchall()
            print(f"Object nodes found for place with centroid ({centroid_x}, {centroid_y}) : {object_nodes}")
            if len(object_nodes) == 0:
                continue
            # compute mean embedding for these object nodes
            embeddings = []
            simscore = 0
            for obj_node in object_nodes:
                cur.execute("SELECT to_jsonb(o) FROM cypher('detections_graph', $$ MATCH (o:Observation)-[:OBSERVES]->(obj:Object {class_name: %s, x: %s, y: %s}) RETURN o $$) AS (o agtype)", (obj_node[0]['properties']['class_name'], obj_node[0]['properties']['x'], obj_node[0]['properties']['y']))
                connected_observations = cur.fetchall()
                print("Number of observations connected to object node: ", len(connected_observations))
                for obs in connected_observations:
                    embedding = json.loads(fetch_embedding(obs[0]['properties']['det_pk']))
                    if embedding is not None:
                        embeddings.append(np.array(embedding, dtype=float))
                mean_embedding = np.mean(embeddings, axis=0) if len(embeddings) > 0 else None
                simscore += cosine_similarity([real_embedding], [mean_embedding])[0][0]
            if len(embeddings) == 0:
                continue
            print(f"Embeddings length for object nodes in place with centroid ({centroid_x}, {centroid_y}) : {len(embeddings)}")
            mean_embedding = np.mean(embeddings, axis=0)
            print(f"Mean embedding for place with centroid ({centroid_x}, {centroid_y}) : {mean_embedding}")
            sim = cosine_similarity([real_embedding], [mean_embedding])[0][0]
            sim = simscore
            print(f"Similarity score between query embedding and mean embedding for place with centroid ({centroid_x}, {centroid_y}): {sim}")
            # place_scores.append((place_id, centroid_x, centroid_y, class_name, sim))
            place_scores.append((place_id, centroid_x, centroid_y, sim))
        # rank places by similarity score and return top k
        # remove duplicates from place_scores based on place_id, keeping the one with the highest similarity score for each place_id
        print("All places: ", places)
        print("Place scores before removing duplicates: ", place_scores)
        unique_place_scores = {}
        for score in place_scores:
            place_id = score[0]
            if place_id not in unique_place_scores or score[3] > unique_place_scores[place_id][3]:
                unique_place_scores[place_id] = score
        place_scores = list(unique_place_scores.values())
        place_scores.sort(key=lambda x: x[3], reverse=True)
        top_places = place_scores[:k]
        print(f"Top {k} candidate places for embedding: {top_places}")
        return top_places
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error fetching candidate places for embedding: {e}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

# want to see if every observation is connected to an object node
def check_observations_connected_to_objects():
    conn = None
    try:
        print("Connecting to graph database...")
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5434
        }
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SET search_path = ag_catalog, \"$user\", public;")
        cur.execute("SELECT COUNT(*) FROM cypher('detections_graph', $$ MATCH (o:Observation) RETURN o $$) AS (o agtype);")
        total_observations = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM cypher('detections_graph', $$ MATCH (o:Observation)-[:OBSERVES]->(obj:Object) RETURN o $$) AS (o agtype);")
        connected_observations = cur.fetchone()[0]
        print(f"Total observations: {total_observations}, Connected observations: {connected_observations}")
        # is every observation connected to an object node? need list of observations and then find if they all have a connection to an object node
        cur.execute("SELECT to_jsonb(o) FROM cypher('detections_graph', $$ MATCH (o:Observation) RETURN o $$) AS (o agtype);")
        observations = cur.fetchall()
        unconnected_observations = []
        for obs in observations:
            cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (o:Observation {det_pk: %s})-[:OBSERVES]->(obj:Object) RETURN o $$) AS (o agtype);", (obs[0]['properties']['det_pk'],))
            if cur.fetchone() is None:
                unconnected_observations.append(obs[0]['properties']['det_pk'])
        print(f"Unconnected observations: {unconnected_observations}")
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error checking observation connections: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

def how_many_objects():
    conn = None
    try:
        print("Connecting to graph database...")
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5434
        }
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SET search_path = ag_catalog, \"$user\", public;")
        cur.execute("SELECT COUNT(*) FROM cypher('detections_graph', $$ MATCH (obj:Object) RETURN obj $$) AS (obj agtype);")
        total_objects = cur.fetchone()[0]
        print(f"Total objects: {total_objects}")
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error counting objects: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

def delete_graph():
    conn = None
    try:
        print("Connecting to graph database...")
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5434
        }
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SET search_path = ag_catalog, \"$user\", public;")
        cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (n) DETACH DELETE n $$) AS (v agtype);")
        conn.commit()
        print("Graph deleted successfully")
        return True
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error deleting graph: {e}")
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

def delete_place_nodes():
    conn = None
    try:
        print("Connecting to graph database...")
        params = {
            "host": "localhost",
            "database": "turtlebot",
            "user": "ren",
            "password": "pwd",
            "port": 5434
        }
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SET search_path = ag_catalog, \"$user\", public;")
        cur.execute("SELECT * FROM cypher('detections_graph', $$ MATCH (place:Place) DETACH DELETE place $$) as (v agtype);")
        conn.commit()
        print("Place nodes deleted successfully")
        return True
    except (DatabaseError, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Error deleting place nodes: {e}")
        return False
    finally:
        if conn:
            cur.close()
            conn.close()

def graph_stats():
    get_keyframe_count()
    get_observation_count()
    get_object_count()
    get_place_count()


if __name__ == "__main__":
    # Helper functions
    # delete_place_nodes()
    # construct_places()
    # check_observations_connected_to_objects()
    # graph_stats()

    # Runs the localisation
    detection_embeddings = get_recent_detections()
    # print the resulting xy 
    print(f"XY coordinates for the most recent detections: {[(embedding_info['x'], embedding_info['y']) for embedding_info in detection_embeddings]}")
    candidates_per_embedding = []
    xy_locations_per_embedding = []
    # print classnames as well
    print(f"Class names for the most recent detections: {[embedding_info['class_name'] for embedding_info in detection_embeddings]}")
    for embedding_info in detection_embeddings:
        embedding = embedding_info["embedding"]
        xy_locations_per_embedding.append((embedding_info["x"], embedding_info["y"]))
        print(f"XY coordinates for embedding: {embedding_info['x']}, {embedding_info['y']}")
        ids = get_similar_detections(embedding, k=10)
        places = []
        for det_pk in ids:
            places.extend(get_places_for_detection(det_pk))
            print(f"Places for detection with det_pk {det_pk}: {places}")
            # filter places by id to avoid duplicates
            unique_places = {}
            for place in places:
                place_id = place[2]
                if place_id not in unique_places:
                    unique_places[place_id] = place
            places = list(unique_places.values())
            print(places)
        candidate_places = get_candidate_places_for_embedding(embedding, places, k=3)
        print(f"Candidate places for embedding: {candidate_places}")
        candidates_per_embedding.append(candidate_places)
    print(f"Candidate places for the first embedding: {candidates_per_embedding[0]}")
    print(f"XY locations for the first embedding: {xy_locations_per_embedding[0]}")
    print(f"Candidate places for the second embedding: {candidates_per_embedding[1]}")
    print(f"XY locations for the second embedding: {xy_locations_per_embedding[1]}")