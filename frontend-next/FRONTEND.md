# Next.js Frontend Documentation

> **RFP Compliance Matrix Generator** - A modern web interface for transforming government RFPs into compliance matrices with AI-powered extraction.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Component Hierarchy](#component-hierarchy)
- [Data Flow](#data-flow)
- [Design System](#design-system)
- [API Integration](#api-integration)
- [Development](#development)
- [Changelog](#changelog)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  App Router │  │   Mantine   │  │   React Query       │ │
│  │  (Pages)    │  │   (UI)      │  │   (Server State)    │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                     │            │
│         └────────────────┼─────────────────────┘            │
│                          │                                  │
│                   ┌──────▼──────┐                          │
│                   │   Zustand   │                          │
│                   │(Client State)│                          │
│                   └──────┬──────┘                          │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │ HTTP/REST
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                           │
│              /api/v1/health, /jobs, /files                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

1. **App Router** - Using Next.js 14 App Router for file-based routing and React Server Components support
2. **Client-side rendering** - Main dashboard is a client component for real-time job status polling
3. **Hybrid state management** - React Query for server state, Zustand for client state (job history, UI state)
4. **Standalone output** - Docker-optimized build with `output: 'standalone'`

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14.2.x | React framework with App Router |
| React | 18.3.x | UI library |
| Mantine | 7.x | Component library & design system |
| React Query | 5.x | Server state management & caching |
| Zustand | 5.x | Client state management |
| Axios | 1.x | HTTP client |
| TypeScript | 5.x | Type safety |
| Bun | 1.x | Package manager (faster than npm) |

---

## Project Structure

```
frontend-next/
├── app/                    # Next.js App Router
│   ├── layout.tsx          # Root layout (providers, fonts)
│   ├── page.tsx            # Main dashboard page
│   ├── providers.tsx       # Client-side providers wrapper
│   └── globals.css         # Global styles & CSS variables
│
├── components/             # React components
│   ├── Header.tsx          # App header with health status
│   ├── JobForm.tsx         # Job submission form
│   ├── FileUpload.tsx      # Drag-drop file uploader
│   ├── JobStatus.tsx       # Real-time job progress
│   ├── JobHistory.tsx      # Sidebar job history
│   ├── ProcessingCard.tsx  # Submit/extract button card
│   ├── ResultsDownload.tsx # Download buttons for outputs
│   └── index.ts            # Barrel exports
│
├── hooks/                  # Custom React hooks
│   ├── useBackendHealth.ts # Health check polling
│   ├── useFileUpload.ts    # File upload mutation
│   ├── useJobSubmit.ts     # Job submission mutation
│   ├── useJobStatus.ts     # Job status polling
│   ├── useJobHistory.ts    # Zustand store for job history
│   └── index.ts            # Barrel exports
│
├── lib/                    # Utilities
│   ├── api.ts              # Axios client & API functions
│   └── types.ts            # TypeScript interfaces
│
├── theme/                  # Design system
│   └── theme.ts            # Mantine theme configuration
│
├── public/                 # Static assets
├── Dockerfile              # Multi-stage build (Bun + Node)
├── package.json            # Dependencies
└── bun.lock               # Bun lockfile
```

---

## Component Hierarchy

```
App (layout.tsx)
└── Providers (MantineProvider, QueryClientProvider)
    └── HomePage (page.tsx)
        ├── AppShell
        │   ├── Navbar
        │   │   ├── Navigation
        │   │   ├── JobHistory
        │   │   └── Footer
        │   │
        │   └── Main
        │       ├── Header
        │       ├── Grid
        │       │   ├── JobForm
        │       │   │   └── FileUpload
        │       │   │
        │       │   └── ProcessingCard | JobStatus
        │       │       └── ResultsDownload
```

---

## Data Flow

### Job Submission Flow

```
User uploads files
       │
       ▼
FileUpload.tsx ──► useFileUpload hook ──► POST /api/v1/files/upload
       │                                           │
       │                                           ▼
       │                                    blob_urls returned
       │                                           │
       ▼                                           │
Zustand store (setBlobUrls) ◄──────────────────────┘
       │
       ▼
ProcessingCard.tsx ──► useJobSubmit hook ──► POST /api/v1/jobs/submit
       │                                             │
       │                                             ▼
       │                                      job_id returned
       │                                             │
       ▼                                             │
Zustand store (setCurrentJobId, addJob) ◄────────────┘
       │
       ▼
JobStatus.tsx ──► useJobStatus hook ──► GET /api/v1/jobs/{id}/status
       │              (polling 2s)              │
       │                                        ▼
       │                              { status, progress, message }
       │
       ▼ (when completed)
ResultsDownload.tsx ──► useJobResults hook ──► GET /api/v1/jobs/{id}/results
                                                       │
                                                       ▼
                                          { zip_sas_url, requirements_sas_url, ... }
```

---

## Design System

### Brand Colors (Parker Tide - Modernized)

| Token | Hex | Usage |
|-------|-----|-------|
| `navy.6` | `#04395E` | Primary brand, text headers |
| `navy.7` | `#0A2E4D` | Darker variant, hover states |
| `cyan.5` | `#0ea5e9` | Accent (Tailwind sky-500 inspired) |
| `cyan.0` | `#f0f9ff` | Light backgrounds |
| `--bg-primary` | `#f8fafc` | Page background |
| `--bg-dots` | `#e2e8f0` | Dot pattern color |

### Background Pattern

```css
background-color: #f8fafc;
background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
background-size: 24px 24px;
```

### Typography

- **Font Family**: Inter (via next/font)
- **Headings**: 600-700 weight (lighter than before)
- **Body**: 400-500 weight
- **Monospace**: `ui-monospace, SFMono-Regular, 'SF Mono'` for job IDs, file sizes

### Border Radius

- Default: `md` (8px) - crisp, modern feel
- All components use consistent 8px radius

### Shadows & Borders

Preferring subtle borders over heavy shadows:
- Cards: `shadow="xs"` + `withBorder` (1px solid)
- Hover: `hover-lift` class adds subtle transform + shadow
- Transitions: 150ms ease on all interactive elements

### Status Colors

| Status | Border | Background |
|--------|--------|------------|
| Queued | `#3b82f6` | `#eff6ff` |
| Running | `#f59e0b` | `#fffbeb` |
| Completed | `#10b981` | `#ecfdf5` |
| Failed | `#ef4444` | `#fef2f2` |

---

## API Integration

### Endpoints

| Method | Endpoint | Hook | Purpose |
|--------|----------|------|---------|
| GET | `/api/v1/health` | `useBackendHealth` | Health check (30s interval) |
| POST | `/api/v1/files/upload` | `useFileUpload` | Upload files to blob storage |
| POST | `/api/v1/jobs/submit` | `useJobSubmit` | Submit processing job |
| GET | `/api/v1/jobs/{id}/status` | `useJobStatus` | Poll job status (2s interval) |
| GET | `/api/v1/jobs/{id}/results` | `useJobResults` | Get download URLs |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_BACKEND_API_URL` | Backend API base URL |

---

## Development

### Local Development

```bash
cd frontend-next
bun install
bun run dev      # http://localhost:3000
```

### Production Build

```bash
bun run build
bun run start
```

### Docker Build

```bash
docker compose build frontend
docker compose up frontend
```

The Dockerfile uses a hybrid approach:
- **Stage 1**: Bun for fast dependency installation and build
- **Stage 2**: Node.js Alpine for stable production runtime

---

## Changelog

### v1.1.0 - UI Modernization (Complete)

**Goal**: Transform from "corporate dashboard" to modern "Novu/Linear" SaaS aesthetic.

#### Design Changes

- [x] **Dot pattern background** - Subtle radial gradient grid replacing flat gradients
- [x] **Muted color palette** - Desaturated cyan (`#0ea5e9`) for technical feel
- [x] **Smaller border radius** - `md` (8px) default for crisp, modern edges
- [x] **Subtle shadows** - `shadow="xs"` + borders instead of heavy drop shadows
- [x] **Filled inputs** - `variant="filled"` for premium feel
- [x] **Smooth transitions** - 150ms ease on all interactive elements

#### Component Updates

- [x] **Header.tsx** - Minimal transparent design with logo mark and dot-style status badge
- [x] **JobForm.tsx** - Clean Card.Section headers with icons, no gradients
- [x] **JobStatus.tsx** - Skeleton loader, monospace job IDs, ring progress
- [x] **ProcessingCard.tsx** - Flat design with icon headers
- [x] **FileUpload.tsx** - Compact layout, skeleton during upload, monospace file sizes
- [x] **JobHistory.tsx** - Hover-lift cards, dot-style status badges, monospace IDs
- [x] **ResultsDownload.tsx** - Flat buttons, compact layout
- [x] **page.tsx** - NavLink sidebar, removed gradient background

---

### v1.0.0 - Initial Release

**Date**: December 2024

#### Features

- Next.js 14 App Router architecture
- Mantine v7 component library with Parker Tide branding
- React Query for server state management
- Zustand for client state (job history persistence)
- File upload with drag-drop (Mantine Dropzone)
- Real-time job status polling
- Download results (ZIP, Excel, Word)
- Docker-ready with Bun package manager

#### Components

- `Header` - Brand header with API health badge
- `JobForm` - Job submission with HigherGov/manual toggle
- `FileUpload` - Drag-drop file uploader
- `JobStatus` - Real-time progress with ring indicator
- `JobHistory` - Sidebar with recent jobs
- `ProcessingCard` - Extract requirements trigger
- `ResultsDownload` - Download buttons for outputs
