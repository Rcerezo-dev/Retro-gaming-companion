// js/state.js — Shared UI state accessible from ES modules and legacy app.js
// Extracted from app.js during Phase 2 migration.
//
// Usage from ES modules:
//   import { getActiveDevice, getDevName, setActiveDevice, setDevName } from '../state.js';
//
// Usage from legacy app.js (via window):
//   window.AppState.activeDevice = 'pc';
//   window.AppState.devName;

const _state = {
  activeDevice: 'pc',             // 'pc' | 'both' | 'anbernic'
  devName: 'Consola Android',     // display name for the Android device
  deviceConnected: false,         // is Android device (ADB or SD card) connected?
  deviceConnectReason: '',        // why is/isn't device connected
};

export function getActiveDevice() { return _state.activeDevice; }
export function getDevName()      { return _state.devName; }
export function getDeviceConnected() { return _state.deviceConnected; }
export function getDeviceConnectReason() { return _state.deviceConnectReason; }

export function setActiveDevice(d) {
  _state.activeDevice = d;
  window._activeDevice = d;   // keep legacy window global in sync for app.js reads
}

export function setDevName(name) {
  _state.devName = name || 'Consola Android';
  window._devName = _state.devName;  // keep legacy window global in sync
}

export function setDeviceConnected(connected, reason = '') {
  _state.deviceConnected = connected;
  _state.deviceConnectReason = reason;
}

// AppState proxy — lets app.js write via window.AppState.activeDevice = 'pc'
export const AppState = {
  get activeDevice() { return _state.activeDevice; },
  set activeDevice(v) { setActiveDevice(v); },
  get devName()      { return _state.devName; },
  set devName(v)     { setDevName(v); },
  get deviceConnected() { return _state.deviceConnected; },
  get deviceConnectReason() { return _state.deviceConnectReason; },
};

// ── Device connectivity polling (UX-1/2-3) ───────────────────────────────────

let _deviceStatusPollTimer = null;

async function _pollDeviceStatus() {
  try {
    const response = await fetch('/api/device-status');
    if (!response.ok) return;
    const data = await response.json();
    setDeviceConnected(data.connected, data.reason);
  } catch (err) {
    // Silently fail — network errors are expected if server is down
  }
}

export function startDeviceStatusPolling(intervalMs = 4000) {
  // Start polling immediately
  _pollDeviceStatus();
  // Then poll on interval
  _deviceStatusPollTimer = setInterval(_pollDeviceStatus, intervalMs);
}

export function stopDeviceStatusPolling() {
  if (_deviceStatusPollTimer) {
    clearInterval(_deviceStatusPollTimer);
    _deviceStatusPollTimer = null;
  }
}
