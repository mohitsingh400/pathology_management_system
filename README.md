# Pathology Management System

This repository contains a Django-based Pathology Management System. The application allows patients to book laboratory services, manage appointments, and view/download test reports. Admin and staff users can manage services, update test results, generate reports, and handle user accounts.

## 📁 Project Structure

- `lab/` – Django project configuration (settings, URLs, WSGI/ASGI).
- `labapp/` – Core application containing models, views, templates, static assets, and admin customizations.
- `db.sqlite3` – SQLite database used for development (ignore in production).
- `manage.py` – Django management utility.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+ (or the version used in your environment).
- `pip` package manager.
- A virtual environment is recommended.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mohitsingh400/pathology_management_system.git
   cd pathology_management_system/weblab
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(If a `requirements.txt` file isn't present, install Django and ReportLab manually:)*
   ```bash
   pip install Django reportlab
   ```

### Configuration

- Adjust settings in `lab/settings.py` as needed (database, allowed hosts, etc.).
- Add any additional environment variables (e.g., `SECRET_KEY`, `DEBUG`) in a `.env` or via your system.

### Database Setup

Run migrations to create the database schema:
```bash
python manage.py migrate
```

Create a superuser for admin access:
```bash
python manage.py createsuperuser
```

### Running the Server

Start the development server:
```bash
python manage.py runserver
```

Access the app in your browser at `http://127.0.0.1:8000/`.
The admin interface is available at `http://127.0.0.1:8000/admin/`.

## 📝 Features

- **User registration & login** with roles (patient, admin, staff).
- **Booking system** for patients to reserve lab services.
- **Report management** including PDF generation and file uploads.
- **Admin dashboard** with appointment and report statistics.
- **Service management** through the admin interface.
- **Search & filtering** for services and reports.

## 📦 Fixtures

Sample data for services is available under `labapp/fixtures/services.json`. Load it with:
```bash
python manage.py loaddata labapp/fixtures/services.json
```

## 🛠 Common Commands

- `python manage.py makemigrations` – create new migrations based on model changes.
- `python manage.py test` – run the test suite.
- `python manage.py collectstatic` – gather static files for production.

## 📁 Gitignore and Media

The `.gitignore` file excludes `db.sqlite3`, `media/` files, `__pycache__/`, and other common artifacts. Media uploads (e.g., report PDFs) are stored in `media/reports/`.

## 🧩 Contribution

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/awesome-feature`).
3. Commit your changes and push to your fork.
4. Open a pull request describing your work.

## 📄 License

Specify your project's license here (e.g., MIT). If none, add a placeholder or remove this section.

---

Feel free to improve this README with more information about deployment, testing, or architecture as needed!
