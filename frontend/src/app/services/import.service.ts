// src/app/services/import.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ImportedRow {
  row_id: number;
  message_id: string;
  cusip: string;
  ticker: string;
  date: string;
  rank: number;
  px: number;
  bid: number;
  mid: number;
  ask: number;
  source: string;
  bias: string;
  is_parent: boolean;
  parent_id: number | null;
  child_count: number;
  color: string;
}

export interface ImportResponse {
  success: boolean;
  session_id: string;
  filename: string;
  rows_imported: number;
  rows_valid: number;
  parsing_errors: string[];
  sorted_preview: ImportedRow[];
  statistics: {
    total_rows: number;
    parent_rows: number;
    child_rows: number;
    unique_cusips: number;
  };
  duration_seconds: number;
}

@Injectable({
  providedIn: 'root'
})
export class ImportService {
  private apiUrl = 'http://127.0.0.1:3334/api';

  constructor(private http: HttpClient) {}

  importExcelFile(file: File, userId: number = 1): Observable<ImportResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId.toString());

    return this.http.post<ImportResponse>(`${this.apiUrl}/manual-color/import`, formData);
  }

  getPreview(sessionId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/manual-color/preview/${sessionId}`);
  }

  deleteRows(sessionId: string, rowIds: number[]): Observable<any> {
    return this.http.post(`${this.apiUrl}/manual-color/delete-rows`, {
      session_id: sessionId,
      row_ids: rowIds
    });
  }

  applyRules(sessionId: string, ruleIds: number[]): Observable<any> {
    return this.http.post(`${this.apiUrl}/manual-color/apply-rules`, {
      session_id: sessionId,
      rule_ids: ruleIds
    });
  }

  saveManualColors(sessionId: string, userId: number = 1): Observable<any> {
    return this.http.post(`${this.apiUrl}/manual-color/save`, {
      session_id: sessionId,
      user_id: userId
    });
  }
}