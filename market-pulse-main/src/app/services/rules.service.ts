import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../enviornments/environment';

/**
 * Rule Interface - Represents a business rule for filtering data
 * Matches backend API structure exactly
 */
export interface Rule {
  id?: number;
  name: string;
  conditions: RuleCondition[];  // Array of conditions
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

/**
 * Rule Condition - Single condition in a rule
 */
export interface RuleCondition {
  type: 'where' | 'and' | 'or';  // Condition type
  column: string;                 // Column name (e.g., 'BWIC_COVER')
  operator: string;               // Operator (e.g., 'equals', 'contains')
  value: string;                  // Value to compare
}

/**
 * Rule Response - API response when creating/updating rules
 */
export interface RuleResponse {
  message: string;
  rule: Rule;
}

/**
 * Rules List Response - API response for listing all rules
 */
export interface RulesListResponse {
  rules: Rule[];
  count: number;
}

/**
 * Rule Test Request - For testing rules without saving
 */
export interface RuleTestRequest {
  rules: Array<{
    field: string;
    operator: string;
    value: any;
    action: string;
  }>;
  data: any[];
}

/**
 * Rule Test Response - Results of rule testing
 */
export interface RuleTestResponse {
  message: string;
  results: {
    original_count: number;
    filtered_count: number;
    excluded_count: number;
    filtered_data: any[];
  };
}

/**
 * Operators Response - List of available operators
 */
export interface OperatorsResponse {
  operators: Array<{
    value: string;
    label: string;
    description: string;
  }>;
}

/**
 * Rules Service - Manages business rules for data filtering
 * 
 * This service provides all operations for the Rules Engine:
 * - Create, read, update, delete rules
 * - Toggle rules on/off
 * - Test rules before saving
 * - Get available operators
 */
@Injectable({
  providedIn: 'root'
})
export class RulesService {
  private baseUrl = `${environment.baseURL}${environment.apiPrefix}${environment.endpoints.rules}`;

  constructor(private http: HttpClient) {}

  /**
   * Get all rules
   * @returns Observable of rules list with count
   */
  getAllRules(): Observable<RulesListResponse> {
    return this.http.get<RulesListResponse>(this.baseUrl);
  }

  /**
   * Get single rule by ID
   * @param id - Rule ID
   * @returns Observable of single rule
   */
  getRuleById(id: number): Observable<Rule> {
    return this.http.get<Rule>(`${this.baseUrl}/${id}`);
  }

  /**
   * Create new rule
   * @param rule - Rule data (without ID)
   * @returns Observable of created rule response
   */
  createRule(rule: Omit<Rule, 'id' | 'created_at' | 'updated_at'>): Observable<RuleResponse> {
    return this.http.post<RuleResponse>(this.baseUrl, rule);
  }

  /**
   * Update existing rule
   * @param id - Rule ID
   * @param rule - Updated rule data
   * @returns Observable of updated rule response
   */
  updateRule(id: number, rule: Partial<Rule>): Observable<RuleResponse> {
    return this.http.put<RuleResponse>(`${this.baseUrl}/${id}`, rule);
  }

  /**
   * Delete rule
   * @param id - Rule ID
   * @returns Observable of delete confirmation
   */
  deleteRule(id: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.baseUrl}/${id}`);
  }

  /**
   * Toggle rule active status
   * @param id - Rule ID
   * @returns Observable of updated rule
   */
  toggleRule(id: number): Observable<RuleResponse> {
    return this.http.post<RuleResponse>(`${this.baseUrl}/${id}/toggle`, {});
  }

  /**
   * Test rule without saving
   * @param testRequest - Test data including rules and sample data
   * @returns Observable of test results
   */
  testRule(testRequest: RuleTestRequest): Observable<RuleTestResponse> {
    return this.http.post<RuleTestResponse>(`${this.baseUrl}/test`, testRequest);
  }

  /**
   * Get available operators
   * @returns Observable of operators list with descriptions
   */
  getOperators(): Observable<OperatorsResponse> {
    return this.http.get<OperatorsResponse>(`${this.baseUrl}/operators/list`);
  }
}
