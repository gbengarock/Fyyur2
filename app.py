#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import psycopg2
from models import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format = "EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format = "EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    venues = db.session.query(Venue).all()
    data = []
    areas = Venue.query.with_entities(Venue.city, Venue.state).distinct().all()
    for cities in areas:
        city = cities[0]
        state = cities[1]
        venue = Venue.query.filter_by(city=city, state=state).all()
        data.append({
            "city": city,
            "state": state,
            "venues": venue
            })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    search_results = Venue.query.filter(Venue.name.ilike(
        f"%{search_term}%")).all()
    data = []

    for venue in search_results:
        data.append({
            "id": venue.id,
            "name": venue.name,
            })

    response = {
            'count': len(search_results),
            'data': data
            }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    venues = Venue.query.get(venue_id)
    all_past_shows = db.session.query(Show).join(Venue).filter(Show.venue_id == venue_id).filter(
        Show.start_time < datetime.now()).all()
    all_upcoming_shows = db.session.query(Show).join(Venue).filter(Show.venue_id == venue_id).filter(
        Show.start_time > datetime.now()).all()

    data = []

    past_shows = []
    for past_show in all_past_shows:
        past_shows.append({
            "artist_id": past_show.artist_id,
            "artist_name": past_show.artist.name,
            "artist_image_link": past_show.artist.image_link,
            "start_time": str(past_show.start_time)
            })

    upcoming_shows = []
    for upcoming_show in all_upcoming_shows:
        upcoming_shows.append({
            "artist_id": upcoming_show.artist_id,
            "artist_name": upcoming_show.artist.name,
            "artist_image_link": upcoming_show.artist.image_link,
            "start_time": str(upcoming_show.start_time)
            })

    data.append({
        "id": venues.id,
        "name": venues.name,
        "genres": venues.genres,
        "city": venues.city,
        "state": venues.state,
        "phone": venues.phone,
        "address": venues.address,
        "website_link": venues.website_link,
        "facebook_link": venues.facebook_link,
        "seeking_talent": venues.seeking_talent,
        "seeking_description": venues.seeking_description,
        "image_link": venues.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    })
    data = list(filter(lambda d: d['id'] == venue_id, data))[0]
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)
    try:
        if request.method == 'POST':
            venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website_link=form.website_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data
                )
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except error:
        db.session.rollback()
        flash('An error occurred. Venue '
              + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        delete_venue = Venue.query.get(venue_id)
        db.session.delete(delete_venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was Deleted Successfully')
    except error:
        db.session.rollback()
        flash('Venue ' + request.form['name'] + ' not deleted')
    finally:
        db.session.close()

    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():

    data = Artist.query.all()

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    search_results = Artist.query.filter(Artist.name.ilike(
        f"%{search_term}%")).all()
    data = []

    for artist in search_results:
        data.append({
                "id": artist.id,
                "name": artist.name,
                })

    response = {
                'count': len(search_results),
                'data': data
                }

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artists = Artist.query.get(artist_id)
    all_past_shows = db.session.query(Show).join(Artist).filter(Show.artist_id == artist_id).filter(
        Show.start_time < datetime.now()).all()
    all_upcoming_shows = db.session.query(Show).join(Artist).filter(Show.artist_id == artist_id).filter(
        Show.start_time > datetime.now()).all()

    data = []

    past_shows = []
    for past_show in all_past_shows:
        past_shows.append({
                "venue_id": past_show.venue_id,
                "venue_name": past_show.venue.name,
                "venue_image_link": past_show.venue.image_link,
                "start_time": str(past_show.start_time)
            })

    upcoming_shows = []
    for upcoming_show in all_upcoming_shows:
        upcoming_shows.append({
                "venue_id": upcoming_show.venue_id,
                "venue_name": upcoming_show.venue.name,
                "venue_image_link": upcoming_show.venue.image_link,
                "start_time": str(upcoming_show.start_time)
            })

    data.append({
        "id": artists.id,
        "name": artists.name,
        "genres": artists.genres,
        "city": artists.city,
        "state": artists.state,
        "phone": artists.phone,
        "website_link": artists.website_link,
        "facebook_link": artists.facebook_link,
        "seeking_venue": artists.seeking_venue,
        "seeking_description": artists.seeking_description,
        "image_link": artists.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    })
    data = list(filter(lambda d: d['id'] == artist_id, data))[0]
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).first()
    form = ArtistForm(obj=artist)

  # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist_id)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)
    update_artist = Artist.query.get_or_404(artist_id)
    try:
        if request.method == 'POST':
            update_artist.name = form.name.data
            update_artist.genres = form.genres.data
            update_artist.city = form.city.data
            update_artist.state = form.state.data
            update_artist.phone = form.phone.data
            update_artist.website_link = form.website_link.data
            update_artist.facebook_link = form.facebook_link.data
            update_artist.seeking_venue = form.seeking_venue.data
            update_artist.seeking_description = form.seeking_description.data
            update_artist.image_link = form.image_link.data
            db.session.commit()
        flash("Artist was successfully updated")
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Artist '
              + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).first()
    form = VenueForm(obj=venue)

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    update_venue = Venue.query.get_or_404(venue_id)
    try:
        if request.method == 'POST':
            update_venue.name = form.name.data
            update_venue.genres = form.genres.data
            update_venue.address = form.address.data
            update_venue.city = form.city.data
            update_venue.state = form.state.data
            update_venue.phone = form.phone.data
            update_venue.website_link = form.website_link.data
            update_venue.facebook_link = form.facebook_link.data
            update_venue.seeking_talent = form.seeking_talent.data
            update_venue.seeking_description = form.seeking_description.data
            update_venue.image_link = form.image_link.data

        db.session.commit()
    except error:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)
    try:
        artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            genres=form.genres.data,
            facebook_link=form.facebook_link.data,
            image_link=form.image_link.data,
            website_link=form.website_link.data,
            seeking_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data
            )
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except error:
        db.session.rollback()
        flash('An error occurred. Artist '
              + data.name + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = db.session.query(Show).join(Artist).join(Venue).all()

    data = []
    for show in shows:
        data.append({
          "venue_id": show.venue_id,
          "venue_name": show.venue.name,
          "artist_id": show.artist_id,
          "artist_name": show.artist.name,
          "artist_image_link": show.artist.image_link,
          "start_time": str(show.start_time)
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    try:
        show = Show(
            artist_id=form.artist_id.data,
            venue_id=form.venue_id.data,
            start_time=form.start_time.data
            )
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except error:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
# '''
# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 5000))
#     app.run(host='0.0.0.0', port=port)
# '''
# '''
