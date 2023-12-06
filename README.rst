A few of my students wanted to use PostGIS to help them easily query a Postgres
database for all the points within a certain distance of a given location. 
Getting them up and running proved a bit of a struggle, so I decided to put
together a little tutorial for others who might be interested.

The first half of this tutorial covers working with PostGIS in pure SQL, and
the second half covers using PostGIS in Python with SQLAlchemy, GeoAlchemy2, and
Flask-SQLAlchemy. If none of the Python bits interest you, then you can still
learn something from the material before the "Use PostGIS with SQLAlchemy"
section. :)


Prerequisites
=============

You should have Postgres, Python, pip, and virtualenv installed on your 
to complete this tutorial. For the Python bit, I used Python 2.7.

Since PostGIS is the focus of this tutorial, I also assume you have some
experience using SQLAlchemy for the ORM portion. 


PostGIS Installation
====================

I assume you've already installed Postgres itself on your machine and that
you've figured out how to set up the ``psql`` command to run Postgres from
the command line.

For all operating systems, first open the Postgres command line interface:

.. parsed-literal::

    $ psql <your database name>
    
From inside the command line interface, use the ``CREATE EXTENSION`` syntax
desrcibed on the PostGIS website to try to add the PostGIS extension to your
database.

.. code-block:: sql

    CREATE EXTENSION postgis;

If you see an error along the lines of: 

**ERROR:  could not open extension control file "path/to/file": No such file or directory**

then you don't have PostGIS installed yet. Fortunately, the `setup instructions 
on the PostGIS website <http://postgis.net/install/>`_ are pretty straightforward. 
Since I've installed PostGIS on OSX and Ubuntu, however, I do some advice there. 


OSX Tip
-------

I highly recommend using the `Postgres.app <http://postgresapp.com/>`_ version of 
Postgres, as it comes with PostGIS already.


Ubuntu Tip
----------

If your version of Postgres doesn't include PostGIS, then you're likely just an 
``apt-get`` away from having it. Run:

.. parsed-literal::

    sudo apt-get install postgis

If you run into an error that mentions some dependencies not getting installed,
update apt-get:

.. parsed-literal::

    sudo apt-get update

And then try installing again.

`This link <http://trac.osgeo.org/postgis/wiki/UsersWikiPostGIS23UbuntuPGSQL96Apt>`_ 
(found originally on the PostGIS website) was pretty helpful.


However you arrive at your PostGIS installation, you should now be able to run
the ``CREATE EXTENSION`` command. Go into `psql` now and try it.


Start With Pure SQL
===================

Once you have PostGIS set up, I suggest tinkering around in pure SQL for a bit
so you're familiar with how querying should work. 

Go into `psql` now and make yourself a table to play around with. I kept mine
simple:

.. code-block:: sql

    CREATE TABLE cities (                                                             
        point_id SERIAL PRIMARY KEY,
        location VARCHAR(30),
        latitude FLOAT,
        longitude FLOAT,
        geo geometry(POINT)
    );

This SQL creates a table called cities with an automatically incrementing 
integer primary key. It has a column for the location (limited to 30 characters
long), the latitude, and the longitude. The geo column is where our PostGIS
point data will go. I chose to use the geometry type here because I read that
it would be the simplest to work with. 


Get Data
--------

Next, add some data to your table. You could do this by hand with `INSERT` 
statements, or you could load data from a CSV file that includes latitudes and 
longitudes.


Copy from a CSV File
++++++++++++++++++++

To save you some manual typing, I'll show you how to get some seed data from
a CSV file to start.

First, find yourself a CSV file. You could do a quick search on a site like
`ProgrammableWeb <https://www.programmableweb.com/>`_ for some data that intrigues 
you, or you can copy this CSV-formatted text:

.. parsed-literal::

    location, latitude, longitude
    San Francisco, 37.773972, -122.43129
    Seattle, 47.608013, -122.335167
    Sacramento, 38.575764, -121.478851
    Oakland, 37.804363, -122.271111
    Los Angeles, 34.052235, -118.243683
    Alameda, 37.7652, -122.2416 

Notice that while the `cities` table has a `geo` column, this data lacks
information for that column. That's perfectly fine; in fact, it's intentional.

If you copy this example data, just paste it into a file with the `.csv` 
extension. I called mine `postgis.csv`.

Once you have a CSV file, go back to your `psql` shell and enter the following
command to load the data into your `cities` table:

.. code-block:: sql

    \copy cities(location, latitude, longitude) FROM 'postgis.csv' DELIMITERS ',' CSV HEADER;

This uses Postgres' `copy` command to fill the location, latitude, and longitude
columns in the `cities` table with the corresponding data from the CSV file. I
was able to just give a filename because the file was in the directory I was in
when I opened the `psql` shell; if your CSV isn't in your current working
directory, then you'll need to give a full file path. The `DELIMITERS` value
tells Postgres what the data is separated by, CSV indicates the file type, and
HEADER indicates that the file has column headers.

After seeding with this information, try selecting everything from the `cities`
table:

.. code-block:: sql
   
    SELECT * FROM cities;

You should see output like this:

.. parsed-literal::

     point_id |   location    | latitude  |  longitude  | geo 
    ----------+---------------+-----------+-------------+-----
            1 | San Francisco | 37.773972 |  -122.43129 | 
            2 | Seattle       | 47.608013 | -122.335167 | 
            3 | Sacramento    | 38.575764 | -121.478851 | 
            4 | Oakland       | 37.804363 | -122.271111 | 
            5 | Los Angeles   | 34.052235 | -118.243683 | 
            6 | Alameda       |   37.7652 |   -122.2416 | 
    (6 rows)


Fill in the Geometry Column
+++++++++++++++++++++++++++

Now that you have some latitudes and longitudes to work with, let's get some
data into that `geo` column. Run the following `UPDATE` command:

.. code-block:: sql

    UPDATE cities
    SET geo = ST_Point(longitude, latitude);

The `ST_Point` function takes a longitude and a longitude and creates a blob
that represents that point in a given coordinate system. By default, ST_Point
uses the `WGS84 <http://gisgeography.com/wgs84-world-geodetic-system/>`_ format, 
which is the same standard used for GPS. You can read more about `ST_Point` in
`the PostGIS docs <https://postgis.net/docs/ST_Point.html>`_ 

(If you need to use a different coordinate system, you'll need to change the
spatial reference system identifier (srid) on your column. The `ST_SetSRID function <https://postgis.net/docs/ST_SetSRID.html>`_ can help with that.)

If you select everything from cities, you should now see output like this:

.. parsed-literal::

     point_id |   location    | latitude  |  longitude  |                    geo                     
    ----------+---------------+-----------+-------------+--------------------------------------------
            1 | San Francisco | 37.773972 |  -122.43129 | 0101000000E1455F419A9B5EC08602B68311E34240
            2 | Seattle       | 47.608013 | -122.335167 | 0101000000B3EC496073955EC07C45B75ED3CD4740
            3 | Sacramento    | 38.575764 | -121.478851 | 01010000000B2AAA7EA55E5EC0691B7FA2B2494340
            4 | Oakland       | 37.804363 | -122.271111 | 01010000007FA5F3E159915EC0658EE55DF5E64240
            5 | Los Angeles   | 34.052235 | -118.243683 | 0101000000D6E59480988F5DC0715AF0A2AF064140
            6 | Alameda       |   37.7652 |   -122.2416 | 0101000000ACADD85F768F5EC01973D712F2E14240
    (6 rows)

Cool! We've got some data. Don't worry if you can't make any sense of the
contents of the `geo` column. PostGIS will take care of it.


Insert a Point with Geometry Data
+++++++++++++++++++++++++++++++++

Eventually, you might also want to add a new city complete with its geometry
data without using an `UPDATE` statement. Here's how:

.. code-block:: sql

    INSERT INTO cities (location, latitude, longitude, geo)
    VALUES ('San Bruno', 37.6305, -122.4111, 'POINT(-122.4111 37.6305)');

The string passed for the `geo` column is written in `Well-Known Text 
<https://en.wikipedia.org/wiki/Well-known_text>`_, a language used to 
communicate vector geometries.

You could also make your point like this:

.. code-block:: sql

    INSERT INTO cities (location, latitude, longitude, geo)
    VALUES ('San Rafael', 37.9735, -122.5311, ST_Point(-122.5311, 37.9735));

Here, the `ST_Point` function makes a point out of the longitude and latitude.


Query For Points Within a Given Radius
--------------------------------------

Now that you have some geospatial data stored with PostGIS, you can ask for
all points within a given distance of a particular point. Let's ask for all
cities within 50 miles of San Francisco.

.. code-block:: sql

    SELECT * FROM cities
    WHERE ST_Distance_Sphere(geo, 
        (SELECT geo FROM cities WHERE location = 'San Francisco')
    ) < 83000;

The `ST_Distance_Sphere` gives a linear distance between two given points, as
described `here <https://postgis.net/docs/manual-1.4/ST_Distance_Sphere.html>`_.
The distance it returns is in meters, so if you're working in miles, you'll 
need to convert. I used an SQL subquery to get San Francisco's geometry blob,
but you could hard code, too.

Your results should look something like this:

    .. parsed-literal:: 

         point_id |   location    | latitude  |  longitude  |                    geo                     
        ----------+---------------+-----------+-------------+--------------------------------------------
                1 | San Francisco | 37.773972 |  -122.43129 | 0101000000E1455F419A9B5EC08602B68311E34240
                4 | Oakland       | 37.804363 | -122.271111 | 01010000007FA5F3E159915EC0658EE55DF5E64240
                6 | Alameda       |   37.7652 |   -122.2416 | 0101000000ACADD85F768F5EC01973D712F2E14240
                8 | San Rafael    |   37.9735 |   -122.5311 | 0101000000F5B9DA8AFDA15EC0F853E3A59BFC4240
                9 | San Bruno     |   37.6305 |   -122.4111 | 0101000000AED85F764F9A5EC062105839B4D04240
        (5 rows)

Sacramento, Los Angeles, and Seattle have all been filtered out, as they should. 
Hooray!

From here, I'll leave it to you to poke around the PostGIS docs a bit, try out
some other functions, and so on. When you're ready to try integrating PostGIS
with SQLAlchemy, read on.


Use PostGIS with SQLAlchemy
===========================

If you don't want to live in a pure SQL world anymore, you can also use PostGIS
via an ORM. I'm most comfortable with SQLAlchemy after my work at Hackbright,
so that's what I'm using.


Install Packages
----------------

First, create a virtual environment, activate it, and install the following
requirements:

.. parsed-literal::

    click==6.7
    Flask==0.12.2
    Flask-SQLAlchemy==2.3.2
    GeoAlchemy2==0.4.0
    itsdangerous==0.24
    Jinja2==2.10
    MarkupSafe==1.0
    psycopg2==2.7.3.2
    SQLAlchemy==1.1.15
    Werkzeug==0.12.2

Flask-SQLAlchemy makes working with SQLAlchemy a bit nicer, and GeoAlchemy2 is
the package that allows us to use PostGIS.


Start Your Python File
----------------------

We'll need to import a few things and create a couple of global objects before
we can begin. Open a new Python file and add this to the top:

.. code-block:: python

    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy import func
    from geoalchemy2 import Geometry

    app = Flask(__name__)
    db = SQLAlchemy()

We need `Flask` to create an application context to bind our `SQLAlchemy` 
session to. The lowercase `sqlalchemy` (and lowercase is key here) import,
`func`, will allow us to execute PostGIS functions and other SQL functions 
that aren't exposed otherwise through the SQLAlchemy model. The `Geometry`
class imported from `geoalchemy2` will let us make our geospatial column.


Write a Model Class
-------------------

Now, let's make an SQLAlchemy model class to work with. Add this code to your
Python file:

.. code-block:: python

    class City(db.Model):
        """A city, including its geospatial data."""

        __tablename__ = "cities"

        point_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        location = db.Column(db.String(30))
        longitude = db.Column(db.Float)
        latitude = db.Column(db.Float)
        geo = db.Column(Geometry(geometry_type="POINT"))

        def __repr__(self):
            return "<City {name} ({lat}, {lon})>".format(
                name=self.location, lat=self.latitude, lon=self.longitude)

        def get_cities_within_radius(self, radius):
            """Return all cities within a given radius (in meters) of this city."""

            return City.query.filter(func.ST_Distance_Sphere(City.geo, self.geo) < radius).all()

        @classmethod
        def add_city(cls, location, longitude, latitude):
            """Put a new city in the database."""

            geo = 'POINT({} {})'.format(longitude, latitude)
            city = City(location=location,
                               longitude=longitude,
                               latitude=latitude,
                              geo=geo)

            db.session.add(city)
            db.session.commit()

        @classmethod
        def update_geometries(cls):
            """Using each city's longitude and latitude, add geometry data to db."""

            cities = City.query.all()

            for city in cities:
                point = 'POINT({} {})'.format(city.longitude, city.latitude)
                city.geo = point

            db.session.commit()

This model represents the same data as the `cities` table from earlier. It has
the same columns and types, but we define the type of the `geo` column using
GeoAlchemy2 syntax.

When I went through this process, I used the `\copy` command described in the
"Copy from a CSV File" section to get my city and point data into the table.
I tried to also use the `UPDATE` statement to add the geometries since I had it
conveniently typed out, but unfortunately, when I queried for objects in the
Python terminal, I only got back ``None`` for the `geo` column. I added the
`update_geometries()` method to create points as strings and add the geometries
through SQLAlchemy and GeoAlchemy2. It seems when you do this from
within the ORM, the geospatial data gets turned into a `WKElement` object when
it's added to the record.

The `get_cities_within_radius()` method shows the syntax for querying for all
points within a given radius (our stated goal at the beginning). Let's break it
down.

- SQLAlchemy's `func` lets us access the `ST_Distance_Sphere` function we used when we
  were still working in pure SQL.

- `ST_Distance_Sphere` takes two points and returns how far apart those points are.

From here, everything is just SQLAlchemy. We compare the number returned by
`ST_Distance_Sphere` against the passed radius, use that condition in a 
`filter` clause, query the whole table, and ask for all results found.


Necessary Boilerplate
---------------------

At the end of your Python file, add the following code to help you actually
use your model:

.. code-block:: Python

    def connect_to_db(app):
        """Connect the database to Flask app."""

        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres:///yourdatabasename'
        app.config['SQLALCHEMY_ECHO'] = False
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.app = app
        db.init_app(app)


    if __name__ == "__main__":

        connect_to_db(app)
        db.create_all()
        print "Connected to database."

The `connect_to_db()` function sets some config variables and connects
our app to the database. (Needed here because we're using Flask-SQLAlchemy.)
Be sure to replace "yourdatabasename" in the URI definition with the correct 
name for your database. The `ECHO` and `TRACK_MODIFICATIONS` variables are set 
to ``False`` to turn off some features for the moment. 

Under the ``if __name__ == "__main__"`` line, we tell Python to connect to the
database, create all tables, and give a helpful message when the file is 
run from the command line.

Run your model file interactively with ``python -i model.py`` now to make sure
your code runs without error.


Try it Out in the Terminal
--------------------------

At this point, you should have:

- Created a database

- Written a model.py file

- Loaded your model.py file in Python and connected to the database

Now, we can play with our city records in the terminal. Try these snippets
in the interactive console:

.. code-block:: python

    >>> for city in City.query.all():
    ...     print city
    ...     
    <City San Francisco (37.773972, -122.43129)>
    <City Seattle (47.608013, -122.335167)>
    <City Sacramento (38.575764, -121.478851)>
    <City Oakland (37.804363, -122.271111)>
    <City Los Angeles (34.052235, -118.243683)>
    <City Alameda (37.7652, -122.2416)>

    >>> sb = City(location='San Bruno', 
    ...           longitude=-122.4111, 
    ...           latitude=37.6305, 
    ...           geo='POINT(-122.4111 37.6305)')
    >>> db.session.add(sb)
    >>> db.session.commit()

    >>> sb.geo
    'POINT(-122.4111 37.6305)'

    >>> sf = db.session.query(City).filter(City.location == 'San Francisco').one()
    >>> sf
    <City San Francisco (37.773972, -122.43129)>

    >>> sr = City(location='San Rafael', 
    ...           longitude=-122.5311, 
    ...           latitude=37.9735, 
    ...           geo=func.ST_Point(-122.5311, 37.9735))
    >>> sr
    <City San Rafael (37.9735, -122.5311)>
    >>> sr.geo
    <sqlalchemy.sql.functions.Function at 0x107817150; ST_Point>
    >>> db.session.add(sr)
    >>> db.session.commit()
    >>> sr.geo
    <WKBElement at 0x107788a10; 0101000000f5b9da8afda15ec0f853e3a59bfc4240>

    >>> fifty_miles_in_meters = 83000
    >>> ten_miles_in_meters = 16093.4
    >>> nearish_cities = sf.get_cities_within_radius(ten_miles_in_meters)
    >>> farish_cities = sf.get_cities_within_radius(83000)

    >>> for city in nearish_cities:
    ...     print city
    ...     
    <City San Francisco (37.773972, -122.43129)>
    <City Oakland (37.804363, -122.271111)>
    <City San Bruno (37.6305, -122.4111)>

    >>> for city in farish_cities:
    ...     print city
    ...     
    <City San Francisco (37.773972, -122.43129)>
    <City Oakland (37.804363, -122.271111)>
    <City Alameda (37.7652, -122.2416)>
    <City San Bruno (37.6305, -122.4111)>
    <City San Rafael (37.9735, -122.5311)>

    >>> City.add_city("Sausalito", -122.4853, 37.8591)
    >>> City.add_city("Daly City", -122.4702, 37.6879)
    >>> City.add_city("San Jose", -121.8863, 37.3382)
    >>> City.add_city("Vallejo", -122.2566, 38.1041)
    >>> City.add_city("Orlando", -81.3815, 28.5469)
    >>> City.add_city("New York City", -73.9603, 40.7666)

    >>> cities_within_ten_miles = City.query.filter(
    ...     func.ST_Distance_Sphere(City.geo, sf.geo) < ten_miles_in_meters).all()
    >>> for city in cities_within_ten_miles:
    ...     print city
    ...     
    <City San Francisco (37.773972, -122.43129)>
    <City Oakland (37.804363, -122.271111)>
    <City San Bruno (37.6305, -122.4111)>
    <City Sausalito (37.8591, -122.4853)>
    <City Daly City (37.6879, -122.4702)>

    >>> # Order the cities by distance from SF.
    >>> cities_within_ten_miles = City.query.filter(
    ...     func.ST_Distance_Sphere(City.geo, sf.geo) < ten_miles_in_meters).order_by(
    ...     func.ST_Distance_Sphere(City.geo, sf.geo)).all()

    >>> for city in cities_within_ten_miles:
    ...     distance = db.session.query(func.ST_Distance_Sphere(city.geo, sf.geo)).one()[0]
    ...     print "{} is {} meters from SF".format(city.location, distance)
    ...     
    San Francisco is 0.0 meters from SF
    Daly City is 10164.110173 meters from SF
    Sausalito is 10588.2148564 meters from SF
    Oakland is 14475.5833668 meters from SF
    San Bruno is 16051.9613992 meters from SF

The cities ultimately returned by `get_cities_within_radius()` seem correct
enough to be getting on with, and when I ordered by the distance apart and printed
the distances, they seem close. Google Maps says Daly City is a 7.6 mile drive from
San Francisco, which converts to about 12231 meters. I'd believe that the drive
would take an extra couple thousand meters (about 1.2 miles) compared to a 
pure distance measurement.

If you've gotten this far, then congrats: you have PostGIS working with Flask and SQLAlchemy!

Resources
=========

I put together this tutorial after much debugging with fellow staff members
at Hackbright on a few student projects this cohort. We would likely have spent
much more time beating our heads against PostGIS without referencing a past
student project: `Joanne Yeung's Investable 
<https://github.com/jttyeung/investable/blob/master/postgis_setup_notes.txt>`_. 
Joanne's excellent documentation of the PostGIS setup process inspired me to 
take things a step further and actually write up a tutorial.

The rest of this section lists some docs, posts, and other resources I found 
helpful throughout the debugging process.


Read the Docs!
--------------

- `PostGIS <https://postgis.net/>`_
- `GeoAlchemy2 <https://geoalchemy-2.readthedocs.io/en/latest/>`_
- `SQLAlchemy <https://www.sqlalchemy.org/>`_


Helpful StackOverflow Posts
---------------------------

- `Querying for points within a certain distance
  <https://gis.stackexchange.com/questions/41242/finding-nearest-point-from-poi-in-postgis>`_

- `Inserting a point into PostGIS 
  <https://gis.stackexchange.com/questions/24486/inserting-point-into-postgis>`_

- `Usage of ST_SetSRID, etc. <https://gis.stackexchange.com/questions/24486/inserting-point-into-postgis>`_

- `Using ST_DWithin <https://stackoverflow.com/questions/23981056/geoalchemy-st-dwithin-implementation>`_ 
  (It wound up making more sense to use ST_Distance_Sphere instead, but this syntax example was helpful.)

- `Blog post where I got the idea to use a CSV and copy
  <http://www.kevfoo.com/2012/01/Importing-CSV-to-PostGIS/>`_

Hope you've found this tutorial helpful! @ me on Twitter or something if you did. :)
