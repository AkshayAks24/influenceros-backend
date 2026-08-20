# Influencer OS Backend

This is the backend API for **Influencer OS**, a platform connecting brands with influencers to manage campaigns, deliverables, content creation, and reviews. 

## Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: MySQL (via SQLAlchemy & asyncmy)
- **Migrations**: Alembic
- **Authentication**: JWT (JSON Web Tokens)
- **Testing**: Pytest

## Prerequisites

- Python 3.12+
- MySQL 8.x running locally

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository_url>
   cd influencer-os-backend
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in the required values, particularly your MySQL database credentials.

5. **Create the database**
   Log into your local MySQL instance and create the database:
   ```sql
   CREATE DATABASE influencer_os;
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **(Optional) Seed demo data**
   If you want to populate the database with mock data for testing:
   ```bash
   python -m app.seed
   ```

8. **Start the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

Once the server is running, the interactive API documentation can be accessed at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Testing

To run the full test suite, simply run:
```bash
pytest -v
```
