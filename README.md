# Campfire Adelaide Dashboard

A lightweight Flask dashboard for running hackathons. It provides authentication, team management, timelines, file uploads, and admin controls in one web app.

## Features

* Admin and user roles with secure login
* 6-digit registration codes for sign-up
* Create and manage teams
* Team and global timelines with image posts
* User profiles with pictures and post history
* Admin tools for managing users, teams, and codes

## Requirements

* Python 3.8+
* SQLite (PostgreSQL recommended for production)

## Quick Start

```bash
git clone https://github.com/adlcampfire/dashboard
cd dashboard
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python init_db.py
python app.py
```

Open [http://localhost:5000](http://localhost:5000)

## Default Admin

* Username: admin
* Password: changemeasap
  Change the password after first login.

## Configuration

Optional environment variables:

```bash
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///campfire.db
FLASK_DEBUG=True
```
Also make sure to change all instances of 'Adelaide' to what your event city is.
We plan to add a setup assistant soonish.

## Documentation

[https://github.com/adlcampfire/dashboard/wiki](https://github.com/adlcampfire/dashboard/wiki)

## License

MIT