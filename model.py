from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from geoalchemy2 import Geometry

app = Flask(__name__)
db = SQLAlchemy()


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


def connect_to_db(app):
    """Connect the database to Flask app."""

    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres:///geostuff'
    app.config['SQLALCHEMY_ECHO'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


if __name__ == "__main__":

    connect_to_db(app)
    db.create_all()
    print "Connected to database."
