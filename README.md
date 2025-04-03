# Health & Diet Plan API

A Flask web application that integrates with Garmin Connect to fetch and display fitness metrics like heart rate, steps, and sleep data.

## Features

- Garmin Connect OAuth2 integration
- Real-time fitness metrics display
- Heart rate monitoring
- Step counting
- Sleep tracking
- Device information

## Prerequisites

- Python 3.8 or higher
- Garmin Connect account
- Garmin Developer account (for OAuth credentials)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/health-diet-plan-api.git
cd health-diet-plan-api
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your configuration:
     - Get Garmin OAuth credentials from [Garmin Developer Portal](https://developer.garmin.com/connect-iq/developer-tools/)
     - Set your Flask secret key
     - Configure database URL if needed

5. Initialize the database:
```bash
flask db upgrade
```

## Running the Application

1. Start the Flask development server:
```bash
python run.py
```

2. Open your browser and navigate to:
```
http://localhost:5001
```

## Garmin OAuth Setup

1. Go to [Garmin Developer Portal](https://developer.garmin.com/connect-iq/developer-tools/)
2. Create a new OAuth 2.0 Client
3. Set the redirect URI to `http://localhost:5001/garmin/callback`
4. Copy the Client ID and Client Secret to your `.env` file

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 