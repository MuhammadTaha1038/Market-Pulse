import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../enviornments/environment';

export interface ColorData {
  message_id: string;
  ticker: string;
  cusip: string;
  bias: string;
  date: string;
  price: number;
  spread: number;
  source: string;
  rank: number;
  is_parent: boolean;
  parent_message_id?: string;
  children_count?: number;
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
   * Get colors with pagination and filtering
   */
  getColors(skip: number = 0, limit: number = 50, assetClass?: string): Observable<ColorsResponse> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());
    
    if (assetClass) {
      params = params.set('asset_class', assetClass);
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
