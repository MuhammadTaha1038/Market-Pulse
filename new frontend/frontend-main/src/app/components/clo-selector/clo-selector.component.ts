import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ApiService, CLOHierarchy, MainCLO, CLOType, UserCLOSelection } from '../../services/api.service';

@Component({
    selector: 'app-clo-selector',
    standalone: true,
    imports: [CommonModule, ProgressSpinnerModule],
    template: `
    <div class="clo-selection-page">
        <div class="container">
            <div class="header">
                <h1>Select your asset class</h1>
                <p class="info-text">You can change asset class later from settings if needed</p>
            </div>

            <!-- Step 1: Select Main CLO -->
            <div *ngIf="selectionStep === 1" class="clo-options">
                <h2 class="step-title">Step 1: Select Main CLO Type</h2>
                <div class="options-grid">
                    <div *ngFor="let mainCLO of mainCLOs" class="clo-card"
                        [class.selected]="selectedMainCLO === mainCLO.id"
                        (click)="selectMainCLO(mainCLO.id)">
                        <div class="card-icon">📊</div>
                        <h3>{{ mainCLO.display_name }}</h3>
                        <p class="card-description">{{ mainCLO.description || 'Select this type' }}</p>
                        <span class="card-badge">{{ mainCLO.sub_clos.length }} types</span>
                    </div>
                </div>
            </div>

            <!-- Step 2: Select Sub CLO -->
            <div *ngIf="selectionStep === 2" class="clo-options">
                <div class="step-header">
                    <button class="back-button" (click)="goBackToMainSelection()">
                        <i class="pi pi-arrow-left"></i> Back
                    </button>
                    <h2 class="step-title">Step 2: Select {{ getSelectedMainCLOName() }} Type</h2>
                </div>
                <div class="options-grid">
                    <div *ngFor="let subCLO of getSubCLOs()" class="clo-card sub-clo"
                        [class.selected]="selectedSubCLO === subCLO.id"
                        (click)="selectSubCLO(subCLO.id)">
                        <h3>{{ subCLO.display_name }}</h3>
                        <p class="card-description">{{ subCLO.description || 'Select this type' }}</p>
                    </div>
                </div>
            </div>

            <div class="loading-message" *ngIf="loading">
                <p-progressSpinner [style]="{width: '30px', height: '30px'}" strokeWidth="4"></p-progressSpinner>
                <span>Loading CLO options...</span>
            </div>
            <div class="error-message" *ngIf="error">{{ error }}</div>

            <!-- Action Buttons -->
            <div class="action-buttons">
                <button *ngIf="selectionStep === 1" class="btn btn-primary"
                    [disabled]="!selectedMainCLO || loading" (click)="goToSubCLOSelection()">
                    Next <i class="pi pi-arrow-right"></i>
                </button>
                <button *ngIf="selectionStep === 2" class="btn btn-primary"
                    [disabled]="!selectedSubCLO || loading" (click)="onConfirm()">
                    Continue to Dashboard <i class="pi pi-check"></i>
                </button>
            </div>
        </div>
    </div>
    `,
    styles: [`
        .clo-selection-page { min-height: 100vh; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); display: flex; align-items: center; justify-content: center; padding: 2rem; }
        .container { background: white; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 900px; width: 100%; padding: 3rem; }
        .header { text-align: center; margin-bottom: 3rem; }
        .header h1 { font-size: 2rem; font-weight: 700; color: #1e293b; margin-bottom: 0.5rem; }
        .info-text { color: #64748b; font-size: 0.95rem; }
        .step-title { font-size: 1.25rem; font-weight: 600; color: #334155; margin-bottom: 1.5rem; text-align: center; }
        .step-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; }
        .back-button { background: none; border: none; color: #111827; font-size: 0.95rem; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; border-radius: 8px; transition: background 0.2s; }
        .back-button:hover { background: #f3f4f6; }
        .options-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .clo-card { background: white; border: 2px solid #e5e7eb; border-radius: 12px; padding: 1.5rem; cursor: pointer; transition: all 0.2s ease; text-align: center; }
        .clo-card:hover { border-color: #111827; transform: translateY(-2px); box-shadow: 0 8px 16px rgba(0,0,0,0.08); }
        .clo-card.selected { border-color: #111827; background: #f9fafb; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .card-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }
        .clo-card h3 { font-size: 1.1rem; font-weight: 600; color: #1e293b; margin-bottom: 0.5rem; }
        .card-description { font-size: 0.85rem; color: #64748b; margin-bottom: 0.75rem; }
        .card-badge { display: inline-block; background: #111827; color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; font-weight: 500; }
        .action-buttons { display: flex; justify-content: center; margin-top: 2rem; }
        .btn { padding: 0.75rem 2rem; font-size: 1rem; font-weight: 600; border-radius: 9999px; border: none; cursor: pointer; display: inline-flex; align-items: center; gap: 0.5rem; transition: all 0.2s; }
        .btn-primary { background: #111827; color: white; }
        .btn-primary:hover:not(:disabled) { background: #000; transform: translateY(-1px); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .loading-message { display: flex; align-items: center; justify-content: center; gap: 0.75rem; padding: 2rem; color: #64748b; font-size: 0.95rem; }
        .error-message { color: #ef4444; padding: 1rem; background: #fee2e2; border-radius: 8px; font-size: 0.9rem; margin-bottom: 1rem; text-align: center; }
    `]
})
export class CLOSelectorComponent implements OnInit {
    selectionStep: 1 | 2 = 1;
    selectedMainCLO = '';
    selectedSubCLO = '';
    mainCLOs: MainCLO[] = [];
    loading = false;
    error = '';

    private readonly STORAGE_KEY = 'user_clo_selection';

    constructor(
        private apiService: ApiService,
        private router: Router
    ) {}

    ngOnInit() {
        this.loadCLOOptions();
        const stored = this.getCurrentSelection();
        if (stored) {
            this.selectedSubCLO = stored.cloId;
        }
    }

    selectMainCLO(cloId: string) { this.selectedMainCLO = cloId; }
    selectSubCLO(cloId: string) { this.selectedSubCLO = cloId; }

    private loadCLOOptions() {
        this.loading = true;
        this.error = '';
        this.apiService.getCloHierarchy().subscribe({
            next: (hierarchy: CLOHierarchy) => {
                this.mainCLOs = hierarchy.main_clos;
                this.loading = false;
            },
            error: () => {
                this.loading = false;
                this.error = 'Failed to load CLO options. Please try again.';
            }
        });
    }

    onConfirm() {
        if (!this.selectedSubCLO) { this.error = 'Please select a CLO type'; return; }
        this.loading = true;
        this.error = '';

        this.apiService.getUserColumns(this.selectedSubCLO).subscribe({
            next: (response: any) => {
                const mainCLO = this.mainCLOs.find(m => m.sub_clos.some(s => s.id === this.selectedSubCLO));
                const subCLO = mainCLO?.sub_clos.find(s => s.id === this.selectedSubCLO);
                if (subCLO && mainCLO) {
                    const selection: UserCLOSelection = {
                        cloId: this.selectedSubCLO,
                        cloName: subCLO.name,
                        mainCLO: mainCLO.name,
                        visibleColumns: response.visible_columns || [],
                        selectedAt: new Date()
                    };
                    this.saveSelection(selection);
                    this.loading = false;
                    this.router.navigate(['/home']);
                }
            },
            error: () => {
                this.loading = false;
                this.error = 'Failed to load column configuration. Please try again.';
            }
        });
    }

    goToSubCLOSelection() { if (!this.selectedMainCLO) return; this.selectionStep = 2; this.selectedSubCLO = ''; }
    goBackToMainSelection() { this.selectionStep = 1; this.selectedSubCLO = ''; }
    getSubCLOs(): CLOType[] { const m = this.mainCLOs.find(c => c.id === this.selectedMainCLO); return m ? m.sub_clos : []; }
    getSelectedMainCLOName(): string { const m = this.mainCLOs.find(c => c.id === this.selectedMainCLO); return m ? m.display_name : ''; }

    getCurrentSelection(): UserCLOSelection | null {
        try {
            const stored = localStorage.getItem(this.STORAGE_KEY);
            if (stored) { const parsed = JSON.parse(stored); parsed.selectedAt = new Date(parsed.selectedAt); return parsed; }
        } catch { }
        return null;
    }

    private saveSelection(selection: UserCLOSelection) {
        try { localStorage.setItem(this.STORAGE_KEY, JSON.stringify(selection)); } catch { }
    }
}
