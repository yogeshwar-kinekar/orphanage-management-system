# Orphanage Management System (Flask OMS)

A web application built with Flask to manage records for an orphanage, including orphans, donations, expenses, and NGO members. Features a dashboard with visual statistics.



https://github.com/user-attachments/assets/0f2558ed-525c-4fda-b551-bde9d38ac73f



## Setup and Installation

Follow these steps to clone the repository and get the application running on your local machine:

1.  **Prerequisites:**
    *   Make sure you have **Python 3.8** or newer installed. ([Download Python](https://www.python.org/downloads/))
    *   Make sure you have **Git** installed. ([Download Git](https://git-scm.com/downloads))

2.  **Clone the Repository:**
    Open your terminal or command prompt and run the following command, replacing `<YourGitHubUsername>` and `<YourRepositoryName>` with the actual values:
    ```bash
    git clone https://github.com/VinitHudiya19/CEP_OMS.git
    ```
    Then, navigate into the newly cloned directory:
    ```bash
    cd CEP_OMS
    ```

3.  **Create and Activate a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.

    *   **On Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    *   **On macOS / Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    You should see `(venv)` prepended to your terminal prompt, indicating the environment is active.

4.  **Install Required Packages:**
    Install all the necessary Python libraries listed in `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure Environment Variables:**
    *   Create a new file named `.env` in the root directory of the project (the same level as `run.py` and the `app` folder).
    *   Open the `.env` file and add the following lines:

        ```dotenv
        # Generate a strong, random secret key for session security
        # You can generate one using: python -c "import secrets; print(secrets.token_hex(16))"
        SECRET_KEY='YOUR_VERY_STRONG_RANDOM_SECRET_KEY_HERE'

        # Location of the database file (SQLite is used by default)
        DATABASE_URL='sqlite:///orphanage.db'

        # Optional: Uncomment for development mode (enables debugger, auto-reload)
        # FLASK_DEBUG=1
        ```
    *   **Important:** Replace `'YOUR_VERY_STRONG_RANDOM_SECRET_KEY_HERE'` with a real, randomly generated secret key. Do *not* use a weak or guessable key.

6.  **Database Initialization:**
    *   create the `orphanage_db` MySQL database file and all necessary tables when you run it for the first time.
    *   It will also create a default **admin** user with the following credentials:
        *   **Username:** `admin`
        *   **Password:** `password`
    *   **SECURITY WARNING:** You should **change this default password immediately** after logging in for the first time, or modify the initial user creation logic in `app/__init__.py` before any serious use or deployment.

7.  **Run the Application:**
    With your virtual environment still active, run the Flask development server:
    ```bash
    flask run
    ```
    *(Flask should automatically detect the `app` instance via `run.py` or `app/__init__.py`)*

8.  **Access the Application:**
    Open your web browser and navigate to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)
    (Or the address provided in your terminal output).

    You should see the login page. Use the default credentials (`admin`/`password`) to log in.

---
