
1) NAMES:
	Husam Abdul-Kafi - hsa2136
	Qitong Liu - ql2257

2) PosgreSQL Account:
	psql -U ql2257 -h w4111a.eastus.cloudapp.azure.com proj1part2

3) Three Interesting SQL Queries:

The following will get the videos that are in the top 10 of the hightest ratio of likes to dislikes amongst the videos the channels User 0 subscribes to uploaded or liked.  

(SELECT v1.video_id, v1.title, v1.dislike_count, v1.like_count, v1.view_count, v1.like_count/(1 + v1.dislike_count) AS ratio
FROM uploaded_by ub1, video v1
WHERE v1.video_id = ub1.video_id AND ub1.c_id IN (SELECT st1.c_id
FROM subscribes_to st1
WHERE st1.user_id = 0))
UNION
(SELECT v.video_id, v.title, v.dislike_count, v.like_count, v.view_count, v.like_count/(1 + v.dislike_count) AS ratio
FROM likes_2 ub, video v
WHERE v.video_id = ub.video_id AND ub.c_id IN (SELECT st.c_id
FROM subscribes_to st
WHERE st.user_id = 0))
ORDER BY ratio DESC
LIMIT 10;


The following will get the videos that are in the top 10 by like count using the same criteria as above.

(SELECT v1.video_id, v1.title, v1.dislike_count, v1.like_count, v1.view_count
FROM uploaded_by ub1, video v1
WHERE v1.video_id = ub1.video_id AND ub1.c_id IN (SELECT st1.c_id
FROM subscribes_to st1
WHERE st1.user_id = 0))
UNION
(SELECT v.video_id, v.title, v.dislike_count, v.like_count, v.view_count
FROM likes_2 ub, video v
WHERE v.video_id = ub.video_id AND ub.c_id IN (SELECT st.c_id
FROM subscribes_to st
WHERE st.user_id = 0))
ORDER BY like_count DESC
LIMIT 10;


The following two queries will get the total number of views/likes on the videos uploaded by each channel in the channel list.

SELECT ub.c_id, SUM(view_count) AS total_views
FROM video v, uploaded_by ub
WHERE v.video_id = ub.video_id
GROUP BY ub.c_id;


SELECT ub.c_id, SUM(like_count) AS total_likes
FROM video v, uploaded_by ub
WHERE v.video_id = ub.video_id
GROUP BY ub.c_id;

