#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from email.policy import default
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from models import *
from forms import *
import sys


# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  venues = Venue.query.order_by(db.desc(Venue.created_at)).limit(10).all()
  artists = Artist.query.order_by(db.desc(Artist.created_at)).limit(10).all()
  return render_template('pages/home.html', venues=venues, artists=artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

  venue_list =[]
  venue_locations = Venue.query.with_entities(Venue.state, Venue.city).distinct(Venue.state).all()

  for venue_location in venue_locations:
    all_venues = Venue.query.filter(Venue.state == venue_location.state, Venue.city == venue_location.city).all()

    data = []
    for venue in all_venues:
      data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": db.session.query(Show).filter(Show.start_time > datetime.now()).count()
      })

    venue_list.append({
      "state": venue_location.state,
      "city": venue_location.city,
      "venues": data
    })
  
  return render_template('pages/venues.html', areas=venue_list);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form['search_term']
  search_result = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()

  response = {
    "count": len(search_result),
    "data": search_result
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  venue = Venue.query.get(venue_id)
  setattr(venue, "genres", venue.genres.split(","))

  data = {}
  data['id'] = venue.id
  data['venue'] = venue.name
  data['genres'] = venue.genres
  data['address'] = venue.address
  data['city'] = venue.city
  data['state'] = venue.state
  data['phone'] = venue.phone
  data['website'] = venue.website
  data['facebook_link'] = venue.facebook_link
  data['seeking_talent'] = venue.seeking_talent
  data['seeking_description'] = venue.seeking_description
  data['image_link'] = venue.image_link


  future_shows_details = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time > datetime.now()).all()

  past_shows_details = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).all()
  
  past_shows = []
  for show in past_shows_details:
    past_shows.append({
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S'),
      "artist_image_link": show.artist.image_link,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name    
    })

  future_shows = []
  for show in future_shows_details:
    future_shows.append({
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S'),
      "artist_image_link": show.artist.image_link,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name    
    })

  data["past_shows"] = past_shows
  data["upcoming_shows"] = future_shows
  data["past_shows_count"] = len(past_shows)
  data["upcoming_shows_count"] = len(future_shows)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    name = request.form['name']
    genres = request.form['genres']
    address = request.form['address']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website = request.form['website_link']
    if request.form['seeking_talent'] == 'y':
      seeking_talent = True
    else:
      seeking_talent = False
    seeking_description = request.form['seeking_description']
    created_at = datetime.utcnow()

    created_venue = Venue(
      name=name,
      genres=genres,
      address=address,
      city=city,
      state=state,
      phone=phone,
      facebook_link=facebook_link,
      image_link=image_link,
      website=website,
      seeking_talent=seeking_talent,
      seeking_description=seeking_description,
      created_at=created_at
    )

    db.session.add(created_venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    # flash(e)
  finally:
    db.session.close()
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully deleted!')
  except Exception as e:
    db.session.rollback()
    flash('Venue couldn\'t be deleted')
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = []
  artists = Artist.query.all()

  for artist in artists:
    data.append({
      'id': artist.id,
      'name': artist.name
    })

  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_term = request.form.get('search_term')
  search_result = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()

  response = {
    "count": len(search_result),
    "data": search_result
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  
  curr_artist = Artist.query.get(artist_id)
  setattr(curr_artist, "genres", curr_artist.genres.split(","))

  upcoming_show_details = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time >= datetime.now()).all()

  past_show_details = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time <= datetime.now()).all()

  upcoming_show = []
  for show in upcoming_show_details:
    upcoming_show.append({
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S'),
      'venue_image_link': show.image_link,
      'venue_id': show.venue_id,
      'venue_name': show.name
    })

  past_show = []
  for show in past_show_details:
    past_show.append({
      'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S'),
      'venue_image_link': show.venue.image_link,
      'venue_id': show.venue_id,
      'venue_name': show.venue.name
    })

  data = {
    "id": curr_artist.id,
    "name": curr_artist.name,
    "genres": curr_artist.genres,
    "city": curr_artist.city,
    "state": curr_artist.state,
    "phone": curr_artist.phone,
    "website": curr_artist.website,
    "facebook_link": curr_artist.facebook_link,
    "seeking_venue": curr_artist.seeking_venue,
    "seeking_description": curr_artist.seeking_description,
    "image_link": curr_artist.image_link,
    "past_shows": past_show,
    "upcoming_shows": upcoming_show,
    "past_shows_count": len(past_show),
    "upcoming_shows_count": len(upcoming_show),
  }


  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  artist = Artist.query.get(artist_id)

  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.genres.data = artist.genres
  form.website_link.data = artist.website
  form.image_link.data = artist.image_link
  form.facebook_link.data = artist.facebook_link
  form.seeking_description.data = artist.seeking_description
  form.seeking_venue.data = artist.seeking_venue

  
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  if request.method == 'POST':
    try:
      artist = Artist.query.get(artist_id)
      artist.name = request.form['name']
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.genres = request.form['genres']
      artist.image_link = request.form['image_link']
      if request.form['seeking_venue'] == 'y':
        artist.seeking_venue = True
      else:
        artist.seeking_venue = False
      artist.seeking_description = request.form['seeking_description']
      artist.facebook_link = request.form['facebook_link']
      artist.website = request.form['website_link']

      db.session.add(artist)
      db.session.commit()

      flash("Artist " + request.form["name"] + " was successfully updated!")
    except Exception as e:
      flash('Artist ' + request.form["name"] + 'was not updated successfully')
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()


  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  venue = Venue.query.get(venue_id)
  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.genres.data = venue.genres
  form.website_link.data = venue.website
  form.image_link.data = venue.image_link
  form.facebook_link.data = venue.facebook_link
  form.seeking_description.data = venue.seeking_description
  form.seeking_talent.data = venue.seeking_talent

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm()


  if request.method == 'POST':
    try:
      venue = Venue.query.get(venue_id)
      venue.name = request.form['name']
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.phone = request.form['phone']
      venue.genres = request.form['genres']
      venue.image_link = request.form['image_link']
      venue.address = request.form['address']
      venue.website = request.form['website_link']
      if request.form['seeking_talent'] == 'y':
        venue.seeking_talent = True
      else:
        venue.seeking_talent = False
      venue.seeking_description = request.form['seeking_description']
      venue.created_at = datetime.utcnow()
              
      db.session.add(venue)
      db.session.commit()
      flash("Updated venue successfully!")
    except Exception as e:
      db.session.rollback()
      flash(e)
      flash("Venue was not edited successfully.")
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
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  if request.method == 'POST':

    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form['genres']
    website = request.form['website_link']
    if request.form['seeking_venue'] == 'y':
      seeking_venue = True
    else:
      seeking_venue = False
    image_link = request.form['image_link']
    seeking_description = request.form['seeking_description']
    facebook_link = request.form['facebook_link']

    try:
      new_artist = Artist(
        name=name,
        city=city,
        state=state,
        phone=phone,
        genres=genres,
        website=website,
        seeking_venue=seeking_venue,
        seeking_description=seeking_description,
        image_link=image_link,
        facebook_link=facebook_link
      )

      db.session.add(new_artist)
      db.session.commit()
      
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
      db.session.close()


  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.

  shows = Show.query.all()
  data = []
  for show in shows:
    data.append({
      "venue_id": show.venue_id,
      "artist_id": show.artist_id,
      "start_time": str(show.start_time),
      "venue_name": show.venue.name,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
    })
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm()

  if request.method == 'POST':
    error = False
    try:
      artist_id = request.form['artist_id']
      venue_id = request.form['venue_id']
      start_time = request.form['start_time']

      show = Show(
        artist_id=artist_id,
        venue_id=venue_id,
        start_time=start_time
      )
      db.session.add(show)
      db.session.commit()

    except Exception as e:
      error = True
      db.session.rollback()
      flash(e)

    finally:
      db.session.close()

  if error is True:
    flash('An error occurred. Show could not be listed.')
  else:
    flash('Show was successfully listed!')
  # on successful db insert, flash success
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
