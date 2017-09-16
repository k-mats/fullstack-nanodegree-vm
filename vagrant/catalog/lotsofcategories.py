from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Item

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create dummy data; Category
category1 = Category(name="Baseball")
category2 = Category(name="Tennis")
category3 = Category(name="Football")

session.add(category1)
session.add(category2)
session.add(category3)
session.commit()


# Create dummy data; Item
item11 = Item(category_id=1, name="Baseball bat", description="A baseball bat is a smooth wooden or metal club used in the sport of baseball to hit the ball after it is thrown by the pitcher. ")  # noqa
item12 = Item(category_id=1, name="Baseball glove", description="A baseball glove or mitt is a large leather glove worn by baseball players of the defending team, which assists players in catching and fielding balls hit by a batter or thrown by a teammate.")  # noqa
item13 = Item(category_id=1, name="Batting helmet", description="A batting helmet is worn by batters in the game of baseball or softball. It is meant to protect the batter's head from errant pitches thrown by the pitcher.")  # noqa
item14 = Item(category_id=1, name="Ball (Baseball)", description="A baseball is a ball used in the sport of the same name, baseball.")  # noqa

session.add(item11)
session.add(item12)
session.add(item13)
session.add(item14)
session.commit()

item21 = Item(category_id=2, name="Tennis racket", description="A racket or racquet is a sports implement consisting of a handled frame with an open hoop across which a network of strings or catgut is stretched tightly.")  # noqa
item22 = Item(category_id=2, name="Strings", description="In tennis, the strings are the part of a tennis racquet which make contact with the ball.")  # noqa
item23 = Item(category_id=2, name="Tennis ball", description="A tennis ball is a ball designed for the sport of tennis. Tennis balls are fluorescent yellow at major sporting events, but in recreational play can be virtually any color.")  # noqa

session.add(item21)
session.add(item22)
session.add(item23)
session.commit()

item31 = Item(category_id=3, name="Football helmet", description="The football helmet is a piece of protective equipment used mainly in American football and Canadian football.")  # noqa
item32 = Item(category_id=3, name="Shoulder pads", description="Shoulder pads are a piece of protective equipment used in many contact sports such as American football, Canadian football, lacrosse and hockey.")  # noqa
item33 = Item(category_id=3, name="Ball (Football)", description="A football is a ball inflated with air that is used to play one of the various sports known as football.")  # noqa

session.add(item31)
session.add(item32)
session.add(item33)
session.commit()


print "Added categories and items."
