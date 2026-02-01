# Cron Jobs API Documentation

## Overview
The Cron Jobs API manages scheduled automation tasks for the MarketPulse system. It uses APScheduler with timezone support to run automated color processing at specified times.

**Base URL**: `/api/cron`

---

## Endpoints

### 1. Get All Cron Jobs
Retrieve all scheduled cron jobs with their next run times.

**Endpoint**: `GET /api/cron/jobs`

**Response**:
```json
{
  "jobs": [
    {
      "id": 1,
      "name": "Daily Morning Run",
      "schedule": "0 9 * * *",
      "is_active": true,
      "created_at": "2026-01-26T10:00:00",
      "updated_at": "2026-01-26T10:00:00",
      "last_run": "2026-01-26T09:00:00",
      "next_run": "2026-01-27T09:00:00"
    }
  ],
  "count": 1
}
```

**Response Fields**:
- `id` (int): Unique job identifier
- `name` (string): Job name/description
- `schedule` (string): Cron expression (e.g., "0 9 * * *")
- `is_active` (boolean): Whether the job is currently active
- `created_at` (string): ISO 8601 timestamp of creation
- `updated_at` (string): ISO 8601 timestamp of last update
- `last_run` (string | null): ISO 8601 timestamp of last execution
- `next_run` (string | null): ISO 8601 timestamp of next scheduled run

---

### 2. Get Active Cron Jobs
Retrieve only the active (enabled) cron jobs.

**Endpoint**: `GET /api/cron/jobs/active`

**Response**: Same format as "Get All Cron Jobs" but filtered to active jobs only.

---

### 3. Get Single Cron Job
Retrieve details of a specific cron job by ID.

**Endpoint**: `GET /api/cron/jobs/{job_id}`

**Path Parameters**:
- `job_id` (int): The unique identifier of the job

**Response**:
```json
{
  "id": 1,
  "name": "Daily Morning Run",
  "schedule": "0 9 * * *",
  "is_active": true,
  "created_at": "2026-01-26T10:00:00",
  "updated_at": "2026-01-26T10:00:00",
  "last_run": "2026-01-26T09:00:00",
  "next_run": "2026-01-27T09:00:00"
}
```

**Error Responses**:
- `404 Not Found`: Job with specified ID doesn't exist

---

### 4. Create Cron Job
Create a new scheduled cron job.

**Endpoint**: `POST /api/cron/jobs`

**Request Body**:
```json
{
  "name": "Daily Morning Run",
  "schedule": "0 9 * * *",
  "is_active": true
}
```

**Request Fields**:
- `name` (string, required): Job name/description
- `schedule` (string, required): Cron expression (format: `minute hour day month day_of_week`)
- `is_active` (boolean, optional): Whether job should be active (default: true)

**Cron Expression Examples**:
- `"0 9 * * *"` - Every day at 9:00 AM
- `"0 */6 * * *"` - Every 6 hours
- `"0 9 * * 1-5"` - Weekdays at 9:00 AM
- `"0 0 * * 0"` - Every Sunday at midnight
- `"30 14 * * *"` - Every day at 2:30 PM

**Response**:
```json
{
  "message": "Cron job created successfully",
  "job": {
    "id": 1,
    "name": "Daily Morning Run",
    "schedule": "0 9 * * *",
    "is_active": true,
    "created_at": "2026-01-26T10:00:00",
    "updated_at": "2026-01-26T10:00:00",
    "last_run": null,
    "next_run": "2026-01-27T09:00:00"
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid cron expression or validation error

---

### 5. Update Cron Job
Update an existing cron job's name, schedule, or active status.

**Endpoint**: `PUT /api/cron/jobs/{job_id}`

**Path Parameters**:
- `job_id` (int): The unique identifier of the job to update

**Request Body**:
```json
{
  "name": "Updated Job Name",
  "schedule": "0 18 * * *",
  "is_active": true
}
```

**Request Fields** (all optional):
- `name` (string): New job name
- `schedule` (string): New cron expression
- `is_active` (boolean): New active status

**Response**:
```json
{
  "message": "Cron job updated successfully",
  "job": {
    "id": 1,
    "name": "Updated Job Name",
    "schedule": "0 18 * * *",
    "is_active": true,
    "created_at": "2026-01-26T10:00:00",
    "updated_at": "2026-01-26T15:30:00",
    "last_run": "2026-01-26T09:00:00",
    "next_run": "2026-01-26T18:00:00"
  }
}
```

**Error Responses**:
- `404 Not Found`: Job with specified ID doesn't exist
- `400 Bad Request`: Invalid cron expression

**Important Notes**:
- When updating the schedule, the job is automatically rescheduled in APScheduler
- The `next_run` timestamp is recalculated based on the new schedule
- If `is_active` is set to `false`, the job is removed from the scheduler

---

### 6. Delete Cron Job
Delete a cron job permanently.

**Endpoint**: `DELETE /api/cron/jobs/{job_id}`

**Path Parameters**:
- `job_id` (int): The unique identifier of the job to delete

**Response**:
```json
{
  "message": "Cron job deleted successfully"
}
```

**Error Responses**:
- `404 Not Found`: Job with specified ID doesn't exist

---

### 7. Get Execution Logs
Retrieve execution history for all cron jobs.

**Endpoint**: `GET /api/cron/logs?limit=50`

**Query Parameters**:
- `limit` (int, optional): Maximum number of logs to return (default: 50)

**Response**:
```json
{
  "logs": [
    {
      "id": 1,
      "job_id": 1,
      "job_name": "Daily Morning Run",
      "triggered_by": "scheduled",
      "start_time": "2026-01-26T09:00:00",
      "end_time": "2026-01-26T09:02:15",
      "status": "success",
      "duration_seconds": 135.5,
      "original_count": 5213,
      "excluded_count": 0,
      "processed_count": 5213,
      "rules_applied": 0,
      "error": null
    },
    {
      "id": 2,
      "job_id": 1,
      "job_name": "Daily Morning Run",
      "triggered_by": "manual",
      "start_time": "2026-01-26T11:30:00",
      "end_time": "2026-01-26T11:30:45",
      "status": "failed",
      "duration_seconds": 45.2,
      "original_count": null,
      "excluded_count": null,
      "processed_count": null,
      "rules_applied": null,
      "error": "Database connection timeout"
    }
  ],
  "count": 2
}
```

**Response Fields**:
- `id` (int | null): Log entry ID (may be null for old logs)
- `job_id` (int): ID of the job that was executed
- `job_name` (string): Name of the job at execution time
- `triggered_by` (string): How the job was triggered ("scheduled" or "manual")
- `start_time` (string): ISO 8601 timestamp when execution started
- `end_time` (string | null): ISO 8601 timestamp when execution completed
- `status` (string): Execution status ("success", "failed", or "running")
- `duration_seconds` (float | null): Time taken to complete (seconds)
- `original_count` (int | null): Number of records fetched from database
- `excluded_count` (int | null): Number of records excluded by rules
- `processed_count` (int | null): Number of records successfully processed
- `rules_applied` (int | null): Number of active rules applied
- `error` (string | null): Error message if status is "failed"

**Notes**:
- Logs are returned in reverse chronological order (most recent first)
- Only the most recent 100 logs are retained in storage

---

### 8. Get Job-Specific Logs
Retrieve execution history for a specific cron job.

**Endpoint**: `GET /api/cron/logs/{job_id}?limit=20`

**Path Parameters**:
- `job_id` (int): The unique identifier of the job

**Query Parameters**:
- `limit` (int, optional): Maximum number of logs to return (default: 20)

**Response**: Same format as "Get Execution Logs" but filtered to the specified job only.

---

### 9. Manual Job Trigger
Manually trigger a cron job to run immediately (outside its schedule).

**Endpoint**: `POST /api/cron/jobs/{job_id}/trigger`

**Path Parameters**:
- `job_id` (int): The unique identifier of the job to trigger

**Response**:
```json
{
  "message": "Job triggered successfully",
  "job_id": 1,
  "status": "running"
}
```

**Error Responses**:
- `404 Not Found`: Job with specified ID doesn't exist

**Notes**:
- The job runs asynchronously in the background
- Check the execution logs endpoint to see the results
- Manual triggers are logged with `triggered_by: "manual"`

---

### 10. Get Schedule Examples
Get common cron schedule expression examples for reference.

**Endpoint**: `GET /api/cron/schedule-examples`

**Response**:
```json
{
  "examples": [
    {
      "schedule": "0 9 * * *",
      "description": "Every day at 9 AM"
    },
    {
      "schedule": "0 */6 * * *",
      "description": "Every 6 hours"
    },
    {
      "schedule": "0 9 * * 1-5",
      "description": "Weekdays at 9 AM"
    }
  ]
}
```

---

## Automation Task Flow

When a cron job executes, it performs these steps automatically:

1. **Fetch Data**: Load raw colors from the database (Excel file or Oracle)
2. **Apply Rules**: Filter data using active exclusion rules
3. **Rank Colors**: Apply ranking engine to determine parent/child relationships
4. **Save Output**: Append processed colors to the output file (S3 or Excel)
5. **Log Results**: Save execution statistics to the logs

**Processing Statistics**:
- `original_count`: Total records fetched from source
- `excluded_count`: Records filtered out by rules
- `processed_count`: Records successfully ranked and saved
- `rules_applied`: Number of active exclusion rules

---

## Timezone Configuration

The scheduler uses **Asia/Karachi (PKT)** timezone by default. This can be changed in `cron_service.py`:

```python
TIMEZONE = pytz.timezone('America/New_York')  # Change to your timezone
```

Common timezone values:
- `'America/New_York'` - Eastern Time
- `'America/Chicago'` - Central Time
- `'Europe/London'` - GMT/BST
- `'Asia/Kolkata'` - India Standard Time
- `'Asia/Tokyo'` - Japan Standard Time

**Important**: After changing timezone, restart the server for changes to take effect.

---

## Error Handling

### Common Error Scenarios:

1. **Invalid Cron Expression**
   - Status: 400 Bad Request
   - Solution: Verify cron expression format (minute hour day month day_of_week)

2. **Job Not Found**
   - Status: 404 Not Found
   - Solution: Verify the job_id exists using GET /api/cron/jobs

3. **Validation Error**
   - Status: 422 Unprocessable Entity
   - Solution: Check request body matches the schema

4. **Execution Failure**
   - Status: Logged in execution logs with status="failed"
   - Solution: Check the `error` field in logs for details

---

## Integration Example

### JavaScript/TypeScript Example:

```typescript
// Create a new cron job
const createJob = async () => {
  const response = await fetch('http://127.0.0.1:3334/api/cron/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'Evening Run',
      schedule: '0 18 * * *',
      is_active: true
    })
  });
  const data = await response.json();
  console.log('Job created:', data.job.id);
};

// Update a cron job
const updateJob = async (jobId: number) => {
  const response = await fetch(`http://127.0.0.1:3334/api/cron/jobs/${jobId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      schedule: '0 20 * * *',
      is_active: true
    })
  });
  const data = await response.json();
  console.log('Job updated:', data.message);
};

// Get execution logs
const getLogs = async () => {
  const response = await fetch('http://127.0.0.1:3334/api/cron/logs?limit=10');
  const data = await response.json();
  data.logs.forEach(log => {
    console.log(`${log.job_name}: ${log.status} - ${log.duration_seconds}s`);
  });
};

// Manually trigger a job
const triggerJob = async (jobId: number) => {
  const response = await fetch(`http://127.0.0.1:3334/api/cron/jobs/${jobId}/trigger`, {
    method: 'POST'
  });
  const data = await response.json();
  console.log('Job triggered:', data.message);
};
```

---

## Version History

### v1.2 (2026-01-26)
- Rules UI now fetches column names dynamically from `/api/config/columns` API
- Column configuration is now centralized for both manual upload and rules
- Frontend ConfigService created for column management

### v1.1 (2026-01-26)
- Added auto-incrementing `id` field to execution logs
- Made log `id` field optional for backward compatibility
- Added timezone support (configurable)
- Fixed execution log timestamp mapping
- Enhanced log details with processed record counts

### v1.0 (Initial Release)
- Basic CRUD operations for cron jobs
- Execution logging and history
- APScheduler integration
- Manual job triggering
