import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../enviornments/environment';

export interface ColorData {
  message_id: number;
  ticker?: string;
  sector?: string;
  cusip?: string;
  date?: string;
  price_level?: number;
  bid?: number;
  ask?: number;
  px?: number;
  source?: string;
  bias?: string;
  rank?: number;
  cov_price?: number;
  percent_diff?: number;
  price_diff?: number;
  confidence?: number;
  date_1?: string;
  diff_status?: string;
  is_parent?: boolean;
  parent_message_id?: number;
  children_count?: number;
  // Legacy fields for backwards compatibility
  price?: number;
  spread?: number;
}

export interface ColorsResponse {
  colors: ColorData[];
  total_count: number;
  skip: number;
  limit: number;
}

export interface MonthlyStats {
  month: string;
  count: number;
}

export interface MonthlyStatsResponse {
  stats: MonthlyStats[];
}

export interface NextRunResponse {
  next_run: string;
  next_run_timestamp: string;
}

export interface AvailableSectorsResponse {
  sectors: string[];
  count: number;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = environment.baseURL;

  constructor(private http: HttpClient) {}

  /**
   * Get monthly statistics for dashboard chart
   */
  getMonthlyStats(assetClass?: string): Observable<MonthlyStatsResponse> {
    let params = new HttpParams();
    if (assetClass) {
      params = params.set('asset_class', assetClass);
    }
    return this.http.get<MonthlyStatsResponse>(`${this.baseUrl}/api/dashboard/monthly-stats`, { params });
  }

  /**
   * Get colors with pagination, filtering, and CLO-based column visibility
   */
  getColors(
    skip: number = 0, 
    limit: number = 50, 
    assetClass?: string, 
    cloId?: string,
    cusip?: string,
    ticker?: string,
    messageId?: number,
    source?: string,
    bias?: string
  ): Observable<ColorsResponse> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());
    
    if (assetClass) {
      params = params.set('asset_class', assetClass);
    }
    
    if (cloId) {
      params = params.set('clo_id', cloId);
    }
    
    if (cusip) {
      params = params.set('cusip', cusip);
    }
    
    if (ticker) {
      params = params.set('ticker', ticker);
    }
    
    if (messageId) {
      params = params.set('message_id', messageId.toString());
    }
    
    if (source) {
      params = params.set('source', source);
    }
    
    if (bias) {
      params = params.set('bias', bias);
    }
    
    return this.http.get<ColorsResponse>(`${this.baseUrl}/api/dashboard/colors`, { params });
  }

  /**
   * Get next run time for cron job
   */
  getNextRunTime(): Observable<NextRunResponse> {
    return this.http.get<NextRunResponse>(`${this.baseUrl}/api/dashboard/next-run`);
  }

  /**
   * Get available sectors/asset classes
   */
  getAvailableSectors(): Observable<AvailableSectorsResponse> {
    return this.http.get<AvailableSectorsResponse>(`${this.baseUrl}/api/dashboard/available-sectors`);
  }

  /**
   * Health check endpoint
   */
  healthCheck(): Observable<string> {
    return this.http.get(`${this.baseUrl}/health`, { responseType: 'text' });
  }
}
