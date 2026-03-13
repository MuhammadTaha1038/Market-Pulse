import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { FormsModule } from '@angular/forms';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { DialogModule } from 'primeng/dialog';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageService } from 'primeng/api';
import { CustomTableComponent, TableColumn, TableRow, TableConfig } from '../custom-table/custom-table.component';
import { FilterDialogComponent, FilterCondition } from '../filter-dialog/filter-dialog.component';
import { ApiService, ColorProcessed, SearchFilter, Rule, RuleConditionBackend, Preset, UserCLOSelection } from '../../services/api.service';
import { AutomationStatusService } from '../../services/automation-status.service';
import { AssetStateService } from '../../services/asset-state.service';
import { TableStateService } from './table-state.service';
import { NextRunService } from '../../services/next-run.service';
import { MenuActiveService } from '../../layout/service/menu-active.service';
import { Subscription } from 'rxjs';
import { StackedChartComponent } from '../stacked-chart/stacked-chart.component';

@Component({
    selector: 'app-home',
    standalone: true,
    imports: [CommonModule, CardModule, ButtonModule, InputTextModule, FormsModule, ToastModule, TooltipModule, DialogModule, ProgressSpinnerModule, CustomTableComponent, FilterDialogComponent, StackedChartComponent],
    templateUrl: './home.html',
    styleUrls: ['./home.css'],
    providers: [MessageService]
})
export class Home implements OnInit, OnDestroy {
    @ViewChild('mainTable') mainTable!: CustomTableComponent;
    @ViewChild('expandedTable') expandedTable!: CustomTableComponent;
    @ViewChild('fileInputRef') fileInputRef!: ElementRef<HTMLInputElement>;

    nextRunTimer = '7H:52M:25S';
    filterVisible: boolean = false;
    isTableExpanded: boolean = false;

    // Import dialog state
    showImportDialog = false;
    isUploading = false;
    selectedFile: File | null = null;
    fileSize: string = '';

    // Run Rules dialog state
    showRunRulesDialog = false;
    availableRules: Rule[] = [];
    selectedRuleIds: Set<number> = new Set();
    ruleSearchText = '';
    loadingRules = false;
    runningRules = false;

    // Run Automation state
    showAutomationMenu = false;
    runningAutomation = false;

    // Presets state
    availablePresets: Preset[] = [];
    selectedPresetId: number | null = null;
    loadingPresets = false;

    // Active filters for display as chips
    activeFilters: FilterCondition[] = [];

    // Table data
    tableData: TableRow[] = [];
    selectedRows: TableRow[] = [];
    searchQuery: string = '';

    // Security search state
    isSearching = false;
    isImportingIds = false;
    hasImportResults = false;       // true when table is showing import search results
    importPreviewFile: File | null = null;  // file used for last import preview (for re-download)

    // Table configuration - Excel-like editable (messageId column editable, others auto-fill)
    // This default is overwritten by applyColumnVisibility() on init based on CLO selection.
    tableColumns: TableColumn[] = [
        { field: 'messageId', header: 'Message ID', width: '180px', editable: true },
        { field: 'ticker', header: 'Ticker', width: '140px', editable: false },
        { field: 'cusip', header: 'CUSIP', width: '140px', editable: false },
        { field: 'bias', header: 'Bias', width: '120px', editable: false },
        { field: 'date', header: 'Date', width: '120px', editable: false },
        { field: 'bid', header: 'BID', width: '100px', editable: false },
        { field: 'mid', header: 'MID', width: '100px', editable: false },
        { field: 'ask', header: 'ASK', width: '100px', editable: false },
        { field: 'px', header: 'PX', width: '100px', editable: false },
        { field: 'source', header: 'Source', width: '140px', editable: false }
    ];

    tableConfig: TableConfig = {
        editable: false,
        selectable: true,
        showSelectButton: true,
        showRowNumbers: true,
        pagination: true,
        pageSize: 20,
        showExport: false,
        showAddRow: false
    };

    private tableStateSub!: Subscription;
    private timerSub!: Subscription;
    private assetSub?: Subscription;

    /** CLO ID from localStorage selection – passed to every API call */
    private activeCloId: string | undefined;

    /** Oracle column names currently visible for the active CLO – fed to filter dialog */
    activeVisibleOracleColumns: string[] = [];

    /**
     * Static map of Oracle column name -> data type, used for type-aware operator
     * filtering in the filter dialog.
     */
    columnDataTypes: { [oracleName: string]: string } = {
        MESSAGE_ID: 'INTEGER', RANK: 'INTEGER', CONFIDENCE: 'INTEGER', CHILDREN_COUNT: 'INTEGER',
        PRICE_LEVEL: 'FLOAT', BID: 'FLOAT', ASK: 'FLOAT', PX: 'FLOAT',
        COV_PRICE: 'FLOAT', PERCENT_DIFF: 'FLOAT', PRICE_DIFF: 'FLOAT',
        TICKER: 'VARCHAR', SECTOR: 'VARCHAR', CUSIP: 'VARCHAR', SOURCE: 'VARCHAR',
        BIAS: 'VARCHAR', DIFF_STATUS: 'VARCHAR', PROCESSING_TYPE: 'VARCHAR',
        DATE: 'DATE', DATE_1: 'DATE'
    };

    /**
     * Master list of ALL possible table columns matched to their Oracle column name.
     * Visibility is driven by the CLO mapping saved in localStorage.
     */
    private readonly ALL_TABLE_COLUMNS: { oracleKey: string; col: TableColumn }[] = [
        { oracleKey: 'MESSAGE_ID',   col: { field: 'messageId',   header: 'Message ID',   width: '160px', editable: true  } },
        { oracleKey: 'TICKER',       col: { field: 'ticker',      header: 'Ticker',        width: '140px', editable: false } },
        { oracleKey: 'CUSIP',        col: { field: 'cusip',       header: 'CUSIP',         width: '140px', editable: false } },
        { oracleKey: 'SECTOR',       col: { field: 'sector',      header: 'Sector',        width: '140px', editable: false } },
        { oracleKey: 'BIAS',         col: { field: 'bias',        header: 'Bias',          width: '120px', editable: false } },
        { oracleKey: 'DATE',         col: { field: 'date',        header: 'Date',          width: '120px', editable: false } },
        { oracleKey: 'DATE_1',       col: { field: 'date1',       header: 'Date 1',        width: '120px', editable: false } },
        { oracleKey: 'BID',          col: { field: 'bid',         header: 'BID',           width: '100px', editable: false } },
        { oracleKey: 'ASK',          col: { field: 'ask',         header: 'ASK',           width: '100px', editable: false } },
        { oracleKey: 'PX',           col: { field: 'px',          header: 'PX',            width: '100px', editable: false } },
        { oracleKey: 'PRICE_LEVEL',  col: { field: 'priceLevel',  header: 'Price Level',   width: '120px', editable: false } },
        { oracleKey: 'SOURCE',       col: { field: 'source',      header: 'Source',        width: '140px', editable: false } },
        { oracleKey: 'RANK',         col: { field: 'rank',        header: 'Rank',          width: '100px', editable: false } },
        { oracleKey: 'COV_PRICE',    col: { field: 'covPrice',    header: 'Cov Price',     width: '120px', editable: false } },
        { oracleKey: 'PERCENT_DIFF', col: { field: 'percentDiff', header: '% Diff',        width: '100px', editable: false } },
        { oracleKey: 'PRICE_DIFF',   col: { field: 'priceDiff',   header: 'Price Diff',    width: '120px', editable: false } },
        { oracleKey: 'CONFIDENCE',   col: { field: 'confidence',  header: 'Confidence',    width: '100px', editable: false } },
        { oracleKey: 'DIFF_STATUS',  col: { field: 'diffStatus',  header: 'Diff Status',   width: '120px', editable: false } },
        { oracleKey: 'PROCESSING_TYPE', col: { field: 'processingType', header: 'Processing Type', width: '150px', editable: false } },
        { oracleKey: 'PARENT_MESSAGE_ID', col: { field: 'parentMessageId', header: 'Parent Message ID', width: '170px', editable: false } },
        { oracleKey: 'CHILDREN_COUNT', col: { field: 'childrenCount', header: 'Children Count', width: '130px', editable: false } },
    ];

    /** Computed MID column (BID+ASK)/2 — shown only when both BID and ASK are visible */
    private readonly MID_COLUMN: TableColumn = { field: 'mid', header: 'MID', width: '100px', editable: false };

    constructor(
        private apiService: ApiService,
        private automationStatusService: AutomationStatusService,
        private assetStateService: AssetStateService,
        private messageService: MessageService,
        private router: Router,
        private tableStateService: TableStateService,
        private nextRunService: NextRunService,
        private menuActiveService: MenuActiveService
    ) {}

    ngOnInit() {
        console.log('🚀 Home component initialized - loading data from backend...');

        // Fetch fresh CLO column visibility from backend, then load data.
        // applyColumnVisibility() calls loadDataFromBackend() once columns are resolved.
        this.applyColumnVisibility();

        // React to topbar sub-asset changes while staying on /home.
        this.assetSub = this.assetStateService.asset$.subscribe((asset) => {
            const nextCloId = asset?.value;
            if (nextCloId && nextCloId !== this.activeCloId) {
                this.applyColumnVisibility(nextCloId);
            }
        });

        // Set initial active menu item to Dashboard
        this.menuActiveService.setActiveMenuItem('Dashboard');

        this.tableStateSub = this.tableStateService.isTableExpanded$.subscribe((expanded) => {
            // Update active menu item based on table expansion state
            if (expanded) {
                this.menuActiveService.setActiveMenuItem('Security Search');
            } else {
                this.menuActiveService.setActiveMenuItem('Dashboard');
            }

            // Sync the local state with the service state
            if (expanded !== this.isTableExpanded) {
                this.isTableExpanded = expanded;
                this.applyTableExpansionUI();
            }
        });
    }

    ngOnDestroy() {
        this.tableStateSub?.unsubscribe();
        this.timerSub?.unsubscribe();
        this.assetSub?.unsubscribe();
    }

    /**
     * Reads the CLO ID from localStorage, then fetches FRESH visible columns from the backend
     * so any admin changes to the CLO mapping are immediately reflected without re-login.
     * Falls back to localStorage visibleColumns if the API call fails.
     */
    private applyColumnVisibility(cloIdOverride?: string): void {
        try {
            const { cloId, fallbackVisibleColumns } = this.resolveActiveCloContext();
            this.activeCloId = cloIdOverride || cloId;

            // If no active CLO can be resolved, load with default columns.
            if (!this.activeCloId) {
                this.loadDataFromBackend();
                return;
            }

            // Fetch FRESH visible columns from backend — avoids stale localStorage snapshot
            this.apiService.getUserColumns(this.activeCloId).subscribe({
                next: (response: any) => {
                    const visible = new Set<string>(response.visible_columns || []);
                    if (visible.size > 0) {
                        this._buildTableColumns(visible);
                    }
                    // Always reload data after visibility resolution
                    this.loadDataFromBackend();
                },
                error: () => {
                    // Fallback: use the snapshot stored at login time
                    const visible = new Set<string>(fallbackVisibleColumns || []);
                    if (visible.size > 0) {
                        this._buildTableColumns(visible);
                    }
                    this.loadDataFromBackend();
                }
            });
        } catch (e) {
            console.warn('Could not apply CLO column visibility:', e);
            this.loadDataFromBackend();
        }
    }

    /**
     * Resolve active CLO context from both storage patterns used in the app:
     * 1) user_clo_selection (CLO selector flow)
     * 2) selectedAssetState (sub-asset flow used by login)
     */
    private resolveActiveCloContext(): { cloId?: string; fallbackVisibleColumns: string[] } {
        let cloId: string | undefined;
        let fallbackVisibleColumns: string[] = [];

        // Preferred source: current runtime selection used by topbar/sub-asset flow.
        try {
            const rawAsset = localStorage.getItem('selectedAssetState');
            if (rawAsset) {
                const parsed = JSON.parse(rawAsset);
                cloId = parsed?.asset?.value || cloId;
            }
        } catch {
            // Ignore malformed selectedAssetState
        }

        try {
            const rawUser = localStorage.getItem('user_clo_selection');
            if (rawUser) {
                const selection: UserCLOSelection = JSON.parse(rawUser);
                // Fallback source for selector flow (when selectedAssetState is absent).
                if (!cloId) {
                    cloId = selection?.cloId || cloId;
                }
                // Only use fallback visible columns when they correspond to the resolved CLO.
                if (selection?.cloId && selection?.cloId === cloId) {
                    fallbackVisibleColumns = selection?.visibleColumns || fallbackVisibleColumns;
                }
            }
        } catch {
            // Ignore malformed user_clo_selection
        }

        return { cloId, fallbackVisibleColumns };
    }

    /** Build tableColumns from a set of visible oracle column keys */
    private _buildTableColumns(visible: Set<string>): void {
        // Normalize keys to tolerate backend/localStorage/rules differences:
        // e.g. MESSAGE_ID, Message ID, MessageID, PriceLevel, CoveragePrice, Date1.
        const aliasMap: { [k: string]: string } = {
            MESSAGEID: 'MESSAGE_ID',
            DATE1: 'DATE_1',
            PRICELEVEL: 'PRICE_LEVEL',
            COVERAGEPRICE: 'COV_PRICE',
            COVPRICE: 'COV_PRICE',
            PERCENTDIFF: 'PERCENT_DIFF',
            PRICEDIFF: 'PRICE_DIFF',
            DIFFSTATUS: 'DIFF_STATUS',
            PROCESSINGTYPE: 'PROCESSING_TYPE',
            PARENTMESSAGEID: 'PARENT_MESSAGE_ID',
            CHILDRENCOUNT: 'CHILDREN_COUNT'
        };

        const normalize = (k: string) => {
            const raw = String(k || '').trim();
            const underscore = raw.toUpperCase().replace(/\s+/g, '_');
            const compact = underscore.replace(/_/g, '');
            return aliasMap[underscore] || aliasMap[compact] || underscore;
        };

        const visibleNorm = new Set<string>(Array.from(visible).map(normalize));

        // Expose normalized oracle keys so filter-dialog can filter its column dropdown
        this.activeVisibleOracleColumns = Array.from(visibleNorm);

        const columns: TableColumn[] = [];
        let hasBid = false;
        let hasAsk = false;

        for (const { oracleKey, col } of this.ALL_TABLE_COLUMNS) {
            if (visibleNorm.has(oracleKey)) {
                columns.push({ ...col });
                if (oracleKey === 'BID') hasBid = true;
                if (oracleKey === 'ASK') hasAsk = true;
            }
        }

        // Insert computed MID column between BID and ASK when both are visible
        if (hasBid && hasAsk) {
            const bidIdx = columns.findIndex(c => c.field === 'bid');
            columns.splice(bidIdx + 1, 0, { ...this.MID_COLUMN });
        }

        if (columns.length > 0) {
            this.tableColumns = columns;
            console.log(`✅ CLO "${this.activeCloId}" column visibility applied: ${columns.map(c => c.field).join(', ')}`);
        }
    }

    /**
     * Convert a ColorProcessed backend object to a TableRow, mapping ALL available
     * fields so column visibility works for any configured column set.
     */
    private colorToRow(color: ColorProcessed, index: number): TableRow {
        return {
            _rowId: `row_${color.message_id}`,
            _selected: false,
            rowNumber: String(index + 1),
            messageId: String(color.message_id),
            ticker: color.ticker,
            sector: color.sector,
            cusip: color.cusip,
            bias: color.bias,
            date: color.date ? new Date(color.date).toLocaleDateString() : '',
            date1: color.date_1 ? new Date(color.date_1).toLocaleDateString() : '',
            bid: color.bid,
            mid: (color.bid + color.ask) / 2,
            ask: color.ask,
            px: color.px,
            priceLevel: color.price_level,
            source: color.source,
            rank: color.rank,
            covPrice: color.cov_price,
            percentDiff: color.percent_diff,
            priceDiff: color.price_diff,
            confidence: color.confidence,
            diffStatus: color.diff_status,
            processingType: (color as any).processing_type || '',
            parentMessageId: color.parent_message_id || '',
            isParent: color.is_parent,
            parentRow: color.parent_message_id,
            childrenCount: color.children_count || 0
        };
    }

    /**
     * Get filtered table data based on search query
     * Searches by messageId or cusip fields
     */
    get filteredTableData(): TableRow[] {
        if (!this.searchQuery.trim()) {
            return this.tableData;
        }

        const searchLower = this.searchQuery.toLowerCase().trim();
        return this.tableData.filter((row) => {
            const messageId = String(row['messageId'] || '').toLowerCase();
            const cusip = String(row['cusip'] || '').toLowerCase();
            return messageId.includes(searchLower) || cusip.includes(searchLower);
        });
    }

    /**
     * Load color data from backend API
     * Maps the backend response to table format
     */
    private loadDataFromBackend() {
        console.log('📡 Fetching colors from backend API...');

        this.apiService.getColors(0, 100, undefined, this.activeCloId).subscribe({
            next: (response) => {
                console.log('✅ Colors received from backend:', response.colors.length);

                // Convert backend format to table format with parent-child relationships
                this.tableData = response.colors.map((color: ColorProcessed, index: number) => this.colorToRow(color, index));

                console.log('✅ Loaded', this.tableData.length, 'colors from backend');
            },
            error: (error) => {
                console.error('❌ Error loading colors from backend:', error);

                // Show empty rows so user can type message IDs
                this.tableData = this.generateEmptyRows(20);
            }
        });

        // Subscribe to shared next-run countdown service
        this.nextRunService.init();
        this.timerSub = this.nextRunService.timer$.subscribe((val) => {
            this.nextRunTimer = val;
        });
    }

    // ==================== TABLE EVENTS ====================

    onTableDataChanged(data: TableRow[]) {
        console.log('📊 Table data changed:', data.length, 'rows');
        this.tableData = data;
    }

    onTableRowsSelected(selectedRows: TableRow[]) {
        console.log('✅ Rows selected:', selectedRows.length);
        this.selectedRows = selectedRows;
    }

    // ==================== MESSAGE ID LOOKUP ====================

    onMessageIdLookup(event: { row: TableRow; value: any }) {
        const rawValue = String(event.value || '').trim();
        if (!rawValue) return;

        // Detect whether the user typed a CUSIP (contains letters) or a Message ID (purely numeric).
        const isCusipInput = /[a-zA-Z]/.test(rawValue);
        const searchType: 'cusip' | 'message_id' | 'any' = isCusipInput ? 'cusip' : 'message_id';

        const table = this.isTableExpanded ? this.expandedTable : this.mainTable;
        this.apiService.securitySearch(rawValue, searchType, 10).subscribe({
            next: (response) => {
                if (response.results && response.results.length > 0) {
                    const record = response.results[0];
                    const rowData: Partial<TableRow> = {
                        // When input was a CUSIP, keep messageId from record only (don't fall back to rawValue).
                        messageId: isCusipInput ? String(record.MESSAGE_ID || '') : String(record.MESSAGE_ID || rawValue),
                        ticker: record.TICKER || '',
                        sector: record.SECTOR || '',
                        // When input was a CUSIP and record has no CUSIP field, use rawValue.
                        cusip: record.CUSIP || (isCusipInput ? rawValue : ''),
                        bias: record.BIAS || '',
                        date: record.DATE ? new Date(record.DATE).toLocaleDateString() : '',
                        date1: record.DATE_1 ? new Date(record.DATE_1).toLocaleDateString() : '',
                        bid: record.BID || 0,
                        mid: ((Number(record.BID) || 0) + (Number(record.ASK) || 0)) / 2,
                        ask: record.ASK || 0,
                        px: record.PX || 0,
                        priceLevel: record.PRICE_LEVEL || 0,
                        source: record.SOURCE || '',
                        rank: record.RANK || 5,
                        covPrice: record.COV_PRICE || 0,
                        percentDiff: record.PERCENT_DIFF || 0,
                        priceDiff: record.PRICE_DIFF || 0,
                        confidence: record.CONFIDENCE || 0,
                        diffStatus: record.DIFF_STATUS || '',
                        isParent: record.IS_PARENT ?? true,
                        parentRow: record.PARENT_MESSAGE_ID || undefined,
                        childrenCount: record.CHILDREN_COUNT || 0
                    };
                    if (table) table.updateRowData(event.row._rowId!, rowData);
                } else {
                    // Not found: place the typed value in the correct column based on input type.
                    const notFoundData: Partial<TableRow> = {
                        messageId: isCusipInput ? '' : rawValue,
                        cusip: isCusipInput ? rawValue : '',
                        ticker: 'NOT FOUND',
                        bias: '',
                        date: '',
                        bid: 0,
                        mid: 0,
                        ask: 0,
                        px: 0,
                        source: ''
                    };
                    if (table) table.updateRowData(event.row._rowId!, notFoundData);
                }
            },
            error: (error) => {
                console.error('Error during security lookup:', error);
                const errorData: Partial<TableRow> = {
                    messageId: isCusipInput ? '' : rawValue,
                    cusip: isCusipInput ? rawValue : 'ERROR',
                    ticker: 'ERROR',
                    bias: 'ERROR',
                    date: 'ERROR',
                    bid: 'ERROR',
                    mid: 'ERROR',
                    ask: 'ERROR',
                    px: 'ERROR',
                    source: 'ERROR'
                };
                const tbl = this.isTableExpanded ? this.expandedTable : this.mainTable;
                if (tbl) tbl.updateRowData(event.row._rowId!, errorData);
            }
        });
    }

    // ==================== TABLE EXPANSION ====================

    /**
     * Toggle table expansion to full screen
     * Hides sidebar when expanded, restores when minimized
     */
    toggleTableExpansion() {
        console.log('📄 Toggling table expansion - Current state:', this.isTableExpanded);
        this.isTableExpanded = !this.isTableExpanded;

        // Sync state back to the service
        this.tableStateService.setTableExpanded(this.isTableExpanded);

        // Apply UI changes
        this.applyTableExpansionUI();

        console.log('📄 New expanded state:', this.isTableExpanded);
    }

    /**
     * Apply UI changes based on table expansion state
     * Manages sidebar visibility and body overflow
     */
    private applyTableExpansionUI() {
        if (this.isTableExpanded) {
            // Collapse sidebar and hide body scroll
            document.body.style.overflow = 'hidden';
            const sidebar = document.querySelector('.layout-sidebar');
            if (sidebar) {
                (sidebar as HTMLElement).style.display = 'none';
            }
        } else {
            // Restore sidebar and body scroll
            document.body.style.overflow = 'auto';
            const sidebar = document.querySelector('.layout-sidebar');
            if (sidebar) {
                (sidebar as HTMLElement).style.display = 'block';
            }
        }
    }

    // ==================== ACTIONS ====================

    refreshColors() {
        console.log('🔄 Refresh Colors Now - navigating to color process...');
        this.router.navigate(['/color-type']);
    }

    overrideAndRun() {
        console.log('⚙️ Override & Run - canceling scheduled run and running immediately...');
        this.messageService.add({
            severity: 'info',
            summary: 'Override Triggered',
            detail: 'Canceling next scheduled run and running immediately...'
        });
        this.router.navigate(['/color-type']);
    }

    importSample() {
        console.log('📥 Import Sample clicked');
        window.location.href = '/color-type';
    }

    rulesAndPresets() {
        console.log('⚙️ Rules & Presets clicked');
        window.location.href = '/settings?section=rules';
    }

    restoreLastRun() {
        console.log('↩️ Restore last run clicked');
        this.messageService.add({
            severity: 'info',
            summary: 'Restore Last Run',
            detail: 'Restoring previous ranking results...'
        });
    }

    cronJobsAndTime() {
        console.log('⏰ Cron Jobs & Time clicked');
        window.location.href = '/settings?section=cron-jobs';
    }

    goToHelpPage() {
        this.router.navigate(['/temp']);
    }

    importViaExcel() {
        // Import ID via Excel: open file picker → send to backend → download result Excel
        console.log('📥 Import IDs via Excel');
        this.showImportDialog = true;
        this.selectedFile = null;
        this.fileSize = '';
        this.isUploading = false;
    }

    fetchData() {
        const query = (this.searchQuery || '').trim();
        // Clear import results state whenever user triggers a fresh search/reload
        this.hasImportResults = false;
        this.importPreviewFile = null;
        if (query) {
            // Security search: search processed output by Message ID or CUSIP
            console.log('🔍 Security search:', query);
            this.isSearching = true;
            this.apiService.securitySearch(query, 'any', 500).subscribe({
                next: (response) => {
                    this.isSearching = false;
                    this.tableData = response.results.map((record: any, index: number) => ({
                        _rowId: `row_${record.MESSAGE_ID || index}`,
                        _selected: false,
                        rowNumber: String(index + 1),
                        messageId: String(record.MESSAGE_ID || ''),
                        ticker: record.TICKER || '',
                        sector: record.SECTOR || '',
                        cusip: record.CUSIP || '',
                        bias: record.BIAS || '',
                        date: record.DATE ? new Date(record.DATE).toLocaleDateString() : '',
                        date1: record.DATE_1 ? new Date(record.DATE_1).toLocaleDateString() : '',
                        bid: record.BID || 0,
                        mid: ((Number(record.BID) || 0) + (Number(record.ASK) || 0)) / 2,
                        ask: record.ASK || 0,
                        px: record.PX || 0,
                        priceLevel: record.PRICE_LEVEL || 0,
                        source: record.SOURCE || '',
                        rank: record.RANK || 5,
                        covPrice: record.COV_PRICE || 0,
                        percentDiff: record.PERCENT_DIFF || 0,
                        priceDiff: record.PRICE_DIFF || 0,
                        confidence: record.CONFIDENCE || 0,
                        diffStatus: record.DIFF_STATUS || '',
                        isParent: record.IS_PARENT ?? true,
                        parentRow: record.PARENT_MESSAGE_ID || undefined,
                        childrenCount: record.CHILDREN_COUNT || 0
                    }));
                    this.messageService.add({
                        severity: response.total_count > 0 ? 'success' : 'warn',
                        summary: response.total_count > 0 ? 'Search Complete' : 'No Results',
                        detail: response.total_count > 0
                            ? `Found ${response.total_count} record(s) for "${query}"`
                            : `No matching records found for "${query}"`
                    });
                },
                error: (err) => {
                    this.isSearching = false;
                    this.messageService.add({
                        severity: 'error',
                        summary: 'Search Failed',
                        detail: err.error?.detail || 'Failed to search records'
                    });
                }
            });
        } else {
            // No query – refresh all data
            console.log('📥 Fetching latest data...');
            this.loadDataFromBackend();
            this.messageService.add({ severity: 'success', summary: 'Refreshed', detail: 'Data refreshed from backend' });
        }
    }

    exportAll() {
        console.log('📤 Exporting data...');
        const dataToExport = this.selectedRows.length > 0 ? this.selectedRows : this.tableData;

        if (dataToExport.length === 0) {
            this.messageService.add({
                severity: 'warn',
                summary: 'No Data',
                detail: 'No data to export'
            });
            return;
        }

        // Convert to CSV
        const csvContent = this.convertToCSV(dataToExport);
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        const fileName = this.selectedRows.length > 0 ? `marketpulse_selected_rows_${new Date().toISOString().split('T')[0]}.csv` : `marketpulse_colors_${new Date().toISOString().split('T')[0]}.csv`;
        link.download = fileName;
        link.click();
        window.URL.revokeObjectURL(url);

        this.messageService.add({
            severity: 'success',
            summary: 'Exported',
            detail: `${dataToExport.length} row(s) exported to CSV`
        });
    }

    /**
     * Convert table data to CSV format
     */
    private convertToCSV(data: any[]): string {
        if (!data || data.length === 0) return '';
        const headers = Object.keys(data[0]).filter((key) => !key.startsWith('_'));
        const csvRows = [];
        csvRows.push(headers.join(','));
        for (const row of data) {
            const values = headers.map((header) => {
                const value = row[header];
                return typeof value === 'string' && value.includes(',') ? `"${value}"` : value;
            });
            csvRows.push(values.join(','));
        }
        return csvRows.join('\n');
    }

    // ==================== FILTERS ====================

    showFilterDialog() {
        this.filterVisible = true;
    }

    onFiltersApplied(filters: { conditions: FilterCondition[]; subgroups: any[] }) {
        console.log('✅ Filters applied:', filters);

        // Collect all valid conditions (main + subgroups)
        const allConditions: FilterCondition[] = [...filters.conditions];
        if (filters.subgroups) {
            for (const sg of filters.subgroups) {
                allConditions.push(...sg.conditions);
            }
        }

        this.activeFilters = allConditions;

        if (allConditions.length === 0) {
            this.loadDataFromBackend();
            return;
        }

        // Build SearchFilter array for the backend API
        const searchFilters: SearchFilter[] = allConditions.map((c) => ({
            field: c.column,
            operator: c.operator,
            value: c.values,
            value2: c.values2 || undefined
        }));

        console.log('📡 Calling backend search with filters:', searchFilters);

        this.apiService.searchColors(searchFilters, 0, 500).subscribe({
            next: (response) => {
                console.log('✅ Search results:', response.total_count, 'records');

                this.tableData = response.results.map((record: any, index: number) => ({
                    _rowId: `row_${record.MESSAGE_ID || index}`,
                    _selected: false,
                    rowNumber: String(index + 1),
                    messageId: String(record.MESSAGE_ID || ''),
                    ticker: record.TICKER || '',
                    sector: record.SECTOR || '',
                    cusip: record.CUSIP || '',
                    bias: record.BIAS || '',
                    date: record.DATE ? new Date(record.DATE).toLocaleDateString() : '',
                    date1: record.DATE_1 ? new Date(record.DATE_1).toLocaleDateString() : '',
                    bid: record.BID || 0,
                    mid: ((record.BID || 0) + (record.ASK || 0)) / 2,
                    ask: record.ASK || 0,
                    px: record.PX || 0,
                    priceLevel: record.PRICE_LEVEL || 0,
                    source: record.SOURCE || '',
                    rank: record.RANK || 5,
                    covPrice: record.COV_PRICE || 0,
                    percentDiff: record.PERCENT_DIFF || 0,
                    priceDiff: record.PRICE_DIFF || 0,
                    confidence: record.CONFIDENCE || 0,
                    diffStatus: record.DIFF_STATUS || '',
                    isParent: record.IS_PARENT ?? true,
                    parentRow: record.PARENT_MESSAGE_ID || undefined,
                    childrenCount: record.CHILDREN_COUNT || 0
                }));

                this.messageService.add({
                    severity: 'success',
                    summary: 'Filters Applied',
                    detail: `Found ${response.total_count} matching record(s)`
                });
            },
            error: (error) => {
                console.error('❌ Search error:', error);
                this.messageService.add({
                    severity: 'error',
                    summary: 'Filter Error',
                    detail: 'Failed to apply filters. Loading all data instead.'
                });
                this.loadDataFromBackend();
            }
        });
    }

    removeFilter(index: number) {
        this.activeFilters.splice(index, 1);
        if (this.activeFilters.length === 0) {
            this.loadDataFromBackend();
        } else {
            // Re-apply remaining filters
            this.onFiltersApplied({ conditions: this.activeFilters, subgroups: [] });
        }
    }

    removeAllFilters() {
        this.activeFilters = [];
        this.messageService.add({
            severity: 'info',
            summary: 'Filters Cleared',
            detail: 'All filters removed'
        });
        this.loadDataFromBackend();
    }

    // ==================== RUN AUTOMATION ====================

    runAutomation(override: boolean) {
        this.showAutomationMenu = false;

        if (override) {
            this.runningAutomation = true;
            this.automationStatusService.beginRun();
            this.messageService.add({
                severity: 'info',
                summary: 'Override & Run',
                detail: 'Overriding cron schedule and running automation...'
            });

            this.apiService.getActiveCronJobs().subscribe({
                next: (response) => {
                    if (response.jobs.length === 0) {
                        this.messageService.add({
                            severity: 'warn',
                            summary: 'No Active Jobs',
                            detail: 'No active cron jobs found to override'
                        });
                        this.runningAutomation = false;
                        this.automationStatusService.endRun();
                        return;
                    }

                    const job = response.jobs[0];
                    this.apiService.triggerCronJob(job.id, true).subscribe({
                        next: (res) => {
                            this.messageService.add({
                                severity: 'success',
                                summary: 'Automation Complete',
                                detail: res.message || 'Cron job overridden and executed'
                            });
                            this.loadDataFromBackend();
                            this.runningAutomation = false;
                            this.automationStatusService.endRun();
                        },
                        error: (err) => {
                            this.messageService.add({
                                severity: 'error',
                                summary: 'Error',
                                detail: err.error?.detail || 'Failed to trigger automation'
                            });
                            this.runningAutomation = false;
                            this.automationStatusService.endRun();
                        }
                    });
                },
                error: () => {
                    this.messageService.add({
                        severity: 'error',
                        summary: 'Error',
                        detail: 'Failed to fetch active cron jobs'
                    });
                    this.runningAutomation = false;
                    this.automationStatusService.endRun();
                }
            });
        } else {
            if (this.tableData.length === 0) {
                this.messageService.add({
                    severity: 'warn',
                    summary: 'No Data',
                    detail: 'No data in the table to process'
                });
                return;
            }

            this.runningAutomation = true;
            this.automationStatusService.beginRun();
            this.messageService.add({
                severity: 'info',
                summary: 'Processing',
                detail: 'Running all active rules...'
            });

            this.apiService.getActiveRules().subscribe({
                next: (response) => {
                    const activeRules = response.rules;
                    if (activeRules.length === 0) {
                        this.messageService.add({
                            severity: 'warn',
                            summary: 'No Active Rules',
                            detail: 'No active rules found. Go to Settings to configure rules.'
                        });
                        this.runningAutomation = false;
                        this.automationStatusService.endRun();
                        return;
                    }

                    const originalCount = this.tableData.length;

                    const filteredData = this.tableData.filter((row) => {
                        for (const rule of activeRules) {
                            if (this.evaluateRule(row, rule)) {
                                return false;
                            }
                        }
                        return true;
                    });

                    const excludedCount = originalCount - filteredData.length;
                    this.tableData = filteredData;

                    this.apiService.createBackup('Automation run - ' + new Date().toISOString()).subscribe({
                        next: () => {
                            this.messageService.add({
                                severity: 'success',
                                summary: 'Automation Complete',
                                detail: `${activeRules.length} rule(s) applied. ${excludedCount} row(s) excluded, ${filteredData.length} remaining. Data saved.`
                            });
                        },
                        error: () => {
                            this.messageService.add({
                                severity: 'success',
                                summary: 'Automation Complete',
                                detail: `${activeRules.length} rule(s) applied. ${excludedCount} row(s) excluded, ${filteredData.length} remaining.`
                            });
                        }
                    });

                    this.runningAutomation = false;
                    this.automationStatusService.endRun();
                },
                error: () => {
                    this.messageService.add({
                        severity: 'error',
                        summary: 'Error',
                        detail: 'Failed to fetch active rules'
                    });
                    this.runningAutomation = false;
                    this.automationStatusService.endRun();
                }
            });
        }
    }

    // ==================== PRESETS ====================

    loadPresets() {
        this.loadingPresets = true;
        this.apiService.getPresets().subscribe({
            next: (response) => {
                this.availablePresets = response.presets;
                this.loadingPresets = false;
            },
            error: () => {
                this.loadingPresets = false;
            }
        });
    }

    applyPreset(presetId: number) {
        const preset = this.availablePresets.find((p) => p.id === presetId);
        if (!preset) return;

        this.selectedPresetId = presetId;

        const filters: FilterCondition[] = preset.conditions.map((c) => ({
            column: c.column,
            operator: c.operator,
            values: c.value,
            values2: c.value2 || '',
            columnDisplay: c.column,
            operatorDisplay: c.operator,
            logicalOperator: 'AND' as const
        }));

        this.activeFilters = filters;
        this.onFiltersApplied({ conditions: filters, subgroups: [] });

        this.messageService.add({
            severity: 'success',
            summary: 'Preset Loaded',
            detail: `Loaded preset "${preset.name}" with ${preset.conditions.length} filter(s)`
        });
    }

    // ==================== RUN RULES ====================

    openRunRulesDialog() {
        this.showRunRulesDialog = true;
        this.ruleSearchText = '';
        this.selectedRuleIds.clear();
        this.selectedPresetId = null;
        this.loadRulesForDialog();
        this.loadPresets();
    }

    loadRulesForDialog() {
        this.loadingRules = true;
        this.apiService.getRules().subscribe({
            next: (response) => {
                this.availableRules = response.rules;
                this.availableRules.forEach((rule) => {
                    if (rule.is_active) {
                        this.selectedRuleIds.add(rule.id);
                    }
                });
                this.loadingRules = false;
            },
            error: (error) => {
                console.error('Error loading rules:', error);
                this.loadingRules = false;
                this.messageService.add({
                    severity: 'error',
                    summary: 'Error',
                    detail: 'Failed to load rules'
                });
            }
        });
    }

    toggleRuleSelection(ruleId: number) {
        if (this.selectedRuleIds.has(ruleId)) {
            this.selectedRuleIds.delete(ruleId);
        } else {
            this.selectedRuleIds.add(ruleId);
        }
    }

    isRuleSelected(ruleId: number): boolean {
        return this.selectedRuleIds.has(ruleId);
    }

    get filteredRules(): Rule[] {
        if (!this.ruleSearchText.trim()) return this.availableRules;
        const search = this.ruleSearchText.toLowerCase();
        return this.availableRules.filter((r) => r.name.toLowerCase().includes(search));
    }

    get allFilteredRulesSelected(): boolean {
        return this.filteredRules.length > 0 && this.filteredRules.every((r) => this.selectedRuleIds.has(r.id));
    }

    toggleSelectAll() {
        if (this.allFilteredRulesSelected) {
            this.filteredRules.forEach((r) => this.selectedRuleIds.delete(r.id));
        } else {
            this.filteredRules.forEach((r) => this.selectedRuleIds.add(r.id));
        }
    }

    cancelRunRules() {
        this.showRunRulesDialog = false;
    }

    runSelectedRules() {
        if (this.selectedRuleIds.size === 0) {
            this.messageService.add({
                severity: 'warn',
                summary: 'No Rules Selected',
                detail: 'Please select at least one rule to run'
            });
            return;
        }

        if (this.tableData.length === 0) {
            this.messageService.add({
                severity: 'warn',
                summary: 'No Data',
                detail: 'No data in the table to filter'
            });
            return;
        }

        this.runningRules = true;

        const selectedRules = this.availableRules.filter((r) => this.selectedRuleIds.has(r.id));
        const originalCount = this.tableData.length;

        const filteredData = this.tableData.filter((row) => {
            for (const rule of selectedRules) {
                if (this.evaluateRule(row, rule)) {
                    return false;
                }
            }
            return true;
        });

        const excludedCount = originalCount - filteredData.length;
        this.tableData = filteredData;
        this.runningRules = false;
        this.showRunRulesDialog = false;

        // Save snapshot after rules applied
        this.apiService.createBackup('Rules run - ' + new Date().toISOString()).subscribe();

        this.messageService.add({
            severity: 'success',
            summary: 'Rules Applied',
            detail: `${selectedRules.length} rule(s) applied. ${excludedCount} row(s) excluded, ${filteredData.length} remaining. Data saved.`
        });
    }

    // Rule evaluation engine (mirrors backend rules_service.py)
    private evaluateRule(row: any, rule: Rule): boolean {
        const conditions = rule.conditions || [];
        if (conditions.length === 0) return false;

        let result: boolean | null = null;

        for (const condition of conditions) {
            const conditionType = condition.type || 'where';
            const conditionMatch = this.evaluateCondition(row, condition);

            if (result === null) {
                result = conditionMatch;
            } else if (conditionType === 'and') {
                result = result && conditionMatch;
            } else if (conditionType === 'or') {
                result = result || conditionMatch;
            } else if (conditionType === 'where') {
                result = conditionMatch;
            }
        }

        return result ?? false;
    }

    private evaluateCondition(row: any, condition: RuleConditionBackend): boolean {
        const column = condition.column || '';
        let operator = (condition.operator || '').toLowerCase();
        const value = condition.value || '';
        const value2 = condition.value2 || '';

        const operatorMap: { [key: string]: string } = {
            'equal to': 'equal_to',
            'not equal to': 'not_equal_to',
            'less than': 'less_than',
            'greater than': 'greater_than',
            'less than equal to': 'less_than_equal_to',
            'greater than equal to': 'greater_than_equal_to',
            between: 'between',
            contains: 'contains',
            'starts with': 'starts_with',
            'ends with': 'ends_with',
            'is equal to': 'equal_to',
            'is not equal to': 'not_equal_to',
            equals: 'equal_to',
            not_equals: 'not_equal_to',
            not_contains: 'not_contains',
            'does not contain': 'not_contains',
            greater_than: 'greater_than',
            less_than: 'less_than',
            greater_or_equal: 'greater_than_equal_to',
            less_or_equal: 'less_than_equal_to'
        };

        operator = operatorMap[operator] || operator;

        const rowValue = this.getRowValue(row, column);
        const compareValue = String(value);

        switch (operator) {
            case 'equal_to': {
                const numRow = parseFloat(rowValue);
                const numCmp = parseFloat(compareValue);
                if (!isNaN(numRow) && !isNaN(numCmp)) return numRow === numCmp;
                return rowValue.toLowerCase() === compareValue.toLowerCase();
            }
            case 'not_equal_to': {
                const numRow = parseFloat(rowValue);
                const numCmp = parseFloat(compareValue);
                if (!isNaN(numRow) && !isNaN(numCmp)) return numRow !== numCmp;
                return rowValue.toLowerCase() !== compareValue.toLowerCase();
            }
            case 'contains':
                return rowValue.toLowerCase().includes(compareValue.toLowerCase());
            case 'not_contains':
                return !rowValue.toLowerCase().includes(compareValue.toLowerCase());
            case 'starts_with':
                return rowValue.toLowerCase().startsWith(compareValue.toLowerCase());
            case 'ends_with':
                return rowValue.toLowerCase().endsWith(compareValue.toLowerCase());
            case 'less_than': {
                const a = parseFloat(rowValue),
                    b = parseFloat(compareValue);
                return !isNaN(a) && !isNaN(b) && a < b;
            }
            case 'greater_than': {
                const a = parseFloat(rowValue),
                    b = parseFloat(compareValue);
                return !isNaN(a) && !isNaN(b) && a > b;
            }
            case 'less_than_equal_to': {
                const a = parseFloat(rowValue),
                    b = parseFloat(compareValue);
                return !isNaN(a) && !isNaN(b) && a <= b;
            }
            case 'greater_than_equal_to': {
                const a = parseFloat(rowValue),
                    b = parseFloat(compareValue);
                return !isNaN(a) && !isNaN(b) && a >= b;
            }
            case 'between': {
                const rowNum = parseFloat(rowValue);
                const minVal = parseFloat(compareValue);
                const maxVal = parseFloat(value2);
                return !isNaN(rowNum) && !isNaN(minVal) && !isNaN(maxVal) && minVal <= rowNum && rowNum <= maxVal;
            }
            default:
                return false;
        }
    }

    private getRowValue(row: any, column: string): string {
        const lowerCol = column.toLowerCase();

        for (const key of Object.keys(row)) {
            if (key.toLowerCase() === lowerCol) return String(row[key] ?? '');
        }

        const camelCase = lowerCol.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase());
        for (const key of Object.keys(row)) {
            if (key.toLowerCase() === camelCase.toLowerCase()) return String(row[key] ?? '');
        }

        return '';
    }

    // ==================== HELPERS ====================

    getExportButtonLabel(): string {
        return this.selectedRows.length > 0 ? `Export Selected (${this.selectedRows.length})` : 'Export All';
    }

    generateEmptyRows(count: number): TableRow[] {
        const rows: TableRow[] = [];
        for (let i = 0; i < count; i++) {
            rows.push({
                _rowId: `row_empty_${Date.now()}_${i}`,
                _selected: false,
                rowNumber: String(i + 1),
                messageId: '',
                ticker: '',
                cusip: '',
                bias: '',
                date: '',
                bid: '',
                mid: '',
                ask: '',
                px: '',
                source: '',
                isParent: true,
                childrenCount: 0
            });
        }
        return rows;
    }

    // ==================== FILE IMPORT ====================

    triggerFileInput() {
        if (this.fileInputRef?.nativeElement) {
            this.fileInputRef.nativeElement.click();
        }
    }

    onNativeFileSelect(event: any) {
        const files = event.target.files;
        if (!files || files.length === 0) return;

        const file: File = files[0];
        const validExtensions = ['.xlsx', '.xls'];
        const isValidFile = validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));

        if (!isValidFile) {
            this.messageService.add({
                severity: 'error',
                summary: 'Invalid File',
                detail: 'Only .xlsx and .xls files are supported'
            });
            return;
        }

        this.selectedFile = file;
        this.fileSize = this.formatFileSize(file.size);
        event.target.value = '';
    }

    onUploadImport() {
        // Security Search: Import IDs from Excel → auto-detect identifier columns → preview in table
        if (!this.selectedFile) {
            this.messageService.add({ severity: 'warn', summary: 'No File Selected', detail: 'Please select an Excel file containing Message IDs, CUSIPs, or other identifiers' });
            return;
        }

        this.isUploading = true;

        this.apiService.importIdsPreview(this.selectedFile).subscribe({
            next: (response) => {
                this.isUploading = false;
                this.showImportDialog = false;

                // Populate table with search results
                this.tableData = response.results.map((record: any, index: number) => ({
                    _rowId: `row_${record.MESSAGE_ID || index}`,
                    _selected: false,
                    rowNumber: String(index + 1),
                    messageId: String(record.MESSAGE_ID || ''),
                    ticker: record.TICKER || '',
                    cusip: record.CUSIP || '',
                    bias: record.BIAS || '',
                    date: record.DATE ? new Date(record.DATE).toLocaleDateString() : '',
                    bid: record.BID || 0,
                    mid: ((Number(record.BID) || 0) + (Number(record.ASK) || 0)) / 2,
                    ask: record.ASK || 0,
                    px: record.PX || 0,
                    source: record.SOURCE || '',
                    rank: record.RANK || 5,
                    isParent: record.IS_PARENT ?? true,
                    parentRow: record.PARENT_MESSAGE_ID || undefined,
                    childrenCount: record.CHILDREN_COUNT || 0
                }));

                // Remember file + flag for download button
                this.importPreviewFile = this.selectedFile;
                this.hasImportResults = response.total_matches > 0;

                const cols = response.detected_columns.join(', ');
                this.messageService.add({
                    severity: response.total_matches > 0 ? 'success' : 'warn',
                    summary: response.total_matches > 0 ? `${response.total_matches} Match(es) Found` : 'No Results',
                    detail: response.total_matches > 0
                        ? `Identified by: ${cols}. Use "Download Results" to export.`
                        : `No matching records for the identifiers in ${cols || 'uploaded file'}.`
                });
            },
            error: (error) => {
                this.isUploading = false;
                console.error('Import IDs preview error:', error);
                this.messageService.add({
                    severity: 'error',
                    summary: 'Search Failed',
                    detail: error.error?.detail || error.statusText || 'No matching records found or file format error'
                });
            }
        });
    }

    downloadImportResults() {
        // Download the matched results as Excel using the same uploaded file
        const file = this.importPreviewFile;
        if (!file) {
            this.messageService.add({ severity: 'warn', summary: 'No Results', detail: 'Run an import search first' });
            return;
        }

        this.apiService.importIdsForDownload(file).subscribe({
            next: (blob: Blob) => {
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `import_search_results_${new Date().toISOString().slice(0, 10)}.xlsx`;
                link.click();
                window.URL.revokeObjectURL(url);
                this.messageService.add({ severity: 'success', summary: 'Downloaded', detail: 'Import search results saved as Excel' });
            },
            error: (error) => {
                this.messageService.add({
                    severity: 'error',
                    summary: 'Download Failed',
                    detail: error.error?.detail || 'Failed to generate Excel download'
                });
            }
        });
    }

    clearImportResults() {
        this.hasImportResults = false;
        this.importPreviewFile = null;
        this.loadDataFromBackend();
    }

    clearForSearch() {
        this.searchQuery = '';
        this.hasImportResults = false;
        this.importPreviewFile = null;
        this.activeFilters = [];

        const emptyRow: TableRow = {
            _rowId: `row_new_${Date.now()}`,
            _selected: false,
            rowNumber: '1',
            messageId: '',
            ticker: '',
            cusip: '',
            bias: '',
            date: '',
            bid: '',
            mid: '',
            ask: '',
            px: '',
            source: '',
            isParent: true,
            childrenCount: 0
        };
        this.tableData = [emptyRow];

        this.messageService.add({
            severity: 'info',
            summary: 'Table Cleared',
            detail: 'Enter a Message ID or CUSIP in the row to fetch data'
        });
    }

    onCancelImport() {
        this.showImportDialog = false;
        this.selectedFile = null;
        this.fileSize = '';
        this.isUploading = false;
    }

    getFileIcon(): string {
        if (!this.selectedFile) return 'pi-file';
        const name = this.selectedFile.name.toLowerCase();
        if (name.endsWith('.xlsx') || name.endsWith('.xls')) return 'pi-file-excel';
        return 'pi-file';
    }

    private formatFileSize(bytes: number): string {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }
}
