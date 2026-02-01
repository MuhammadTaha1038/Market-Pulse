/**
 * Environment Configuration
 * 
 * IMPORTANT: When deploying to production, update environmentProd.baseURL
 * This is the ONLY place you need to change the backend URL
 * 
 * Development: Uses local FastAPI server (http://localhost:3334)
 * Production: Update baseURL to your deployed backend URL
 */

export const environment = {
  production: false,
  baseURL: 'http://localhost:3334', // FastAPI Backend URL - Development
  apiVersion: 'v1',
  apiPrefix: '/api', // API prefix for all endpoints
  endpoints: {
    // Dashboard endpoints
    dashboard: '/dashboard',
    
    // Admin endpoints (NEW APIs from Milestone 2)
    rules: '/rules',              // Rules Engine API
    cronJobs: '/cron',            // Cron Jobs API (backend prefix is /api/cron)
    manualUpload: '/manual-upload', // Manual Upload API
    backup: '/backup'             // Backup & Restore API
  }
};

/**
 * Production Configuration
 * 
 * TODO: Before deployment, update baseURL to your production backend URL
 * Examples:
 *   - AWS: 'https://api.marketpulse.com'
 *   - Azure: 'https://marketpulse-api.azurewebsites.net'
 *   - Custom: 'https://your-domain.com/api'
 */
export const environmentProd = {
  production: true,
  baseURL: 'https://your-production-domain.com', // UPDATE THIS BEFORE PRODUCTION DEPLOYMENT
  apiVersion: 'v1',
  apiPrefix: '/api',
  endpoints: {
    dashboard: '/dashboard',
    rules: '/rules',
    cronJobs: '/cron',
    manualUpload: '/manual-upload',
    backup: '/backup'
  }
};