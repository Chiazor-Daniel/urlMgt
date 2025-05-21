from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
# Use instance folder for database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/urls.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Ensure instance folder exists
os.makedirs('instance', exist_ok=True)

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    link = db.Column(db.String(2048), nullable=False)

# Initialize database
with app.app_context():
    db.create_all()
    # Ensure the predefined links exist
    predefined_links = [
        {'name': 'voicemail-googleplay', 'link': 'https://play.google.com/store/apps/details?id=com.google.android.apps.googlevoice'},
        {'name': 'voicemail-windows', 'link': 'https://www.microsoft.com/en-us/p/google-voice/9nblggh0h7c9'},
        {'name': 'optimum-google', 'link': 'https://play.google.com/store/apps/details?id=com.altice.optimum'},
        {'name': 'optimum-windows', 'link': 'https://www.microsoft.com/en-us/p/optimum/9nblggh0h7c9'}
    ]
    for link_data in predefined_links:
        link = Link.query.filter_by(name=link_data['name']).first()
        if not link:
            link = Link(name=link_data['name'], link=link_data['link'])
            db.session.add(link)
    db.session.commit()

@app.route('/')
def index():
    links = Link.query.order_by(Link.id.desc()).all()
    return render_template('index.html', links=links)

@app.route('/edit/<int:id>', methods=['POST'])
def edit_link(id):
    link_obj = Link.query.get_or_404(id)
    name = request.form.get('name')
    link = request.form.get('link')
    if not name or not link:
        flash('Both name and link are required!', 'danger')
        return redirect(url_for('index'))
    if Link.query.filter(Link.name == name, Link.id != id).first():
        flash('Name already exists!', 'danger')
        return redirect(url_for('index'))
    link_obj.name = name
    link_obj.link = link
    db.session.commit()
    flash('Link updated!', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_link(id):
    link_obj = Link.query.get_or_404(id)
    db.session.delete(link_obj)
    db.session.commit()
    flash('Link deleted!', 'success')
    return redirect(url_for('index'))

@app.route('/api/links')
def get_links():
    links = Link.query.order_by(Link.id.desc()).all()
    return jsonify([{
        'id': link.id,
        'name': link.name,
        'link': link.link
    } for link in links])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 