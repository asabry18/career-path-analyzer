# Career Path Analyzer - Setup Guide

## Prerequisites

Before starting, ensure you have the following installed:

| Tool | Recommended Version | Download Link |
|------|---------------------|---------------|
| Python | 3.10+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| npm | 9+ (comes with Node.js) | https://nodejs.org/ |
| Git | Latest | https://git-scm.com/ |

---

## Backend Setup (Python/Django)

### Required Packages

| Package | Version | Purpose |
|---------|---------|---------|
| Django | >=5.0 | Web framework |
| djangorestframework | >=3.15 | REST API framework |
| djangorestframework-simplejwt | >=5.3 | JWT authentication |
| django-cors-headers | >=4.6 | CORS handling |
| psycopg[binary] | >=3.2 | PostgreSQL adapter |
| drf-spectacular | >=0.27 | API documentation |
| python-dotenv | >=1.0 | Environment variables |
| numpy | >=2.0 | Numerical computing |
| scipy | >=1.14 | Scientific computing |
| scikit-learn | >=1.5 | Machine learning |
| pulp | >=2.8 | Linear programming |
| pytest | >=8.0 | Testing framework |
| pytest-django | >=4.8 | Django testing |
| factory-boy | >=3.3 | Test data generation |

### Installation Steps

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment (recommended)
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install all dependencies
pip install -r requirements.txt

# 5. Copy environment file and configure
cp .env.example .env
# Edit .env with your database credentials and settings

# 6. Run database migrations
python manage.py migrate

# 7. Create superuser (optional)
python manage.py createsuperuser

# 8. Start development server
python manage.py runserver
```

The backend server will start at: `http://127.0.0.1:8000/`

---

## Frontend Setup (React/TypeScript/Vite)

### Required Packages

#### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| react | ^19.2.4 | UI library |
| react-dom | ^19.2.4 | React DOM rendering |
| react-router-dom | ^7.14.1 | Routing |
| axios | ^1.16.0 | HTTP client |
| lucide-react | ^1.8.0 | Icons |

#### Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| vite | ^8.0.4 | Build tool |
| typescript | ~6.0.2 | Type checking |
| tailwindcss | ^4.2.2 | CSS framework |
| @vitejs/plugin-react | ^6.0.1 | Vite React plugin |
| eslint | ^9.39.4 | Linting |
| @types/react | ^19.2.14 | React types |
| @types/react-dom | ^19.2.3 | React DOM types |
| @types/node | ^24.12.2 | Node.js types |
| typescript-eslint | ^8.58.0 | TypeScript ESLint |
| eslint-plugin-react-hooks | ^7.0.1 | React hooks linting |
| eslint-plugin-react-refresh | ^0.5.2 | React refresh linting |
| @eslint/js | ^9.39.4 | ESLint JS |
| globals | ^17.4.0 | Global variables |
| @tailwindcss/vite | ^4.2.2 | Tailwind Vite plugin |

### Installation Steps

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install all dependencies
npm install

# 3. Start development server
npm run dev
```

The frontend server will start at: `http://localhost:5173/`

---

## Running the Full Project

### Option 1: Two Terminal Windows

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # Windows
python manage.py runserver
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 2: Using npm scripts (if configured)

You can add a concurrent script to run both servers simultaneously.

---

## Available Commands

### Backend Commands

| Command | Description |
|---------|-------------|
| `python manage.py runserver` | Start development server |
| `python manage.py migrate` | Apply database migrations |
| `python manage.py createsuperuser` | Create admin user |
| `python manage.py test` | Run tests |
| `pytest` | Run tests with pytest |

### Frontend Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

---

## Troubleshooting

### Backend Issues

1. **Python version error**: Ensure Python 3.10+ is installed
   ```bash
   python --version
   ```

2. **pip not found**: Install pip or use `python -m pip`

3. **Database errors**: Check your `.env` file for correct database credentials

### Frontend Issues

1. **Node version error**: Ensure Node.js 18+ is installed
   ```bash
   node --version
   npm --version
   ```

2. **Module not found**: Delete `node_modules` and reinstall
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Port already in use**: Change the port in `vite.config.ts` or stop the conflicting process

---

## Project Structure

```
career-path-analyzer/
├── backend/
│   ├── apps/              # Django apps
│   ├── config/            # Django settings
│   ├── data/              # Data files
│   ├── manage.py          # Django management
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── src/               # React source
│   ├── package.json       # Node dependencies
│   └── vite.config.ts     # Vite configuration
└── SETUP.md               # This file