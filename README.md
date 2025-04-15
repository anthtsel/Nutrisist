# Nutrisist

A comprehensive nutrition and health monitoring system that integrates wearable data with personalized meal planning.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update the variables in `.env` with your configuration

4. Initialize the database:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

5. Run the application:
   ```bash
   python run.py
   ```

## Project Structure

The project follows a modular structure:
- `backend/`: Main application code
  - `app/`: Application package
    - `models/`: Database models
    - `routes/`: API routes and views
    - `services/`: Business logic
    - `templates/`: HTML templates
    - `static/`: Static files (CSS, JS) 