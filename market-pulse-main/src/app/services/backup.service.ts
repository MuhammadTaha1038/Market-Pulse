import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../enviornments/environment';

/**
 * Backup Interface - Represents a backup snapshot
 */
export interface Backup {
  id: number;
  filename: string;
  description: string;
  created_by: string;
  created_at: string;
  file_size_mb: number;
  row_count: number;
  checksum: string;
  status: 'success' | 'failed';
  error_message?: string;
}

/**
 * Backup Response - API response when creating backups
 */
export interface BackupResponse {
  message: string;
  backup: Backup;
}

/**
 * Backup History Response - List of all backups
 */
export interface BackupHistoryResponse {
  backups: Backup[];
  count: number;
}

/**
 * Restore Response - Response when restoring from backup
 */
export interface RestoreResponse {
  message: string;
  restore: {
    backup_id: number;
    pre_restore_backup_id: number;
    restored_by: string;
    restored_at: string;
    verification: {
      checksum_match: boolean;
      original_checksum: string;
      restored_checksum: string;
    };
  };
}

/**
 * Activity Log - Record of backup/restore activities
 */
export interface ActivityLog {
  timestamp: string;  // Backend returns timestamp not id
  action: string;
  user: string;       // Backend returns user not performed_by
  details: string;
  metadata: any;      // Backend returns metadata not details as object
}

/**
 * Activity Logs Response - List of activity logs
 */
export interface ActivityLogsResponse {
  logs: ActivityLog[];
  count: number;
}

/**
 * Backup Statistics Response - System statistics
 */
export interface BackupStatsResponse {
  output_file: {
    exists: boolean;
    path: string;
    size_mb: number;
    row_count: number;
    last_modified?: string;
  };
  backups: {
    total_count: number;
    successful_count: number;
    failed_count: number;
    total_size_mb: number;
    oldest_backup?: string;
    newest_backup?: string;
  };
  activity: {
    total_logs: number;
    recent_actions: string[];
  };
}

/**
 * Cleanup Response - Response when cleaning up old backups
 */
export interface CleanupResponse {
  message: string;
  deleted_count: number;
  deleted_backups: number[];
}

/**
 * Verify Response - Response when verifying backup integrity
 */
export interface VerifyResponse {
  message: string;
  verification: {
    backup_id: number;
    checksum_match: boolean;
    original_checksum: string;
    current_checksum: string;
    is_valid: boolean;
  };
}

/**
 * Backup Service - Manages backup and restore operations
 * 
 * This service provides all operations for backup/restore:
 * - Create backups
 * - Restore from backups
 * - View backup history
 * - Get system statistics
 * - Cleanup old backups
 * - Verify backup integrity
 * - View activity logs (audit trail)
 */
@Injectable({
  providedIn: 'root'
})
export class BackupService {
  private baseUrl = `${environment.baseURL}${environment.apiPrefix}${environment.endpoints.backup}`;

  constructor(private http: HttpClient) {}

  /**
   * Create new backup
   * @param description - Description of why backup is being created
   * @param createdBy - Username of person creating backup
   * @returns Observable of backup response
   */
  createBackup(description: string, createdBy: string): Observable<BackupResponse> {
    return this.http.post<BackupResponse>(`${this.baseUrl}/create`, {
      description,
      created_by: createdBy
    });
  }

  /**
   * Get backup history
   * @param limit - Optional limit for number of backups
   * @returns Observable of backup history
   */
  getBackupHistory(limit?: number): Observable<BackupHistoryResponse> {
    let params = new HttpParams();
    if (limit) {
      params = params.set('limit', limit.toString());
    }
    return this.http.get<BackupHistoryResponse>(`${this.baseUrl}/history`, { params });
  }

  /**
   * Get single backup by ID
   * @param id - Backup ID
   * @returns Observable of single backup
   */
  getBackupById(id: number): Observable<Backup> {
    return this.http.get<Backup>(`${this.baseUrl}/history/${id}`);
  }

  /**
   * Restore from backup
   * @param id - Backup ID
   * @param restoredBy - Username of person restoring
   * @param reason - Reason for restoration
   * @returns Observable of restore response
   */
  restoreBackup(id: number, restoredBy: string, reason: string): Observable<RestoreResponse> {
    return this.http.post<RestoreResponse>(`${this.baseUrl}/restore/${id}`, {
      restored_by: restoredBy,
      reason
    });
  }

  /**
   * Delete backup
   * @param id - Backup ID
   * @returns Observable of delete confirmation
   */
  deleteBackup(id: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.baseUrl}/history/${id}`);
  }

  /**
   * Get activity logs (audit trail)
   * @param limit - Optional limit for number of logs
   * @returns Observable of activity logs
   */
  getActivityLogs(limit?: number): Observable<ActivityLogsResponse> {
    let params = new HttpParams();
    if (limit) {
      params = params.set('limit', limit.toString());
    }
    return this.http.get<ActivityLogsResponse>(`${this.baseUrl}/activity-logs`, { params });
  }

  /**
   * Get system statistics
   * @returns Observable of system stats
   */
  getSystemStats(): Observable<BackupStatsResponse> {
    return this.http.get<BackupStatsResponse>(`${this.baseUrl}/stats`);
  }

  /**
   * Cleanup old backups
   * @param keepCount - Number of recent backups to keep
   * @returns Observable of cleanup response
   */
  cleanupOldBackups(keepCount: number): Observable<CleanupResponse> {
    return this.http.post<CleanupResponse>(`${this.baseUrl}/cleanup`, {
      keep_count: keepCount
    });
  }

  /**
   * Log custom activity
   * @param action - Action description
   * @param performedBy - Username
   * @param details - Additional details
   * @returns Observable of confirmation
   */
  logActivity(action: string, performedBy: string, details: any): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.baseUrl}/log-activity`, {
      action,
      performed_by: performedBy,
      details
    });
  }

  /**
   * Verify backup integrity
   * @param id - Backup ID
   * @returns Observable of verification result
   */
  verifyBackup(id: number): Observable<VerifyResponse> {
    return this.http.get<VerifyResponse>(`${this.baseUrl}/verify/${id}`);
  }
}
