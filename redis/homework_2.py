import redis
import datetime

#10 articles hashes
#10 timestamps sorted set
#10 scores sorted set
#6 voting histories set

ONE_WEEK_IN_SECONDS = 7 * 86400
VOTE_SCORE = 432

def article_vote(redis, user, article):
	cutoff = datetime.datetime.now() - datetime.timedelta(seconds=ONE_WEEK_IN_SECONDS)

	if not datetime.datetime.fromtimestamp(redis.zscore('time:', article)) < cutoff:
		article_id = article.split(':')[-1]
		if redis.sadd('voted:' + article_id, user):
			redis.zincrby(name='score:', value=article, amount=VOTE_SCORE)
			redis.hincrby(name=article, key='votes', amount=1)

def article_switch_vote(redis, user, from_article, to_article):
	cutoff = datetime.datetime.now() - datetime.timedelta(seconds=ONE_WEEK_IN_SECONDS)
	to_ = (not datetime.datetime.fromtimestamp(redis.zscore('time:', to_article)) < cutoff) 
	from_ = (not datetime.datetime.fromtimestamp(redis.zscore('time:', from_article)) < cutoff)
	#if both articles are within the cutoff
	if to_ and from_:
		vrem = 'voted:' + from_article.split(':')[-1]
		vadd = 'voted:' + to_article.split(':')[-1]	
		#verify user voting status on articles
		if redis.sismember(vrem, user) and not redis.sismember(vadd, user):
			#remove vote from from_article
			redis.srem(vrem, user)
			redis.zincrby(name='score:', value=from_article, amount=-1*VOTE_SCORE)
			redis.hincrby(name=from_article, key='votes', amount=-1)
			#add vote to to_article
			redis.sadd(vadd, user)
			redis.zincrby(name='score:', value=to_article, amount=VOTE_SCORE)
			redis.hincrby(name=to_article, key='votes', amount=1)


redis = redis.StrictRedis(host='localhost', port=6379, db=0)
# user:3 up votes article:1
article_vote(redis, "user:3", "article:1")
# user:3 up votes article:3
article_vote(redis, "user:3", "article:3")
# user:2 switches their vote from article:8 to article:1
article_switch_vote(redis, "user:2", "article:8", "article:1")

# Which article's score is between 10 and 20?
article = redis.zrangebyscore("score:", 10, 20)
article = article[0]
print(redis.hget(article, "link"))
