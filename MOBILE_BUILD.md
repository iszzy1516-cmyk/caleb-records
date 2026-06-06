# Mobile Build — Student App

This document covers building the **Caleb Records Student** mobile app for Android and iOS.

## Tech Stack

- **Tauri v2 Mobile** — wraps the existing React student portal
- **Android** — minimum SDK 24 (Android 7.0), target SDK 34
- **iOS** — minimum iOS 13

## Prerequisites

### Android

1. **Android Studio** — [developer.android.com/studio](https://developer.android.com/studio)
2. **Android SDK** — installed via Android Studio SDK Manager
3. **Android NDK** — install via SDK Manager (Tools → SDK Manager → SDK Tools → NDK)
4. **Set environment variables:**
   ```bash
   export ANDROID_HOME=$HOME/Android/Sdk
   export NDK_HOME=$ANDROID_HOME/ndk/<version>
   export PATH=$PATH:$ANDROID_HOME/platform-tools
   ```

### iOS (macOS only)

1. **Xcode** — from Mac App Store
2. **iOS Simulator** — install via Xcode

### All Platforms

- **Node.js** 20+
- **Rust** — [rustup.rs](https://rustup.rs)
- **Tauri CLI** — `npm install -g @tauri-apps/cli`

## Quick Start

```bash
cd frontend
npm install
```

### Android

```bash
# Initialize Android project (one-time)
npx tauri android init

# Run on connected device or emulator
npx tauri android dev

# Build release APK
npx tauri android build --apk
```

APK output: `src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release.apk`

### iOS (macOS only)

```bash
# Initialize iOS project (one-time)
npx tauri ios init

# Run on simulator
npx tauri ios dev

# Build
npx tauri ios build
```

## Configuring the Server URL

The mobile app needs to know where your backend is running. On a real device, `localhost` won't work.

1. Open the app
2. Tap **⚙️ Settings** (gear icon in top navbar)
3. Enter your backend URL, e.g.:
   - `http://192.168.1.100:8000` (local network)
   - `https://records.calebuniversity.edu.ng` (production)
4. Tap **Save** and restart the app

## CI/CD — GitHub Actions

A workflow is already set up at `.github/workflows/build-mobile.yml`. Push a `v*` tag to trigger:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The workflow will build and upload the Android APK as an artifact.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ANDROID_HOME not set` | Export `ANDROID_HOME` pointing to your SDK directory |
| `NDK not found` | Install NDK via Android Studio SDK Manager, set `NDK_HOME` |
| `adb not found` | Add `$ANDROID_HOME/platform-tools` to PATH |
| App can't connect to backend | Check that the backend is accessible from the device network, and the correct URL is set in Settings |
| White screen on launch | Check that `VITE_API_URL` or `cul_api_url` in localStorage is valid |
