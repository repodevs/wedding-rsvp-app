# Wedding Invitation and RSVP System

A web-based RSVP system for wedding invitations built with FastAPI, MySQL, and Tailwind CSS.

## Features

- Guest/Tamu management (add, edit, delete)
- RSVP confirmation and tracking
- Comment system
- Dark/Light mode toggle
- Mobile-responsive design
- Admin dashboard with statistics
- Filtering and search capabilities

## Project Structure

```bash
project/
├── static/             # Static files (images, etc.)
├── templates/          # HTML templates
│   ├── adm/           # Admin panel templates
│   └── index.html     # Main landing page
├── .env               # Environment variables
├── database.py        # Database operations
├── docker-compose.yml # Docker Compose file
├── Dockerfile        # Docker file for the app
├── requirements.txt   # Python dependencies
├── rsvp.py           # Main FastAPI application
```

## Prerequisites

- Python 3.11
- Docker
- Docker Compose
- pip (Python package manager)

## Setup Instructions

### Running with Docker Compose (recommended for simple setup)
1. Clone the repository and navigate to the project directory:
```bash
git clone https://github.com/repodevs/wedding-rsvp-app.git project
cd project
```
2. Run the FastAPP Application
```bash
docker-compose up -d --build
```

check the logs
```bash
docker-compose logs -f
```

3. Access the application:
- Main website: http://localhost:8125
- Admin panel: http://localhost:8125/adm

4. (Optional) Clean up the containers and volumes:
```bash
docker-compose down -v
```

### Running Locally (better for development)

1. Clone the repository and navigate to the project directory:
```bash
git clone https://github.com/repodevs/wedding-rsvp-app.git project
cd project
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # For Unix/macOS
# OR
.\venv\Scripts\activate  # For Windows
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following content:
```bash
RSVP_DATABASE_HOST=127.0.0.1
RSVP_DATABASE_USER=root
RSVP_DATABASE_PASSWORD=toor
RSVP_DATABASE_NAME=rsvp
```

5. Start the MySQL service, for my case use Homebrew for installing MySQL -_well i use MariaDB :)_-

6. Run the FastAPI application:
```bash
uvicorn rsvp:app --reload --host 0.0.0.0 --port 8125
```

7. Access the application:
- Main website: http://localhost:8125
- Admin panel: http://localhost:8125/adm
