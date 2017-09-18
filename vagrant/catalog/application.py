from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, make_response
from flask import session as login_session
from database_setup import Base, User, Category, Item
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import random, string, httplib2, json, requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"
API_PATH = '/api/v1'

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Show all categories
@app.route('/')
@app.route('/category/')
def showCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    if categories.count() == 0:
        return render_template('empty_categories.html')
    else:
        return render_template('public_categories.html', categories=categories)


# API to show all categories
@app.route('%s/' % API_PATH)
@app.route('%s/category/' % API_PATH)
def showCategoriesApi():
    categories = session.query(Category).order_by(asc(Category.name))
    return jsonify(categories=[i.serialize for i in categories])


# Show a category with its items
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/item/')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return render_template(
        'public_category.html', category=category, items=items)


# API to show a category
@app.route('%s/category/<int:category_id>/' % API_PATH)
@app.route('%s/category/<int:category_id>/item/' % API_PATH)
def showCategoryApi(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    return jsonify(category=category.serialize)


# Add new category
@app.route('/category/new', methods=['GET', 'POST'])
def createCategory():
    if request.method == 'POST':
        if request.form['name']:
            category = Category(name=request.form['name'])
            session.add(category)
            session.commit()
            flash('Category Successfully Added')
            return redirect(url_for('showCategories'))
        else:
            flash('Please fill in the form properly', 'error')
            return render_template('create_category.html')
    else:
        return render_template('create_category.html')


# API to add new category
# If the creation succeeds, the API returns the created category.
# If the request doesn't contain name key, it returns 400.
@app.route('%s/category/new' % API_PATH, methods=['POST'])
def createCategoryApi():
    if request.json.get('name'):
        category = Category(name=request.json.get('name'))
        session.add(category)
        session.commit()
        return jsonify(item=category.serialize)
    else:
        return abort(400, 'Your request doesn\'t contain name')


# Edit a category
@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()

    if request.method == 'POST':
        if request.form['name']:
            category.name = request.form['name']
            session.add(category)
            session.commit()
            flash('Category Successfully Edited')
            return redirect(url_for('showCategory', category_id=category_id))
        else:
            flash('Please fill in the edit form properly', 'error')
            return render_template('edit_category.html', category=category)
    else:
        return render_template('edit_category.html', category=category)


# API to edit a category
# If the edit succeeds, the API returns the edited category.
# If specified category doesn't exist, it returns 404.
# If the request doesn't contain name key, it returns 400.
@app.route('%s/category/<int:category_id>/edit' % API_PATH, methods=['POST'])
def editCategoryApi(category_id):
    try:
        category = session.query(Category).filter_by(id=category_id).one()
    except SQLAlchemyError:
        abort(404)

    if request.json.get('name'):
        category.name = request.json.get('name')
        session.add(category)
        session.commit()
        return jsonify(category=category.serialize)
    else:
        return abort(400, 'Your request doesn\'t contain name')


# Delete a category
@app.route('/category/<int:category_id>/delete', methods=['POST'])
def deleteCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()

    if request.method == 'POST':
        session.delete(category)
        session.commit()
        flash('Category Successfully Deleted')
        return redirect(url_for('showCategories'))
    else:
        return render_template('delete_category.html', category=category)


# API to delete a category
# If the deletion succeeds, the API returns the deleted category.
# If specified category doesn't exist, it returns 404.
@app.route('%s/category/<int:category_id>/delete' % API_PATH, methods=['POST'])
def deleteCategoryAPI(category_id):
    try:
        category = session.query(Category).filter_by(id=category_id).one()
    except SQLAlchemyError:
        abort(404)

    session.delete(category)
    session.commit()
    return jsonify(category=category.serialize)


# Show an item under a certain category
@app.route('/category/<int:category_id>/item/<int:item_id>/')
def showItem(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    return render_template('public_item.html', category=category, item=item)


# API to show an item under a certain category
@app.route('%s/category/<int:category_id>/item/<int:item_id>/' % API_PATH)
def showItemAPI(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(item=item.serialize)


# Add new item to a certain category
@app.route('/category/<int:category_id>/item/new', methods=['GET', 'POST'])
def createItem(category_id):
    category = session.query(Category).filter_by(id=category_id).one()

    if request.method == 'POST':
        if request.form['name'] and request.form['description']:
            item = Item(name=request.form['name'],
                        description=request.form['description'],
                        category_id=category.id)
            session.add(item)
            session.commit()
            flash('Item Successfully Added')
            return redirect(url_for('showCategory', category_id=category_id))
        else:
            flash('Please fill in the form properly', 'error')
            return render_template('create_item.html', category=category)
    else:
        return render_template('create_item.html', category=category)


# API to add new item to a certain category
# If the creation succeeds, the API returns the created item.
# If specified category doesn't exist, it returns 404.
# If the request doesn't contain name or description key, it returns 400.
@app.route('%s/category/<int:category_id>/item/new' % API_PATH, methods=['POST'])
def createItemApi(category_id):
    try:
        category = session.query(Category).filter_by(id=category_id).one()
    except SQLAlchemyError:
        abort(404)

    if request.json.get('name') and request.json.get('description'):
        item = Item(name=request.json.get('name'),
                    description=request.json.get('description'),
                    category_id=category.id)
        session.add(item)
        session.commit()
        return jsonify(item=item.serialize)
    else:
        return abort(400, 'Your request doesn\'t contain name or description')


# Edit an item
@app.route('/category/<int:category_id>/item/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()

    if request.method == 'POST':
        if request.form['name'] and request.form['description']:
            item.name = request.form['name']
            item.description = request.form['description']
            session.add(item)
            session.commit()
            flash('Item Successfully Edited')
            return redirect(url_for('showItem', category_id=category_id, item_id=item_id))
        else:
            flash('Please fill in the edit form properly', 'error')
            return render_template('edit_item.html', category=category, item=item)
    else:
        return render_template('edit_item.html', category=category, item=item)


# API to edit an item
# If the edit succeeds, the API returns the edited item.
# If specified item doesn't exist, it returns 404.
# If the request doesn't contain name or description key, it returns 400.
@app.route('%s/category/<int:category_id>/item/<int:item_id>/edit' % API_PATH, methods=['POST'])
def editItemApi(category_id, item_id):
    try:
        item = session.query(Item).filter_by(id=item_id).one()
    except SQLAlchemyError:
        abort(404)

    if request.json.get('name') and request.json.get('description'):
        item.name = request.json.get('name')
        item.description = request.json.get('description')
        session.add(item)
        session.commit()
        return jsonify(item=item.serialize)
    else:
        return abort(400, 'Your request doesn\'t contain name or description')


# Delete an item
@app.route('/category/<int:category_id>/item/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()

    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('delete_item.html', category=category, item=item)


# API to delete an item
# If the deletion succeeds, the API returns the deleted item.
# If specified item doesn't exist, it returns 404.
@app.route('%s/category/<int:category_id>/item/<int:item_id>/delete' % API_PATH, methods=['POST'])
def deleteItemApi(category_id, item_id):
    try:
        category = session.query(Category).filter_by(id=category_id).one()
        item = session.query(Item).filter_by(id=item_id).one()
    except SQLAlchemyError:
        abort(404)

    session.delete(item)
    session.commit()
    return jsonify(item=item.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
