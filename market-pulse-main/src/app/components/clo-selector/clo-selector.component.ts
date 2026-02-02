import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { CloMappingService } from '../../services/clo-mapping.service';
import { CLOSelectionService, UserCLOSelection } from '../../services/clo-selection.service';

interface CLOOption {
  id: string;
  name: string;
  mainCLO: string;
  description?: string;
}

@Component({
  selector: 'app-clo-selector',
  standalone: true,
  imports: [
    CommonModule
  ],
  template: `
    <div class="clo-selection-page">
      <div class="container">
        <div class="header">
          <h1>Select your asset class</h1>
          <p class="info-text">
            You can change asset class later from settings if needed
          </p>
        </div>

        <!-- Step 1: Select Main CLO -->
        <div *ngIf="selectionStep === 1" class="clo-options">
          <h2 class="step-title">Step 1: Select Main CLO Type</h2>
          <div class="options-grid">
            <div 
              *ngFor="let mainCLO of mainCLOs" 
              class="clo-card"
              [class.selected]="selectedMainCLO === mainCLO.id"
              (click)="selectMainCLO(mainCLO.id)">
              <div class="card-icon">📊</div>
              <h3>{{ mainCLO.display_name }}</h3>
              <p class="card-description">{{ mainCLO.description }}</p>
              <span class="card-badge">{{ mainCLO.sub_clos.length }} types</span>
            </div>
          </div>
        </div>

        <!-- Step 2: Select Child CLO -->
        <div *ngIf="selectionStep === 2" class="clo-options">
          <div class="step-header">
            <button class="back-button" (click)="goBackToMainSelection()">
              <i class="pi pi-arrow-left"></i> Back
            </button>
            <h2 class="step-title">Step 2: Select {{ getSelectedMainCLOName() }} Type</h2>
          </div>
          <div class="options-grid">
            <div 
              *ngFor="let subCLO of getSubCLOs()" 
              class="clo-card sub-clo"
              [class.selected]="selectedSubCLO === subCLO.id"
              (click)="selectSubCLO(subCLO.id)">
              <h3>{{ subCLO.display_name }}</h3>
              <p class="card-description">{{ subCLO.description || 'Select this type' }}</p>
            </div>
          </div>
        </div>

        <div class="loading-message" *ngIf="loading">
          <i class="pi pi-spin pi-spinner"></i>
          Loading CLO options...
        </div>

        <div class="error-message" *ngIf="error">
          {{ error }}
        </div>

        <!-- Action Buttons -->
        <div class="action-buttons">
          <button 
            *ngIf="selectionStep === 1"
            class="btn btn-primary"
            [disabled]="!selectedMainCLO || loading"
            (click)="goToSubCLOSelection()">
            Next <i class="pi pi-arrow-right"></i>
          </button>
          
          <button 
            *ngIf="selectionStep === 2"
            class="btn btn-primary"
            [disabled]="!selectedSubCLO || loading"
            (click)="onConfirm()">
            Continue to Dashboard <i class="pi pi-check"></i>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .clo-selection-page {
      min-height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }

    .container {
      background: white;
      border-radius: 16px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      max-width: 900px;
      width: 100%;
      padding: 3rem;
    }

    .header {
      text-align: center;
      margin-bottom: 3rem;
    }

    .header h1 {
      font-size: 2rem;
      font-weight: 700;
      color: #1e293b;
      margin-bottom: 0.5rem;
    }

    .info-text {
      color: #64748b;
      font-size: 0.95rem;
      line-height: 1.5;
    }

    .step-title {
      font-size: 1.25rem;
      font-weight: 600;
      color: #334155;
      margin-bottom: 1.5rem;
      text-align: center;
    }

    .step-header {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1.5rem;
    }

    .back-button {
      background: none;
      border: none;
      color: #3b82f6;
      font-size: 1rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem;
      border-radius: 6px;
      transition: background 0.2s;
    }

    .back-button:hover {
      background: #eff6ff;
    }

    .options-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }

    .clo-card {
      background: white;
      border: 2px solid #e2e8f0;
      border-radius: 12px;
      padding: 1.5rem;
      cursor: pointer;
      transition: all 0.3s ease;
      text-align: center;
    }

    .clo-card:hover {
      border-color: #3b82f6;
      transform: translateY(-4px);
      box-shadow: 0 8px 16px rgba(59, 130, 246, 0.15);
    }

    .clo-card.selected {
      border-color: #3b82f6;
      background: #eff6ff;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
    }

    .clo-card.sub-clo {
      padding: 1.25rem;
    }

    .card-icon {
      font-size: 2.5rem;
      margin-bottom: 1rem;
    }

    .clo-card h3 {
      font-size: 1.1rem;
      font-weight: 600;
      color: #1e293b;
      margin-bottom: 0.5rem;
    }

    .card-description {
      font-size: 0.85rem;
      color: #64748b;
      margin-bottom: 0.75rem;
      line-height: 1.4;
    }

    .card-badge {
      display: inline-block;
      background: #10b981;
      color: white;
      padding: 0.25rem 0.75rem;
      border-radius: 12px;
      font-size: 0.75rem;
      font-weight: 500;
    }

    .action-buttons {
      display: flex;
      justify-content: center;
      margin-top: 2rem;
    }

    .btn {
      padding: 0.75rem 2rem;
      font-size: 1rem;
      font-weight: 600;
      border-radius: 8px;
      border: none;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      transition: all 0.2s;
    }

    .btn-primary {
      background: #3b82f6;
      color: white;
    }

    .btn-primary:hover:not(:disabled) {
      background: #2563eb;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .loading-message {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.75rem;
      padding: 2rem;
      color: #64748b;
      font-size: 1rem;
    }

    .error-message {
      color: #ef4444;
      padding: 1rem;
      background-color: #fee2e2;
      border-radius: 8px;
      font-size: 0.95rem;
      margin-bottom: 1.5rem;
      text-align: center;
    }
  `]
})
export class CLOSelectorComponent implements OnInit {
  selectionStep: 1 | 2 = 1; // Step 1: Main CLO, Step 2: Sub CLO
  selectedMainCLO: string = '';
  selectedSubCLO: string = '';
  mainCLOs: any[] = [];
  cloOptions: CLOOption[] = [];
  loading = false;
  error: string = '';

  constructor(
    private cloMappingService: CloMappingService,
    private cloSelectionService: CLOSelectionService,
    private router: Router
  ) {}

  ngOnInit() {
    // Load CLO options (allow user to change selection even if one exists)
    this.loadCLOOptions();
    
    // Pre-select the current selection if it exists
    const currentSelection = this.cloSelectionService.getCurrentSelection();
    if (currentSelection) {
      this.selectedSubCLO = currentSelection.cloId;
      // Find and set the main CLO
      const option = this.cloOptions.find((opt: CLOOption) => opt.id === currentSelection.cloId);
      if (option) {
        this.selectedMainCLO = option.mainCLO;
      }
    }
  }

  /**
   * Select main CLO
   */
  selectMainCLO(cloId: string) {
    this.selectedMainCLO = cloId;
  }

  /**
   * Select sub CLO
   */
  selectSubCLO(cloId: string) {
    this.selectedSubCLO = cloId;
  }

  /**
   * Load available CLO options from backend
   */
  private loadCLOOptions() {
    this.loading = true;
    this.error = '';

    this.cloMappingService.getCLOHierarchy().subscribe({
      next: (hierarchy: any) => {
        // Store main CLOs for first step selection
        this.mainCLOs = hierarchy.main_clos;
        
        // Also create flat list for backward compatibility
        this.cloOptions = [];
        hierarchy.main_clos.forEach((mainCLO: any) => {
          mainCLO.sub_clos.forEach((subCLO: any) => {
            this.cloOptions.push({
              id: subCLO.id,
              name: subCLO.name,
              mainCLO: mainCLO.name,
              description: subCLO.description
            });
          });
        });

        this.loading = false;
        console.log('✅ Loaded', this.mainCLOs.length, 'main CLOs and', this.cloOptions.length, 'sub CLOs');
      },
      error: (error: any) => {
        this.loading = false;
        this.error = 'Failed to load CLO options. Please try again.';
        console.error('Error loading CLO hierarchy:', error);
      }
    });
  }

  /**
   * Handle confirm action - triggered when user clicks "Continue to Dashboard"
   */
  onConfirm() {
    if (!this.selectedSubCLO) {
      this.error = 'Please select a CLO type';
      return;
    }

    this.loading = true;
    this.error = '';

    // Get the visible columns for the selected CLO
    this.cloMappingService.getUserColumns(this.selectedSubCLO).subscribe({
      next: (response: any) => {
        const selectedOption = this.cloOptions.find((opt: CLOOption) => opt.id === this.selectedSubCLO);
        
        if (selectedOption) {
          const selection: UserCLOSelection = {
            cloId: this.selectedSubCLO,
            cloName: selectedOption.name,
            mainCLO: selectedOption.mainCLO,
            visibleColumns: response.visible_columns,
            selectedAt: new Date()
          };

          // Save the selection
          this.cloSelectionService.setSelection(selection);
          
          console.log('✅ CLO selection saved:', selection);
          console.log('📊 Visible columns:', response.visible_columns.length, 'columns');

          this.loading = false;

          // Navigate to dashboard
          this.router.navigate(['/home']);
        }
      },
      error: (error: any) => {
        this.loading = false;
        this.error = 'Failed to load column configuration. Please try again.';
        console.error('Error getting user columns:', error);
      }
    });
  }
  /**
   * Get the current selection
   */
  getCurrentSelection(): UserCLOSelection | null {
    return this.cloSelectionService.getCurrentSelection();
  }

  /**
   * Navigate to Sub CLO selection step
   */
  goToSubCLOSelection() {
    if (!this.selectedMainCLO) {
      return;
    }
    this.selectionStep = 2;
    this.selectedSubCLO = ''; // Reset sub CLO selection
  }

  /**
   * Go back to Main CLO selection
   */
  goBackToMainSelection() {
    this.selectionStep = 1;
    this.selectedSubCLO = '';
  }

  /**
   * Get sub CLOs for selected main CLO
   */
  getSubCLOs(): any[] {
    const mainCLO = this.mainCLOs.find((clo: any) => clo.id === this.selectedMainCLO);
    return mainCLO ? mainCLO.sub_clos : [];
  }

  /**
   * Get selected main CLO display name
   */
  getSelectedMainCLOName(): string {
    const mainCLO = this.mainCLOs.find((clo: any) => clo.id === this.selectedMainCLO);
    return mainCLO ? mainCLO.display_name : '';
  }
}

