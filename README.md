# Social Media Trend Analyzer

A FastAPI-based web application that analyzes social media trends and provides content recommendations for TikTok and Twitter.

## Features

- Real-time trend analysis from multiple social media platforms
- Content recommendations based on trending topics
- Trend prediction using historical data
- Interactive dashboard with data visualization
- Platform comparison analytics
- Automated content generation suggestions

## Tech Stack

- Backend: FastAPI/Python
- Database: PostgreSQL
- ORM: SQLAlchemy
- UI Framework: Bootstrap 5



## Getting Started

1. Clone this Repl
2. Set up your database credentials in the environment variables:
   ```
   DATABASE_URL=your_postgresql_connection_string
   ```
3. Click the Run button to start the FastAPI server
4. Access the application through the provided URL

## Project Structure

```
├── utils/           # Utility modules
├── main.py          # FastAPI application
├── database.py      # Database configuration
├── models.py        # SQLAlchemy models
└── app.py           # Flask application (alternative)
```

## API Endpoints

- `GET /api/trends` - Fetch current trending topics
- `GET /api/recommendations` - Get content recommendations
- `GET /api/trend-predictions` - Get trend forecasts
- `POST /api/generate-content` - Generate content suggestions



## License

This project is open-source and available under the MIT License.
