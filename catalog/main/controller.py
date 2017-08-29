"""
This module controls CRUD operations for Category and Item data.

"""

import os, re, time
from flask import (abort, Blueprint, flash, g, jsonify, make_response, 
                   redirect, render_template, request, url_for)
from flask import session as login_session

# For password protecting resources
# https://flask-httpauth.readthedocs.io/en/latest/
from flask_httpauth import HTTPBasicAuth

from sqlalchemy import asc, desc, join
from catalog.db_setup import Base, Category, Item, User
from catalog.login import controller as login_utils
from catalog.rlimiter import controller as rlimiter
from catalog.connection_manager import DBSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound

# For photo upload feature
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
BASE_URL = "http://localhost"

auth = HTTPBasicAuth()
session = DBSession()
bp_main = Blueprint("bp_main", __name__, template_folder="templates")


class Image(object):
    """Class for managing image paths and urls.

    Args:
        base_url (str): Protocol and domain name (http://foo.com).
        user_id (str|int): User's database record number.
        filename (str): Image file's filename.
    """

    def __init__(self, base_url, user_id, filename):
        self.path_local = ("catalog/static/uploads/{}/{}"
                           .format(user_id, filename))
        self.path_url = ("{}/static/uploads/{}/{}"
                         .format(base_url, user_id, filename))
        self.path_html = "uploads/{}/{}".format(user_id, filename)

    @staticmethod
    def valid_img_request(img_obj):
        """Checks if there is a request object and it has a value.

        Args:
            img_obj(:obj:`dict`): Flask's Request.files object.
        """

        return img_obj and img_obj.filename != ""

    @staticmethod
    def valid_img_file(filename):
        """Checks if uploaded image file is a valid format.

        Args:
            filename(str): The name of the image file sent by the client.
        """

        allowed_ext = set(["png", "jpg", "jpeg"])
        return "." in filename and \
            filename.rsplit(".", 1)[1].lower() in allowed_ext


@bp_main.route("/token")
@auth.login_required
def get_auth_token():
    """Generates a temporary token for accessing protected resources.

    The generated token is passed as an argument in `verify_password()`
    and used as a more secure verification alternative to username
    (email in this project) and password.
    """

    token = g.user.generate_auth_token()
    response = make_response(jsonify(token=token.decode("ascii")), 200)
    return response


@auth.verify_password
def verify_password(email_or_token, password):
    """Callback for @auth.login_required.

    Handles the `@auth.login_required` to protect sensitive resources.

    Args:
        email_or_token (str): User email address or token generted by
        `get_auth_token()`.
        password (str): User's hashed password.
    """

    user_id = User.verify_auth_token(email_or_token)

    if user_id is True:
        user = session.query(User).filter_by(id=user_id).one()
    else:
        # xxx Why can't we use one() here? It returns None??
        user = session.query(User).filter_by(email=email_or_token).one_or_none()

        if not user or not user.verify_password(password):
            return False

    g.user = user
    return True


@bp_main.route("/api/1.0/", methods=["GET", "POST"])
@rlimiter.rate_limiter(limit=300, per=30 * 1)
def send_api_data():
    """Catalog API request handler.

    Returns results in JSON format. Optional parameters are as follows:

    + limit: Restricts the number or results returned.
    + q: Specify categories or items.
    + user_id: Restrict results to a specific user.
    + search: Get a specific item.

    Example GET request path:
        /api/1.0/?q=categories&user_id=2&limit=2
    """

    data = {}
    params = {}
    query = request.args.get("q")
    limit = request.args.get("limit")
    name = request.args.get("search")
    user_id = request.args.get("user_id")

    if name is not None:
        params["name"] = name
    if user_id is not None:
        params["user_id"] = user_id

    if query is not None:
        if query.lower() == "categories":
            db_result = (session.query(Category).filter_by(**params)
                         .order_by(Category.name).all())
        elif query.lower() == "items":
            db_result = (session.query(Item).filter_by(**params)
                         .order_by(asc(Item.category_name)).all())
        else:
            abort(400)
    else:
        db_result = (session.query(Item).order_by(asc(Item.category_name))
                     .all())

    data_length = len(db_result)

    if limit is not None and int(limit) < data_length:
        data_length = int(limit)
    if data_length > 0:
        if query is not None:
            if query.lower() == "categories":
                for cat in db_result:
                    if cat.owner.public is True:
                        data.setdefault(cat.name, []).append(cat.serialize)
            else:
                for item in db_result:
                    if item.owner.public is True:
                        (data.setdefault(item.category_name, [])
                         .append(item.serialize))

            vals = data.values()
            data = [x for li in vals for x in li]
        else:
            for item in db_result:
                if item.owner.public is True:
                    data.setdefault(item.category_name, []).append(item.serialize)

        msg = "Data found."
    else:
        msg = "No data found."

    response = make_response(jsonify(data=data, response=msg, status="200"), 200)
    return response


@bp_main.route("/")
def welcome():
    """Handle for application main page."""

    if "username" in login_session:
        user_id = login_session["user_id"]
        db_categories = (session.query(Category).filter_by(user_id=user_id)
                         .order_by(asc(Category.name)).all())
        db_items = (session.query(Item).filter_by(user_id=user_id)
                    .order_by(desc(Item.create_date)).limit(7).all())

        return render_template("catalog.html", CATEGORIES=db_categories,
                               RECENT_ITEMS=db_items)
    else:
        state = login_session["state"] = login_utils.gen_csrf_token()
        return render_template("login.html", STATE=state)


@bp_main.route("/<username>/<int:user_id>")
def user_public_page(user_id, username):
    """User public welcome page.

    Args:
        user_id (int): User ID value passed from the URL.
        username (str): User's registered username passed from URL.
    """

    try:
        db_user = session.query(User).filter_by(id=user_id).one()
        db_categories = (session.query(Category).filter_by(user_id=user_id)
                         .order_by(asc(Category.name)).all())
        db_items = (session.query(Item).filter_by(user_id=user_id)
                    .order_by(desc(Item.create_date)).limit(7).all())
    except NoResultFound:
        msg = ("<strong>Data not found. That user may have deleted"
               "their account.</strong>")
        response = make_response(msg, 404)
        return response

    owner = login_utils.get_user_info(user_id)

    if db_user.public is False:
        flash("That user set their data to private.")
        return redirect(url_for("bp_main.welcome"), code=302)
    else:
        msg = "Now visiting the page of {}".format(username)
        flash(msg)
        return render_template("catalog_public.html", CATEGORIES=db_categories,
                               RECENT_ITEMS=db_items, OWNER=owner)


@bp_main.route("/<category_name>/<int:user_id>/")
def show_category(category_name, user_id):
    """Handler for a single category view (private and public).

    Args:
        category_name (str): Category value passed from the URL.
        user_id (int): User ID value passed from the URL.
    """

    try:
        db_category = (session.query(Category)
                       .filter_by(user_id=user_id, name=category_name).one())
        db_items = (session.query(Item)
                    .filter_by(user_id=user_id, category_name=category_name)
                    .order_by(asc(Item.name)).all())
    except NoResultFound:
        msg = ("<strong>Data not found. That user may have deleted"
               "their account.</strong>")
        response = make_response(msg, 404)
        return response

    # Allows to add more personalized info about item's creator
    owner = login_utils.get_user_info(user_id)

    # Determine whether to show the public view or the owner view
    if "username" not in login_session or owner.id != login_session["user_id"]:
        if owner.public is False:
            flash("That user set their data to private.")
            return redirect(url_for("bp_main.welcome"), code=302)
        else:
            return render_template("category_public.html", CATEGORY=db_category,
                                   ITEMS=db_items, OWNER=owner)
    else:
        return render_template("category.html", CATEGORY=db_category,
                               ITEMS=db_items)


@bp_main.route("/<category_name>/<item_name>/<int:user_id>")
def item_info(category_name, item_name, user_id):
    """Handler for item view (private and public).

    Args:
        category_name (str): Category value passed from the URL.
        item_name (str): Item value passed from the URL.
        user_id (int): User ID value passed from the URL.
    """

    try:
        db_category = (session.query(Category)
                       .filter_by(user_id=user_id, name=category_name).one())
        db_item = (session.query(Item)
                   .filter_by(user_id=user_id, name=item_name).one())
    except NoResultFound:
        msg = ("<strong>Data not found. That user may have deleted"
               "their account.</strong>")
        response = make_response(msg, 404)
        return response

    owner = login_utils.get_user_info(db_category.user_id)

    # We need the image path for the client view (img-tag src value)
    img_src = None
    img_filename = db_item.image_file

    if img_filename != None:
        user_img = Image(BASE_URL, user_id, img_filename)
        img_src = user_img.path_html

    if "username" not in login_session or owner.id != login_session["user_id"]:
        if owner.public is False:
            flash("That user set their data to private.")
            return redirect(url_for("bp_main.welcome"), code=302)
        else:
            return render_template("item_public.html", ITEM=db_item,
                                   ITEM_IMAGE=img_src, CATEGORY=db_category)
    else:
        return render_template("item.html", ITEM=db_item, ITEM_IMAGE=img_src,
                               CATEGORY=db_category)


@bp_main.route("/item/new", methods=["GET", "POST"])
def create_item():
    """Handler for new item view."""

    if "username" not in login_session:
        flash("You are not logged in.")
        return redirect(url_for("bp_main.welcome"), code=302)

    # Needed for both db lookup and img directory paths
    user_id = login_session["user_id"]

    # Get all the user's categories for the client-side forms select-tag
    db_categories = (session.query(Category).filter_by(user_id=user_id)
                     .order_by(asc(Category.name)).all())

    if request.method == "POST":
        fm_state = request.form["csrf-token"]
        if fm_state != login_session["state"]:
            abort(401)

        # Let's deal with the image file first (if any)
        try:
            img_obj = request.files["fm-image"]
        except RequestEntityTooLarge:
            msg = "<strong>File size exceeded 1 MB limit.</strong>"
            return make_response(msg, 200)

        # For the new image file to add to the database, image save path
        # on the server and url format for the API response data
        new_imgfile = None
        img_path_loc = None
        img_path_url = None

        if Image.valid_img_request(img_obj) and Image.valid_img_file(img_obj.filename):
            new_imgfile = secure_filename(img_obj.filename)

            # Check if and image file with that name already exists
            dup = (session.query(Item)
                   .filter_by(user_id=user_id, image_file=new_imgfile).count())
            if dup != 0:
                msg = "<strong>There is a file with that name already.</strong>"
                return make_response(msg, 200)

            imginst = Image(BASE_URL, user_id, new_imgfile)
            img_path_loc = imginst.path_local
            img_path_url = imginst.path_url
            img_obj.save(img_path_loc)

        # Next we handle the rest of the form fields
        fm_name = request.form["fm-name"]
        fm_description = request.form["fm-description"]
        fm_category = request.form["category_name"]
        db_items = (session.query(Item)
                    .filter_by(user_id=user_id, name=fm_name).count())

        if fm_name == "":
            fm_name = "No title ({}|{})".format(user_id, int(time.time()))
        if db_items != 0:
            flash("That item already exists!")
            return redirect(url_for("bp_main.welcome"), code=302)

        new_item = Item(name=fm_name, description=fm_description,
                        image_file=new_imgfile, image_url=img_path_url,
                        category_name=fm_category, user_id=user_id)

        # Add to db and redirect
        session.add(new_item)
        session.commit()
        flash("New item added!")
        return redirect(url_for("bp_main.welcome"), code=302)
    else:
        state = login_session["state"] = login_utils.gen_csrf_token()
        return render_template("item_new.html",
                               CATEGORIES=db_categories,
                               STATE=state)


@bp_main.route("/item/<item_name>/<int:user_id>/edit", methods=["GET", "POST"])
def edit_item(item_name, user_id):
    """Handler for edit item view.

    Args:
        item_name (str): Item value passed from the URL.
        user_id (id): User ID value passed from the URL.
    """

    if "username" not in login_session:
        flash("You are not logged in.")
        return redirect(url_for("bp_main.welcome"), code=302)

    try:
        db_item = (session.query(Item)
                   .filter_by(user_id=user_id, name=item_name).one())
        db_categories = session.query(Category).filter_by(user_id=user_id).all()
    except NoResultFound:
        msg = ("<strong>Item data not found. That user may have deleted"
               "their account.</strong>")
        response = make_response(msg, 404)
        return response

    if db_item.user_id != login_session["user_id"]:
        flash("You are not authorized to make changes.")
        return redirect(url_for("bp_main.welcome"), code=302)

    if request.method == "POST":
        fm_state = request.form["csrf-token"]
        if fm_state != login_session["state"]:
            abort(401)

        fm_name = request.form["fm-name"]
        fm_description = request.form["fm-description"]
        fm_category = request.form["fm-category"]

        try:
            img_obj = request.files["fm-image"]
        except RequestEntityTooLarge:
            msg = "<strong>File size exceeded 1 MB limit.</strong>"
            return make_response(msg, 200)

        if fm_name == "":
            fm_name = "No title ({}|{})".format(user_id, int(time.time()))

        # Remove old image file before updating
        if db_item.image_file != None:
            old_imginst = Image(BASE_URL, user_id, db_item.image_file)
            old_imgfile = old_imginst.path_local
            os.remove(old_imgfile)

        new_imgfile = None
        img_path_loc = None
        img_path_url = None

        if Image.valid_img_request(img_obj) and Image.valid_img_file(img_obj.filename):
            new_imgfile = secure_filename(img_obj.filename)
            imginst = Image(BASE_URL, user_id, new_imgfile)
            img_path_loc = imginst.path_local
            img_path_url = imginst.path_url
            img_obj.save(img_path_loc)

        # Update, commit and redirect
        db_item.name = fm_name
        db_item.description = fm_description
        db_item.image_file = new_imgfile
        db_item.image_url = img_path_url
        db_item.category_name = fm_category
        session.add(db_item)
        session.commit()
        flash("Item data updated!")
        return redirect(url_for("bp_main.welcome"), code=302)
    else:
        state = login_session["state"] = login_utils.gen_csrf_token()
        return render_template("item_edit.html", ITEM=db_item,
                               CATEGORIES=db_categories, STATE=state)


@bp_main.route("/item/<item_name>/<user_id>/delete", methods=["GET", "POST"])
def delete_item(item_name, user_id):
    """Handler for delete item view.

    Args:
        item_name (str): Item value passed from the URL.
        user_id (int): User ID value passed from the URL.
    """

    if "username" not in login_session:
        flash("You are not logged in.")
        return redirect(url_for("bp_main.welcome"), code=302)

    try:
        db_item = (session.query(Item)
                   .filter_by(user_id=user_id, name=item_name).one())
    except NoResultFound:
        msg = ("<strong>Data not found. That user may have deleted"
               "their account.</strong>")
        response = make_response(msg, 404)
        return response

    if request.method == "POST":
        fm_yn = request.form["fm-yn"]

        if fm_yn == "N":
            return redirect(url_for("bp_main.welcome"), code=302)

        if db_item.user_id != login_session["user_id"]:
            flash("You are not authorized to delete this.")
            return redirect(url_for("bp_main.welcome"), code=302)

        # Delete the image file in Uploads/< user_id >
        if db_item.image_file != None and db_item.image_url != None:
            imginst = Image(BASE_URL, user_id, db_item.image_file)
            img_path_loc = imginst.path_local
            os.remove(img_path_loc)

        # Delete item record and redirect
        session.delete(db_item)
        session.commit()
        flash("Item deleted!")
        return redirect(url_for("bp_main.welcome"), code=302)
    else:
        state = login_session["state"] = login_utils.gen_csrf_token()
        return render_template("item_delete.html", ITEM_NAME=item_name,
                               USER_ID=user_id, STATE=state)


@bp_main.route("/category/new", methods=["GET", "POST"])
def create_category():
    """Handler for new category view."""

    if "username" not in login_session:
        flash("You are not logged in.")
        return redirect(url_for("bp_main.welcome"), code=302)

    if request.method == "POST":
        fm_state = request.form["csrf-token"]
        if fm_state != login_session["state"]:
            abort(401)

        fm_name = request.form["fm-name"]
        user_id = login_session["user_id"]
        dup = session.query(Category).filter_by(user_id=user_id,
                                                name=fm_name).count()

        if fm_name == "":
            flash("Name field empty.")
            return redirect(url_for("bp_main.create_category"), code=302)
        if dup != 0:
            flash("That category already exists!")
            return redirect(url_for("bp_main.welcome"), code=302)

        new_category = Category(user_id=user_id, name=fm_name)
        session.add(new_category)
        session.commit()

        flash("Category added!")
        return redirect(url_for("bp_main.welcome"), code=302)
    else:
        state = login_session["state"] = login_utils.gen_csrf_token()
        return render_template("category_new.html", STATE=state)


@bp_main.route("/category/<category_name>/<int:user_id>/edit",
               methods=["GET", "POST"])
def edit_category(category_name, user_id):
    """Handler for edit category view.

    Args:
        category_name (str): Category value passed from the URL.
        user_id (int): User ID value passed from the URL.
    """

    if "username" not in login_session:
        flash("You are not logged in.")
        return redirect(url_for("bp_main.welcome"), code=302)

    try:
        db_category = (session.query(Category)
                       .filter_by(user_id=user_id, name=category_name).one())
    except NoResultFound:
        msg = ("<strong>Data not found. That user may have deleted"
               "their account.</strong>")
        response = make_response(msg, 404)
        return response

    if db_category.user_id != login_session["user_id"]:
        flash("You are not authorized to make changes.")
        return redirect(url_for("bp_main.welcome"), code=302)

    if request.method == "POST":
        fm_state = request.form["csrf-token"]
        if fm_state != login_session["state"]:
            abort(401)

        fm_category_name = request.form["fm-name"]

        if fm_category_name == "":
            flash("Empty category name field.")
            return render_template("category_edit.html",
                                   CATEGORY_NAME=category_name,
                                   USER_ID=user_id, STATE=fm_state)
        elif fm_category_name == db_category.name:
            flash("Category name unchanged!")
            return redirect(url_for("bp_main.welcome"), code=302)
        else:
            db_category.name = fm_category_name
            session.add(db_category)
            session.commit()

            flash("Category name changed!")
            return redirect(url_for("bp_main.welcome"), code=302)
    else:
        state = login_utils.gen_csrf_token()
        login_session["state"] = state

        if category_name == "Unsorted":
            flash("Cannot change that category name!")
            return redirect(url_for("bp_main.welcome"), code=302)
        else:
            return render_template("category_edit.html",
                                   CATEGORY_NAME=category_name, USER_ID=user_id,
                                   STATE=state)


@bp_main.route("/category/<category_name>/<int:user_id>/delete",
               methods=["GET", "POST"])
def delete_category(category_name, user_id):
    """Handler for delete category view.

    Args:
        category_name (str): Category value passed from the URL.
        user_id (int): User ID value passed from the URL.
    """

    if "username" not in login_session:
        flash("You are not logged in.")
        return redirect(url_for("bp_main.welcome"), code=302)

    try:
        db_category = (session.query(Category)
                       .filter_by(user_id=user_id, name=category_name).one())
    except NoResultFound:
        msg = ("<strong>Data not found. That user may have deleted"
               "their account.</strong>")
        response = make_response(msg, 404)
        return response

    if db_category.user_id != login_session["user_id"]:
        flash("You are not authorized to make deletions.")
        redirect(url_for("bp_main.welcome"), code=302)

    if request.method == "POST":
        fm_state = request.form["csrf-token"]
        if fm_state != login_session["state"]:
            abort(401)

        fm_yn = request.form["fm-yn"]

        if fm_yn == "N":
            flash("Cancelled deletion.")
            return redirect(url_for("bp_main.welcome"), code=302)

        (session.query(Item)
         .filter_by(user_id=user_id, category_name=category_name)
         .update({Item.category_name: "Unsorted"},
                 synchronize_session="evaluate"))
        session.delete(db_category)
        session.commit()
        flash("Category deleted!")
        return redirect(url_for("bp_main.welcome"), code=302)
    else:
        state = login_utils.gen_csrf_token()
        login_session["state"] = state

        if category_name == "Unsorted":
            flash("Cannot delete that category!")
            return render_template("catalog.html")
        else:
            return render_template("category_delete.html",
                                   CATEGORY_NAME=category_name,
                                   USER_ID=user_id,
                                   STATE=state)
