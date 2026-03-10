import { Component, Input, Output, EventEmitter, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DialogModule } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { FormsModule } from '@angular/forms';


export interface FilterCondition {
  column: string;        // Backend column name (e.g. 'CUSIP', 'TICKER')
  columnDisplay: string; // Frontend display name (e.g. 'CUSIP', 'Ticker')
  operator: string;      // Backend operator (e.g. 'equals', 'contains')
  operatorDisplay: string; // Frontend display label (e.g. 'Equal to', 'Contains')
  values: string;
  values2?: string;      // For 'between' operator
  logicalOperator: 'AND' | 'OR';
}

export interface FilterSubgroup {
  id: number;
  logicalOperator: 'AND' | 'OR';
  conditions: FilterCondition[];
}

// Column mapping: frontend display name -> backend oracle column name
// This is the MASTER list. Actual columnOptions shown to users are filtered by CLO visibility.
const COLUMN_MAPPING: { [key: string]: string } = {
  'Message ID': 'MESSAGE_ID',
  'Ticker': 'TICKER',
  'CUSIP': 'CUSIP',
  'Sector': 'SECTOR',
  'Bias': 'BIAS',
  'Date': 'DATE',
  'Date 1': 'DATE_1',
  'Source': 'SOURCE',
  'Rank': 'RANK',
  'Price Level': 'PRICE_LEVEL',
  'BID': 'BID',
  'ASK': 'ASK',
  'PX': 'PX',
  'Confidence': 'CONFIDENCE',
  'Cov Price': 'COV_PRICE',
  'Percent Diff': 'PERCENT_DIFF',
  'Price Diff': 'PRICE_DIFF',
  'Diff Status': 'DIFF_STATUS'
};

/** Full list of all possible column display names (used when no CLO filter is active) */
const ALL_COLUMN_OPTIONS = Object.keys(COLUMN_MAPPING);

@Component({
  selector: 'app-filter-dialog',
  standalone: true,
  imports: [
    CommonModule,
    DialogModule,
    ButtonModule,
    InputTextModule,
    FormsModule
  ],
  templateUrl: './filter-dialog.component.html',
  styleUrls: ['./filter-dialog.component.css']
})
export class FilterDialogComponent implements OnInit, OnChanges {
  @Input() visible: boolean = false;
  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() filtersApplied = new EventEmitter<{
    conditions: FilterCondition[];
    subgroups: FilterSubgroup[];
  }>();

  /**
   * Oracle column names that are visible for the active CLO.
   * When provided, the column dropdown is restricted to these columns only.
   * When empty/undefined the full list is shown.
   */
  @Input() visibleOracleColumns: string[] = [];

  // Filter data
  filterConditions: FilterCondition[] = [];
  filterSubgroups: FilterSubgroup[] = [];

  // Column options (display names) — filtered by CLO visibility
  columnOptions: string[] = ALL_COLUMN_OPTIONS;

  // Operators aligned with backend (search.py + rules_service.py)
  operatorOptions = [
    { label: 'Equal to', value: 'equals' },
    { label: 'Not equal to', value: 'not equal to' },
    { label: 'Contains', value: 'contains' },
    { label: 'Starts with', value: 'starts_with' },
    { label: 'Ends with', value: 'ends with' },
    { label: 'Greater than', value: 'gt' },
    { label: 'Less than', value: 'lt' },
    { label: 'Greater than or equal', value: 'gte' },
    { label: 'Less than or equal', value: 'lte' },
    { label: 'Between', value: 'between' }
  ];

  logicalOperators = [
    { label: 'AND', value: 'AND' },
    { label: 'OR', value: 'OR' }
  ];

  ngOnInit() {
    this.refreshColumnOptions();
    if (this.filterConditions.length === 0) {
      this.addCondition();
    }
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['visibleOracleColumns']) {
      this.refreshColumnOptions();
    }
  }

  /** Rebuild the column dropdown based on the current CLO's visible oracle columns */
  private refreshColumnOptions(): void {
    if (this.visibleOracleColumns && this.visibleOracleColumns.length > 0) {
      const visibleSet = new Set(this.visibleOracleColumns);
      this.columnOptions = ALL_COLUMN_OPTIONS.filter(displayName => {
        const oracleKey = COLUMN_MAPPING[displayName];
        return oracleKey && visibleSet.has(oracleKey);
      });
    } else {
      this.columnOptions = ALL_COLUMN_OPTIONS;
    }
  }

  // ==================== COLUMN MAPPING ====================

  /** Map a frontend column display name to a backend oracle column name */
  getBackendColumn(displayName: string): string {
    return COLUMN_MAPPING[displayName] || displayName.toUpperCase();
  }

  /** Get operator display label from value */
  getOperatorLabel(value: string): string {
    const operator = this.operatorOptions.find(op => op.value === value);
    return operator ? operator.label : value;
  }

  // ==================== MAIN CONDITIONS ====================

  addCondition() {
    this.filterConditions.push({
      column: '',
      columnDisplay: '',
      operator: '',
      operatorDisplay: '',
      values: '',
      logicalOperator: 'AND'
    });
  }

  removeCondition(index: number) {
    this.filterConditions.splice(index, 1);
    if (this.filterConditions.length === 0) {
      this.addCondition();
    }
  }

  // ==================== SUBGROUPS ====================

  addSubgroup() {
    this.filterSubgroups.push({
      id: Date.now(),
      logicalOperator: 'AND',
      conditions: [{
        column: '',
        columnDisplay: '',
        operator: '',
        operatorDisplay: '',
        values: '',
        logicalOperator: 'AND'
      }]
    });
  }

  removeSubgroup(subgroupId: number) {
    const index = this.filterSubgroups.findIndex(s => s.id === subgroupId);
    if (index > -1) {
      this.filterSubgroups.splice(index, 1);
    }
  }

  addSubgroupCondition(subgroupId: number) {
    const subgroup = this.filterSubgroups.find(s => s.id === subgroupId);
    if (subgroup) {
      subgroup.conditions.push({
        column: '',
        columnDisplay: '',
        operator: '',
        operatorDisplay: '',
        values: '',
        logicalOperator: 'AND'
      });
    }
  }

  removeSubgroupCondition(subgroupId: number, conditionIndex: number) {
    const subgroup = this.filterSubgroups.find(s => s.id === subgroupId);
    if (subgroup) {
      subgroup.conditions.splice(conditionIndex, 1);
      if (subgroup.conditions.length === 0) {
        this.removeSubgroup(subgroupId);
      }
    }
  }

  // ==================== ACTIONS ====================

  removeAllFilters() {
    this.filterConditions = [];
    this.filterSubgroups = [];
    this.addCondition();
  }

  applyFilters() {
    // Map conditions: set backend column names and operator display labels
    const mappedConditions = this.filterConditions
      .filter(c => c.columnDisplay && c.operator && c.values)
      .map(c => ({
        ...c,
        column: this.getBackendColumn(c.columnDisplay),
        operatorDisplay: this.getOperatorLabel(c.operator)
      }));

    const mappedSubgroups = this.filterSubgroups.map(sg => ({
      ...sg,
      conditions: sg.conditions
        .filter(c => c.columnDisplay && c.operator && c.values)
        .map(c => ({
          ...c,
          column: this.getBackendColumn(c.columnDisplay),
          operatorDisplay: this.getOperatorLabel(c.operator)
        }))
    }));

    this.filtersApplied.emit({
      conditions: mappedConditions,
      subgroups: mappedSubgroups
    });
    this.closeDialog();
  }

  closeDialog() {
    this.visible = false;
    this.visibleChange.emit(false);
  }

  /** Check if operator is 'between' (needs two value inputs) */
  isBetweenOperator(operator: string): boolean {
    return operator === 'between';
  }
}
