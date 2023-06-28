from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# an Engine, which the Session will use for connection
# resources
engine = create_engine('postgresql://caronabot:2YNbgzSGooWvRE7qj5DSPoj6UVacpYnH@dpg-chr3q5grddlba9q0srkg-a.oregon-postgres.render.com/caronabot')

Session = sessionmaker(engine)
