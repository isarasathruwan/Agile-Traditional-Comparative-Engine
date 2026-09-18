# MethodAlign IS Frontend

Next.js 16 frontend for the Agile vs Traditional Comparative Engine. Built with React 19, Tailwind CSS, Framer Motion, and Recharts.

## Local Development

### Setup

```bash
cd frontend
npm install
```

### Run Dev Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

The app auto-reloads when you edit files.

### Build for Production

```bash
npm run build
npm start
```

## Docker Deployment

The frontend is containerized and runs via the root `docker-compose.yml`. **No local Node.js or npm required** — the build happens entirely inside Docker.

```bash
# From project root — starts frontend, backend, database, and two workers
docker compose up -d --build
```

### Container Details

- **Image:** `node:20-alpine` (multi-stage build)
- **Port:** 3000
- **Output:** Next.js standalone (optimized for Docker)
- **User:** `nextjs` (non-root)
- **Build location:** Entirely inside the container

### Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | URL the browser uses to reach the backend API |

**Important:** `NEXT_PUBLIC_*` variables are baked into the build at Docker image build time, not runtime.

### API URL Configurations

**Development (direct ports):**
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

**Production (with Nginx reverse proxy):**
```bash
NEXT_PUBLIC_API_BASE_URL=/api
```

## Project Structure

```
frontend/
├── app/              # Next.js App Router
│   ├── page.tsx      # Assessment wizard (landing → questions → results)
│   ├── admin/        # Admin dashboard
│   └── layout.tsx    # Root layout with fonts & metadata
├── components/       # React components
│   ├── TextQuestion.tsx
│   ├── PillSelectQuestion.tsx
│   ├── LikertScreen.tsx
│   ├── ProgressBar.tsx
│   ├── BackButton.tsx
│   └── results/      # Result visualization components
├── hooks/            # Custom React hooks
├── lib/              # Utilities & API clients
│   ├── api.ts        # Public API client
│   ├── adminApi.ts   # Admin API client
│   └── pageMeta.ts   # Page metadata helpers
├── public/           # Static assets
├── Dockerfile
└── next.config.ts
```

## Tech Stack

- [Next.js 16](https://nextjs.org/)
- [React 19](https://react.dev/)
- [Tailwind CSS 4](https://tailwindcss.com/)
- [Framer Motion](https://www.framer.com/motion/) — animations
- [Recharts](https://recharts.org/) — data visualization
- [Phosphor Icons](https://phosphoricons.com/)
