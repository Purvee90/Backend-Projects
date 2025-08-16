# URL Shortener

A modern URL shortening service built with FastAPI and Streamlit, featuring user authentication, analytics, and advanced URL management capabilities.

## Overview

The URL Shortener is a full-featured web application that allows users to create shortened URLs with various customization options. Built with FastAPI for the backend and Streamlit for the frontend, it provides a robust and user-friendly solution for URL management.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PyJWT
- **Frontend**: Streamlit
- **Database**: SQLite
- **Additional**: Pytz (IST timezone support), QR code generation, Caching

## Key Features

- **User Authentication**
  - Secure registration and login
  - JWT-based authentication
  - User-specific URL management

- **URL Management**
  - Custom or auto-generated short codes
  - Optional expiration (date/minutes based)
  - IST timezone support
  - Automatic deactivation of expired URLs

- **Analytics & Tracking**
  - Click counting and tracking
  - Unique visitor tracking
  - Time-based analytics (24h/7d/30d)
  - Browser usage statisticshis project idea let’s focus on the following features, which you should be more than capable of implementing on your local environment, no matter your OS.

Ability to pass a long URL as part of the request and get a shorter version of it. You’re free to decide how you’ll perform the shortening .
Save the shorter and longer versions of the URL in the database to be used later during redirection.
Configure a catch-all route on your service that gets all the traffic (no matter the URI used), finds the correct longer version and performs a redirection so the user is seamlessly redirected to the proper destination

✅ Enhancement Features Added
1. Click Tracking
Each time a short URL is accessed, the clicks field is incremented in the database.
2. Expiration Time
You can specify expire_in_minutes when creating a short URL.
If the current time exceeds expires_at, the redirect will fail with a 404.
3. Custom Short Codes
You can pass a custom_code in the POST request.
If the code already exists, the API returns an error.
4. Streamlit Frontend
A simple UI to input long URLs, custom codes, and expiration time.
Displays the shortened URL or error message.


🚀 Core Features
1. URL Shortening
Accepts a long URL via a POST request.
Generates a unique short code (random or user-defined).
Returns a shortened URL.
2. Redirection
Catch-all route (/{short_code}) redirects to the original long URL.
Seamless user experience via HTTP 307/302 redirects.
3. Database Persistence
Stores:
long_url
short_code
created_at
expires_at (optional)
clicks (for tracking)
Uses SQLite for lightweight, file-based storage.
📊 Advanced Features
4. Click Tracking
Each time a short URL is accessed, the click count is incremented.
Useful for analytics and monitoring usage.
5. Expiration Time
Optional expiration time (in minutes) can be set during URL creation.
Expired URLs return a 404 error on access.
6. Custom Short Codes
Users can specify their own short code.
Validates uniqueness to avoid collisions.
7. Caching
Uses aiocache with in-memory caching for faster redirection.
Reduces database load for frequently accessed URLs.
🖥️ Frontend Integration
8. Streamlit Frontend
Simple UI for:
Entering long URLs
Custom short codes
Expiration time
Displays shortened URL or error messages.
Communicates with FastAPI backend via HTTP requests.
🧪 Testing & Extensibility
9. Testable Architecture
Modular code structure for easy unit and integration testing.
Can be extended with:
- Enhanced analytics dashboard
- Rate limiting
- Geographic tracking
- Advanced security features

## Installation & Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd url-shortener
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the backend server:
```bash
uvicorn main:app --reload
```

4. Run the Streamlit frontend:
```bash
streamlit run streamlit_frontend.py
```

## Future Enhancements

1. **User-Specific Short Codes**
   - Implementation of user-scoped unique short codes
   - Same short code can be used by different users
   - Short codes only need to be unique within a user's scope
   - Enhanced collision checking within user context

2. **Advanced Analytics**
   - Geographic location tracking
   - Device type statistics
   - Time-based click patterns
   - Analytics export functionality

3. **Security Enhancements**
   - Two-factor authentication
   - Enhanced password policies
   - CSRF protection
   - Rate limiting

4. **Infrastructure Improvements**
   - Docker containerization
   - Redis caching
   - PostgreSQL database migration
   - CI/CD pipeline setup

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
