import pandas
from sqlalchemy import create_engine

engine = create_engine("postgresql://ql2257:3368@w4111a.eastus.cloudapp.azure.com/proj1part2")

cur = engine.connect()

df = pandas.read_sql("SELECT * FROM channel",con=engine)

for c_id in list(df["c_id"]):
	user_id = [0,1] * 5
	q = "INSERT INTO subscribes_to VALUES ('" + user_id + "','" + c_id + "')" 
	cur.execute(q)
