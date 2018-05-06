# Put the use case you chose here. Then justify your database choice:
# I chose to use the Instagram use-case. I used neo4j with this because as a social network, most of the meaningful insights are derived from relations between entities (users and posts). 
#
# Explain what will happen if coffee is spilled on one of the servers in your cluster, causing it to go down.
# In my current implementation, I would lose all my data because I am not using the right kind of driver to support neo4j's causal clustring. However, if this were deployed, there are redundencies of the core clusters, so if coffee was spilled on one of the core servers, another server would have a copy of that. Neo4j confirms that each core server has a copy of the data as a part of each transaction, so it is guaranteed to be up-to-date.
#
# What data is it not ok to lose in your app? What can you do in your commands to mitigate the risk of lost data?
# As a photo-sharing app with social network features, none of this is incredibly crucial as far as data loss goes, compared to an application that actually involved money of some kind. However, some operations, such as creating a node for a photo and creating the relationship that links it to its poster. In order to make sure these execute together, they are not separated by a semi-colon, so neo4j treats them as a transaction, and will only execute one if the other goes through as well.  
#

from neo4j.v1 import GraphDatabase
from uuid import uuid1
from datetime import datetime

class Connection():
	def __init__(self):
		self.driver = GraphDatabase.driver('bolt://localhost:7687', auth=("neo4j", "test"))
		
	def populate(self):
		self.clear()
		users =  ['Kylie', 'Kylie Cosmetics', 'Dana', 'Katrina']
		following = {'Kylie': ['Kylie Cosmetics'], 'Dana': ['Katrina'], 'Kylie Cosmetics':['Kylie'], 'Katrina': ['Dana', 'Kylie']}
		photos = {'Kylie':[('paradise',[],datetime.strptime('05/04/18 01:43','%m/%d/%y %H:%M'))], 'Kylie Cosmetics':[('check out my new lipkits', ["Kylie"], datetime.strptime('05/03/18 15:21','%m/%d/%y %H:%M'))], 'Dana':[('as requested',[],datetime.strptime('05/06/18 16:07','%m/%d/%y %H:%M')),('tb to 11th grade', ["Katrina"], datetime.strptime('05/02/18 10:32','%m/%d/%y %H:%M'))]}
		for a in users:
			self.new_user(a)
		for a, l in following.iteritems():
			for t in l:
				self.follow_user(a, t)
		for k, v in photos.iteritems():
			for p in v:
				cap, tags, ts = p
				self.post_photo(k, cap, tags, ts)
		with self.driver.session() as session:
			results = session.run("MATCH (p:Photo)-[:BELONGS_TO]->(n:User) WHERE n.name = 'Dana' OR n.name = 'Kylie' RETURN p.id, p.caption;")
			for record in results:
				uuid = record['p.id']
				caption = record['p.caption']
				if 'tb to' in caption:
					self.comment_on_photo('Katrina', uuid, 'whyy')
				self.like_photo('Katrina', uuid)
			results = session.run("MATCH (p:Photo)-[:BELONGS_TO]->(n:User) WHERE n.name = 'Kylie Cosmetics' RETURN p.id;")
			for record in results:
				uuid = record['p.id']
				self.like_photo('Kylie', uuid)
				self.repost_photo('Kylie', uuid, datetime.strptime('05/03/18 15:23','%m/%d/%y %H:%M'))

	def clear(self):
		with self.driver.session() as session:
			session.run("""MATCH (n)
					DETACH DELETE n;""")

	def new_user(self, name):
		with self.driver.session() as session:
			session.run("CREATE (a:User {name: $name});", name=name)
	
	def post_photo(self, name, caption = "", tags = [], ts = None):
		with self.driver.session() as session:
			uuid = str(uuid1())
			if ts:
				time = int(ts.strftime('%s'))
			else:
				time = int(datetime.now().strftime('%s'))
			session.run("""MATCH (n:User)
						WHERE n.name = $name
						CREATE (p:Photo {id: $uuid, caption: $caption})
						CREATE UNIQUE (p)-[:BELONGS_TO {timestamp: $time}]->(n);""", name = name, uuid = uuid, caption = caption, time = time)
			for tagged in tags:
				session.run("""MATCH (p:Photo),(t:User)
							WHERE p.id = $uuid AND t.name = $tagged
							CREATE UNIQUE (p)-[:CONTAINS]->(t);""", uuid = uuid, tagged = tagged)


	def like_photo(self, name, photoid):
		with self.driver.session() as session:
			session.run("""MATCH (n:User), (p:Photo)
						WHERE n.name = $name AND p.id = $uuid
						CREATE UNIQUE (n)-[:LIKES]->(p)""", name = name, uuid = photoid)

	def comment_on_photo(self, name, photoid, comment):
		with self.driver.session() as session:
			session.run("""MATCH (n:User), (p:Photo)
						WHERE n.name = $name AND p.id = $uuid
						CREATE (n)-[:COMMENT {content: $comment}]->(p);""", name = name, uuid = photoid, comment = comment)

	def repost_photo(self, name, photoid, ts = None):
		with self.driver.session() as session:
			if ts:
				time = int(ts.strftime('%s'))
			else:
				time = int(datetime.now().strftime('%s'))
			session.run("""MATCH (n:User), (p:Photo) WHERE n.name = $name AND p.id = $uuid
						CREATE (p)-[:REPOSTED_BY {timestamp: $time}]->(n);""", name = name, uuid = photoid, time = time)

	def follow_user(self, name, to_follow):
		with self.driver.session() as session:
			session.run("""MATCH (a:User), (t:User)
						WHERE a.name = $name AND t.name = $to
						CREATE UNIQUE (a)-[r:FOLLOWS]->(t)
						RETURN type(r);""", name = name, to = to_follow)
						
	def get_feed(self, name, days_to_fetch = None):
		if days_to_fetch:
			timestamp = int(datetime.now().strftime('%s')) - days_to_fetch*24*3600
		else:
			timestamp = 0
		with self.driver.session() as session:
			results = session.run("""MATCH (a:User)-[:FOLLOWS]->(b:User)<-[r:BELONGS_TO]-(p:Photo) 
						WHERE a.name = $name AND r.timestamp > $timestamp RETURN r.timestamp, b.name, p.id, p.caption ORDER BY r.timestamp DESC;""", name = name, timestamp = timestamp)
		return [[str(result['p.id']),str(datetime.fromtimestamp(result['r.timestamp']).strftime('%m/%d/%y %H:%M')), str(result['b.name']), str(result['p.caption'])] for result in results]
	
	def get_profile(self, name):
		with self.driver.session() as session:
			results = session.run("""MATCH (a:User)<-[r:BELONGS_TO]-(p:Photo)
						WHERE a.name = $name RETURN r.timestamp, p.id, p.caption ORDER BY r.timestamp DESC;""", name = name)
		return [[str(result['p.id']),str(datetime.fromtimestamp(result['r.timestamp']).strftime('%m/%d/%y %H:%M')), str(result['p.caption'])] for result in results]
	
	def get_tagged(self,name):
		with self.driver.session() as session:
			results = session.run("""MATCH (a:User)<-[:CONTAINS]-(p:Photo)-[r:BELONGS_TO]->(b:User)
						WHERE a.name = $name RETURN r.timestamp, b.name, p.id, p.caption ORDER BY r.timestamp DESC;""", name = name)
		return [[str(result['p.id']),str(datetime.fromtimestamp(result['r.timestamp']).strftime('%m/%d/%y %H:%M')), str(result['b.name']), str(result['p.caption'])] for result in results]

a = Connection()
a.populate()

# Action 1: Kylie posts a new photo
a.post_photo('Kylie')

# Action 2: Katrina checks her feed 
feed = a.get_feed('Katrina', 7)

# Action 3: Dana posts a new photo and tags Katrina
a.post_photo('Dana', "can't wait to see you in NY", ['Katrina'])

# Action 4: Katrina scrolls through her feed, and likes all of Dana's posts
for post in feed:
	print(post[1:])
	if 'Dana' == post[2]:
		a.like_photo('Katrina', post[0])
print('\n')

# Action 5: Katrina refreshes her feed and reshares the first item in her feed (Dana's new post)
feed = a.get_feed('Katrina', 7)
post = feed[0]
a.repost_photo('Katrina', post[0])

# Action 6: Katrina checks Kylie Cosmetics' page, and follows them
feed = a.get_profile('Kylie Cosmetics')
for post in feed:
	print(post[1:])
a.follow_user('Katrina', "Kylie Cosmetics")
print('\n')

# Action 7: Victoria signs up for an account and follows Katrina
a.new_user('Victoria')
a.follow_user('Victoria', 'Katrina')

# Action 8: Victoria looks through Katrina's tagged photos
feed = a.get_tagged('Katrina')
for post in feed:
	print(post[1:])



