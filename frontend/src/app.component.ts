import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import { DashboardCacheService } from './app/services/dashboard-cache.service';

@Component({
    selector: 'app-root',
    standalone: true,
    imports: [RouterModule],
    template: `<router-outlet></router-outlet>`
})
export class AppComponent {
    constructor(private dashboardCache: DashboardCacheService) {
        this.dashboardCache.startVersionMonitor();
    }
}
