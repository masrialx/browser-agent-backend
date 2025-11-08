# Frontend - AI Agent Dashboard

This is the frontend application for the AI Agent Dashboard, built with React + Vite.

## Project Structure

```
frontend/
├── my-react-app/          # Main React application (Vite)
│   ├── src/              # Source files
│   ├── public/           # Public assets
│   └── package.json      # Vite app dependencies
└── package.json          # Root package.json (proxy scripts)
```

## Quick Start

### Option 1: Run from frontend directory (Recommended)

```bash
# From the frontend directory
cd frontend
npm run dev
```

### Option 2: Run directly from my-react-app

```bash
# Navigate to the app directory
cd frontend/my-react-app
npm run dev
```

The application will be available at `http://localhost:5173`

## Installation

If you haven't installed dependencies yet:

```bash
# Navigate to frontend directory
cd frontend

# Install app dependencies (required)
npm run install:app

# Or install manually:
cd my-react-app
npm install
```

## Available Scripts

From the `frontend` directory:

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run linter
- `npm run install:app` - Install app dependencies (in my-react-app)

## Backend Connection

Make sure your backend server is running on `http://localhost:5000`:

```bash
cd backend/flask_app
python run.py
```

The frontend is configured to proxy `/api` requests to the backend automatically in development mode.

## Troubleshooting

### Port already in use
If port 5173 is already in use, Vite will automatically try the next available port. Check the terminal output for the actual port.

### Backend connection issues
- Ensure the backend is running on port 5000
- Check that CORS is enabled in the backend
- Verify the proxy configuration in `my-react-app/vite.config.js`

### Module not found errors
```bash
cd frontend/my-react-app
rm -rf node_modules package-lock.json
npm install
```

## More Information

See `my-react-app/README.md` for detailed documentation about the React application.

