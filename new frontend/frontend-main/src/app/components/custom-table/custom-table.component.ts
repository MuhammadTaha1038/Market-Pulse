import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges, ChangeDetectionStrategy, ChangeDetectorRef, ElementRef, ViewChildren, QueryList, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';

export interface TableColumn {
  field: string;
  header: string;
  width?: string;
  editable?: boolean;
  type?: 'text' | 'number' | 'date';
}

export interface TableRow {
  [key: string]: any;
  _selected?: boolean;
  _rowId?: string;
  isParent?: boolean;
  parentRow?: string | number;
  childrenCount?: number;
  rowNumber?: string | number;
}

export interface TableConfig {
  editable: boolean;
  selectable: boolean;
  showSelectButton: boolean;
  showRowNumbers: boolean;
  pagination?: boolean;
  pageSize?: number;
  showExport?: boolean;
  showAddRow?: boolean;
}

@Component({
  selector: 'app-custom-table',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonModule, TooltipModule, ToastModule],
  templateUrl: './custom-table.component.html',
  styleUrls: ['./custom-table.component.css'],
  providers: [MessageService],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CustomTableComponent implements OnChanges, AfterViewChecked {
  @Input() columns: TableColumn[] = [];
  @Input() set data(value: TableRow[]) {
    this._rawData = value;
  }
  get data(): TableRow[] {
    return this._processedData;
  }
  @Input() config: TableConfig = {
    editable: false,
    selectable: true,
    showSelectButton: true,
    showRowNumbers: false,
    pagination: true,
    pageSize: 20
  };
  @Input() primaryField: string = 'messageId';
  @Input() lookupFields: string[] = ['messageId'];
  @Input() isExpanded: boolean = false;
  @Input() showExpandButton: boolean = false; // Only show on home page

  @Output() dataChanged = new EventEmitter<TableRow[]>();
  @Output() rowsSelected = new EventEmitter<TableRow[]>();
  @Output() cellEdited = new EventEmitter<{ row: TableRow; field: string; oldValue: any; newValue: any }>();
  @Output() onExpandButtonClick = new EventEmitter<void>();
  @Output() primaryFieldLookup = new EventEmitter<{ row: TableRow; value: any }>();

  private _rawData: TableRow[] = [];
  private _processedData: TableRow[] = [];
  displayData: TableRow[] = [];
  selectedRows: TableRow[] = [];
  currentPage = 1;
  totalPages = 1;
  editingCell: { rowId: string; field: string } | null = null;
  tempEditValue: any = '';
  private _needsFocus = false;

  /** Track which parent rows are expanded (by _rowId) */
  expandedRows = new Set<string>();

  /** Sorting state */
  sortField: string | null = null;
  sortOrder: 'asc' | 'desc' | null = null;

  Math = Math;

  @ViewChildren('cellInput') cellInputs!: QueryList<ElementRef<HTMLInputElement>>;

  constructor(
    private messageService: MessageService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnChanges(changes: SimpleChanges) {
    if (changes['data']) {
      this.initializeData();
      this.updatePagination();
      this.cdr.markForCheck();
    }
  }

  ngAfterViewChecked() {
    if (this._needsFocus && this.cellInputs && this.cellInputs.length > 0) {
      this.cellInputs.first.nativeElement.focus();
      this._needsFocus = false;
    }
  }

  private _rowIdCounter = 0;

  private initializeData() {
    // Guarantee unique _rowId for every row, even if the parent component
    // passes duplicate _rowId values (e.g. same message_id for multiple rows).
    const usedIds = new Set<string>();

    this._processedData = this._rawData.map((row, index) => {
      let rowId = row._rowId || `row_${index}_${++this._rowIdCounter}`;

      // If the ID is already taken, make it unique with a suffix
      if (usedIds.has(rowId)) {
        rowId = `${rowId}_${++this._rowIdCounter}`;
      }
      usedIds.add(rowId);

      return {
        ...row,
        _rowId: rowId,
        _selected: row._selected || false
      };
    });

    this.updateDisplayData();
  }

  // ==================== DISPLAY DATA ====================

  /**
   * Build display data: show only parent rows by default.
   * Children appear when their parent is expanded (chevron toggle).
   * Works in both editable and non-editable modes.
   */
  private updateDisplayData() {
    let visibleRows: TableRow[] = [];

    // Always show parent-only with expand/collapse
    for (const row of this._processedData) {
      if (row.isParent === true) {
        visibleRows.push(row);
        // If this parent is expanded, add its children
        if (this.expandedRows.has(row._rowId!)) {
          const children = this._processedData.filter(
            r => !r.isParent && r.parentRow !== undefined && r.parentRow !== null &&
                 this.getParentRowId(r) === row._rowId
          );
          visibleRows.push(...children);
        }
      }
    }

    // If no rows have isParent set (e.g. all rows are flat), show everything
    if (visibleRows.length === 0 && this._processedData.length > 0) {
      const hasAnyParent = this._processedData.some(r => r.isParent === true);
      if (!hasAnyParent) {
        visibleRows = [...this._processedData];
      }
    }

    // Apply pagination only if enabled
    if (this.config.pagination && !this.config.editable) {
      const pageSize = this.config.pageSize || 20;
      // Count only parents for pagination
      const parentRows = visibleRows.filter(r => r.isParent === true);
      this.totalPages = Math.ceil(parentRows.length / pageSize);

      // Paginate by parent groups
      const pagedRows: TableRow[] = [];
      let parentCount = 0;
      for (const row of visibleRows) {
        if (row.isParent === true) {
          parentCount++;
        }
        if (parentCount > (this.currentPage - 1) * (this.config.pageSize || 20) &&
            parentCount <= this.currentPage * (this.config.pageSize || 20)) {
          pagedRows.push(row);
        }
      }
      this.displayData = pagedRows;
    } else {
      this.displayData = visibleRows;
    }
  }

  private updatePagination() {
    if (this.config.pagination && !this.config.editable) {
      const parentCount = this._processedData.filter(r => r.isParent === true).length;
      this.totalPages = Math.ceil(parentCount / (this.config.pageSize || 20));
      if (this.currentPage > this.totalPages && this.totalPages > 0) {
        this.currentPage = this.totalPages;
        this.updateDisplayData();
      }
    }
  }

  /** Find the _rowId of the parent for a child row using parentRow field */
  private getParentRowId(childRow: TableRow): string | null {
    if (childRow.parentRow === undefined || childRow.parentRow === null) return null;

    const parentRef = String(childRow.parentRow);
    const childCusip = String(childRow['cusip'] ?? '').trim().toUpperCase();
    const candidateParents: TableRow[] = [];

    // Match parentRow value against parent's _rowId or messageId
    for (const row of this._processedData) {
      if (row.isParent !== true) continue;
      // Direct _rowId match (e.g. parentRow = "row_123")
      if (row._rowId === parentRef) return row._rowId!;
      // parentRow is the raw message_id, _rowId is "row_{message_id}"
      if (row._rowId === `row_${parentRef}`) return row._rowId!;
      // Match against messageId field
      if (String(row['messageId'] ?? '') === parentRef) {
        candidateParents.push(row);
      }
    }

    // If duplicate message IDs exist, prefer parent from the same CUSIP.
    if (candidateParents.length > 0) {
      if (childCusip) {
        const sameCusipParent = candidateParents.find(
          p => String(p['cusip'] ?? '').trim().toUpperCase() === childCusip
        );
        if (sameCusipParent?._rowId) return sameCusipParent._rowId;
      }
      // Fallback to first candidate when CUSIP is unavailable.
      if (candidateParents[0]?._rowId) return candidateParents[0]._rowId;
    }

    return null;
  }

  // ==================== EXPAND / COLLAPSE ====================

  toggleRowExpand(row: TableRow) {
    if (this.expandedRows.has(row._rowId!)) {
      this.expandedRows.delete(row._rowId!);
    } else {
      this.expandedRows.add(row._rowId!);
    }
    this.updateDisplayData();
    this.cdr.markForCheck();
  }

  isRowExpanded(row: TableRow): boolean {
    return this.expandedRows.has(row._rowId!);
  }

  hasChildren(row: TableRow): boolean {
    if (row.isParent !== true) return false;
    // Use childrenCount if available, otherwise check actual data
    if ((row.childrenCount ?? 0) > 0) return true;
    // Fallback: check if any row in _processedData references this as parent
    return this._processedData.some(
      r => !r.isParent && r.parentRow !== undefined && r.parentRow !== null &&
           this.getParentRowId(r) === row._rowId
    );
  }

  // ==================== SELECTION ====================

  toggleSelectAll() {
    const allVisibleSelected = this.isAllSelected();
    const newState = !allVisibleSelected;
    // displayData rows are the same object references as _processedData entries,
    // so setting _selected here updates both arrays automatically.
    this.displayData.forEach(row => {
      row._selected = newState;
    });
    this.updateSelectedRows();
    this.cdr.markForCheck();
  }

  isAllSelected(): boolean {
    return this.displayData.length > 0 && this.displayData.every(row => row._selected === true);
  }

  isSomeSelected(): boolean {
    return this.displayData.some(row => row._selected === true) && !this.isAllSelected();
  }

  toggleRowSelection(row: TableRow) {
    // row is already a direct reference to the _processedData object
    // (displayData pushes the same references), so toggle directly.
    row._selected = !row._selected;
    this.updateSelectedRows();
    this.cdr.markForCheck();
  }

  private updateSelectedRows() {
    this.selectedRows = this._processedData.filter(row => row._selected === true);
    this.rowsSelected.emit(this.selectedRows);
  }

  clearSelection() {
    this._processedData.forEach(row => row._selected = false);
    this.displayData.forEach(row => row._selected = false);
    this.selectedRows = [];
    this.rowsSelected.emit([]);
    this.cdr.markForCheck();
  }

  isRowSelected(row: TableRow): boolean {
    return row._selected === true;
  }

  // ==================== SORTING ====================

  sortBy(field: string, order?: 'asc' | 'desc') {
    // If order is specified, use it directly
    if (order) {
      this.sortField = field;
      this.sortOrder = order;
    } else {
      // If no order specified, toggle (backward compatibility)
      if (this.sortField === field && this.sortOrder) {
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
      } else {
        // New field clicked, start with ascending
        this.sortField = field;
        this.sortOrder = 'asc';
      }
    }

    // Sort the processed data
    this._processedData.sort((a, b) => {
      const aVal = a[field];
      const bVal = b[field];

      // Handle null/undefined values
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return this.sortOrder === 'asc' ? 1 : -1;
      if (bVal == null) return this.sortOrder === 'asc' ? -1 : 1;

      // Compare values
      let comparison = 0;
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        comparison = aVal - bVal;
      } else {
        comparison = String(aVal).localeCompare(String(bVal));
      }

      return this.sortOrder === 'asc' ? comparison : -comparison;
    });

    this.updateDisplayData();
    this.cdr.markForCheck();
  }

  // ==================== EDITING ====================

  startEdit(row: TableRow, field: string) {
    // If already editing this exact cell, do nothing (prevents re-trigger on input click)
    if (this.editingCell &&
        this.editingCell.rowId === row._rowId &&
        this.editingCell.field === field) {
      return;
    }

    const isLookupField = this.isLookupField(field);

    // In non-editable mode, only allow editing configured lookup fields
    if (!this.config.editable && !isLookupField) return;

    // In editable mode, respect per-column editable flag
    if (this.config.editable) {
      const column = this.columns.find(col => col.field === field);
      if (!column || column.editable === false) return;
    }

    this.editingCell = { rowId: row._rowId!, field };
    this.tempEditValue = row[field];
    this._needsFocus = true;
    this.cdr.markForCheck();
  }

  saveEdit(row: TableRow, field: string) {
    if (!this.editingCell) return;

    const oldValue = row[field];
    const newValue = this.tempEditValue;

    // In non-editable mode, lookup fields trigger backend lookup instead of local save
    if (!this.config.editable && this.isLookupField(field)) {
      if (newValue && newValue !== oldValue) {
        // row is a direct reference to _processedData entry, so this updates both
        row[field] = newValue;
        this.primaryFieldLookup.emit({ row, value: newValue });
      }
      this.editingCell = null;
      this.tempEditValue = '';
      this.cdr.markForCheck();
      return;
    }

    if (oldValue !== newValue) {
      // row is a direct reference to _processedData entry, so this updates both
      row[field] = newValue;

      this.cellEdited.emit({ row, field, oldValue, newValue });
      this.dataChanged.emit(this._processedData);
    }

    this.editingCell = null;
    this.tempEditValue = '';
    this.cdr.markForCheck();
  }

  cancelEdit() {
    this.editingCell = null;
    this.tempEditValue = '';
    this.cdr.markForCheck();
  }

  isEditing(row: TableRow, field: string): boolean {
    return this.editingCell !== null &&
           this.editingCell.rowId === row._rowId &&
           this.editingCell.field === field;
  }

  onKeyDown(event: KeyboardEvent, row: TableRow, field: string) {
    if (event.key === 'Enter') {
      this.saveEdit(row, field);
    } else if (event.key === 'Escape') {
      this.cancelEdit();
    }
  }

  // ==================== ROW OPERATIONS ====================

  addNewRow() {
    const newRow: TableRow = {
      _rowId: `row_new_${Date.now()}`,
      _selected: false,
      isParent: true
    };

    this.columns.forEach(col => {
      if (col.field !== 'select' && col.field !== 'rowNumber') {
        newRow[col.field] = '';
      }
    });

    this._processedData.unshift(newRow);
    this.updateDisplayData();
    this.dataChanged.emit(this._processedData);

    this.messageService.add({
      severity: 'success',
      summary: 'Row Added',
      detail: 'New row added to the table'
    });

    this.cdr.markForCheck();
  }

  deleteSelectedRows() {
    if (this.selectedRows.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Selection',
        detail: 'Please select rows to delete'
      });
      return;
    }

    const rowsToDelete = new Set<string>();

    this.selectedRows.forEach(selectedRow => {
      rowsToDelete.add(selectedRow._rowId!);

      if (selectedRow['isParent']) {
        this.findAndMarkChildren(selectedRow, rowsToDelete);
      }
    });

    this._processedData = this._processedData.filter(row => !rowsToDelete.has(row._rowId!));

    this.clearSelection();
    this.updatePagination();
    this.updateDisplayData();
    this.dataChanged.emit(this._processedData);

    this.messageService.add({
      severity: 'success',
      summary: 'Deleted',
      detail: `${rowsToDelete.size} row(s) deleted successfully`
    });

    this.cdr.markForCheck();
  }

  private findAndMarkChildren(parentRow: TableRow, deleteSet: Set<string>) {
    const parentRowId = parentRow._rowId;

    this._processedData.forEach(row => {
      if (!row.isParent && row._rowId !== parentRowId) {
        const rowParentId = this.getParentRowId(row);
        if (rowParentId === parentRowId) {
          deleteSet.add(row._rowId!);
        }
      }
    });
  }

  // ==================== PARENT/CHILD OPERATIONS ====================

  swapParentChild() {
    if (this.selectedRows.length !== 2) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Invalid Selection',
        detail: 'Please select exactly 2 rows — one parent and one child — to swap'
      });
      return;
    }

    const rowA = this.selectedRows[0];
    const rowB = this.selectedRows[1];

    // Determine which is parent and which is child
    let parentRow: TableRow;
    let childRow: TableRow;

    if (rowA.isParent === true && this.isChildRow(rowB)) {
      parentRow = rowA;
      childRow = rowB;
    } else if (rowB.isParent === true && this.isChildRow(rowA)) {
      parentRow = rowB;
      childRow = rowA;
    } else {
      this.messageService.add({
        severity: 'warn',
        summary: 'Invalid Selection',
        detail: 'Please select one parent row and one of its child rows to swap'
      });
      return;
    }

    // Verify the child actually belongs to this parent
    const childParentId = this.getParentRowId(childRow);
    if (childParentId !== parentRow._rowId) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Invalid Selection',
        detail: 'The selected child does not belong to the selected parent'
      });
      return;
    }

    // Collect all children of the old parent (excluding the child that will become parent)
    const otherChildren = this._processedData.filter(
      r => !r.isParent && r._rowId !== childRow._rowId &&
           r.parentRow !== undefined && r.parentRow !== null &&
           this.getParentRowId(r) === parentRow._rowId
    );

    // Swap: child becomes the new parent
    childRow.isParent = true;
    childRow.childrenCount = (parentRow.childrenCount || 0);
    const oldChildParentRow = childRow.parentRow;
    childRow.parentRow = undefined;

    // Old parent becomes child of new parent
    parentRow.isParent = false;
    parentRow.parentRow = childRow['messageId'] || childRow._rowId;
    parentRow.childrenCount = 0;

    // Re-point all other children to the new parent
    for (const otherChild of otherChildren) {
      otherChild.parentRow = childRow['messageId'] || childRow._rowId;
    }

    // Move the new parent to the position of the old parent in the data array
    const oldParentIndex = this._processedData.indexOf(parentRow);
    const newParentIndex = this._processedData.indexOf(childRow);
    if (oldParentIndex !== -1 && newParentIndex !== -1) {
      // Remove child (now new parent) from current position
      this._processedData.splice(newParentIndex, 1);
      // Insert it at the old parent's position
      const insertAt = this._processedData.indexOf(parentRow);
      this._processedData.splice(insertAt, 0, childRow);
    }

    // If the old parent was expanded, transfer expansion to the new parent
    if (this.expandedRows.has(parentRow._rowId!)) {
      this.expandedRows.delete(parentRow._rowId!);
      this.expandedRows.add(childRow._rowId!);
    }

    this.clearSelection();
    this.updateDisplayData();
    this.dataChanged.emit(this._processedData);

    this.messageService.add({
      severity: 'success',
      summary: 'Swapped',
      detail: 'Parent and child rows have been swapped'
    });

    this.cdr.markForCheck();
  }

  assignAsParent() {
    if (this.selectedRows.length !== 1) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Invalid Selection',
        detail: 'Please select exactly one child row'
      });
      return;
    }

    const row = this.selectedRows[0];

    if (row.isParent === true) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Already a Parent',
        detail: 'This row is already a parent row'
      });
      return;
    }

    // Find the old parent and decrement its children count
    const oldParentRowId = this.getParentRowId(row);
    if (oldParentRowId) {
      const oldParent = this._processedData.find(r => r._rowId === oldParentRowId);
      if (oldParent && (oldParent.childrenCount ?? 0) > 0) {
        oldParent.childrenCount = (oldParent.childrenCount || 0) - 1;
      }
    }

    // Promote child to independent parent
    row.isParent = true;
    row.parentRow = undefined;
    row.childrenCount = 0;

    this.clearSelection();
    this.updateDisplayData();
    this.dataChanged.emit(this._processedData);

    this.messageService.add({
      severity: 'success',
      summary: 'Updated',
      detail: 'Child row is now an independent parent'
    });

    this.cdr.markForCheck();
  }

  saveSelectedRows() {
    if (this.selectedRows.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Selection',
        detail: 'Please select rows to save'
      });
      return;
    }

    this.messageService.add({
      severity: 'success',
      summary: 'Saved',
      detail: `${this.selectedRows.length} row(s) saved`
    });

    this.rowsSelected.emit(this.selectedRows);
  }

  // ==================== PAGINATION ====================

  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.updateDisplayData();
      this.cdr.markForCheck();
    }
  }

  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.updateDisplayData();
      this.cdr.markForCheck();
    }
  }

  previousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.updateDisplayData();
      this.cdr.markForCheck();
    }
  }

  getPageNumbers(): number[] {
    const pages: number[] = [];
    const maxVisible = 5;

    let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(this.totalPages, start + maxVisible - 1);

    if (end - start < maxVisible - 1) {
      start = Math.max(1, end - maxVisible + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    return pages;
  }

  // ==================== EXPORT ====================

  getExportLabel(): string {
    return this.selectedRows.length > 0
      ? `Export Selected (${this.selectedRows.length})`
      : 'Export All';
  }

  exportToCSV() {
    const dataToExport = this.selectedRows.length > 0 ? this.selectedRows : this._processedData;

    if (dataToExport.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Data',
        detail: 'No data to export'
      });
      return;
    }

    const headers = this.columns
      .filter(col => col.field !== 'select')
      .map(col => col.header);

    const fields = this.columns
      .filter(col => col.field !== 'select')
      .map(col => col.field);

    let csv = headers.join(',') + '\n';

    dataToExport.forEach(row => {
      const values = fields.map(field => {
        let value = row[field] || '';
        if (typeof value === 'string' && value.includes(',')) {
          value = `"${value}"`;
        }
        return value;
      });
      csv += values.join(',') + '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `export_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);

    this.messageService.add({
      severity: 'success',
      summary: 'Exported',
      detail: `${dataToExport.length} row(s) exported to CSV`
    });
  }

  // ==================== HELPERS ====================

  trackByRowId(index: number, row: TableRow): string {
    return row._rowId || `${index}`;
  }

  isChildRow(row: TableRow): boolean {
    return row.isParent !== true && row.parentRow !== undefined && row.parentRow !== null;
  }

  isParentRow(row: TableRow): boolean {
    return row.isParent === true;
  }

  isLookupField(field: string): boolean {
    const fields = this.lookupFields?.length ? this.lookupFields : [this.primaryField];
    return fields.includes(field);
  }

  canEditCell(column: TableColumn): boolean {
    if (this.config.editable && column.editable !== false) return true;
    if (!this.config.editable && this.isLookupField(column.field)) return true;
    return false;
  }

  updateRowData(rowId: string, data: Partial<TableRow>) {
    const dataRow = this._processedData.find(r => r._rowId === rowId);
    if (dataRow) {
      Object.assign(dataRow, data);
    }
    const displayRow = this.displayData.find(r => r._rowId === rowId);
    if (displayRow) {
      Object.assign(displayRow, data);
    }
    this.cdr.markForCheck();
  }

  /** Get the display row number for a row */
  getDisplayRowNumber(row: TableRow): string {
    const index = this.displayData.indexOf(row);
    if (index < 0) return '';
    return String(index + 1);
  }

  /** Get parent count for display */
  getParentCount(): number {
    return this._processedData.filter(r => r.isParent === true).length;
  }

  getTotalCount(): number {
    return this._processedData.length;
  }
}
