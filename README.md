# AI Code Agent

An AI-powered code generation, analysis, and refactoring platform.

## Project Structure

```
.
├── backend/           # FastAPI backend
│   ├── api/          # API routes
│   ├── config/       # Configuration
│   ├── models/       # Data models
│   ├── services/     # Business logic
│   ├── utils/        # Utility functions
│   └── tests/        # Tests
├── frontend/         # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API services
│   │   ├── utils/        # Utility functions
│   │   └── assets/       # Static assets
│   └── public/       # Public files
└── docs/             # Documentation
```

## Features

- 🚀 Code generation from natural language prompts
- 🔍 Code analysis and suggestions
- 🔧 Code refactoring capabilities
- 💻 Support for multiple programming languages
- 🌐 Modern web interface

## Setup

### Backend

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the server:
```bash
python app.py
```

### Frontend

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file:
```bash
REACT_APP_API_URL=http://localhost:8000/api/v1
```

4. Run the development server:
```bash
npm start
```

## API Endpoints

- `POST /api/v1/agent/generate` - Generate code from prompt
- `POST /api/v1/agent/analyze` - Analyze code
- `POST /api/v1/agent/refactor` - Refactor code

## Technologies

- **Backend**: FastAPI, Python
- **Frontend**: React, JavaScript
- **AI**: (Configure your AI provider)

## License

MIT

