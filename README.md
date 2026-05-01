# Movember Step Tracker

A Streamlit web application for tracking steps during the Movember campaign, featuring user authentication, leaderboards, and automated health checks.

## 🚀 Features

- **User Authentication**: Secure signup/login with bcrypt password hashing
- **Step Tracking**: Log and track daily steps
- **Leaderboards**: Compete with other participants
- **Admin Dashboard**: Manage users and view statistics
- **Automated Keep-Alive**: GitHub Actions to keep Supabase and Streamlit app active

## 📁 Project Structure

```
MovemberStepTracker/
├── .github/
│   └── workflows/
│       ├── ping-supabase.yml    # Keeps Supabase database alive
│       └── wake-streamlit.yml   # Wakes Streamlit app if sleeping
├── streamlit-app/
│   ├── Home.py                  # Main entry point
│   ├── pages/                   # Application pages
│   │   ├── Admin.py
│   │   ├── Leaderboard.py
│   │   ├── Login.py
│   │   └── Signup.py
│   ├── src/                     # Source code modules
│   ├── assets/                  # Images and static files
│   ├── db.py                    # Supabase database connection
│   ├── requirements.txt         # Python dependencies
│   └── .streamlit/
│       └── config.toml          # Streamlit configuration
├── runner.py                    # Selenium script for app wake-up
├── runner-req.txt               # Dependencies for runner script
└── README.md
```

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.10+
- Supabase account
- Streamlit Cloud account (for deployment)

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DWandless/MovemberStepTracker.git
   cd MovemberStepTracker
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   cd streamlit-app
   pip install -r requirements.txt
   ```

4. **Configure Supabase:**
   - Create a `.streamlit/secrets.toml` file:
     ```toml
     SUPABASE_URL = "your-supabase-url"
     SUPABASE_KEY = "your-supabase-anon-key"
     ```

5. **Run the application:**
   ```bash
   streamlit run Home.py
   ```

## 🌐 Deployment

The app is deployed on Streamlit Cloud: [https://movembersteptracker.streamlit.app/](https://movembersteptracker.streamlit.app/)

### GitHub Actions

Two automated workflows keep the services alive:

1. **Supabase Ping** - Runs every 3 days to prevent database hibernation
2. **Streamlit Wake** - Runs every 4 hours to wake the app if sleeping

## 🗄️ Database Schema

The application uses Supabase with the following main tables:
- `members` - User accounts and authentication
- `steps` - Daily step tracking data

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🎗️ About Movember

This application supports the Movember movement, raising awareness for men's health issues including prostate cancer, testicular cancer, and mental health.
