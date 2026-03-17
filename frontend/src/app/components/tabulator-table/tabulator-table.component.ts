import { Component, OnInit, AfterViewInit, ViewChild, ElementRef, Input, Output, EventEmitter, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { FileUploadModule } from 'primeng/fileupload';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService } from 'primeng/api';
import { TabulatorService, TableData } from './tabulator.service';

declare var Tabulator: any;

export interface TableConfig {
    title?: string;
    editable?: boolean;
    allowImport?: boolean;
    allowExport?: boolean;
    allowS3Fetch?: boolean;
    pagination?: boolean;
    paginationSize?: number;
    selectable?: boolean;
    movableColumns?: boolean;
    headerFilter?: boolean;
}

@Component({
    selector: 'app-tabulator-table',
    standalone: true,
    imports: [CommonModule, FormsModule, ButtonModule, FileUploadModule, ToastModule, TooltipModule],
    templateUrl: './tabulator-table.component.html',
    styleUrls: ['./tabulator-table.component.css'],
    providers: [MessageService]
})
export class TabulatorTableComponent implements AfterViewInit {
    @ViewChild('tableContainer') tableContainer!: ElementRef;

    // Configuration inputs
    @Input() config: TableConfig = {
        title: 'Data Table',
        editable: false,
        allowImport: true,
        allowExport: true,
        allowS3Fetch: true,
        pagination: true,
        paginationSize: 20,
        selectable: true,
        movableColumns: true,
        headerFilter: true
    };

    @Input() initialData: any[] = [];
    @Input() columns: any[] = [];
    @Input() showExpandButton: boolean = false; // Only show on home page

    // Output events
    @Output() dataChanged = new EventEmitter<any[]>();
    @Output() rowSelected = new EventEmitter<any[]>();
    @Output() dataLoaded = new EventEmitter<any[]>();
    @Output() expandToggled = new EventEmitter<boolean>();

    table: any;
    tableData: any[] = [];
    selectedRows: any[] = [];
    isLoading: boolean = false;
    isExpanded: boolean = false;
    isInitialized: boolean = false; // Prevent duplicate initialization
    s3BucketName: string = '';
    s3FileName: string = '';

    // Floating action dialog
    showFloatingActions: boolean = false;
    floatingActionsPosition = { bottom: '20px', left: '50%' };

    constructor(
        private tabulatorService: TabulatorService,
        private messageService: MessageService,
        private cdr: ChangeDetectorRef
    ) {}

    ngAfterViewInit() {
        console.log('🚀 Tabulator component view initialized (Editable:', this.config.editable, ')');

        // Prevent duplicate initialization
        if (this.isInitialized) {
            console.log('⚠️ Already initialized, skipping');
            return;
        }

        // Detect changes first to ensure DOM is updated
        this.cdr.detectChanges();

        // Use multiple setTimeout approach for better reliability
        setTimeout(() => {
            const tableElement = document.getElementById('data-table');

            if (tableElement && tableElement.offsetParent !== null) {
                // Element exists and is visible
                this.initializeTable();
                this.isInitialized = true;

                if (this.initialData && this.initialData.length > 0) {
                    // Add another small delay before loading data
                    setTimeout(() => {
                        this.loadTableData(this.initialData);
                    }, 100);
                }
            } else {
                console.error('❌ Table element not ready or not visible');
            }
        }, 100);
    }

    /**
     * Initialize Tabulator table based on configuration
     */
    private initializeTable() {
        // Check if DOM element exists and is visible
        const tableElement = document.getElementById('data-table');
        if (!tableElement) {
            console.error('❌ Table element #data-table not found');
            return;
        }

        // Check if element has dimensions (is rendered)
        const rect = tableElement.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) {
            console.error('❌ Table element has no dimensions');
            return;
        }

        console.log('✅ Table element ready:', rect.width, 'x', rect.height);

        // Use custom columns if provided, otherwise use defaults
        const tableColumns = this.columns.length > 0 ? this.columns : this.getDefaultColumns();

        // Configure columns based on editable mode
        const configuredColumns = tableColumns.map((col) => {
            // Never make select and rowNumber columns editable
            const isNonEditableField = col.field === 'select' || col.field === 'rowNumber';

            return {
                ...col,
                editor: isNonEditableField ? false : this.config.editable ? 'input' : false,
                editable: isNonEditableField ? false : this.config.editable,
                resizable: true,
                headerSort: col.headerSort !== false,
                headerFilter: col.headerFilter // Use column-specific setting
            };
        });

        const tableConfig: any = {
            data: [],
            layout: 'fitDataFill', // Better for responsive + fixed widths
            responsiveLayout: false,
            locale: 'en-us',
            placeholder: 'No Data Available',
            columns: configuredColumns,

            // Pagination
            pagination: this.config.pagination ? 'local' : false,
            paginationSize: this.config.paginationSize || 20,
            paginationSizeSelector: [10, 20, 50, 100],

            // Features
            movableColumns: this.config.movableColumns,
            movableRows: this.config.editable,
            selectable: this.config.selectable ? 'highlight' : false,

            clipboard: true,
            clipboardCopyStyled: false,

            history: this.config.editable,

            // Height - dynamic based on expanded state
            height: this.isExpanded ? 'calc(100vh - 220px)' : '600px',

            // Virtual rendering for performance
            renderVertical: 'virtual',
            renderHorizontal: 'virtual'
        };

        try {
            this.table = new Tabulator('#data-table', tableConfig);
            console.log('✅ Tabulator initialized successfully');

            // Wait for table to be fully built before returning
            this.table.on('tableBuilt', () => {
                console.log('✅ Tabulator table built and ready');
            });
        } catch (error) {
            console.error('❌ Error initializing Tabulator:', error);
            this.messageService.add({
                severity: 'error',
                summary: 'Error',
                detail: 'Failed to initialize table'
            });
            this.isInitialized = false; // Reset flag on error
            return;
        }

        // Event listeners
        if (this.config.editable) {
            this.table.on('cellEdited', (cell: any) => {
                const updatedData = this.table.getData();
                this.tableData = updatedData;
                this.dataChanged.emit(updatedData);
            });

            this.table.on('rowMoved', () => {
                const updatedData = this.table.getData();
                this.tableData = updatedData;
                this.dataChanged.emit(updatedData);
            });
        }

        if (this.config.selectable) {
            this.table.on('rowSelectionChanged', (data: any, rows: any) => {
                const selectedData = rows.map((row: any) => row.getData());
                this.selectedRows = selectedData;
                this.rowSelected.emit(selectedData);

                // Show floating actions only in editable mode when rows are selected
                this.showFloatingActions = this.config.editable === true && selectedData.length > 0;

                console.log('📊 Selected rows:', selectedData.length);
            });
        }
    }

    /**
     * Get default columns for the table
     */
    private getDefaultColumns() {
        return [
            {
                title: '',
                field: 'select',
                width: 80,
                editor: false,
                headerSort: false,
                frozen: true,
                hozAlign: 'center',
                headerFilter: false,
                formatter: (cell: any) => {
                    return '<button class="select-row-btn">Select</button>';
                },
                cellClick: (e: any, cell: any) => {
                    const row = cell.getRow();
                    row.toggleSelect();
                }
            },
            {
                title: '#',
                field: 'rowNumber',
                width: 60,
                editor: false,
                headerSort: false,
                frozen: true,
                hozAlign: 'center',
                headerFilter: false,
                formatter: (cell: any) => {
                    const data = cell.getData();
                    // Display hierarchical number but editable rows use simple numbering
                    return data.hierarchyNumber || data.rowNumber || cell.getRow().getPosition() + 1;
                }
            },
            {
                title: 'Message ID',
                field: 'messageId',
                width: 180,
                headerFilter: false
            },
            {
                title: 'Ticker ID',
                field: 'tickerId',
                width: 140,
                headerFilter: false
            },
            {
                title: 'CUSIP',
                field: 'cusip',
                width: 140,
                headerFilter: false
            },
            {
                title: 'Bias',
                field: 'bias',
                width: 140,
                headerFilter: false
            },
            {
                title: 'Date',
                field: 'date',
                width: 120,
                sorter: 'date',
                headerFilter: false
            },
            {
                title: 'BID',
                field: 'bid',
                width: 100,
                hozAlign: 'center',
                headerFilter: false
            },
            {
                title: 'MID',
                field: 'mid',
                width: 100,
                hozAlign: 'center',
                headerFilter: false
            },
            {
                title: 'ASK',
                field: 'ask',
                width: 100,
                hozAlign: 'center',
                headerFilter: false
            },
            {
                title: 'Source',
                field: 'source',
                width: 140,
                headerFilter: false
            }
        ];
    }

    /**
     * Handle Excel file upload
     */
    onExcelFileSelected(event: any) {
        const file: File = event.target?.files?.[0];
        if (!file) return;

        console.log('📥 Excel file selected:', file.name);
        this.isLoading = true;

        this.tabulatorService
            .parseExcelFile(file)
            .then(
                (tableData: TableData) => {
                    console.log('✅ Excel parsed:', tableData.data.length, 'rows');
                    this.loadTableData(tableData.data);
                    this.dataLoaded.emit(tableData.data);
                    this.messageService.add({
                        severity: 'success',
                        summary: 'Success',
                        detail: `Loaded ${tableData.data.length} rows from Excel`
                    });
                    event.target.value = '';
                },
                (error) => {
                    console.error('❌ Error parsing Excel:', error);
                    this.messageService.add({
                        severity: 'error',
                        summary: 'Error',
                        detail: error.message
                    });
                    event.target.value = '';
                }
            )
            .finally(() => {
                this.isLoading = false;
            });
    }

    /**
     * Fetch data from S3
     */
    fetchFromS3() {
        if (!this.s3BucketName || !this.s3FileName) {
            this.messageService.add({
                severity: 'warn',
                summary: 'Warning',
                detail: 'Please enter bucket name and file name'
            });
            return;
        }

        console.log('📥 Fetching from S3:', this.s3BucketName, this.s3FileName);
        this.isLoading = true;

        this.tabulatorService
            .fetchFromS3(this.s3BucketName, this.s3FileName)
            .subscribe({
                next: (tableData: TableData) => {
                    console.log('✅ S3 data fetched:', tableData.data.length, 'rows');
                    this.loadTableData(tableData.data);
                    this.dataLoaded.emit(tableData.data);
                    this.messageService.add({
                        severity: 'success',
                        summary: 'Success',
                        detail: `Loaded ${tableData.data.length} rows from S3`
                    });
                },
                error: (error) => {
                    console.error('❌ Error fetching S3 data:', error);
                    this.messageService.add({
                        severity: 'error',
                        summary: 'Error',
                        detail: 'Failed to fetch data from S3'
                    });
                }
            })
            .add(() => {
                this.isLoading = false;
            });
    }

    /**
     * Load data into table with row numbers
     */
    private loadTableData(data: any[]) {
        if (!this.table) {
            console.warn('⚠️ Table not initialized yet, data will be loaded after initialization');
            return;
        }

        const dataWithRowNumbers = data.map((row, index) => ({
            rowNumber: row.rowNumber || String(index + 1),
            ...row
        }));

        this.tableData = dataWithRowNumbers;
        this.table.setData(dataWithRowNumbers);
        console.log('📊 Table updated with', dataWithRowNumbers.length, 'rows');
    }

    /**
     * Export to CSV (selected rows if any, otherwise all)
     */
    exportToCSV() {
        const dataToExport = this.selectedRows.length > 0 ? this.selectedRows : this.table.getData();

        if (dataToExport.length === 0) {
            this.messageService.add({
                severity: 'warn',
                summary: 'Warning',
                detail: 'No data to export'
            });
            return;
        }

        const fileName = this.selectedRows.length > 0 ? 'selected-rows' : 'table-data';
        this.tabulatorService.exportToCSV(dataToExport, fileName);

        this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: `Exported ${dataToExport.length} row(s) to CSV`
        });
    }

    /**
     * Export to Excel (selected rows if any, otherwise all)
     */
    exportToExcel() {
        const dataToExport = this.selectedRows.length > 0 ? this.selectedRows : this.table.getData();

        if (dataToExport.length === 0) {
            this.messageService.add({
                severity: 'warn',
                summary: 'Warning',
                detail: 'No data to export'
            });
            return;
        }

        const fileName = this.selectedRows.length > 0 ? 'selected-rows' : 'table-data';
        this.tabulatorService.exportToExcel(dataToExport, fileName);

        this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: `Exported ${dataToExport.length} row(s) to Excel`
        });
    }

    /**
     * Clear all data
     */
    clearData() {
        this.table.clearData();
        this.tableData = [];
        this.selectedRows = [];
        this.messageService.add({
            severity: 'info',
            summary: 'Info',
            detail: 'Table cleared'
        });
    }

    /**
     * Clear selection
     */
    clearSelection() {
        this.table.deselectRow();
        this.selectedRows = [];
        this.messageService.add({
            severity: 'info',
            summary: 'Info',
            detail: 'Selection cleared'
        });
    }

    /**
     * Get current table data
     */
    getTableData(): any[] {
        return this.table.getData();
    }

    /**
     * Get selected rows
     */
    getSelectedRows(): any[] {
        const rows = this.table.getSelectedRows();
        return rows.map((row: any) => row.getData());
    }

    /**
     * Undo last change (only in editable mode)
     */
    undoChange() {
        if (this.config.editable && this.table.getHistoryUndoSize() > 0) {
            this.table.undo();
            this.dataChanged.emit(this.table.getData());
        }
    }

    /**
     * Redo last change (only in editable mode)
     */
    redoChange() {
        if (this.config.editable && this.table.getHistoryRedoSize() > 0) {
            this.table.redo();
            this.dataChanged.emit(this.table.getData());
        }
    }

    /**
     * Add new row (only in editable mode)
     */
    addNewRow() {
        if (this.config.editable) {
            const newRow = { rowNumber: this.tableData.length + 1 };
            this.table.addRow(newRow, false);
            this.tableData = this.table.getData();
            this.dataChanged.emit(this.tableData);
        }
    }

    /**
     * Delete selected rows (only in editable mode)
     */
    deleteSelectedRows() {
        if (this.config.editable) {
            const selectedRows = this.table.getSelectedRows();
            selectedRows.forEach((row: any) => row.delete());
            this.tableData = this.table.getData();
            this.selectedRows = [];
            this.dataChanged.emit(this.tableData);
            this.messageService.add({
                severity: 'info',
                summary: 'Info',
                detail: 'Selected rows deleted'
            });
        }
    }

    /**
     * Get export button label
     */
    getExportLabel(): string {
        return this.selectedRows.length > 0 ? `Export Selected (${this.selectedRows.length})` : 'Export All';
    }

    // ==================== PARENT/CHILD HIERARCHY OPERATIONS ====================

    /**
     * Swap parent row with child row
     */
    swapParentChild() {
        if (this.selectedRows.length !== 1) {
            this.messageService.add({
                severity: 'warn',
                summary: 'Warning',
                detail: 'Please select exactly one row to swap'
            });
            return;
        }

        console.log('🔄 Swapping parent with child for:', this.selectedRows[0]);
        this.messageService.add({
            severity: 'info',
            summary: 'Swap Operation',
            detail: 'Parent/Child swap functionality - Implementation needed'
        });
        // TODO: Implement swap logic based on your data structure
    }

    /**
     * Assign child row as parent
     */
    assignAsParent() {
        if (this.selectedRows.length !== 1) {
            this.messageService.add({
                severity: 'warn',
                summary: 'Warning',
                detail: 'Please select exactly one row to assign as parent'
            });
            return;
        }

        console.log('⬆️ Assigning as parent:', this.selectedRows[0]);
        this.messageService.add({
            severity: 'success',
            summary: 'Assign as Parent',
            detail: 'Row assigned as parent successfully'
        });
        // TODO: Implement assign as parent logic
    }

    /**
     * Delete selected rows (and their children if parent)
     */
    deleteSelectedRowsFromFloating() {
        if (this.selectedRows.length === 0) {
            this.messageService.add({
                severity: 'warn',
                summary: 'Warning',
                detail: 'No rows selected to delete'
            });
            return;
        }

        const count = this.selectedRows.length;
        console.log('🗑️ Deleting selected rows:', count);

        // Collect all rows to delete (including children of parents)
        const rowsToDelete = new Set<string>();

        this.selectedRows.forEach((selectedRow) => {
            // Add the selected row itself
            rowsToDelete.add(selectedRow.messageId);

            // If it's a parent, add all its children
            if (selectedRow.isParent && selectedRow.childrenCount > 0) {
                const parentRowNum = selectedRow.rowNumber;

                // Find all children with this parent
                this.tableData.forEach((row) => {
                    if (row.parentRow === parentRowNum) {
                        rowsToDelete.add(row.messageId);

                        // If child is also a parent (nested), find its children
                        if (row.isParent && row.childrenCount > 0) {
                            const childParentRowNum = row.rowNumber;
                            this.tableData.forEach((nestedRow) => {
                                if (nestedRow.parentRow === childParentRowNum) {
                                    rowsToDelete.add(nestedRow.messageId);
                                }
                            });
                        }
                    }
                });
            }
        });

        console.log('🗑️ Total rows to delete (including children):', rowsToDelete.size);

        // Delete from Tabulator
        const allRows = this.table.getRows();
        allRows.forEach((row: any) => {
            const rowData = row.getData();
            if (rowsToDelete.has(rowData.messageId)) {
                row.delete();
            }
        });

        this.tableData = this.table.getData();
        this.selectedRows = [];
        this.showFloatingActions = false;
        this.dataChanged.emit(this.tableData);

        this.messageService.add({
            severity: 'success',
            summary: 'Deleted',
            detail: `${rowsToDelete.size} row(s) deleted successfully`
        });
    }

    toggleExpand() {
        this.isExpanded = !this.isExpanded;
        this.expandToggled.emit(this.isExpanded);

        // Update table height
        if (this.table) {
            const newHeight = this.isExpanded ? 'calc(100vh - 220px)' : '600px';
            this.table.setHeight(newHeight);

            // Redraw table to ensure proper rendering
            setTimeout(() => {
                this.table.redraw(true);
            }, 50);
        }

        console.log('🔄 Table expansion toggled:', this.isExpanded ? 'Expanded' : 'Minimized');
    }
    /**
     * Custom operation (placeholder for first icon)
     */
    customOperation() {
        if (this.selectedRows.length === 0) {
            this.messageService.add({
                severity: 'warn',
                summary: 'Warning',
                detail: 'No rows selected'
            });
            return;
        }

        console.log('⚙️ Custom operation for:', this.selectedRows);
        this.messageService.add({
            severity: 'info',
            summary: 'Custom Operation',
            detail: 'Custom operation - Implementation needed'
        });
        // TODO: Implement custom operation based on requirements
    }
}
