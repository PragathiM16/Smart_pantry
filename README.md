# Smart Pantry 🥗

A comprehensive pantry management application that helps you track food inventory, discover recipes, plan meals, and reduce food waste.

## Features

- **Inventory Management**: Track food items with expiry dates
- **Recipe Discovery**: Get personalized Indian recipes based on available ingredients
- **Meal Planning**: Plan weekly meals efficiently
- **Email Notifications**: Get alerts for expiring items
- **Analytics**: View pantry statistics and insights
- **User Authentication**: Secure login and signup system

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript
- **Email**: SendGrid API
- **Images**: Pixabay API, Unsplash
- **Charts**: Chart.js

## Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your API keys
4. Run the application: `python app.py`

## Environment Variables

- `SENDGRID_API_KEY`: Your SendGrid API key for email notifications
- `PIXABAY_API_KEY`: Your Pixabay API key for food images
- `MONGO_URI`: MongoDB connection string
- `SENDER_EMAIL`: Email address for sending notifications
- `SECRET_KEY`: Flask secret key for sessions

## Deployment

This application is ready for deployment on:
- Heroku
- Railway
- Render
- PythonAnywhere
- DigitalOcean App Platform

## License

MIT License