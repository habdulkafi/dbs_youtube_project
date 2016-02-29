import pandas
from sqlalchemy import create_engine

engine = create_engine("postgresql://ql2257:3368@w4111a.eastus.cloudapp.azure.com/proj1part2")

cur = engine.connect()

df = pandas.read_sql("SELECT * FROM channel",con=engine)

df["c_id"]
list(df["c_id"])