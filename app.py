from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from models import db, User, Product, Showcase, ChatMessage
from forms import RegisterForm, LoginForm, ProductForm, ShowcaseForm
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import send_from_directory
from flask_socketio import SocketIO, join_room, leave_room, send

import os

# db = SQLAlchemy()


app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)
socketio = SocketIO(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # type: ignore[attr-defined]

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = User()
        new_user.username = form.username.data
        new_user.role = form.role.data
        new_user.email = form.email.data
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash("Registered successfully!", "success")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/products', methods=['GET'])
def products():
    search_query = request.args.get('search', '')
    user_filter = request.args.get('filter_user', '')
    category_filter = request.args.get('filter_category', '')
    sort = request.args.get('sort', '')

    query = Product.query

    if search_query:
        query = query.filter(
            Product.name.ilike(f'%{search_query}%') |
            Product.description.ilike(f'%{search_query}%')
        )

    if user_filter:
        query = query.filter(Product.recommended_for.like(f'%{user_filter}%'))

    if category_filter:
        query = query.filter_by(category=category_filter)

    # Sorting
    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'date_asc':
        query = query.order_by(Product.id.asc())
    elif sort == 'date_desc':
        query = query.order_by(Product.id.desc())

    items = query.all()

    return render_template(
        'products.html',
        products=items,
        search_query=search_query,
        user_filter=user_filter,
        category_filter=category_filter
    )



@app.route('/add-products', methods=['GET', 'POST'])
@login_required
def add_products():
    if current_user.role != 'admin':
        flash("Admins only!", "danger")
        return redirect(url_for('index'))
    form = ProductForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join('static', 'uploads', filename))
        new_product = Product()
        new_product.name = form.name.data
        new_product.category = form.category.data
        new_product.recommended_for = ",".join(form.recommended_for.data) if form.recommended_for.data else None
        new_product.description = form.description.data
        new_product.price = form.price.data
        new_product.image_filename = filename
        db.session.add(new_product)
        db.session.commit()
        flash("Product added.", "success")
        return redirect(url_for('products'))
    return render_template('add_products.html', form=form)

@app.route('/pc-builders')
def pc_builders():
    return render_template('pc_builders.html')

@app.route('/audiophiles')
def audiophiles():
    return render_template('audiophiles.html')

@app.route('/keyboards')
def keyboards():
    return render_template('keyboards.html')

@app.route('/smart-home')
def smart_home():
    return render_template('smart_home.html')

@app.route('/showcase')
def showcase():
    showcases = Showcase.query.order_by(Showcase.created_at.desc()).all()
    return render_template('showcase.html', showcases=showcases)


@app.route('/create-showcase', methods=['GET', 'POST'])
@login_required
def create_showcase():
    form = ShowcaseForm()
    if form.validate_on_submit():
        image_filenames = []
        if form.images.data:
            for img in form.images.data:
                filename = secure_filename(img.filename)
                save_path = os.path.join('static', 'uploads', filename)
                img.save(save_path)
                image_filenames.append(filename)

        new_showcase = Showcase()
        new_showcase.title = form.title.data
        new_showcase.category = ",".join(form.category.data) if form.category.data else None
        new_showcase.components = form.components.data
        new_showcase.image_filenames = ",".join(image_filenames)
        new_showcase.user_id = current_user.id
        db.session.add(new_showcase)
        db.session.commit()
        flash('Showcase created successfully!', 'success')
        return redirect(url_for('showcase'))
    
    return render_template('create_showcase.html', form=form)

@app.route('/chat/<category>')
@login_required
def chat(category):
    allowed_categories = ['PC', 'Audio', 'Keyboard', 'SmartHome']
    if category not in allowed_categories:
        flash('Invalid chat room', 'danger')
        return redirect(url_for('index'))

    # Load last 50 messages for the category
    messages = ChatMessage.query.filter_by(category=category).order_by(ChatMessage.timestamp.asc()).limit(50).all()

    return render_template('chat.html', category=category, messages=messages)

@socketio.on('join_room')
def handle_join(data):
    room = data['room']
    join_room(room)
    msg = {'user': 'System', 'message': f'{current_user.username} has joined the room.'}
    socketio.emit('message', msg, room=room)  # type: ignore

@socketio.on('leave_room')
def handle_leave(data):
    room = data['room']
    leave_room(room)
    msg = {'user': 'System', 'message': f'{current_user.username} has left the room.'}
    socketio.emit('message', msg, room=room)  # type: ignore

@socketio.on('send_message')
def handle_message(data):
    room = data['room']
    message = data['message']

    # Save to database
    chat_msg = ChatMessage()
    chat_msg.user_id = current_user.id
    chat_msg.username = current_user.username
    chat_msg.category = room
    chat_msg.message = message
    db.session.add(chat_msg)
    db.session.commit()

    # Broadcast to the room
    msg = {'user': current_user.username, 'message': message}
    socketio.emit('message', msg, room=room)  # type: ignore

@app.route('/showcase/<int:showcase_id>')
def showcase_detail(showcase_id):
    showcase = Showcase.query.get_or_404(showcase_id)
    images = showcase.image_filenames.split(',') if showcase.image_filenames else []
    return render_template('showcase_detail.html', showcase=showcase, images=images)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)