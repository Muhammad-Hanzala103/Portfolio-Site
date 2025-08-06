# Portfolio Website

This is a Flask-based portfolio website that showcases projects, skills, and other relevant information. The application is designed to be user-friendly and visually appealing, making it easy for visitors to navigate and explore the content.

## Features

- User authentication and authorization
- Admin dashboard for managing content
- Dynamic project and skill listings
- Error handling with custom error pages
- File uploads for images and documents
- Responsive design with CSS and JavaScript

## Technologies Used

- Flask: A lightweight WSGI web application framework.
- SQLAlchemy: An ORM for database interactions.
- Flask-Migrate: For handling database migrations.
- Flask-Login: For user session management.
- Flask-WTF: For form handling and CSRF protection.
- PostgreSQL: The database used for storing application data.
- HTML/CSS/JavaScript: For front-end development.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/portfolio-website.git
   cd portfolio-website
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up the environment variables:
   - Create a `.env` file in the root directory and add your configuration settings, such as:
     ```
     SECRET_KEY=your_secret_key
     DATABASE_URL=postgresql://username:password@localhost:5432/yourdatabase
     FLASK_ENV=development
     ```

5. Run the application:
   ```
   python app.py
   ```

## Usage

- Access the website at `http://localhost:5000`.
- Use the admin panel at `http://localhost:5000/admin` to manage content (login with admin credentials).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.