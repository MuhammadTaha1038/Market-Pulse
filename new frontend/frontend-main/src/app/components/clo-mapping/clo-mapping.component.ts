import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TreeModule } from 'primeng/tree';
import { TreeNode } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { CheckboxModule } from 'primeng/checkbox';
import { MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ChipModule } from 'primeng/chip';
import { InputTextModule } from 'primeng/inputtext';
import { TabsModule } from 'primeng/tabs';
import { DialogModule } from 'primeng/dialog';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import {
    ApiService,
    CLOHierarchy,
    MainCLO,
    CLOMapping,
    ColumnDetail,
    SystemStatus
} from '../../services/api.service';

@Component({
    selector: 'app-clo-mapping',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        TreeModule,
        ButtonModule,
        CardModule,
        CheckboxModule,
        ToastModule,
        ProgressSpinnerModule,
        ChipModule,
        InputTextModule,
        TabsModule,
        DialogModule,
        TagModule,
        TooltipModule
    ],
    providers: [MessageService],
    template: `
    <div class="px-6 py-4 space-y-4 mt-2">
        <p-toast position="top-right"></p-toast>

        <!-- Header -->
        <div class="mb-4">
            <h1 class="text-2xl font-bold text-gray-900 mb-1">Super Admin — CLO Configuration</h1>
            <p class="text-gray-500 text-sm">Configure column visibility, Oracle queries, and data source for each CLO type</p>
        </div>

        <!-- System Status Banner -->
        <div class="bg-white rounded-2xl border border-gray-200 p-4 mb-4 flex flex-wrap items-center gap-4">
            <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-600">Data Source:</span>
                <p-tag [value]="dataSourceType | uppercase" [severity]="dataSourceType === 'oracle' ? 'success' : 'info'" [rounded]="true"></p-tag>
            </div>
            <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-600">Output:</span>
                <p-tag [value]="outputType | uppercase" [severity]="outputType === 's3' ? 'success' : outputType === 'both' ? 'warn' : 'info'" [rounded]="true"></p-tag>
            </div>
            <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-600">Oracle:</span>
                <span class="inline-block w-2.5 h-2.5 rounded-full" [class.bg-green-500]="oracleReady" [class.bg-red-400]="!oracleReady"></span>
                <span class="text-xs text-gray-500">{{ oracleReady ? 'Connected' : 'Not Connected' }}</span>
            </div>
            <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-600">S3:</span>
                <span class="inline-block w-2.5 h-2.5 rounded-full" [class.bg-green-500]="s3Ready" [class.bg-red-400]="!s3Ready"></span>
                <span class="text-xs text-gray-500">{{ s3Ready ? 'Ready' : 'Not Configured' }}</span>
            </div>
            <div class="flex-1"></div>
            <button pButton label="Test Oracle Connection" icon="pi pi-bolt" class="!rounded-full !px-4 !py-2 !bg-gray-900 !text-white !text-sm hover:!bg-black"
                (click)="testOracleConnection()" [disabled]="testingConnection" [loading]="testingConnection"></button>
        </div>

        <div class="grid grid-cols-12 gap-4">
            <!-- Left Panel: CLO Tree -->
            <div class="col-span-12 md:col-span-4">
                <div class="bg-white rounded-2xl border border-gray-200 p-5 h-full">
                    <h3 class="text-lg font-semibold text-gray-900 mb-3">CLO Hierarchy</h3>

                    <div *ngIf="loading" class="flex flex-col items-center py-8">
                        <p-progressSpinner [style]="{width: '40px', height: '40px'}" strokeWidth="4"></p-progressSpinner>
                        <p class="text-sm text-gray-500 mt-3">Loading CLO structure...</p>
                    </div>

                    <div *ngIf="!loading">
                        <div class="flex items-center gap-3 mb-3 text-xs text-gray-500">
                            <span><strong class="text-gray-800">{{ totalMainCLOs }}</strong> Main CLOs</span>
                            <span><strong class="text-gray-800">{{ totalSubCLOs }}</strong> Sub CLOs</span>
                        </div>
                        <p-tree
                            [value]="cloTreeNodes"
                            selectionMode="single"
                            [(selection)]="selectedNode"
                            (onNodeSelect)="onNodeSelect($event)"
                            [style]="{'width': '100%'}"
                            styleClass="clo-tree"
                        ></p-tree>
                    </div>
                </div>
            </div>

            <!-- Right Panel: Configuration -->
            <div class="col-span-12 md:col-span-8">
                <!-- Empty state -->
                <div *ngIf="!selectedCLO" class="bg-white rounded-2xl border border-gray-200 p-10 text-center">
                    <i class="pi pi-info-circle text-4xl text-gray-300 mb-3"></i>
                    <p class="text-gray-500">Select a CLO from the tree to configure</p>
                </div>

                <!-- Configuration panel -->
                <div *ngIf="selectedCLO" class="bg-white rounded-2xl border border-gray-200">
                    <!-- CLO Header -->
                    <div class="p-5 border-b border-gray-100 flex items-center gap-3">
                        <h3 class="text-lg font-semibold text-gray-900">{{ selectedCLO.clo_name }}</h3>
                        <p-tag [value]="selectedCLO.clo_type === 'main' ? 'Main CLO' : 'Sub CLO'" [severity]="selectedCLO.clo_type === 'main' ? 'info' : 'secondary'" [rounded]="true"></p-tag>
                        <span *ngIf="selectedCLO.parent_clo" class="text-sm text-gray-400">under {{ selectedCLO.parent_clo }}</span>
                    </div>

                    <!-- Tabs -->
                    <p-tabs [(value)]="activeTabIndex" styleClass="super-admin-tabs">
                        <p-tablist>
                            <p-tab [value]="0">Oracle Query</p-tab>
                            <p-tab [value]="1">Column Mapping</p-tab>
                            <p-tab [value]="2">Connection & S3</p-tab>
                        </p-tablist>
                        <p-tabpanels>
                        <!-- Tab 1: Oracle Query -->
                        <p-tabpanel [value]="0">
                            <div class="p-4">
                                <p class="text-sm text-gray-500 mb-3">Configure the SQL query to fetch data from Oracle for this CLO. Each sub-asset CLO can have its own custom query.</p>

                                <div *ngIf="dataSourceType === 'excel'" class="mb-4 p-3 bg-amber-50 border-l-4 border-amber-400 rounded text-sm text-amber-800">
                                    <i class="pi pi-exclamation-triangle mr-2"></i>
                                    <strong>Note:</strong> Currently using Excel data source. Set <code class="bg-amber-100 px-1 rounded">DATA_SOURCE=oracle</code> in backend .env to enable Oracle queries. You can still save a query below — it will be used when Oracle mode is activated.
                                </div>

                                <!-- Column alias requirement notice (always shown) -->
                                <div class="mb-4 p-3 bg-blue-50 border-l-4 border-blue-400 rounded text-sm text-blue-800">
                                    <i class="pi pi-info-circle mr-2"></i>
                                    <strong>Required column aliases:</strong> Your query's SELECT must alias its output columns to these exact names (case-insensitive):
                                    <code class="block bg-blue-100 px-2 py-1 rounded mt-1 font-mono text-xs leading-6">
                                        MESSAGE_ID, TICKER, SECTOR, CUSIP, DATE, PRICE_LEVEL, BID, ASK, PX, SOURCE, BIAS, RANK, COV_PRICE, PERCENT_DIFF, PRICE_DIFF, CONFIDENCE, DATE_1, DIFF_STATUS
                                    </code>
                                    Example: <code class="bg-blue-100 px-1 rounded">SELECT col.PRICE_BID AS BID, col.PRICE_ASK AS ASK ...</code>
                                </div>

                                <!-- Saved query indicator -->
                                <div *ngIf="savedQueryInfo" class="mb-3 p-3 bg-green-50 border-l-4 border-green-500 rounded text-sm text-green-800">
                                    <i class="pi pi-check-circle mr-2"></i>
                                    <strong>Saved query loaded</strong> — Last updated: {{ savedQueryInfo.updated_at || 'N/A' }}
                                </div>

                                <div class="flex items-center gap-2 mb-2">
                                    <label class="block text-sm font-medium text-gray-700">SQL Query</label>
                                    <button pButton label="Load Saved Query" icon="pi pi-download"
                                        class="!rounded-full !px-3 !py-1 !bg-blue-50 !text-blue-700 !border !border-blue-300 !text-xs"
                                        (click)="loadSavedQuery()" [disabled]="loadingSavedQuery" [loading]="loadingSavedQuery"></button>
                                </div>
                                <textarea
                                    [(ngModel)]="oracleQuery"
                                    placeholder="SELECT * FROM your_table WHERE ..."
                                    rows="8"
                                    class="w-full p-3 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-gray-900 focus:border-gray-900"
                                ></textarea>

                                <div class="flex items-center gap-3 mt-3">
                                    <button pButton label="Run Query & Fetch Columns" icon="pi pi-play"
                                        class="!rounded-full !px-4 !py-2 !bg-gray-900 !text-white !text-sm hover:!bg-black"
                                        (click)="executeOracleQuery()" [disabled]="!oracleQuery || queryExecuting || dataSourceType !== 'oracle'" [loading]="queryExecuting"
                                        [pTooltip]="dataSourceType !== 'oracle' ? 'Switch DATA_SOURCE=oracle in backend .env to run queries' : ''" tooltipPosition="top"></button>
                                    <button pButton label="Save Query" icon="pi pi-save"
                                        class="!rounded-full !px-4 !py-2 !bg-green-600 !text-white !text-sm hover:!bg-green-700"
                                        (click)="saveOracleQuery()" [disabled]="!oracleQuery || querySaving" [loading]="querySaving"></button>
                                    <span *ngIf="queryResult" class="text-green-600 text-sm"><i class="pi pi-check-circle mr-1"></i>{{ queryResult }}</span>
                                    <span *ngIf="queryError" class="text-red-500 text-sm"><i class="pi pi-times-circle mr-1"></i>{{ queryError }}</span>
                                </div>

                                <!-- Sample data preview -->
                                <div *ngIf="sampleData.length > 0" class="mt-4">
                                    <h4 class="text-sm font-semibold text-gray-700 mb-2">Sample Data ({{ sampleData.length }} rows)</h4>
                                    <div class="overflow-x-auto border border-gray-200 rounded-lg">
                                        <table class="w-full text-sm">
                                            <thead class="bg-gray-50">
                                                <tr>
                                                    <th *ngFor="let col of sampleColumns" class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ col }}</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr *ngFor="let row of sampleData" class="border-t border-gray-100">
                                                    <td *ngFor="let col of sampleColumns" class="px-3 py-2 text-gray-700">{{ row[col] }}</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </p-tabpanel>

                        <!-- Tab 2: Column Mapping -->
                        <p-tabpanel [value]="1">
                            <div class="p-4">
                                <div class="flex flex-wrap items-center gap-3 mb-4">
                                    <div class="relative flex-1 min-w-[200px]">
                                        <input type="text" pInputText [(ngModel)]="searchText" (input)="filterColumns()"
                                            placeholder="Search columns..."
                                            class="w-full !rounded-full !px-4 !py-2 !bg-gray-50 !border !border-gray-300 !text-sm" />
                                        <i class="pi pi-search absolute right-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
                                    </div>
                                    <button pButton label="Select All" icon="pi pi-check-square"
                                        class="!rounded-full !px-4 !py-2 !bg-gray-50 !text-gray-700 !border !border-gray-300 !text-sm"
                                        (click)="selectAllColumns()"></button>
                                    <button pButton label="Deselect All" icon="pi pi-times"
                                        class="!rounded-full !px-4 !py-2 !bg-gray-50 !text-gray-700 !border !border-gray-300 !text-sm"
                                        (click)="deselectAllColumns()"></button>
                                    <button pButton label="Reset" icon="pi pi-refresh"
                                        class="!rounded-full !px-4 !py-2 !bg-amber-50 !text-amber-700 !border !border-amber-300 !text-sm"
                                        (click)="resetToDefault()"></button>
                                </div>

                                <div class="flex gap-2 mb-4">
                                    <span class="px-3 py-1 bg-green-50 text-green-700 rounded-full text-xs font-medium">{{ visibleCount }} Visible</span>
                                    <span class="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium">{{ hiddenCount }} Hidden</span>
                                    <span class="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">Total: {{ selectedCLO.total_columns }}</span>
                                </div>

                                <div class="max-h-[400px] overflow-y-auto border border-gray-200 rounded-xl">
                                    <div *ngFor="let column of filteredColumns" class="flex items-center gap-3 px-4 py-3 border-b border-gray-100 hover:bg-gray-50">
                                        <p-checkbox [(ngModel)]="column.visible" [binary]="true" (onChange)="onColumnToggle()"></p-checkbox>
                                        <div class="flex-1">
                                            <span class="text-sm font-medium text-gray-900">{{ column.display_name }}</span>
                                            <span class="text-xs text-gray-400 font-mono ml-2">{{ column.oracle_name }}</span>
                                        </div>
                                        <span class="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs">{{ column.data_type }}</span>
                                        <span *ngIf="column.required" class="px-2 py-0.5 bg-amber-50 text-amber-600 rounded text-xs">Required</span>
                                    </div>
                                    <div *ngIf="filteredColumns.length === 0" class="text-center py-8 text-gray-400 text-sm">
                                        <i class="pi pi-search text-2xl block mb-2"></i>
                                        No columns match your search
                                    </div>
                                </div>

                                <div class="flex items-center gap-3 mt-4 pt-4 border-t border-gray-200">
                                    <button pButton label="Save Changes" icon="pi pi-save"
                                        class="!rounded-full !px-5 !py-2.5 !bg-gray-900 !text-white !text-sm hover:!bg-black"
                                        (click)="saveMapping()" [disabled]="saving || !hasChanges" [loading]="saving"></button>
                                    <button pButton label="Cancel" icon="pi pi-times"
                                        class="!rounded-full !px-5 !py-2.5 !bg-gray-50 !text-gray-700 !border !border-gray-300 !text-sm"
                                        (click)="cancelChanges()" [disabled]="saving"></button>
                                </div>

                                <div *ngIf="selectedCLO.updated_by" class="mt-3 text-xs text-gray-400">
                                    Last updated by <strong>{{ selectedCLO.updated_by }}</strong> on {{ selectedCLO.updated_at }}
                                </div>
                            </div>
                        </p-tabpanel>

                        <!-- Tab 3: Connection & S3 -->
                        <p-tabpanel [value]="2">
                            <div class="p-4 space-y-4">
                                <!-- Credentials API Status -->
                                <div class="bg-gray-50 rounded-xl p-4 border border-gray-200">
                                    <h4 class="text-sm font-semibold text-gray-800 mb-3"><i class="pi pi-key mr-2"></i>Credentials API</h4>
                                    <p class="text-xs text-gray-500 mb-3">Oracle credentials are fetched from the client's API endpoint (ORACLE_CREDENTIALS_API_URL). No manual credentials needed.</p>
                                    <div class="flex items-center gap-3 mb-3">
                                        <span class="inline-block w-2.5 h-2.5 rounded-full" [class.bg-green-500]="credentialsApiOk" [class.bg-red-400]="!credentialsApiOk" [class.bg-gray-300]="credentialsApiStatus === null"></span>
                                        <span class="text-sm text-gray-700">{{ credentialsApiMessage || 'Not tested yet' }}</span>
                                    </div>
                                    <div *ngIf="credentialsApiSource" class="text-xs text-gray-500 mb-3">
                                        Source: <span class="font-medium text-gray-800">{{ credentialsApiSource }}</span>
                                    </div>
                                    <button pButton label="Test Credentials API" icon="pi pi-sync"
                                        class="!rounded-full !px-4 !py-2 !bg-gray-900 !text-white !text-sm hover:!bg-black"
                                        (click)="testCredentialsApi()" [disabled]="testingCredentials" [loading]="testingCredentials"></button>
                                </div>

                                <!-- Oracle Connection Info -->
                                <div class="bg-gray-50 rounded-xl p-4 border border-gray-200">
                                    <h4 class="text-sm font-semibold text-gray-800 mb-3"><i class="pi pi-database mr-2"></i>Oracle Connection</h4>
                                    <div *ngIf="connectionInfo" class="grid grid-cols-2 gap-3 text-sm">
                                        <div><span class="text-gray-500">Mode:</span> <span class="font-medium text-gray-800">{{ connectionInfo.mode || 'N/A' }}</span></div>
                                        <div><span class="text-gray-500">Host:</span> <span class="font-mono text-gray-800">{{ connectionInfo.oracle_config?.host || 'Not configured' }}</span></div>
                                        <div><span class="text-gray-500">Service:</span> <span class="font-mono text-gray-800">{{ connectionInfo.oracle_config?.service_name || 'Not configured' }}</span></div>
                                        <div><span class="text-gray-500">Columns:</span> <span>{{ connectionInfo.column_count || 0 }}</span></div>
                                    </div>
                                    <div *ngIf="!connectionInfo" class="text-sm text-gray-400">Loading connection info...</div>
                                    <div class="flex gap-3 mt-3">
                                        <button pButton label="Test Connection" icon="pi pi-bolt"
                                            class="!rounded-full !px-4 !py-2 !bg-gray-50 !text-gray-700 !border !border-gray-300 !text-sm"
                                            (click)="testOracleConnection()" [disabled]="testingConnection" [loading]="testingConnection"></button>
                                    </div>
                                </div>

                                <!-- S3 Output Info -->
                                <div class="bg-gray-50 rounded-xl p-4 border border-gray-200">
                                    <h4 class="text-sm font-semibold text-gray-800 mb-3"><i class="pi pi-cloud mr-2"></i>S3 Output Destination</h4>
                                    <div class="text-sm space-y-1">
                                        <div><span class="text-gray-500">Output Mode:</span> <span class="font-medium text-gray-800">{{ outputType }}</span></div>
                                        <div><span class="text-gray-500">S3 Status:</span>
                                            <span [class.text-green-600]="s3Ready" [class.text-red-500]="!s3Ready">{{ s3Ready ? 'Connected & Ready' : 'Not Configured' }}</span>
                                        </div>
                                    </div>
                                    <p class="mt-3 text-xs text-gray-400">S3 configuration is set via backend environment: S3_BUCKET_NAME, S3_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, OUTPUT_DESTINATION</p>
                                </div>

                                <!-- Configuration Note -->
                                <div class="bg-blue-50 rounded-xl p-4 border border-blue-200">
                                    <h4 class="text-sm font-semibold text-blue-800 mb-2"><i class="pi pi-info-circle mr-2"></i>Configuration Notes</h4>
                                    <ul class="text-xs text-blue-700 space-y-1">
                                        <li>• Credentials are auto-fetched from client's API — no table name or column names in .env</li>
                                        <li>• Each sub-asset CLO can have its own custom SQL query (saved in Oracle Query tab)</li>
                                        <li>• Backend .env requires: ORACLE_CREDENTIALS_API_URL, ORACLE_HOST, ORACLE_PORT, ORACLE_SERVICE_NAME</li>
                                        <li>• Set DATA_SOURCE=oracle and OUTPUT_DESTINATION=s3 (or both) in backend .env</li>
                                    </ul>
                                </div>
                            </div>
                        </p-tabpanel>
                        </p-tabpanels>
                    </p-tabs>
                </div>
            </div>
        </div>
    </div>
    `,
    styles: [`
        :host { display: block; }
        ::ng-deep .clo-tree .p-tree { border: none !important; padding: 0 !important; }
        ::ng-deep .clo-tree .p-treenode-content { border-radius: 8px !important; padding: 0.5rem !important; }
        ::ng-deep .clo-tree .p-treenode-content:hover { background: #f3f4f6 !important; }
        ::ng-deep .clo-tree .p-highlight > .p-treenode-content { background: #111827 !important; color: white !important; }
        ::ng-deep .super-admin-tabs .p-tablist { border-bottom: 1px solid #e5e7eb; padding: 0 1rem; }
        ::ng-deep .super-admin-tabs .p-tab { border: none !important; border-bottom: 2px solid transparent !important; color: #6b7280; font-size: 0.875rem; padding: 0.75rem 1rem; cursor: pointer; }
        ::ng-deep .super-admin-tabs .p-tab-active { border-bottom-color: #111827 !important; color: #111827 !important; font-weight: 600; }
        ::ng-deep .super-admin-tabs .p-tabpanels { padding: 0 !important; }
    `]
})
export class CloMappingComponent implements OnInit {
    // Tree
    cloTreeNodes: TreeNode[] = [];
    selectedNode: TreeNode | null = null;
    selectedCLO: CLOMapping | null = null;
    originalMapping: CLOMapping | null = null;
    activeTabIndex: number = 0;

    // Columns
    allColumns: ColumnDetail[] = [];
    filteredColumns: ColumnDetail[] = [];
    searchText = '';

    // Counts
    totalMainCLOs = 0;
    totalSubCLOs = 0;

    // State
    loading = false;
    saving = false;

    // Oracle Query
    oracleQuery = '';
    queryExecuting = false;
    querySaving = false;
    queryResult = '';
    queryError = '';
    sampleData: any[] = [];
    sampleColumns: string[] = [];

    // System status
    dataSourceType = 'excel';
    outputType = 'local';
    oracleReady = false;
    s3Ready = false;
    connectionInfo: any = null;
    testingConnection = false;

    // Credentials API
    credentialsApiOk = false;
    credentialsApiMessage = '';
    credentialsApiSource = '';
    credentialsApiStatus: any = null;
    testingCredentials = false;

    // Saved query
    savedQueryInfo: any = null;
    loadingSavedQuery = false;

    constructor(
        private apiService: ApiService,
        private messageService: MessageService
    ) {}

    ngOnInit() {
        this.loadCLOHierarchy();
        this.loadSystemStatus();
        this.loadConnectionInfo();
        this.testCredentialsApi();
    }

    // ==================== SYSTEM STATUS ====================

    loadSystemStatus() {
        this.apiService.getSystemStatus().subscribe({
            next: (status: SystemStatus) => {
                this.dataSourceType = status.data_source?.info?.type?.toLowerCase() || 'excel';
                this.outputType = status.output_destination?.info?.type?.toLowerCase() || 'local';
                this.oracleReady = status.oracle_ready || false;
                this.s3Ready = status.s3_ready || false;
            },
            error: (err) => console.error('Error loading system status:', err)
        });
    }

    loadConnectionInfo() {
        this.apiService.getConnectionInfo().subscribe({
            next: (info) => this.connectionInfo = info,
            error: (err) => console.error('Error loading connection info:', err)
        });
    }

    testOracleConnection() {
        this.testingConnection = true;
        this.apiService.testOracleConnection().subscribe({
            next: (res: any) => {
                this.testingConnection = false;
                this.messageService.add({ severity: 'success', summary: 'Connection OK', detail: res.message || 'Oracle connection successful' });
                this.loadSystemStatus();
                this.loadConnectionInfo();
            },
            error: (err) => {
                this.testingConnection = false;
                this.messageService.add({ severity: 'error', summary: 'Connection Failed', detail: err.error?.detail || 'Could not connect to Oracle' });
            }
        });
    }

    testCredentialsApi() {
        this.testingCredentials = true;
        this.apiService.testCredentialsApi().subscribe({
            next: (res: any) => {
                this.testingCredentials = false;
                this.credentialsApiOk = res.success;
                this.credentialsApiMessage = res.message || 'Unknown';
                this.credentialsApiSource = res.credentials_source || '';
                this.credentialsApiStatus = res;
                if (res.success) {
                    this.messageService.add({ severity: 'success', summary: 'Credentials API', detail: 'Credentials fetched successfully' });
                }
            },
            error: (err) => {
                this.testingCredentials = false;
                this.credentialsApiOk = false;
                this.credentialsApiMessage = err.error?.detail || 'Failed to test credentials API';
            }
        });
    }

    // ==================== CLO HIERARCHY ====================

    loadCLOHierarchy() {
        this.loading = true;
        this.apiService.getCloHierarchy().subscribe({
            next: (hierarchy: CLOHierarchy) => {
                this.totalMainCLOs = hierarchy.total_main_clos;
                this.totalSubCLOs = hierarchy.total_sub_clos;
                this.buildTreeNodes(hierarchy);
                this.loading = false;
            },
            error: (error) => {
                this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load CLO hierarchy' });
                this.loading = false;
            }
        });
    }

    buildTreeNodes(hierarchy: CLOHierarchy) {
        this.cloTreeNodes = hierarchy.main_clos.map((mainCLO: MainCLO) => ({
            label: mainCLO.display_name,
            data: { cloId: mainCLO.id, type: 'main' },
            icon: 'pi pi-folder',
            expanded: false,
            children: mainCLO.sub_clos.map(subCLO => ({
                label: subCLO.display_name,
                data: { cloId: subCLO.id, type: 'sub' },
                icon: 'pi pi-file'
            }))
        }));
    }

    onNodeSelect(event: any) {
        const cloId = event.node.data.cloId;
        this.loadCLOMapping(cloId);
        this.loadSavedQuery();
    }

    loadCLOMapping(cloId: string) {
        this.apiService.getCloMapping(cloId).subscribe({
            next: (mapping: CLOMapping) => {
                this.selectedCLO = mapping;
                this.originalMapping = JSON.parse(JSON.stringify(mapping));
                this.prepareColumnsForDisplay();
            },
            error: (error) => {
                this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load CLO mapping' });
            }
        });
    }

    // ==================== SAVED QUERY ====================

    loadSavedQuery() {
        if (!this.selectedCLO && !this.selectedNode) return;
        const cloId = this.selectedCLO?.clo_id || this.selectedNode?.data?.cloId;
        if (!cloId) return;

        this.loadingSavedQuery = true;
        this.savedQueryInfo = null;
        this.apiService.getSavedQuery(cloId).subscribe({
            next: (res: any) => {
                this.loadingSavedQuery = false;
                if (res.query) {
                    this.oracleQuery = res.query;
                    this.savedQueryInfo = { updated_at: res.updated_at, query_name: res.query_name };
                    this.messageService.add({ severity: 'info', summary: 'Query Loaded', detail: `Saved query loaded for ${cloId}` });
                } else {
                    this.oracleQuery = '';
                    this.savedQueryInfo = null;
                    this.messageService.add({ severity: 'info', summary: 'No Query', detail: `No saved query for ${cloId}` });
                }
            },
            error: () => {
                this.loadingSavedQuery = false;
                this.messageService.add({ severity: 'warn', summary: 'Warning', detail: 'Could not load saved query' });
            }
        });
    }

    // ==================== ORACLE QUERY ====================

    executeOracleQuery() {
        if (!this.oracleQuery || !this.selectedCLO) {
            this.messageService.add({ severity: 'warn', summary: 'Warning', detail: 'Please enter a SQL query' });
            return;
        }
        this.queryExecuting = true;
        this.queryResult = '';
        this.queryError = '';
        this.sampleData = [];
        this.sampleColumns = [];

        this.apiService.executeQueryWithSample(this.oracleQuery, this.selectedCLO.clo_id).subscribe({
            next: (response: any) => {
                this.queryExecuting = false;
                this.queryResult = response.message || `Found ${response.columns?.length || 0} columns`;

                // Show sample data result — do NOT overwrite allColumns here.
                // allColumns drives the Column Mapping tab (tab 1) and must retain
                // the visible/hidden state from clo_mappings.json.
                // Overwriting it with Oracle query response (which has `enabled` not `visible`)
                // would reset all checkboxes to unchecked and corrupt the mapping on next Save.
                if (response.sample_data && response.sample_data.length > 0) {
                    this.sampleData = response.sample_data;
                    this.sampleColumns = Object.keys(response.sample_data[0]);
                }

                this.messageService.add({ severity: 'success', summary: 'Query Executed', detail: `Found ${response.columns?.length || 0} columns — switch to Column Mapping tab to configure visibility` });
                setTimeout(() => { this.queryResult = ''; }, 5000);
            },
            error: (error) => {
                this.queryExecuting = false;
                this.queryError = error.error?.detail || 'Failed to execute query';
                this.messageService.add({ severity: 'error', summary: 'Query Failed', detail: this.queryError });
                setTimeout(() => { this.queryError = ''; }, 10000);
            }
        });
    }

    saveOracleQuery() {
        if (!this.oracleQuery || !this.selectedCLO) {
            this.messageService.add({ severity: 'warn', summary: 'Warning', detail: 'Please enter a SQL query' });
            return;
        }
        this.querySaving = true;
        this.apiService.saveQueryConfig(this.oracleQuery, this.selectedCLO.clo_id, 'base_query').subscribe({
            next: () => {
                this.querySaving = false;
                this.messageService.add({ severity: 'success', summary: 'Saved', detail: `Query saved for ${this.selectedCLO!.clo_name}` });
            },
            error: (error) => {
                this.querySaving = false;
                this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to save Oracle query' });
            }
        });
    }

    // ==================== COLUMN MAPPING ====================

    prepareColumnsForDisplay() {
        if (!this.selectedCLO) return;
        this.allColumns = [
            ...this.selectedCLO.visible_columns.map(col => ({ ...col, visible: true })),
            ...this.selectedCLO.hidden_columns.map(col => ({ ...col, visible: false }))
        ];
        this.filterColumns();
    }

    filterColumns() {
        if (!this.searchText) {
            this.filteredColumns = [...this.allColumns];
        } else {
            const search = this.searchText.toLowerCase();
            this.filteredColumns = this.allColumns.filter(col =>
                col.display_name.toLowerCase().includes(search) ||
                col.oracle_name.toLowerCase().includes(search) ||
                col.description?.toLowerCase().includes(search)
            );
        }
    }

    onColumnToggle() { /* Triggers Angular change detection for hasChanges getter */ }
    selectAllColumns() { this.allColumns.forEach(col => col.visible = true); this.filterColumns(); }
    deselectAllColumns() { this.allColumns.forEach(col => col.visible = false); this.filterColumns(); }

    resetToDefault() {
        if (!this.selectedCLO) return;
        if (confirm('Reset this CLO to show all columns?')) {
            this.apiService.resetCloMapping(this.selectedCLO.clo_id).subscribe({
                next: () => {
                    this.messageService.add({ severity: 'success', summary: 'Reset', detail: 'CLO mapping reset to default' });
                    this.loadCLOMapping(this.selectedCLO!.clo_id);
                },
                error: () => this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to reset CLO mapping' })
            });
        }
    }

    saveMapping() {
        if (!this.selectedCLO) return;
        const visibleColumns = this.allColumns.filter(col => col.visible).map(col => col.oracle_name);
        this.saving = true;
        this.apiService.updateCloMapping(this.selectedCLO.clo_id, visibleColumns, 'admin').subscribe({
            next: () => {
                this.messageService.add({ severity: 'success', summary: 'Saved', detail: `Updated column mapping for ${this.selectedCLO!.clo_name}` });
                this.loadCLOMapping(this.selectedCLO!.clo_id);
                this.saving = false;
            },
            error: () => {
                this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to save CLO mapping' });
                this.saving = false;
            }
        });
    }

    cancelChanges() {
        if (this.originalMapping) {
            this.selectedCLO = JSON.parse(JSON.stringify(this.originalMapping));
            this.prepareColumnsForDisplay();
            this.messageService.add({ severity: 'info', summary: 'Cancelled', detail: 'Changes discarded' });
        }
    }

    get visibleCount(): number { return this.allColumns.filter(col => col.visible).length; }
    get hiddenCount(): number { return this.allColumns.filter(col => !col.visible).length; }
    get hasChanges(): boolean {
        if (!this.selectedCLO || !this.originalMapping) return false;
        const currentVisible = this.allColumns.filter(col => col.visible).map(col => col.oracle_name).sort();
        const originalVisible = this.originalMapping.visible_columns.map(col => col.oracle_name).sort();
        return JSON.stringify(currentVisible) !== JSON.stringify(originalVisible);
    }
}
