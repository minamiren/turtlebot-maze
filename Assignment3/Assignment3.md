## Code locations:
pgvector + AGE schema
- This is in /detector/database/graph.py

Embedding generator
- This is in crop_image() in /detector/event_subscriber.py 
- Being inserted into the postgresql database in /detector/database/postgresql.py

Graph builder
- Also located in /detector/database/graph.py 

Semantic relocalizer
- Likely to be located in /detector/database/relocalize.py

Demo report with success and failure analysis
- As follows:

At the beginning, I started with a very small graph with only a few observations, objects, and places. This is mostly to ensure that the code actually works in its entirely. To be doubly sure, I am actually doing semantic localization on embeddings that I used to populate my graph, so I expect very high results. I did manage to get the results as expected:

- Candidate places for the first embedding: [(0, -0.061957284399356646, -0.5927830227034773, 'car', 0.9999999999999998)]
- XY locations for the first embedding: (-0.061957284399356646, -0.5927830227034773)
- Candidate places for the second embedding: [(0, -0.061957284399356646, -0.5927830227034773, 'bicycle', 1.0)]
- XY locations for the second embedding: (-0.061957284399356646, -0.5927830227034773)

Both nodes were found in place 0, as expected, because the observations were taken in nearly the same location. We can see an exact match for the second embedding, implying that the object node was only connected to a single observation, the one that I am using to find the place. The car was likely at least two slightly different observations, as the similarity scores is not entirely exact. For the purposes of picking up observations more quickly, I disabled the restriction on distance, so many of the added observations have identical embeddings.

Obviously, when doing semantic localization, we will get good results if we are getting our results with observations that were used to populate the graph. The next step is to populate this graph further with more nodes and verify with a second run whether or not we can still create a pose estimate.

Redo, this time with a few extra nodes in the graph and with embedding snapshots not included within the graph:

- Candidate places for the first embedding: [(0, -0.02817768024925916, -0.612270983703955, 'bicycle', 0.9902544339027377)]
- XY locations for the first embedding: (-0.08330290389524445, -0.5291078678004287)
- Candidate places for the second embedding: [(0, -0.02817768024925916, -0.612270983703955, 'bicycle', 0.9902544339027377)]
- XY locations for the second embedding: (-0.08330290389524445, -0.5291078678004287)

Finally, I repopulate the graph to have keyfrmaes and observations in all of the three main rooms. I tweak the dbscan variables so that I receive what feels like a 'reeasonable' number of places, and since I have three main rooms, three places felt reasonable. Next I gather a few observations that I do not populate the graph with in order to check the location candidates. 

### Final candidate results
- Candidate places for the first embedding: [(0, 1.8727965108704832, -0.0467024987460683, 'chair', 0.9617092087379001), (0, 0.2878011392072061, -0.6919949292239563, 'chair', 0.9617092087379001), (0, 0.3199800443919476, 1.8684966155557177, 'chair', 0.9617092087379001)]
- XY locations for the first embedding: (-0.7889262280987567, -1.243690713722371)
- Candidate places for the second embedding: [(0, 1.8727965108704832, -0.0467024987460683, 'bed', 0.9590995517137213), (0, 1.8727965108704832, -0.0467024987460683, 'cake', 0.9573520445893545), (0, 0.2878011392072061, -0.6919949292239563, 'cake', 0.9573520445893545)]
- XY locations for the second embedding: (-0.7889262280987567, -1.243690713722371)

You'll note that all of these results are for the same place with different XY coordinates and classname; this is because I separated my places based on which object localization fed into them where the centroid was taken based on the object localization--I felt as if I could get more specific localizations in that case, although my results ultimately were not very good. 

Otherwise the results are as follows:

- Candidate places for the first embedding: [(0, 1.8727965108704832, -0.0467024987460683, 18.29593943885792)]
- XY locations for the first embedding: (-0.7889262280987567, -1.243690713722371)
- Candidate places for the second embedding: [(0, 1.8727965108704832, -0.0467024987460683, 18.069031359041745)]
- XY locations for the second embedding: (-0.7889262280987567, -1.243690713722371)

There is only one candidate place for each embedding because all of the top ten det_pks were located in the same place, so there were not a series of places to compare against; therefore, the first set of results is somewhat more interesting. 

I know that my observations were a bycicle and a car, not a chair or bed, so the class name here is not remotely correct. Additionally, we can see that the location assumption is totally off is well; this is because the embedding similarity was so high for both chair and bed, that our position localization was assumed to be in the bottom-right room that my chair and bed detections happened in, as opposed to the bottom left room where the bycicle and car are. We definitely saw better results in the previous runs, rather than this one. I followed the code back and found that the result comes from attempting to choose the most similar detections; for whatever reason, finding similar embeddings is very difficult. This results in bad location predictions. I would have expected lower similarity summations, but they are interestingly high even despite knowing there is an object mismatch.  Given how promising the smaller iterations were, I was hoping that the results would be better. Unfortunately, it appears to be very difficult to compare different embeddings and find similarities. It is possible that I would need dozens more nodes in the graph before I would be able to make a better pose estimation, because I might have a better embedding match. 

### Stats for observation, objects, and places in the graph:
First graph stats:

- Total keyframe count: 5
- Total observation count: 10
- Total object count: 2
- Total place count: 1

Final graph stats:
- Total keyframe count: 12
- Total observation count: 30
- Total object count: 8
- Total place count: 3