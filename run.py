# run.py
from app import create_app, db # Import db
from app.models import Admin # Import Admin model

app = create_app()

# Optional: Add CLI commands (e.g., for creating admin)
@app.shell_context_processor
def make_shell_context():
    # Makes these available in `flask shell` without importing
    return {'db': db, 'Admin': Admin}

if __name__ == '__main__':
    # Set debug=False for production
    app.run(debug=True, host='0.0.0.0', port=5000)