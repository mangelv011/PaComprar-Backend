
# PacomprarServer

PacomprarServer is the backend for a web auction platform developed with Django and Django REST Framework. It enables the management of auctions, bids, ratings, comments, and users, providing a robust and secure API for frontend and mobile applications.

## Main Features

- **Auction Management:** Create, list, update, and delete auctions with advanced validations.
- **Bidding:** Users can place bids on open auctions, with price and state control.
- **Ratings:** Users can rate auctions and view the average rating.
- **Comments:** Comment system for each auction.
- **Categories:** Organize auctions by category.
- **Users:** Registration, JWT authentication, profile, password change, and user management.
- **Pagination & Filtering:** Support for pagination, search, and advanced filtering in endpoints.
- **Security:** Custom permissions for each resource and JWT authentication.
- **OpenAPI Documentation:** Automatically generated with drf-spectacular.
- **CORS:** Configuration to allow access from different origins.

## Technologies Used

- Django 5.2
- Django REST Framework
- PostgreSQL
- drf-spectacular (OpenAPI/Swagger)
- JWT (rest_framework_simplejwt)
- dotenv (environment variables)
- CORS

## Project Structure

- `subastas/`: Auction, bid, rating, and comment logic.
- `usuarios/`: User management and authentication.
- `PacomprarServer/`: Main project configuration.

## Installation

1. Clone the repository.
2. Install dependencies with `pip install -r requirements.txt`.
3. Configure the database and environment variables in `.env`.
4. Run migrations with `python manage.py migrate`.
5. Start the server with `python manage.py runserver`.

## Collaborators

- **mange** (Main administrator)
- [Add other collaborators here]

Want to contribute? Fork the repo and submit your pull request.

## License

This project is licensed under the MIT License.
 
