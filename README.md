# AI-Powered Phishing Domain Detector

This project is a prototype for an AI-powered system designed to detect newly registered phishing domains in near real time.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. **Clone the repository** (if you haven't already).
2. **Start the environment** using Docker Compose:

   ```bash
   docker-compose up --build
   ```

3. **Access the services:**
   - **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
   - **Backend API:** [http://localhost:8000](http://localhost:8000)
   - **API Documentation (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

## Project Structure

- `/backend`: FastAPI Python backend for data ingestion, ML scoring, and APIs.
- `/frontend`: React dashboard for analysts.
- `docker-compose.yml`: Orchestrates the API, Frontend, PostgreSQL DB, and Redis cache.

## Core Components

- **Database:** PostgreSQL stores historical domains, scores, and alerts.
- **Cache:** Redis is used to cache WHOIS/hosting lookups and prevent third-party API rate limits.
