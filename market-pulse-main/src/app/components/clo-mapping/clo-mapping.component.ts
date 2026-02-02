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
import { CloMappingService, CLOHierarchy, MainCLO, CLOMapping, ColumnDetail } from '../../services/clo-mapping.service';

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
    InputTextModule
  ],
  providers: [MessageService],
  template: `
    <div class="clo-mapping-container">
      <p-toast></p-toast>

      <div class="header">
        <h1>CLO Column Mapping Configuration</h1>
        <p class="subtitle">Configure which columns each CLO type can access</p>
      </div>

      <div class="grid">
        <!-- Left Panel: CLO Tree -->
        <div class="col-12 md:col-4">
          <p-card header="CLO Hierarchy" [style]="{'height': '100%'}">
            <div *ngIf="loading" class="loading">
              <p-progressSpinner [style]="{width: '50px', height: '50px'}"></p-progressSpinner>
              <p>Loading CLO structure...</p>
            </div>

            <div *ngIf="!loading">
              <div class="tree-header">
                <span class="summary">
                  <strong>{{ totalMainCLOs }}</strong> Main CLOs
                  <strong>{{ totalSubCLOs }}</strong> Sub CLOs
                </span>
              </div>
              
              <p-tree 
                [value]="cloTreeNodes" 
                selectionMode="single"
                [(selection)]="selectedNode"
                (onNodeSelect)="onNodeSelect($event)"
                [style]="{'width': '100%', 'margin-top': '1rem'}"
              ></p-tree>
            </div>
          </p-card>
        </div>

        <!-- Right Panel: Column Configuration -->
        <div class="col-12 md:col-8">
          <p-card *ngIf="!selectedCLO" header="Select a CLO">
            <div class="empty-state">
              <i class="pi pi-info-circle" style="font-size: 3rem; color: #6B7280;"></i>
              <p>Select a CLO from the tree to configure column visibility</p>
            </div>
          </p-card>

          <p-card *ngIf="selectedCLO" [header]="'Configure: ' + selectedCLO.clo_name">
            <ng-template pTemplate="header">
              <div class="card-header-custom">
                <div>
                  <h3>{{ selectedCLO.clo_name }}</h3>
                  <p-chip 
                    [label]="selectedCLO.clo_type === 'main' ? 'Main CLO' : 'Sub CLO'" 
                    [style]="{'margin-left': '0.5rem'}"
                  ></p-chip>
                  <span *ngIf="selectedCLO.parent_clo" class="parent-info">
                    under {{ selectedCLO.parent_clo }}
                  </span>
                </div>
              </div>
            </ng-template>

            <div class="column-config">
              <div class="config-actions">
                <div class="search-box">
                  <span class="p-input-icon-left" style="width: 100%;">
                    <i class="pi pi-search"></i>
                    <input 
                      type="text" 
                      pInputText 
                      placeholder="Search columns..." 
                      [(ngModel)]="searchText"
                      (input)="filterColumns()"
                      style="width: 100%;"
                    />
                  </span>
                </div>

                <div class="action-buttons">
                  <button 
                    pButton 
                    label="Select All" 
                    icon="pi pi-check-square"
                    class="p-button-sm p-button-outlined"
                    (click)="selectAllColumns()"
                  ></button>
                  <button 
                    pButton 
                    label="Deselect All" 
                    icon="pi pi-times"
                    class="p-button-sm p-button-outlined"
                    (click)="deselectAllColumns()"
                  ></button>
                  <button 
                    pButton 
                    label="Reset to Default" 
                    icon="pi pi-refresh"
                    class="p-button-sm p-button-warning"
                    (click)="resetToDefault()"
                  ></button>
                </div>
              </div>

              <div class="column-stats">
                <p-chip 
                  [label]="visibleCount + ' Visible'" 
                  icon="pi pi-eye"
                  styleClass="chip-success"
                ></p-chip>
                <p-chip 
                  [label]="hiddenCount + ' Hidden'" 
                  icon="pi pi-eye-slash"
                  styleClass="chip-secondary"
                ></p-chip>
                <p-chip 
                  [label]="'Total: ' + selectedCLO.total_columns" 
                  icon="pi pi-database"
                ></p-chip>
              </div>

              <div class="columns-list">
                <div *ngFor="let column of filteredColumns" class="column-item">
                  <p-checkbox 
                    [(ngModel)]="column.visible"
                    [binary]="true"
                    [inputId]="column.oracle_name"
                    (onChange)="onColumnToggle()"
                  ></p-checkbox>
                  <label [for]="column.oracle_name" class="column-label">
                    <div class="column-info">
                      <span class="column-name">{{ column.display_name }}</span>
                      <span class="column-oracle-name">{{ column.oracle_name }}</span>
                    </div>
                    <div class="column-meta">
                      <p-chip [label]="column.data_type" styleClass="chip-type"></p-chip>
                      <p-chip *ngIf="column.required" label="Required" styleClass="chip-required"></p-chip>
                    </div>
                  </label>
                </div>

                <div *ngIf="filteredColumns.length === 0" class="no-results">
                  <i class="pi pi-search"></i>
                  <p>No columns match your search</p>
                </div>
              </div>

              <div class="save-actions">
                <button 
                  pButton 
                  label="Save Changes" 
                  icon="pi pi-save"
                  class="p-button-lg p-button-success"
                  (click)="saveMapping()"
                  [disabled]="saving || !hasChanges"
                  [loading]="saving"
                ></button>
                <button 
                  pButton 
                  label="Cancel" 
                  icon="pi pi-times"
                  class="p-button-lg p-button-text"
                  (click)="cancelChanges()"
                  [disabled]="saving"
                ></button>
              </div>

              <div *ngIf="selectedCLO.updated_by" class="last-updated">
                <small>
                  Last updated by <strong>{{ selectedCLO.updated_by }}</strong>
                  on {{ selectedCLO.updated_at | date:'medium' }}
                </small>
              </div>
            </div>
          </p-card>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .clo-mapping-container {
      padding: 2rem;
      background: #f8f9fa;
      min-height: 100vh;
    }

    .header {
      margin-bottom: 2rem;
    }

    .header h1 {
      margin: 0 0 0.5rem 0;
      color: #1e293b;
      font-size: 2rem;
    }

    .subtitle {
      color: #64748b;
      margin: 0;
    }

    .loading {
      text-align: center;
      padding: 2rem;
    }

    .tree-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.5rem 0;
      border-bottom: 1px solid #e2e8f0;
    }

    .summary {
      font-size: 0.9rem;
      color: #64748b;
    }

    .summary strong {
      color: #1e293b;
      margin: 0 0.25rem;
    }

    .empty-state {
      text-align: center;
      padding: 3rem;
      color: #6B7280;
    }

    .empty-state p {
      margin-top: 1rem;
      font-size: 1.1rem;
    }

    .card-header-custom {
      padding: 1rem;
    }

    .card-header-custom h3 {
      margin: 0;
      display: inline-block;
    }

    .parent-info {
      color: #64748b;
      font-size: 0.9rem;
      margin-left: 0.5rem;
    }

    .column-config {
      padding: 1rem 0;
    }

    .config-actions {
      display: flex;
      gap: 1rem;
      margin-bottom: 1.5rem;
      flex-wrap: wrap;
    }

    .search-box {
      flex: 1;
      min-width: 250px;
    }

    .action-buttons {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }

    .column-stats {
      display: flex;
      gap: 0.5rem;
      margin-bottom: 1.5rem;
      flex-wrap: wrap;
    }

    .columns-list {
      max-height: 500px;
      overflow-y: auto;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 1rem;
      background: white;
    }

    .column-item {
      display: flex;
      align-items: flex-start;
      padding: 1rem;
      border-bottom: 1px solid #f1f5f9;
      gap: 1rem;
    }

    .column-item:last-child {
      border-bottom: none;
    }

    .column-item:hover {
      background: #f8fafc;
    }

    .column-label {
      flex: 1;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .column-info {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .column-name {
      font-weight: 600;
      color: #1e293b;
    }

    .column-oracle-name {
      font-size: 0.85rem;
      color: #64748b;
      font-family: 'Courier New', monospace;
    }

    .column-meta {
      display: flex;
      gap: 0.5rem;
      align-items: center;
    }

    .save-actions {
      display: flex;
      gap: 1rem;
      margin-top: 2rem;
      padding-top: 1.5rem;
      border-top: 1px solid #e2e8f0;
    }

    .last-updated {
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid #f1f5f9;
      color: #64748b;
    }

    .no-results {
      text-align: center;
      padding: 3rem;
      color: #94a3b8;
    }

    .no-results i {
      font-size: 2rem;
      display: block;
      margin-bottom: 1rem;
    }

    ::ng-deep .chip-success {
      background: #dcfce7 !important;
      color: #166534 !important;
    }

    ::ng-deep .chip-secondary {
      background: #f1f5f9 !important;
      color: #475569 !important;
    }

    ::ng-deep .chip-type {
      background: #dbeafe !important;
      color: #1e40af !important;
      font-size: 0.75rem !important;
    }

    ::ng-deep .chip-required {
      background: #fef3c7 !important;
      color: #92400e !important;
      font-size: 0.75rem !important;
    }
  `]
})
export class CloMappingComponent implements OnInit {
  cloTreeNodes: TreeNode[] = [];
  selectedNode: TreeNode | null = null;
  selectedCLO: CLOMapping | null = null;
  
  allColumns: ColumnDetail[] = [];
  filteredColumns: any[] = [];
  originalMapping: CLOMapping | null = null;
  
  loading = false;
  saving = false;
  searchText = '';
  
  totalMainCLOs = 0;
  totalSubCLOs = 0;
  
  constructor(
    private cloService: CloMappingService,
    private messageService: MessageService
  ) {}

  ngOnInit() {
    this.loadCLOHierarchy();
  }

  loadCLOHierarchy() {
    this.loading = true;
    this.cloService.getCLOHierarchy().subscribe({
      next: (hierarchy: CLOHierarchy) => {
        console.log('✅ Loaded CLO hierarchy:', hierarchy);
        this.totalMainCLOs = hierarchy.total_main_clos;
        this.totalSubCLOs = hierarchy.total_sub_clos;
        this.buildTreeNodes(hierarchy);
        this.loading = false;
      },
      error: (error) => {
        console.error('❌ Error loading CLO hierarchy:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load CLO hierarchy'
        });
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
    console.log('Selected CLO:', cloId);
    this.loadCLOMapping(cloId);
  }

  loadCLOMapping(cloId: string) {
    this.cloService.getCLOMapping(cloId).subscribe({
      next: (mapping: CLOMapping) => {
        console.log('✅ Loaded mapping for', cloId, ':', mapping);
        this.selectedCLO = mapping;
        this.originalMapping = JSON.parse(JSON.stringify(mapping)); // Deep copy
        this.prepareColumnsForDisplay();
      },
      error: (error) => {
        console.error('❌ Error loading mapping:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load CLO mapping'
        });
      }
    });
  }

  prepareColumnsForDisplay() {
    if (!this.selectedCLO) return;

    // Combine visible and hidden columns with visibility flag
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

  onColumnToggle() {
    // Update visibility counts
  }

  selectAllColumns() {
    this.allColumns.forEach(col => col.visible = true);
    this.filterColumns();
  }

  deselectAllColumns() {
    this.allColumns.forEach(col => col.visible = false);
    this.filterColumns();
  }

  resetToDefault() {
    if (!this.selectedCLO) return;

    if (confirm('Reset this CLO to show all columns?')) {
      this.cloService.resetCLOMapping(this.selectedCLO.clo_id).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Reset Complete',
            detail: 'CLO mapping reset to default (all columns visible)'
          });
          this.loadCLOMapping(this.selectedCLO!.clo_id);
        },
        error: (error) => {
          console.error('❌ Error resetting:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to reset CLO mapping'
          });
        }
      });
    }
  }

  saveMapping() {
    if (!this.selectedCLO) return;

    const visibleColumns = this.allColumns
      .filter(col => col.visible)
      .map(col => col.oracle_name);

    this.saving = true;
    this.cloService.updateCLOMapping(this.selectedCLO.clo_id, visibleColumns, 'admin').subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Saved',
          detail: `Updated column mapping for ${this.selectedCLO!.clo_name}`
        });
        this.loadCLOMapping(this.selectedCLO!.clo_id);
        this.saving = false;
      },
      error: (error) => {
        console.error('❌ Error saving:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to save CLO mapping'
        });
        this.saving = false;
      }
    });
  }

  cancelChanges() {
    if (this.originalMapping) {
      this.selectedCLO = JSON.parse(JSON.stringify(this.originalMapping));
      this.prepareColumnsForDisplay();
      this.messageService.add({
        severity: 'info',
        summary: 'Cancelled',
        detail: 'Changes discarded'
      });
    }
  }

  get visibleCount(): number {
    return this.allColumns.filter(col => col.visible).length;
  }

  get hiddenCount(): number {
    return this.allColumns.filter(col => !col.visible).length;
  }

  get hasChanges(): boolean {
    if (!this.selectedCLO || !this.originalMapping) return false;
    
    const currentVisible = this.allColumns.filter(col => col.visible).map(col => col.oracle_name).sort();
    const originalVisible = this.originalMapping.visible_columns.map(col => col.oracle_name).sort();
    
    return JSON.stringify(currentVisible) !== JSON.stringify(originalVisible);
  }
}
