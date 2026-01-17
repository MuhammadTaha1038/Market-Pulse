import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { RadioButtonModule } from 'primeng/radiobutton';
import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'app-sub-asset',
  imports: [FormsModule, RadioButtonModule, ButtonModule],
  templateUrl: './sub-asset.html'
})
export class SubAsset {
  selectedAsset: string = '';

  constructor(private router: Router) {}

  onOkay() {
    if (this.selectedAsset) {
      console.log('Selected Asset:', this.selectedAsset);
      
      // Store the selected asset for future use
      localStorage.setItem('selectedAsset', this.selectedAsset);
      
      // Navigate to home within the layout
      this.router.navigate(['/home']);
    }
  }

  onCancel() {
    // Navigate back to login
    this.router.navigate(['/login']);
  }
}