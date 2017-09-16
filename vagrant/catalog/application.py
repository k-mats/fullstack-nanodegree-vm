from flask import Flask, render_template, request, redirect, url_for, flash
from database_setup import Base, Category, Item
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

APPLICATION_NAME = "Catalog Application"


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


# Show a category with its items
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/item/')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return render_template(
        'public_category.html', category=category, items=items)


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


# Delete a category
@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()

    if request.method == 'POST':
        session.delete(category)
        session.commit()
        flash('Category Successfully Deleted')
        return redirect(url_for('showCategories'))
    else:
        return render_template('delete_category.html', category=category)


# Show an item under a certain category
@app.route('/category/<int:category_id>/item/<int:item_id>/')
def showItem(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    return render_template('public_item.html', category=category, item=item)


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


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
