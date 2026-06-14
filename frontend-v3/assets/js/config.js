/**
 * Aurelian Guide — Configuration
 * Global constants and settings for the frontend application.
 */
window.Aurelian = window.Aurelian || {};

Aurelian.config = {
  // Backend API base URL (served from same origin via StaticFiles mount)
  API_BASE: '/api',
  UPLOADS_BASE: '/uploads',

  // Polling intervals (milliseconds)
  POLL_INTERVAL_ROOM: 5000,       // Room status polling
  POLL_INTERVAL_AVATAR: 3000,     // Avatar state polling
  DASHBOARD_REFRESH_MS: 30000,    // Dashboard auto-refresh

  // UI timing
  TOAST_DURATION_MS: 4000,

  // Network
  REQUEST_TIMEOUT_MS: 15000,
  MAX_RETRIES: 1,
  RETRY_DELAY_MS: 1000,
};
