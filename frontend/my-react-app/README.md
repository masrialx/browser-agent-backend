# AI Agent Dashboard

A modern, responsive React + Vite dashboard for visualizing AI browser agent execution results.

## Features

- 🎨 **Modern UI**: Built with Tailwind CSS and Framer Motion
- 📱 **Fully Responsive**: Works on mobile, tablet, and desktop
- 🔍 **Interactive Steps**: Expandable step cards with detailed information
- 🎯 **Filtering & Search**: Filter steps by status and search through results
- 🚨 **Error Handling**: Clear error messages and CAPTCHA detection alerts
- 🔗 **Clickable URLs**: Direct links to visited pages
- 📊 **Statistics**: Overview of step success/failure rates

## Setup

### Prerequisites

- Node.js 18+ and npm
- Backend server running on `http://localhost:5000`

### Installation

1. Install dependencies:
```bash
npm install
```

2. (Optional) Configure environment variables:
```bash
cp .env.example .env
# Edit .env if needed (proxy is configured by default)
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Usage

1. Enter a task query in the input field (e.g., "Find latest news about OpenAI")
2. Optionally provide an Agent ID
3. Click "Execute" to run the task
4. View the results:
   - Agent information (ID, query, overall success)
   - List of steps with expandable details
   - Filter by success/failure/CAPTCHA status
   - Search through steps

## Project Structure

```
src/
  components/
    AgentHeader.jsx    # Displays agent info and status
    StepCard.jsx       # Individual step card with expand/collapse
    StepList.jsx       # List of steps with filtering
    ResultTable.jsx    # Table for extracted results
  services/
    agentService.js    # API service for backend communication
  App.jsx             # Main app component
  main.jsx            # Entry point
```

## API Endpoints

The app connects to the backend API:

- `POST /api/v1/browser-agent/execute` - Execute browser task
- `GET /api/v1/browser-agent/health` - Health check

## Technologies

- **React 19** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Lucide React** - Icons

## Development

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Backend Integration

The frontend expects the backend to be running on `http://localhost:5000` by default. The Vite proxy is configured to forward `/api` requests to the backend in development.

For production, update the `VITE_API_URL` environment variable to point to your backend server.

## Response Format

The app expects the following JSON response format:

```json
{
  "success": true,
  "data": {
    "agent_id": "agent_123",
    "overall_success": true,
    "query": "Find latest news about OpenAI",
    "steps": [
      {
        "step": "Step description",
        "success": true,
        "result": {
          "success": true,
          "message": "Execution message",
          "data": {
            "title": "Page title",
            "url": "https://example.com"
          },
          "error": null
        }
      }
    ]
  }
}
```
