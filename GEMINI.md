# Project Overview

This is a Django-based web application called "simuladoapp_v2". The project appears to be a platform for creating and managing "simulados" (mock tests), likely for educational purposes. It includes features for user authentication, question management, student class management, performance tracking, and a credit system. The project also exposes a REST API for some of its functionality.

## Main Technologies

*   **Backend:** Django, Django REST Framework
*   **Database:** MySQL
*   **Frontend:** Django Templates, with CKEditor for rich text editing.
*   **API Authentication:** JSON Web Tokens (JWT)

## Project Structure

The project is organized into several Django apps:

*   `accounts`: Handles user registration, login, and profile management.
*   `questions`: The core application for creating, managing, and displaying "simulados" and their questions.
*   `classes`: Manages student groups, their performance, and related dashboards.
*   `api`: Provides a RESTful API for the application, likely for use with a mobile app or a separate frontend.
*   `creditos`: Implements a credit management system, possibly for controlling access to certain features.

# Building and Running

## Prerequisites

*   Python 3
*   MySQL
*   The dependencies listed in `requirements.txt`

## Setup

1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the environment:**
    *   Create a `.env` file in the project root.
    *   Add the following variables to the `.env` file, replacing the placeholder values with your actual database credentials:
        ```
        SECRET_KEY=your-secret-key
        DEBUG=True
        DB_NAME=your_db_name
        DB_USER=your_db_user
        DB_PASSWORD=your_db_password
        DB_HOST=localhost
        DB_PORT=3306
        ```

4.  **Run database migrations:**
    ```bash
    python manage.py migrate
    ```

## Running the Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`.

# Development Conventions

## Testing

The project uses Django's built-in testing framework. Each app has a `tests.py` file for its tests.

To run all tests:

```bash
python manage.py test
```

To run tests for a specific app:

```bash
python manage.py test <app_name>
```
