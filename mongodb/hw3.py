# require the driver package
import pymongo
from pprint import pprint

# Create a client
client = pymongo.MongoClient()
db = client.test

collection = db.movies

# A. Update all movies with "NOT RATED" at the "rated" key to be "Pending rating". The operation must be in-place and atomic.

collection.update_many({'rated':'NOT RATED'},{'$set':{'rated':'Pending rating'}})

# B. Find a movie with your genre in imdb and insert it into your database with the fields listed in the hw description.

collection.insert_one({'title':'Generation Wealth', 'year':2018, 'countries':['USA'], 'genres':['Documentary'], 'directors':['Lauren Greenfield'], 'imdb':{'id':5268348, 'rating':5.5, 'votes':155}})

# C. Use the aggregation framework to find the total number of movies in your genre.

# Example result:
#  => [{"_id"=>"Comedy", "count"=>14046}]

out = collection.aggregate([{'$match': {'genres': 'Documentary'}}, {'$group': {'_id':'Documentary', 'count': {'$sum': 1}}}])
print(list(out))

# D. Use the aggregation framework to find the number of movies made in the country you were born in with a rating of "Pending rating".

out = collection.aggregate([{'$match': {'countries': 'China', 'rated': 'Pending rating'}}, {'$group': {'_id': "China + Pending rating", 'count': {'$sum': 1}}}])
print(list(out))

# Example result when country is Hungary:
#  => [{"_id"=>{"country"=>"Hungary", "rating"=>"Pending rating"}, "count"=>9}]


# E. Create an example using the $lookup pipeline operator. See hw description for more info.

db.cust.insert_many([{'name': 'Victoria', 'age': 19, 'unit': 3203},{'name': 'Katrina', 'age':18, 'unit': 1728}])
db.order.insert_many([{'unit': 3203, 'price':35.23, 'quantity':2}, {'unit':1728, 'price':18.32, 'quantity': 1}, {'unit':3203, 'price':12.56, 'quantity':1}])

out = db.order.aggregate([{'$lookup': {'from': 'cust', 'localField': 'unit', 'foreignField': 'unit', 'as': 'customer'}}])
for entry in out:
	pprint(entry)
