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
};

export function getActiveDevice() { return _state.activeDevice; }
export function getDevName()      { return _state.devName; }

export function setActiveDevice(d) {
  _state.activeDevice = d;
  window._activeDevice = d;   // keep legacy window global in sync for app.js reads
}

export function setDevName(name) {
  _state.devName = name || 'Consola Android';
  window._devName = _state.devName;  // keep legacy window global in sync
}

// AppState proxy — lets app.js write via window.AppState.activeDevice = 'pc'
export const AppState = {
  get activeDevice() { return _state.activeDevice; },
  set activeDevice(v) { setActiveDevice(v); },
  get devName()      { return _state.devName; },
  set devName(v)     { setDevName(v); },
};
