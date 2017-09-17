from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from database_setup import Base, Category, Item
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

APPLICATION_NAME = "Catalog Application"
API_PATH = '/api/v1'

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


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
