from backend.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
columns = inspector.get_columns('incidents')
for column in columns:
    print(column['name'])
