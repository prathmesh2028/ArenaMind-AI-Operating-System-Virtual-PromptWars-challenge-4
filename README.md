# ArenaMind AI: The Intelligent Stadium Operating System

ArenaMind AI functions as the digital intelligence layer for a FIFA World Cup 2026 stadium. It monitors, predicts, coordinates, and optimizes operations in real-time. By utilizing an event-driven digital twin, a rules-based decision engine, and specialized Gemini-powered explainability agents, it transitions from a passive chat assistant into a proactive operating system.

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

## Tech Stack
- **Frontend**: Next.js, React, TailwindCSS, TypeScript, Zustand, Firebase Client SDK
- **Backend**: FastAPI, Python, SQLAlchemy, Alembic, PostgreSQL, Firebase Admin SDK, Gemini SDK
- **DevOps**: Docker, Docker Compose
