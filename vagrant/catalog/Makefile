# Run Flask app with tables filled by dummy data
all: clean setup fill run

# Run Flask app with empty tables
empty-run: clean setup run

# Re-create DB
init: clean setup

# Re-create DB and fill tables wit dummy data
reload: clean setup fill

# Delete all files related to DB
clean:
	-rm *.db database_setup.pyc

# Create DB
setup:
	python database_setup.py

# Fill tables with dummy data
fill:
	python lotsofcategories.py

# Run Flask app
run:
	python application.py
