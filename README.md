# Personal Finance Tracker (Django)

Log income/expenses, categorize them, set monthly budgets, and see charts.

## Run it
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations tracker
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin
python manage.py runserver
```
Open http://127.0.0.1:8000 and register an account.

For deployment, set `DJANGO_SECRET_KEY` to a private, randomly generated key,
set `DJANGO_DEBUG=False`, and set `DJANGO_ALLOWED_HOSTS` to a comma-separated
list of the hostnames serving the app. The built-in key and debug setting are
for local development only.

## Features
- Register / login / logout (each user sees only their own data)
- Add, edit, delete transactions; filter by type and category; pagination
- Categories (6 starter ones created on signup)
- Monthly budgets per category with progress bars (red when exceeded)
- Dashboard: monthly totals, spending doughnut chart, 6-month income vs expense chart

## Structure
- `config/`   settings and root URLs
- `tracker/`  models, forms, views, urls
- `templates/` base layout, auth pages, tracker pages

## Ideas to extend
CSV export, recurring transactions, REST API (Django REST Framework), deployment on Render/Railway.
