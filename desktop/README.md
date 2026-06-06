# Caleb Records Desktop

A unified desktop launcher for the Caleb University Records Management System, built with [Tauri](https://tauri.app/) v2.

## Features

- **Single Launcher Window** — branded dashboard showing service status
- **Start/Stop Backend** — manage the FastAPI backend directly from the desktop
- **Open Portals** — launch Student or Staff portals in separate native windows
- **System Tray** — quick access from the system tray (desktop platforms)
- **Auto-Status Polling** — real-time indicators for Backend (8000), Student (5173), Staff (5174)
- **"Back to Launcher" Button** — appears inside portal windows when running from desktop

## Prerequisites

- **Rust** ≥ 1.77 (`rustc --version`)
- **Node.js** ≥ 18 (`node --version`)
- **System Libraries** (Linux):
  ```bash
  sudo apt-get install libwebkit2gtk-4.1-dev libsoup-3.0-dev libayatana-appindicator3-dev
  ```

## Quick Start

```bash
cd desktop
npm install
npm run tauri dev          # Development mode
npm run tauri build        # Production build (creates .deb, .rpm, .AppImage)
```

## Build Artifacts

After `npm run tauri build`, artifacts are in:

```
src-tauri/target/release/bundle/
├── deb/Caleb Records Desktop_1.0.0_amd64.deb
├── rpm/Caleb Records Desktop-1.0.0-1.x86_64.rpm
└── appimage/Caleb Records Desktop_1.0.0_amd64.AppImage  (requires linuxdeploy)
```

The raw binary is also available at:

```
src-tauri/target/release/caleb-records-desktop
```

## How It Works

1. The **launcher window** (`tauri://localhost`) shows three status cards
2. **Start Backend** runs the Python FastAPI server from `../backend/`
3. **Open Student Portal** creates a new Tauri window at `http://localhost:5173`
4. **Open Staff Portal** creates a new Tauri window at `http://localhost:5174`
5. When the backend is started by the launcher, it can also be stopped via **Stop Backend**

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CUL_BACKEND_PATH` | Override path to the backend directory |

## Architecture

```
desktop/
├── src/
│   ├── index.html      # Launcher page (HTML/CSS/JS)
│   ├── styles.css      # Caleb-branded styling
│   ├── main.js         # Status polling & Tauri commands
│   └── assets/
│       └── caleb-logo.jpg
├── src-tauri/
│   ├── src/
│   │   ├── lib.rs      # Rust: tray, menus, process manager
│   │   └── main.rs     # Binary entry point
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   └── capabilities/
│       └── default.json
└── package.json
```

## Troubleshooting

- **Backend not found**: Ensure the `backend/` directory is at the project root, or set `CUL_BACKEND_PATH`
- **Port already in use**: The backend and frontends must use ports 8000, 5173, 5174 respectively
- **AppImage fails to bundle**: Install `linuxdeploy` or use `.deb`/`.rpm` instead
