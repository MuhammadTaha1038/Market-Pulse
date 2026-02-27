import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RadioButtonModule } from 'primeng/radiobutton';
import { ButtonModule } from 'primeng/button';
import { ApiService } from '../../services/api.service';
import { AssetStateService, MainAssetType } from '../../services/asset-state.service';

@Component({
    selector: 'app-sub-asset',
    imports: [CommonModule, FormsModule, RadioButtonModule, ButtonModule],
    templateUrl: './sub-asset.html',
    styleUrls: ['./sub-asset.css']
})
export class SubAsset implements OnInit {
    /** All main asset types from the backend hierarchy */
    mainTypes: MainAssetType[] = [];

    /** The user's assigned main type (from login/role).
     *  For now, read from localStorage; later this comes from auth. */
    assignedMainType: MainAssetType | null = null;

    /** The sub-asset the user selects via radio button */
    selectedSubAssetId = '';

    loading = true;
    error = '';

    constructor(
        private router: Router,
        private apiService: ApiService,
        private assetStateService: AssetStateService
    ) {}

    ngOnInit(): void {
        this.loadHierarchy();
    }

    loadHierarchy(): void {
        this.loading = true;
        this.error = '';

        this.apiService.getCloHierarchy().subscribe({
            next: (res) => {
                this.mainTypes = res.main_clos || [];

                // The main asset type is assigned during authentication
                const storedMainId = localStorage.getItem('userMainAssetType');
                if (storedMainId) {
                    this.assignedMainType = this.mainTypes.find(m => m.id === storedMainId) || null;
                }

                // Fallback: auto-assign the first main type if none stored
                if (!this.assignedMainType && this.mainTypes.length > 0) {
                    this.assignedMainType = this.mainTypes[0];
                    localStorage.setItem('userMainAssetType', this.mainTypes[0].id);
                }

                if (!this.assignedMainType) {
                    this.error = 'No asset classes available. Please contact your administrator.';
                }

                this.loading = false;
            },
            error: (err) => {
                console.error('Failed to load asset hierarchy:', err);
                this.error = 'Failed to load asset classes. Please try again.';
                this.loading = false;
            }
        });
    }

    onOkay(): void {
        if (!this.assignedMainType || !this.selectedSubAssetId) return;

        const subAsset = this.assignedMainType.sub_clos.find(s => s.id === this.selectedSubAssetId);
        if (!subAsset) return;

        // Store in AssetStateService (persists to localStorage)
        this.assetStateService.setMainType(this.assignedMainType);
        this.assetStateService.setAsset({
            name: subAsset.display_name || subAsset.name,
            value: subAsset.id
        });

        this.router.navigate(['/home']);
    }

    onCancel(): void {
        this.router.navigate(['/login']);
    }
}
