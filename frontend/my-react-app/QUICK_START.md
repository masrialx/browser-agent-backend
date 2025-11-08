# Quick Start Guide

## Prerequisites

1. **Backend Server**: Make sure your Flask backend is running on `http://localhost:5000`
   ```bash
   cd backend/flask_app
   python run.py
   ```

2. **Node.js**: Ensure you have Node.js 18+ installed

## Installation & Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend/my-react-app
   ```

2. **Install dependencies** (if not already done):
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser**:
   - The app will be available at `http://localhost:5173`
   - The Vite proxy is configured to forward `/api` requests to `http://localhost:5000`

## Usage

1. **Enter a Task Query**:
   - Type your query in the input field (e.g., "Find latest news about OpenAI")
   - Optionally provide an Agent ID

2. **Execute the Task**:
   - Click the "Execute" button
   - Wait for the agent to process your query

3. **View Results**:
   - Agent information (ID, query, overall success status)
   - List of steps with expandable details
   - Filter steps by status (All, Success, Failed, CAPTCHA)
   - Search through steps
   - Click URLs to open in new tabs

## Features

- ✅ **Real-time Status**: Server health check indicator
- ✅ **Interactive Steps**: Expand/collapse step details
- ✅ **Filtering**: Filter by success/failure/CAPTCHA status
- ✅ **Search**: Search through step descriptions and results
- ✅ **Responsive Design**: Works on mobile, tablet, and desktop
- ✅ **Error Handling**: Clear error messages and CAPTCHA alerts
- ✅ **Clickable URLs**: Direct links to visited pages

## Troubleshooting

### Backend Connection Issues

If you see "Server Offline" in the header:
1. Check if the backend server is running on port 5000
2. Verify CORS is enabled in the backend
3. Check browser console for detailed error messages

### Build Issues

If you encounter build errors:
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Port Already in Use

If port 5173 is already in use:
- Vite will automatically try the next available port
- Check the terminal output for the actual port number

## Production Build

To build for production:
```bash
npm run build
```

The built files will be in the `dist/` directory.

## Environment Variables

Create a `.env` file in the frontend directory (optional):
```env
VITE_API_URL=http://localhost:5000
```

In development, the Vite proxy handles this automatically. In production, set this to your backend URL.


