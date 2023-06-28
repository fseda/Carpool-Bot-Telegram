from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

db_uri = os.environ['DB_URI']

# an Engine, which the Session will use for connection
# resources
engine = create_engine(db_uri)

Session = sessionmaker(engine)
