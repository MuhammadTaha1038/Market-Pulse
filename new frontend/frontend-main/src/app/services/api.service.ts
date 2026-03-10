import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from 'src/enviornments/environment';
// ==================== COLOR INTERFACES ====================

// Backend ColorRaw model
export interface ColorRaw {
    message_id: number;
    ticker: string;
    sector: string;
    cusip: string;
    date: string;
    price_level: number;
    bid: number;
    ask: number;
    px: number;
    source: string;
    bias: string;
    rank: number;
    cov_price: number;
    percent_diff: number;
    price_diff: number;
    confidence: number;
    date_1: string;
    diff_status: string;
}

// Backend ColorProcessed model (with parent/child hierarchy)
export interface ColorProcessed extends ColorRaw {
    is_parent: boolean;
    parent_message_id?: number;
    children_count?: number;
    children?: ColorProcessed[];
}

// For frontend display (mapped from backend)
export interface ColorDisplay {
    rowNumber: string;
    messageId: string;
    ticker: string;
    sector: string;
    cusip: string;
    date: string;
    price_level: number;
    bid: number;
    ask: number;
    px: number;
    source: string;
    bias: string;
    rank: number;
    cov_price: number;
    percent_diff: number;
    price_diff: number;
    confidence: number;
    isParent: boolean;
    childrenCount?: number;
    parentMessageId?: string;
}

// ==================== DASHBOARD RESPONSES ====================

export interface MonthlyStats {
    month: string;
    count: number;
}

export interface MonthlyStatsResponse {
    stats: MonthlyStats[];
}

export interface ColorResponse {
    total_count: number;
    page: number;
    page_size: number;
    colors: ColorProcessed[];
}

export interface NextRunResponse {
    next_run: string;
    next_run_timestamp: string;
    status: string;
}

export interface AvailableSectorsResponse {
    sectors: string[];
    count: number;
}

export interface OutputStats {
    automated_count: number;
    manual_count: number;
    parent_count: number;
    child_count: number;
    total_count: number;
}

// ==================== MANUAL UPLOAD RESPONSES ====================

export interface UploadResponse {
    success: boolean;
    filename: string;
    total_rows: number;
    valid_colors: number;
    errors_count: number;
    errors: string[];
    colors: ColorRaw[];
}

export interface ProcessResponse {
    success: boolean;
    input_count: number;
    processed_count: number;
    parents: number;
    children: number;
    message: string;
}

export interface ClearOutputResponse {
    success: boolean;
    message: string;
}

// ==================== ADMIN/COLUMN CONFIG ====================

export interface ColumnConfig {
    id?: number;
    oracle_name: string;
    display_name: string;
    data_type: string;
    required: boolean;
    description: string;
}

export interface ColumnsResponse {
    success: boolean;
    oracle_table: string;
    total_columns: number;
    columns: ColumnConfig[];
}

export interface SqlPreviewResponse {
    success: boolean;
    sql_query: string;
    column_count: number;
    oracle_table: string;
}

export interface OracleConfig {
    host: string;
    port: number;
    service_name: string;
    user: string;
    password: string;
}

// Add to interfaces in api.service.ts
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

export interface ConnectionInfo {
    success: boolean;
    using_oracle: boolean;
    oracle_table?: string;
    column_count?: number;
    connection_status?: string;
}

// ==================== RULES INTERFACES ====================

export interface RuleConditionBackend {
    type: string;       // 'where', 'and', 'or'
    column: string;
    operator: string;
    value: string;
    value2?: string;    // For 'between' operator
}

export interface Rule {
    id: number;
    name: string;
    conditions: RuleConditionBackend[];
    is_active: boolean;
    created_at?: string;
    updated_at?: string;
}

export interface RuleCreate {
    name: string;
    conditions: RuleConditionBackend[];
    is_active: boolean;
}

export interface RuleUpdate {
    name?: string;
    conditions?: RuleConditionBackend[];
    is_active?: boolean;
}

export interface RulesResponse {
    rules: Rule[];
    count: number;
}

export interface RuleOperator {
    value: string;
    label: string;
    type: string;   // 'numeric' | 'text'
}

// ==================== CRON JOB INTERFACES ====================

export interface CronJob {
    id: number;
    name: string;
    schedule: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
    last_run?: string;
    next_run?: string;
}

export interface CronJobCreate {
    name: string;
    schedule: string;
    is_active: boolean;
}

export interface CronJobUpdate {
    name?: string;
    schedule?: string;
    is_active?: boolean;
}

export interface CronJobsResponse {
    jobs: CronJob[];
    count: number;
}

export interface CronExecutionLog {
    id?: number;
    job_id: number;
    job_name: string;
    triggered_by: string;
    start_time: string;
    end_time?: string;
    status: string;
    duration_seconds?: number;
    original_count?: number;
    excluded_count?: number;
    processed_count?: number;
    rules_applied?: number;
    error?: string;
}

export interface CronScheduleExample {
    expression: string;
    description: string;
    frequency: string;
}

// ==================== LOGS INTERFACES ====================

export interface LogEntry {
    log_id: number;
    module: string;
    action: string;
    description: string;
    performed_by: string;
    performed_at: string;
    entity_id?: number;
    entity_name?: string;
    can_revert: boolean;
    reverted_at?: string;
    reverted_by?: string;
    metadata?: any;
}

export interface LogsResponse {
    logs: LogEntry[];
    count: number;
    module?: string;
}

// ==================== PRESETS INTERFACES ====================

export interface PresetConditionBackend {
    column: string;
    operator: string;
    value: string;
    value2?: string;
}

export interface Preset {
    id: number;
    name: string;
    description?: string;
    conditions: PresetConditionBackend[];
    created_at?: string;
    created_by?: string;
}

export interface PresetCreate {
    name: string;
    conditions: PresetConditionBackend[];
    description?: string;
}

export interface PresetUpdate {
    name?: string;
    conditions?: PresetConditionBackend[];
    description?: string;
}

export interface PresetsResponse {
    presets: Preset[];
    count: number;
}

// ==================== SEARCH / FILTER INTERFACES ====================

export interface SearchFilter {
    field: string;
    operator: string;
    value: any;
    value2?: any;
}

export interface SearchRequest {
    filters: SearchFilter[];
    skip?: number;
    limit?: number;
    sort_by?: string;
    sort_order?: string;
    clo_id?: string;
}

export interface SearchResponse {
    total_count: number;
    returned_count: number;
    page: number;
    page_size: number;
    results: any[];
    available_fields: string[];
}

export interface SearchableField {
    name: string;
    display_name: string;
    data_type: string;
    required: boolean;
    description: string;
    searchable: boolean;
}

export interface SearchFieldsResponse {
    version: string;
    total_fields: number;
    fields: SearchableField[];
    clo_filtered: boolean;
    supported_operators: { [key: string]: string[] };
}

export interface DashboardFilterParams {
    cusip?: string;
    ticker?: string;
    message_id?: number;
    asset_class?: string;
    source?: string;
    bias?: string;
    processing_type?: string;
    date_from?: string;
    date_to?: string;
}

// ==================== CLO MAPPING INTERFACES ====================

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
    visible?: boolean;
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

export interface UserCLOSelection {
    cloId: string;
    cloName: string;
    mainCLO: string;
    visibleColumns: string[];
    selectedAt: Date;
}

// ==================== SYSTEM STATUS INTERFACES ====================

export interface SystemStatus {
    data_source: {
        info: {
            type: string;
            [key: string]: any;
        };
    };
    output_destination: {
        info: {
            type: string;
            [key: string]: any;
        };
    };
    s3_ready: boolean;
    oracle_ready: boolean;
}

export interface ExecuteQueryRequest {
    query: string;
    clo_id?: string;
}

export interface SaveQueryRequest {
    query: string;
    clo_id: string;
    query_name?: string;
}

@Injectable({
    providedIn: 'root'
})
export class ApiService {
    private baseUrl = environment.baseURL;

    constructor(private http: HttpClient) {}

    // ==================== DASHBOARD ENDPOINTS ====================

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
     * Get colors with pagination and filtering (supports CLO filtering for Oracle)
     */
    getColors(skip: number = 0, limit: number = 50, assetClass?: string, cloId?: string): Observable<ColorResponse> {
        let params = new HttpParams().set('skip', skip.toString()).set('limit', limit.toString());

        if (assetClass) {
            params = params.set('asset_class', assetClass);
        }
        if (cloId) {
            params = params.set('clo_id', cloId);
        }

        return this.http.get<ColorResponse>(`${this.baseUrl}/api/dashboard/colors`, { params });
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
     * Get CLO hierarchy (main types + sub types)
     */
    getCloHierarchy(): Observable<CLOHierarchy> {
        return this.http.get<CLOHierarchy>(`${this.baseUrl}/api/clo-mappings/hierarchy`);
    }

    /**
     * Get all CLO mappings
     */
    getAllCloMappings(): Observable<CLOMapping[]> {
        return this.http.get<CLOMapping[]>(`${this.baseUrl}/api/clo-mappings/mappings`);
    }

    /**
     * Get CLO mapping for a specific CLO
     */
    getCloMapping(cloId: string): Observable<CLOMapping> {
        return this.http.get<CLOMapping>(`${this.baseUrl}/api/clo-mappings/mappings/${cloId}`);
    }

    /**
     * Update CLO column mapping (visible columns)
     */
    updateCloMapping(cloId: string, visibleColumns: string[], updatedBy: string = 'admin'): Observable<any> {
        const request: UpdateMappingRequest = { clo_id: cloId, clo_type: 'main', visible_columns: visibleColumns };
        return this.http.put(`${this.baseUrl}/api/clo-mappings/mappings/${cloId}?updated_by=${updatedBy}`, request);
    }

    /**
     * Reset CLO mapping to default (all columns visible)
     */
    resetCloMapping(cloId: string, updatedBy: string = 'admin'): Observable<any> {
        return this.http.post(`${this.baseUrl}/api/clo-mappings/reset/${cloId}?updated_by=${updatedBy}`, {});
    }

    /**
     * Get user-visible columns for a CLO
     */
    getUserColumns(cloId: string): Observable<any> {
        return this.http.get(`${this.baseUrl}/api/clo-mappings/user-columns/${cloId}`);
    }

    // ==================== ORACLE ADMIN ENDPOINTS ====================

    /**
     * Execute Oracle query and get column metadata
     */
    executeOracleQuery(query: string, cloId?: string): Observable<any> {
        return this.http.post(`${this.baseUrl}/api/admin/oracle/execute-query`, { query, clo_id: cloId });
    }

    /**
     * Save Oracle query for a CLO
     */
    saveOracleQuery(query: string, cloId: string, queryName: string = 'base_query'): Observable<any> {
        return this.http.post(`${this.baseUrl}/api/admin/oracle/save-query`, { query, clo_id: cloId, query_name: queryName });
    }

    /**
     * Execute query with sample data (returns up to 5 rows)
     */
    executeQueryWithSample(query: string, cloId?: string): Observable<any> {
        return this.http.post(`${this.baseUrl}/api/admin/execute-query`, { query, clo_id: cloId });
    }

    /**
     * Save CLO query to column_config.json
     */
    saveQueryConfig(query: string, cloId: string, queryName: string = 'base_query'): Observable<any> {
        return this.http.post(`${this.baseUrl}/api/admin/save-query`, { query, clo_id: cloId, query_name: queryName });
    }

    /**
     * Update enabled columns for a CLO
     */
    updateCloColumns(cloId: string, columns: string[]): Observable<any> {
        return this.http.post(`${this.baseUrl}/api/admin/update-clo-columns`, { clo_id: cloId, columns });
    }

    /**
     * Get comprehensive system status (data source, output destination, S3/Oracle readiness)
     */
    getSystemStatus(): Observable<SystemStatus> {
        return this.http.get<SystemStatus>(`${this.baseUrl}/api/admin/system-status`);
    }

    /**
     * Get saved Oracle query for a specific CLO
     */
    getSavedQuery(cloId: string): Observable<any> {
        return this.http.get(`${this.baseUrl}/api/admin/oracle/saved-query/${cloId}`);
    }

    /**
     * Test Oracle credentials API connectivity
     * Checks if ORACLE_CREDENTIALS_API_URL is configured and reachable
     */
    testCredentialsApi(): Observable<any> {
        return this.http.post(`${this.baseUrl}/api/admin/oracle/test-credentials-api`, {});
    }

    /**
     * Get output statistics
     */
    getOutputStats(): Observable<OutputStats> {
        return this.http.get<OutputStats>(`${this.baseUrl}/api/dashboard/output-stats`);
    }

    // ==================== MANUAL COLOR ENDPOINTS ====================

    /**
     * Upload Excel file for manual processing
     */
    // Change the existing uploadManualColors method in api.service.ts
    uploadManualColors(file: File): Observable<any> {
        const formData = new FormData();
        formData.append('file', file);

        // Change from /api/manual/upload-excel to /api/manual-color/import
        return this.http.post<any>(`${this.baseUrl}/api/manual-color/import`, formData);
    }

    /**
     * Process manual colors through ranking engine
     */
    processManualColors(colors: ColorRaw[]): Observable<ProcessResponse> {
        return this.http.post<ProcessResponse>(`${this.baseUrl}/api/manual/process-manual-colors`, colors);
    }

    /**
     * Clear output file (WARNING: deletes all processed data)
     */
    clearOutputFile(): Observable<ClearOutputResponse> {
        return this.http.post<ClearOutputResponse>(`${this.baseUrl}/api/manual/clear-output`, {});
    }

    // ==================== ADMIN ENDPOINTS ====================

    /**
     * Get all column configurations
     */
    getColumnConfig(): Observable<ColumnsResponse> {
        return this.http.get<ColumnsResponse>(`${this.baseUrl}/api/admin/columns`);
    }

    /**
     * Add new column configuration
     */
    addColumn(column: ColumnConfig): Observable<any> {
        return this.http.post(`${this.baseUrl}/api/admin/columns`, column);
    }

    /**
     * Update column configuration
     */
    updateColumn(columnId: number, updates: Partial<ColumnConfig>): Observable<any> {
        return this.http.put(`${this.baseUrl}/api/admin/columns/${columnId}`, updates);
    }

    /**
     * Delete column configuration
     */
    deleteColumn(columnId: number): Observable<any> {
        return this.http.delete(`${this.baseUrl}/api/admin/columns/${columnId}`);
    }

    /**
     * Update Oracle table name
     */
    updateOracleTable(tableName: string): Observable<any> {
        return this.http.put(`${this.baseUrl}/api/admin/oracle-table`, { table_name: tableName });
    }

    /**
     * Preview SQL query
     */
    previewSqlQuery(whereClause?: string): Observable<SqlPreviewResponse> {
        let params = new HttpParams();
        if (whereClause) {
            params = params.set('where_clause', whereClause);
        }
        return this.http.get<SqlPreviewResponse>(`${this.baseUrl}/api/admin/sql-preview`, { params });
    }

    /**
     * Test Oracle connection
     */
    testOracleConnection(): Observable<any> {
        return this.http.post(`${this.baseUrl}/api/admin/oracle/test-connection`, {});
    }

    /**
     * Enable Oracle mode
     */
    enableOracle(config: OracleConfig): Observable<any> {
        return this.http.post(`${this.baseUrl}/api/admin/oracle/enable`, config);
    }

    /**
     * Get connection information
     */
    getConnectionInfo(): Observable<ConnectionInfo> {
        return this.http.get<ConnectionInfo>(`${this.baseUrl}/api/admin/connection-info`);
    }

    // ==================== LOOKUP METHODS ====================

    /**
     * Fetch color data by message ID
     */
    getColorByMessageId(messageId: number): Observable<ColorResponse> {
        const params = new HttpParams()
            .set('message_id', messageId.toString())
            .set('limit', '1');
        return this.http.get<ColorResponse>(`${this.baseUrl}/api/dashboard/colors`, { params });
    }

    // ==================== UTILITY METHODS ====================

    /**
     * Health check endpoint
     */
    healthCheck(): Observable<string> {
        return this.http.get(`${this.baseUrl}/health`, { responseType: 'text' });
    }

    /**
     * Get API version
     */
    getVersion(): Observable<string> {
        return this.http.get(`${this.baseUrl}/version`, { responseType: 'text' });
    }

    /**
     * Fetch live Oracle query data for a CLO and create a preview session.
     * Same response format as importManualColorFile.
     */
    fetchManualColorFromQuery(cloId: string, userId: number = 1): Observable<any> {
        return this.http.post<any>(`${this.baseUrl}/api/manual-color/fetch-from-query`, {
            clo_id: cloId,
            user_id: userId
        });
    }

    /**
     * Import Excel file for manual color processing (NEW BACKEND)
     * This should replace the existing uploadManualColors method
     */
    importManualColorFile(file: File, userId: number = 1): Observable<any> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', userId.toString());

        return this.http.post<any>(`${this.baseUrl}/api/manual-color/import`, formData);
    }

    /**
     * Get preview data
     */
    getManualColorPreview(sessionId: string): Observable<any> {
        return this.http.get(`${this.baseUrl}/api/manual-color/preview/${sessionId}`);
    }

    /**
     * Apply rules to imported data
     */
    applyManualColorRules(sessionId: string, ruleIds: number[]): Observable<any> {
        return this.http.post(`${this.baseUrl}/api/manual-color/apply-rules`, {
            session_id: sessionId,
            rule_ids: ruleIds
        });
    }

    /**
     * Delete rows from imported data
     */
    deleteManualColorRows(sessionId: string, rowIds: number[]): Observable<any> {
        return this.http.post(`${this.baseUrl}/api/manual-color/delete-rows`, {
            session_id: sessionId,
            row_ids: rowIds
        });
    }

    /**
     * Save manual colors
     */
    saveManualColors(sessionId: string, userId: number = 1): Observable<any> {
        return this.http.post(`${this.baseUrl}/api/manual-color/save`, {
            session_id: sessionId,
            user_id: userId
        });
    }

    // ==================== SEARCH / FILTER ENDPOINTS ====================

    /**
     * Generic search with multiple filters (POST /api/search/generic)
     */
    searchColors(filters: SearchFilter[], skip: number = 0, limit: number = 500, sortBy?: string, sortOrder?: string): Observable<SearchResponse> {
        const body: SearchRequest = {
            filters,
            skip,
            limit,
            sort_by: sortBy,
            sort_order: sortOrder || 'desc'
        };
        return this.http.post<SearchResponse>(`${this.baseUrl}/api/search/generic`, body);
    }

    /**
     * Get all searchable fields from column config (GET /api/search/fields)
     * Pass cloId to get only the columns visible for that CLO.
     */
    getSearchableFields(cloId?: string): Observable<SearchFieldsResponse> {
        let params = new HttpParams();
        if (cloId) params = params.set('clo_id', cloId);
        return this.http.get<SearchFieldsResponse>(`${this.baseUrl}/api/search/fields`, { params });
    }

    /**
     * Get colors with filter params via dashboard endpoint
     */
    getColorsFiltered(skip: number = 0, limit: number = 100, filters?: DashboardFilterParams): Observable<ColorResponse> {
        let params = new HttpParams().set('skip', skip.toString()).set('limit', limit.toString());

        if (filters) {
            if (filters.cusip) params = params.set('cusip', filters.cusip);
            if (filters.ticker) params = params.set('ticker', filters.ticker);
            if (filters.message_id) params = params.set('message_id', filters.message_id.toString());
            if (filters.asset_class) params = params.set('asset_class', filters.asset_class);
            if (filters.source) params = params.set('source', filters.source);
            if (filters.bias) params = params.set('bias', filters.bias);
            if (filters.processing_type) params = params.set('processing_type', filters.processing_type);
            if (filters.date_from) params = params.set('date_from', filters.date_from);
            if (filters.date_to) params = params.set('date_to', filters.date_to);
        }

        return this.http.get<ColorResponse>(`${this.baseUrl}/api/dashboard/colors`, { params });
    }

    /**
     * Convert backend ColorProcessed to frontend ColorDisplay format
     */
    convertToDisplayFormat(color: ColorProcessed, index: number): ColorDisplay {
        return {
            rowNumber: String(index + 1),
            messageId: String(color.message_id),
            ticker: color.ticker,
            sector: color.sector,
            cusip: color.cusip,
            date: color.date,
            price_level: color.price_level,
            bid: color.bid,
            ask: color.ask,
            px: color.px,
            source: color.source,
            bias: color.bias,
            rank: color.rank,
            cov_price: color.cov_price,
            percent_diff: color.percent_diff,
            price_diff: color.price_diff,
            confidence: color.confidence,
            isParent: color.is_parent,
            childrenCount: color.children_count || 0,
            parentMessageId: color.parent_message_id ? String(color.parent_message_id) : undefined
        };
    }

    /**
     * Convert frontend ColorDisplay back to backend ColorRaw format
     */
    convertToBackendFormat(color: ColorDisplay): ColorRaw {
        return {
            message_id: parseInt(color.messageId),
            ticker: color.ticker,
            sector: color.sector,
            cusip: color.cusip,
            date: color.date,
            price_level: color.price_level,
            bid: color.bid,
            ask: color.ask,
            px: color.px,
            source: color.source,
            bias: color.bias,
            rank: color.rank,
            cov_price: color.cov_price,
            percent_diff: color.percent_diff,
            price_diff: color.price_diff,
            confidence: color.confidence,
            date_1: color.date,
            diff_status: ''
        };
    }

    // ==================== RULES ENDPOINTS ====================

    getRules(): Observable<RulesResponse> {
        return this.http.get<RulesResponse>(`${this.baseUrl}/api/rules`);
    }

    getActiveRules(): Observable<RulesResponse> {
        return this.http.get<RulesResponse>(`${this.baseUrl}/api/rules/active`);
    }

    getRuleById(ruleId: number): Observable<{ rule: Rule }> {
        return this.http.get<{ rule: Rule }>(`${this.baseUrl}/api/rules/${ruleId}`);
    }

    createRule(rule: RuleCreate): Observable<{ message: string; rule: Rule }> {
        return this.http.post<{ message: string; rule: Rule }>(`${this.baseUrl}/api/rules`, rule);
    }

    updateRule(ruleId: number, rule: RuleUpdate): Observable<{ message: string; rule: Rule }> {
        return this.http.put<{ message: string; rule: Rule }>(`${this.baseUrl}/api/rules/${ruleId}`, rule);
    }

    deleteRule(ruleId: number): Observable<{ message: string }> {
        return this.http.delete<{ message: string }>(`${this.baseUrl}/api/rules/${ruleId}`);
    }

    toggleRule(ruleId: number): Observable<{ message: string; rule: Rule }> {
        return this.http.post<{ message: string; rule: Rule }>(`${this.baseUrl}/api/rules/${ruleId}/toggle`, {});
    }

    getRuleOperators(): Observable<{ operators: RuleOperator[] }> {
        return this.http.get<{ operators: RuleOperator[] }>(`${this.baseUrl}/api/rules/operators/list`);
    }

    getRuleLogs(limit: number = 50): Observable<{ logs: any[]; count: number }> {
        const params = new HttpParams().set('limit', limit.toString());
        return this.http.get<{ logs: any[]; count: number }>(`${this.baseUrl}/api/rules/logs`, { params });
    }

    // ==================== CRON JOB ENDPOINTS ====================

    getCronJobs(): Observable<CronJobsResponse> {
        return this.http.get<CronJobsResponse>(`${this.baseUrl}/api/cron/jobs`);
    }

    getActiveCronJobs(): Observable<CronJobsResponse> {
        return this.http.get<CronJobsResponse>(`${this.baseUrl}/api/cron/jobs/active`);
    }

    getCronJobById(jobId: number): Observable<CronJob> {
        return this.http.get<CronJob>(`${this.baseUrl}/api/cron/jobs/${jobId}`);
    }

    createCronJob(job: CronJobCreate): Observable<{ message: string; job: CronJob }> {
        return this.http.post<{ message: string; job: CronJob }>(`${this.baseUrl}/api/cron/jobs`, job);
    }

    updateCronJob(jobId: number, job: CronJobUpdate): Observable<{ message: string; job: CronJob }> {
        return this.http.put<{ message: string; job: CronJob }>(`${this.baseUrl}/api/cron/jobs/${jobId}`, job);
    }

    deleteCronJob(jobId: number): Observable<{ message: string; job_id: number }> {
        return this.http.delete<{ message: string; job_id: number }>(`${this.baseUrl}/api/cron/jobs/${jobId}`);
    }

    toggleCronJob(jobId: number): Observable<{ message: string; job: CronJob }> {
        return this.http.post<{ message: string; job: CronJob }>(`${this.baseUrl}/api/cron/jobs/${jobId}/toggle`, {});
    }

    triggerCronJob(jobId: number, override: boolean = false): Observable<any> {
        const params = new HttpParams().set('override', override.toString());
        return this.http.post<any>(`${this.baseUrl}/api/cron/jobs/${jobId}/trigger`, {}, { params });
    }

    getCronExecutionLogs(limit: number = 50): Observable<{ logs: CronExecutionLog[]; count: number }> {
        const params = new HttpParams().set('limit', limit.toString());
        return this.http.get<{ logs: CronExecutionLog[]; count: number }>(`${this.baseUrl}/api/cron/logs`, { params });
    }

    getCronJobExecutionLogs(jobId: number, limit: number = 20): Observable<{ logs: CronExecutionLog[]; count: number }> {
        const params = new HttpParams().set('limit', limit.toString());
        return this.http.get<{ logs: CronExecutionLog[]; count: number }>(`${this.baseUrl}/api/cron/logs/${jobId}`, { params });
    }

    getCronScheduleExamples(): Observable<{ examples: CronScheduleExample[] }> {
        return this.http.get<{ examples: CronScheduleExample[] }>(`${this.baseUrl}/api/cron/schedule-examples`);
    }

    // ==================== UNIFIED LOGS ENDPOINTS ====================

    getLogs(module?: string, limit: number = 4): Observable<LogsResponse> {
        let params = new HttpParams().set('limit', limit.toString());
        if (module) {
            params = params.set('module', module);
        }
        return this.http.get<LogsResponse>(`${this.baseUrl}/api/logs`, { params });
    }

    getRulesLogs(limit: number = 4): Observable<LogsResponse> {
        const params = new HttpParams().set('limit', limit.toString());
        return this.http.get<LogsResponse>(`${this.baseUrl}/api/logs/rules`, { params });
    }

    getRestoreLogs(limit: number = 4): Observable<LogsResponse> {
        const params = new HttpParams().set('limit', limit.toString());
        return this.http.get<LogsResponse>(`${this.baseUrl}/api/logs/restore`, { params });
    }

    getCronLogs(limit: number = 4): Observable<LogsResponse> {
        const params = new HttpParams().set('limit', limit.toString());
        return this.http.get<LogsResponse>(`${this.baseUrl}/api/logs/cron`, { params });
    }

    getLogStats(): Observable<any> {
        return this.http.get<any>(`${this.baseUrl}/api/logs/stats`);
    }

    revertLog(logId: number, revertedBy: string = 'admin'): Observable<any> {
        return this.http.post<any>(`${this.baseUrl}/api/logs/${logId}/revert`, { reverted_by: revertedBy });
    }

    // ==================== PRESETS ENDPOINTS ====================

    getPresets(): Observable<PresetsResponse> {
        return this.http.get<PresetsResponse>(`${this.baseUrl}/api/presets`);
    }

    getPresetById(presetId: number): Observable<{ preset: Preset }> {
        return this.http.get<{ preset: Preset }>(`${this.baseUrl}/api/presets/${presetId}`);
    }

    createPreset(preset: PresetCreate): Observable<{ message: string; preset: Preset }> {
        return this.http.post<{ message: string; preset: Preset }>(`${this.baseUrl}/api/presets`, preset);
    }

    updatePreset(presetId: number, preset: PresetUpdate): Observable<{ message: string; preset: Preset }> {
        return this.http.put<{ message: string; preset: Preset }>(`${this.baseUrl}/api/presets/${presetId}`, preset);
    }

    deletePreset(presetId: number): Observable<{ message: string }> {
        return this.http.delete<{ message: string }>(`${this.baseUrl}/api/presets/${presetId}`);
    }

    getPresetStats(): Observable<any> {
        return this.http.get<any>(`${this.baseUrl}/api/presets/stats`);
    }

    // ==================== EMAIL ====================

    sendEmail(payload: { to_emails?: string[]; subject?: string; body?: string; attach_output_file?: boolean }): Observable<{ success: boolean; message: string }> {
        return this.http.post<{ success: boolean; message: string }>(`${this.baseUrl}/api/email/send`, payload);
    }

    getEmailConfig(): Observable<any> {
        return this.http.get<any>(`${this.baseUrl}/api/email/config`);
    }

    testEmailConnection(): Observable<{ success: boolean; message: string }> {
        return this.http.post<{ success: boolean; message: string }>(`${this.baseUrl}/api/email/test`, {});
    }

    getEmailLogs(limit: number = 50): Observable<{ logs: any[]; count: number }> {
        const params = new HttpParams().set('limit', limit.toString());
        return this.http.get<{ logs: any[]; count: number }>(`${this.baseUrl}/api/email/logs`, { params });
    }

    // ==================== BACKUP & RESTORE ====================

    getBackupHistory(limit: number = 50): Observable<{ backups: any[]; count: number }> {
        const params = new HttpParams().set('limit', limit.toString());
        return this.http.get<{ backups: any[]; count: number }>(`${this.baseUrl}/api/backup/history`, { params });
    }

    createBackup(description?: string, createdBy?: string): Observable<{ message: string; backup: any }> {
        const formData = new FormData();
        if (description) formData.append('description', description);
        if (createdBy) formData.append('created_by', createdBy);
        return this.http.post<{ message: string; backup: any }>(`${this.baseUrl}/api/backup/create`, formData);
    }

    restoreBackup(backupId: number, restoredBy?: string): Observable<{ message: string; result: any }> {
        const formData = new FormData();
        if (restoredBy) formData.append('restored_by', restoredBy);
        return this.http.post<{ message: string; result: any }>(`${this.baseUrl}/api/backup/restore/${backupId}`, formData);
    }

    deleteBackup(backupId: number): Observable<{ message: string }> {
        return this.http.delete<{ message: string }>(`${this.baseUrl}/api/backup/history/${backupId}`);
    }

    deleteRunOutput(runId: number): Observable<{ message: string; deleted: number; log_id: number }> {
        return this.http.delete<{ message: string; deleted: number; log_id: number }>(
            `${this.baseUrl}/api/cron/logs/${runId}/output`
        );
    }

    getBackupStats(): Observable<any> {
        return this.http.get<any>(`${this.baseUrl}/api/backup/stats`);
    }

    // ==================== SECURITY SEARCH ====================

    /**
     * Search processed output (local or S3) by Message ID or CUSIP string.
     * POST /api/search/security
     */
    securitySearch(query: string, searchType: 'message_id' | 'cusip' | 'any' = 'any', limit: number = 500): Observable<{ total_count: number; results: any[]; search_query: string; search_type: string }> {
        return this.http.post<any>(`${this.baseUrl}/api/search/security`, {
            query,
            search_type: searchType,
            limit
        });
    }

    /**
     * Upload Excel file with Message IDs / CUSIPs → backend searches processed output → returns Excel download.
     * POST /api/search/import-ids
     * Returns a Blob (Excel file to be downloaded by the browser).
     */
    importIdsForDownload(file: File): Observable<Blob> {
        const formData = new FormData();
        formData.append('file', file);
        return this.http.post(`${this.baseUrl}/api/search/import-ids`, formData, {
            responseType: 'blob'
        });
    }

    /**
     * Upload Excel file with identifier columns → auto-detect columns → return JSON preview.
     * POST /api/search/import-ids/preview
     */
    importIdsPreview(file: File): Observable<{ detected_columns: string[]; total_matches: number; results: any[]; search_summary: Record<string, any> }> {
        const formData = new FormData();
        formData.append('file', file);
        return this.http.post<any>(`${this.baseUrl}/api/search/import-ids/preview`, formData);
    }
}
