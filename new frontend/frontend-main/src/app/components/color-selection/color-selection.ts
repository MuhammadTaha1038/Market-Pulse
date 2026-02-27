import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { ChipModule } from 'primeng/chip';
import { DividerModule } from 'primeng/divider';
import { ApiService } from '../../services/api.service';
import { NextRunService } from '../../services/next-run.service';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-color-selection',
  standalone: true,
  imports: [CommonModule, ButtonModule, ChipModule, DividerModule],
  templateUrl: './color-selection.html',
  styleUrls: ['./color-selection.css']
})
export class ColorSelection implements OnInit, OnDestroy {
  nextRunTimer = '--:--:--';
  uploading = false;
  private timerSub!: Subscription;

  constructor(
    private apiService: ApiService,
    private router: Router,
    private nextRunService: NextRunService
  ) {}

  ngOnInit() {
    this.nextRunService.init();
    this.timerSub = this.nextRunService.timer$.subscribe(val => {
      this.nextRunTimer = val;
    });
  }

  goToPresetSettings() {
    this.router.navigate(['/settings'], { queryParams: { section: 'preset' } });
  }

  goToRulesPage() {
    this.router.navigate(['/settings'], { queryParams: { section: 'rules' } });
  }

  runAutomation() {
    this.router.navigate(['/home']);
  }

  runManual() {
    this.router.navigate(['/manual-color']);
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];

      // Check file type
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        alert('Please upload an Excel file (.xlsx or .xls)');
        return;
      }

      this.uploading = true;

      // Navigate to manual-color page with uploaded file
      setTimeout(() => {
        this.uploading = false;
        alert(`File "${file.name}" uploaded successfully! You can now review and process the data.`);
        this.router.navigate(['/manual-color']);
      }, 1500);
    }
  }
  goToHelpPage(): void {
        this.router.navigate(['/temp']);
    }

  ngOnDestroy() {
    this.timerSub?.unsubscribe();
  }
}
