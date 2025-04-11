# Voice Assistant Widget

A Flask-based web application that provides a voice assistant widget with multilingual support (English and German).

## Features

- Voice-based interaction
- Calendar event management
- Product information queries 
- Knowledge base integration
- Multi-language support (EN/DE)
- User authentication
- Dashboard interface
- Secure data storage

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix
.\venv\Scripts\activate   # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and configure your environment variables:
```bash
cp .env.example .env
```

5. Update the `.env` file with your actual configuration values

## Running the Application

For development:
```bash
python app.py
```

## Docker Support

Build the container:
```bash
docker build -t voice-assistant .
```

Run the container:
```bash
docker run -p 5000:5000 voice-assistant
```

## Project Structure

- `/app` - Main application directory
  - `/static` - Static files (CSS, JavaScript, configurations)
  - `/templates` - HTML templates (with language variations)
  - `/storage` - Data storage
  - `/utils` - Utility functions and helpers

## Contributing

1. Create a feature branch
2. Commit your changes
3. Push to the branch
4. Create a Pull Request

## License

[Your License Here]

