# ArenaMind AI: The Intelligent Stadium Operating System

ArenaMind AI functions as the digital intelligence layer for a FIFA World Cup 2026 stadium. It monitors, predicts, coordinates, and optimizes operations in real-time. By utilizing an event-driven digital twin, a rules-based decision engine, and specialized Gemini-powered explainability agents, it transitions from a passive chat assistant into a proactive operating system.

---

## Repository Structure

```
/
├── backend/                  # FastAPI Application
│   ├── app/                  # Main application package
│   │   ├── engine/           # Twin, Predictor, and Decider engines
│   │   ├── routers/          # API endpoint routers
│   │   └── services/         # Third-party integrations (Gemini, Firebase)
│   ├── migrations/           # Alembic database migrations
│   ├── Dockerfile
│   └── requirements.txt
│
└── frontend/                 # Next.js Application
    ├── app/                  # App Router views (Ops, Fan, Volunteer, Replay)
    ├── components/           # UI, layout, maps, and charts components
    ├── types/                # Shared TypeScript models
    └── Dockerfile
```

---

## Tech Stack
- **Frontend**: Next.js (React), TailwindCSS, TypeScript, Zustand, Recharts, Lucide-React
- **Backend**: FastAPI, Python, SQLAlchemy, PostgreSQL, Alembic, Uvicorn, EventBus
- **DevOps**: Docker, Docker Compose, Google Cloud Run, GCP Secret Manager

---

## Core Operations Portals
1. **Executive Command Dashboard** (`/operations`): Real-time operations console featuring stadium composite health status gauges, active timeline consoles, live crowd density/energy charts, and specialized agent mission control desks.
2. **Fan Experience Portal** (`/fan`): Mobile-first layout implementing interactive seat navigators, queue wait forecast engines, live logistics charts, Web Speech API Voice control, and SOS emergency report triggers.
3. **Volunteer Copilot** (`/volunteer`): Amber warning-accented portal containing prioritize task board cards, elapsed response chronometers, dictated voice issue dictation, camera file uploads, concourse navigation waypoints, and LocalStorage offline caches.
4. **Scenario Replay Engine** (`/replay`): Historical incident replay cockpit equipped with play/pause frames interpolation, playback speed controls, animated heatmaps, and synchronized reference line charts.

---

## Local Development (Quick Start)
To launch the complete integrated environment locally:

1. Clone the repository and navigate to the root directory.
2. Build and launch all services using Docker Compose:
   ```bash
   docker-compose up --build
   ```
3. Access the portals:
   - **Main Landing Page**: `http://localhost:3000`
   - **Operations Command Dashboard**: `http://localhost:3000/operations`
   - **Fan Portal**: `http://localhost:3000/fan`
   - **Volunteer Copilot**: `http://localhost:3000/volunteer`
   - **Scenario Replayer**: `http://localhost:3000/replay`
   - **Backend API Docs**: `http://localhost:8000/docs`

---

## Production Deployment
To deploy ArenaMind AI directly to Google Cloud Run from GitHub, please refer to the detailed [DEPLOYMENT_GUIDE.md](file:///c:/IT/Hackathons/PromptWars4/DEPLOYMENT_GUIDE.md).
