import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface CLOType {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  parent_clo_id?: string;
}

export interface MainCLO extends CLOType {
  sub_clos: CLOType[];
}

export interface CLOHierarchy {
  main_clos: MainCLO[];
  total_main_clos: number;
  total_sub_clos: number;
}

export interface ColumnDetail {
  id: number;
  oracle_name: string;
  display_name: string;
  data_type: string;
  required: boolean;
  description?: string;
  visible?: boolean; // For UI state management
}

export interface CLOMapping {
  clo_id: string;
  clo_name: string;
  clo_type: string;
  parent_clo?: string;
  visible_columns: ColumnDetail[];
  hidden_columns: ColumnDetail[];
  total_columns: number;
  updated_by?: string;
  updated_at?: string;
}

export interface UpdateMappingRequest {
  clo_id: string;
  clo_type: string;
  visible_columns: string[];
}

@Injectable({
  providedIn: 'root'
})
export class CloMappingService {
  private apiUrl = 'http://127.0.0.1:3334/api/clo-mappings';
  private adminUrl = 'http://127.0.0.1:3334/api/admin';

  constructor(private http: HttpClient) {}

  /**
   * Get complete CLO hierarchy (main CLOs + sub CLOs)
   */
  getCLOHierarchy(): Observable<CLOHierarchy> {
    return this.http.get<CLOHierarchy>(`${this.apiUrl}/hierarchy`);
  }

  /**
   * Get all CLO-column mappings
   */
  getAllMappings(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/mappings`);
  }

  /**
   * Get mapping for a specific CLO
   */
  getCLOMapping(cloId: string): Observable<CLOMapping> {
    return this.http.get<CLOMapping>(`${this.apiUrl}/mappings/${cloId}`);
  }

  /**
   * Update column visibility for a CLO
   */
  updateCLOMapping(cloId: string, visibleColumns: string[], updatedBy: string = 'admin'): Observable<any> {
    const request: UpdateMappingRequest = {
      clo_id: cloId,
      clo_type: 'main', // Will be determined by backend
      visible_columns: visibleColumns
    };
    return this.http.put(`${this.apiUrl}/mappings/${cloId}?updated_by=${updatedBy}`, request);
  }

  /**
   * Reset CLO mapping to show all columns
   */
  resetCLOMapping(cloId: string, updatedBy: string = 'admin'): Observable<any> {
    return this.http.post(`${this.apiUrl}/reset/${cloId}?updated_by=${updatedBy}`, {});
  }

  /**
   * Get columns visible to a user based on their CLO type
   */
  getUserColumns(cloId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/user-columns/${cloId}`);
  }
  
  /**
   * Execute Oracle query and fetch column metadata
   */
  executeOracleQuery(query: string, cloId?: string): Observable<any> {
    return this.http.post(`${this.adminUrl}/oracle/execute-query`, {
      query: query,
      clo_id: cloId
    });
  }
  
  /**
   * Save Oracle query for a CLO
   */
  saveOracleQuery(query: string, cloId: string, queryName: string = 'base_query'): Observable<any> {
    return this.http.post(`${this.adminUrl}/oracle/save-query`, {
      query: query,
      clo_id: cloId,
      query_name: queryName
    });
  }
  
  /**
   * Get system status (data source type, etc.)
   */
  getSystemStatus(): Observable<any> {
    return this.http.get(`${this.adminUrl}/system-status`);
  }
}
