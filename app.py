import sqlite3
import requests
from flask import Flask, render_template, request, redirect, url_for, g

# --- App and Database Configuration ---
app = Flask(__name__)
DATABASE = 'journal.db'

# --- Database Connection Management (for web requests) ---
def get_db():
    """Opens a new database connection for the current request."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    """Closes the database at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- Database Initialization Command (Self-Contained) ---
@app.cli.command('init-db')
def init_db_command():
    """Creates the database tables. This is a self-contained command."""
    # It connects, initializes, and closes its own connection.
    try:
        db = sqlite3.connect(DATABASE)
        with app.open_resource('schema.sql', mode='r') as f:
            db.executescript(f.read())
        db.commit()
        db.close()
        print('Initialized the database.')
    except Exception as e:
        print(f"An error occurred during database initialization: {e}")

# --- Quote API Function ---
def get_daily_quote():
    """Fetches a random quote from the ZenQuotes API."""
    try:
        response = requests.get("https://zenquotes.io/api/random")
        response.raise_for_status()
        data = response.json()[0]
        return f'"{data["q"]}" - {data["a"]}'
    except requests.exceptions.RequestException as e:
        print(f"Could not retrieve quote: {e}")
        return "Your daily inspiration is the journey itself."

# --- Main Application Routes ---
@app.route('/')
def index():
    """Main page: displays the quote, entry form, and all journal entries."""
    quote = get_daily_quote()
    db = get_db()
    entries = db.execute(
        'SELECT id, content, created_at FROM journal_entries ORDER BY created_at DESC'
    ).fetchall()
    return render_template('index.html', quote=quote, entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
    """Handles the submission of a new journal entry."""
    entry_content = request.form['content']
    if entry_content:
        db = get_db()
        db.execute('INSERT INTO journal_entries (content) VALUES (?)', (entry_content,))
        db.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
