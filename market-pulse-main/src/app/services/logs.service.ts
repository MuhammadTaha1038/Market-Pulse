import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, forkJoin } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../enviornments/environment';

/**
 * Unified Log Entry - Standard format for all log types
 */
export interface UnifiedLogEntry {
  id: number;
  action: string;
  details: string;
  timestamp: string;
  user?: string;
  source: 'rules' | 'cron' | 'manual' | 'backup' | 'preset';
  canRevert?: boolean;
  revertData?: any;
}

/**
 * Logs Service - Fetches and aggregates logs from all sources
 */
@Injectable({
  providedIn: 'root'
})
export class LogsService {
  private baseUrl = environment.baseURL + environment.apiPrefix;

  constructor(private http: HttpClient) {}

  /**
   * Get recent rule logs from unified logs endpoint
   */
  getRuleLogs(limit: number = 2): Observable<UnifiedLogEntry[]> {
    return this.http.get<any>(`${this.baseUrl}/logs/rules?limit=${limit}`).pipe(
      map(response => {
        if (!response.logs) return [];
        return response.logs.map((log: any) => ({
          id: log.log_id,
          action: log.action,
          details: log.description,
          timestamp: log.performed_at,
          user: log.performed_by,
          source: 'rules' as const,
          canRevert: log.can_revert,
          revertData: log.revert_data
        }));
      })
    );
  }

  /**
   * Get recent cron job execution logs
   */
  getCronLogs(limit: number = 2): Observable<UnifiedLogEntry[]> {
    return this.http.get<any>(`${this.baseUrl}/cron/logs?limit=${limit}`).pipe(
      map(response => {
        if (!response.logs) return [];
        return response.logs.map((log: any) => ({
          id: log.id,
          action: `Job executed: ${log.status}`,
          details: `${log.job_name} - Duration: ${log.duration_seconds?.toFixed(2)}s - Processed: ${log.processed_count || 0} records`,
          timestamp: log.end_time || log.start_time,
          user: 'system',
          source: 'cron' as const
        }));
      })
    );
  }

  /**
   * Get recent manual upload logs
   */
  getManualUploadLogs(limit: number = 2): Observable<UnifiedLogEntry[]> {
    return this.http.get<any>(`${this.baseUrl}/manual-upload/history?limit=${limit}`).pipe(
      map(response => {
        if (!response.uploads) return [];
        return response.uploads.map((upload: any) => ({
          id: upload.id,
          action: `File uploaded: ${upload.status}`,
          details: `${upload.filename} - ${upload.rows_processed || 0} rows processed`,
          timestamp: upload.upload_time,
          user: upload.uploaded_by,
          source: 'manual' as const
        }));
      })
    );
  }

  /**
   * Get recent backup/restore activity logs
   */
  getBackupLogs(limit: number = 2): Observable<UnifiedLogEntry[]> {
    return this.http.get<any>(`${this.baseUrl}/backup/activity-logs?limit=${limit}`).pipe(
      map(response => {
        if (!response.logs) return [];
        return response.logs.map((log: any) => ({
          id: log.id || log.timestamp,
          action: log.action,
          details: log.details || '',
          timestamp: log.timestamp,
          user: log.user,
          source: 'backup' as const
        }));
      })
    );
  }

  /**
   * Get all recent logs from all sources
   */
  getAllRecentLogs(limitPerSource: number = 2): Observable<{
    rules: UnifiedLogEntry[];
    cron: UnifiedLogEntry[];
    manual: UnifiedLogEntry[];
    backup: UnifiedLogEntry[];
  }> {
    return forkJoin({
      rules: this.getRuleLogs(limitPerSource),
      cron: this.getCronLogs(limitPerSource),
      manual: this.getManualUploadLogs(limitPerSource),
      backup: this.getBackupLogs(limitPerSource)
    });
  }

  /**
   * Get combined logs from all sources, sorted by timestamp
   */
  getCombinedLogs(limitPerSource: number = 10): Observable<UnifiedLogEntry[]> {
    return this.getAllRecentLogs(limitPerSource).pipe(
      map(logs => {
        const combined = [
          ...logs.rules,
          ...logs.cron,
          ...logs.manual,
          ...logs.backup
        ];
        
        // Sort by timestamp descending (most recent first)
        combined.sort((a, b) => {
          return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
        });
        
        return combined;
      })
    );
  }

  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  /**
   * Revert a log entry (undo operation)
   */
  revertLog(logId: number, revertedBy: string = 'admin'): Observable<any> {
    return this.http.post(`${this.baseUrl}/logs/${logId}/revert`, { reverted_by: revertedBy });
  }
}
