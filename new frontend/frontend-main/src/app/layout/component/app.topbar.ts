import { Component, OnInit, OnDestroy } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { RouterModule, Router, NavigationEnd } from '@angular/router';
import { CommonModule } from '@angular/common';
import { StyleClassModule } from 'primeng/styleclass';
import { LayoutService } from '../service/layout.service';
import { SelectModule } from 'primeng/select';
import { FormsModule } from '@angular/forms';
import { AssetStateService } from 'src/app/services/asset-state.service';
import { AutomationStatusService } from 'src/app/services/automation-status.service';
import { NextRunService } from 'src/app/services/next-run.service';
import { TableStateService } from '../../components/home/table-state.service';
import { filter, Subscription } from 'rxjs';

@Component({
    selector: 'app-topbar',
    standalone: true,
    imports: [RouterModule, CommonModule, StyleClassModule, SelectModule, FormsModule],
    template: `
        <div class="layout-topbar">
            <!-- LEFT: Sidebar-width title box + Menu toggle + Content area -->
            <div class="layout-topbar-left">
                <!-- Title box matching sidebar width -->
                <div class="topbar-title-box">
                    <a class="layout-topbar-logo" routerLink="/" (click)="onLogoClick()">
                        <div class="flex flex-col leading-tight">
                            <b><span class="main-title font-bold whitespace-nowrap">Market Pulse</span></b>
                            <span class="text-xs text-gray-500 whitespace-nowrap"> Movement Intelligence </span>
                        </div>
                    </a>

                    <!-- MENU TOGGLE -->
                    <button class="layout-menu-button mx-2" [disabled]="isMenuButtonDisabled" [style.opacity]="isMenuButtonDisabled ? '0.4' : '1'" [style.cursor]="isMenuButtonDisabled ? 'not-allowed' : 'pointer'" (click)="onMenuToggle($event)">
                        <svg width="17" height="17" viewBox="0 0 17 17" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path
                                fill-rule="evenodd"
                                clip-rule="evenodd"
                                d="M7.6753 1.77128H1.7713C1.30128 1.77128 0.850801 1.9578 0.519051 2.29023C0.186626 2.62198 0 3.07245 0 3.54248V12.989C0 13.459 0.186621 13.9094 0.519051 14.2412C0.850801 14.5737 1.30128 14.7602 1.7713 14.7602H7.6753V15.941C7.6753 16.2669 7.93975 16.5314 8.26562 16.5314C8.5916 16.5314 8.85605 16.2669 8.85605 15.941V14.7602H14.7601C15.2301 14.7602 15.6806 14.5737 16.0123 14.2412C16.3447 13.9094 16.5312 13.459 16.5312 12.989V3.54248C16.5312 3.07245 16.3447 2.62198 16.0123 2.29023C15.6806 1.9578 15.2301 1.77128 14.7601 1.77128H8.85605V0.590425C8.85605 0.26455 8.5916 0 8.26562 0C7.93975 0 7.6753 0.26455 7.6753 0.590425V1.77128ZM7.6753 2.95202V13.5793H1.7713C1.61476 13.5793 1.46428 13.5173 1.35383 13.4062C1.24289 13.2959 1.18088 13.1453 1.18088 12.9889V3.54235C1.18088 3.38591 1.24289 3.23533 1.35383 3.12488C1.46428 3.01394 1.61478 2.95193 1.7713 2.95193L7.6753 2.95202ZM8.85605 2.95202H14.7601C14.9165 2.95202 15.0671 3.01404 15.1775 3.12497C15.2885 3.23542 15.3505 3.386 15.3505 3.54245V12.9889C15.3505 13.1454 15.2885 13.296 15.1775 13.4063C15.0671 13.5174 14.9165 13.5794 14.7601 13.5794H8.85605V2.95202Z"
                                fill="currentColor"
                            />
                        </svg>
                    </button>
                </div>

                <!-- Vertical divider at sidebar boundary -->
                <div class="topbar-sidebar-divider"></div>

                <!-- PAGE TITLE (HOME ONLY) -->
                <span *ngIf="isHomeRoute" class="main-title hidden md:block text-base font-bold text-gray-950 whitespace-nowrap ml-4"> {{ mainAssetType }} Data & Insights </span>
            </div>

            <!-- RIGHT: Actions -->
            <div class="layout-topbar-actions">
                <!-- ASSET SELECTION -->
                <div class="asset-selection" *ngIf="isHomeRoute && assetOptions.length > 0">
                    <span class="asset-dot" [class.running]="showRunningIndicator" [attr.title]="showRunningIndicator ? 'Running' : null"></span>
                    <p-select [options]="assetOptions" [(ngModel)]="selectedAsset" optionLabel="name" class="asset-selector" (ngModelChange)="onAssetChange($event)"> </p-select>
                </div>

                <!-- NEXT RUN TIMER -->
                <div class="next-run-wrapper">
                    <span class="next-run-label">Next Run in</span>
                    <span class="next-run-timer-pill">{{ nextRunTimer }}</span>
                </div>

                <!-- USER INFO + DROPDOWN -->
                <div class="user-info">
                    <span class="user-divider"></span>
                    <div class="user-menu-wrapper">
                        <div class="user-trigger" (click)="showUserMenu = !showUserMenu">
                            <div class="user-details">
                                <div class="user-name">Shashank S.</div>
                                <div class="user-email">Shashank.Srivastava&#64;spglobal.com</div>
                            </div>
                            <i class="pi pi-chevron-down user-chevron" [class.rotated]="showUserMenu"></i>
                        </div>

                        <!-- Dropdown -->
                        <div class="user-dropdown" *ngIf="showUserMenu">
                            <button class="dropdown-item" (click)="onLogout()">
                                <i class="pi pi-sign-out"></i>
                                <span>Logout</span>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Backdrop to close dropdown -->
                <div class="menu-backdrop" *ngIf="showUserMenu" (click)="showUserMenu = false"></div>
            </div>
        </div>
    `,
    styles: [
        `
            .layout-topbar {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 1rem;
                height: 5rem;
                background-color: var(--surface-card);
                border-bottom: 1px solid var(--surface-border);
                position: fixed;
                inset: 0;
                z-index: 1000;
            }

            .layout-topbar-left {
                display: flex;
                align-items: center;
            }

            .topbar-title-box {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                width: 14rem;
                flex-shrink: 0;
            }

            .topbar-sidebar-divider {
                width: 1px;
                height: 5rem;
                background-color: #d1d5db;
                flex-shrink: 0;
            }

            .layout-topbar-logo {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                text-decoration: none;
                color: inherit;
            }

            .layout-topbar-actions {
                display: flex;
                align-items: center;
                gap: 1.5rem;
            }

            .asset-selection {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.2rem 0.75rem;
                border-radius: 9999px;
                border: 1px solid #e5e7eb; /* soft gray */
                background: #ffffff;
            }

            .asset-dot {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background-color: #cbd5e1;
                transition:
                    background-color 0.2s ease,
                    box-shadow 0.2s ease,
                    transform 0.2s ease;
            }

            .asset-dot.running {
                background-color: #22c55e;
                box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.18);
                animation: assetDotPulse 1.8s ease-in-out infinite;
            }

            @keyframes assetDotPulse {
                0%,
                100% {
                    transform: scale(1);
                    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.22);
                }

                50% {
                    transform: scale(1.08);
                    box-shadow: 0 0 0 6px rgba(34, 197, 94, 0.12);
                }
            }

            .asset-selector {
                min-width: 110px;
            }

            /* REMOVE BORDER/SHADOW FROM THE RENDERED P-SELECT ROOT */
            :host ::ng-deep p-select.asset-selector.p-select {
                border: none !important;
                box-shadow: none !important;
            }

            /* NEXT RUN */
            .next-run-wrapper {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 0.35rem 0.75rem;
                border-radius: 9999px;
                border: 1px solid var(--surface-border);
                background: var(--surface-card);
            }

            .next-run-label {
                font-size: 0.75rem;
                color: var(--text-color-secondary);
                white-space: nowrap;
            }

            .next-run-timer-pill {
                padding: 0.25rem 0.75rem;
                border-radius: 9999px;
                border: 1px solid var(--surface-border);
                font-size: 0.875rem;
                font-weight: 600;
                background: var(--surface-card);
                white-space: nowrap;
            }

            /* USER INFO */
            .user-info {
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }

            .user-divider {
                width: 1px;
                height: 2rem;
                background-color: #e5e7eb;
            }

            .user-menu-wrapper {
                position: relative;
            }

            .user-trigger {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                cursor: pointer;
                padding: 0.25rem 0.5rem;
                border-radius: 0.5rem;
                transition: background-color 0.15s ease;
            }

            .user-trigger:hover {
                background-color: #f3f4f6;
            }

            .user-details {
                display: flex;
                flex-direction: column;
                align-items: flex-start;
            }

            .user-name {
                font-family: 'Degular Display', sans-serif;
                font-size: 17px;
                font-weight: 600;
            }

            .user-email {
                font-size: 0.75rem;
                color: var(--text-color-secondary);
            }

            .user-chevron {
                font-size: 0.7rem;
                color: #9ca3af;
                transition: transform 0.2s ease;
            }

            .user-chevron.rotated {
                transform: rotate(180deg);
            }

            .user-dropdown {
                position: absolute;
                top: calc(100% + 0.5rem);
                right: 0;
                min-width: 160px;
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 0.5rem;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                z-index: 1100;
                padding: 0.25rem;
                animation: dropdownFade 0.15s ease;
            }

            @keyframes dropdownFade {
                from {
                    opacity: 0;
                    transform: translateY(-4px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .dropdown-item {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                width: 100%;
                padding: 0.5rem 0.75rem;
                border: none;
                background: transparent;
                color: #374151;
                font-size: 0.875rem;
                cursor: pointer;
                border-radius: 0.375rem;
                transition:
                    background-color 0.15s ease,
                    color 0.15s ease;
            }

            .dropdown-item:hover {
                background-color: #fee2e2;
                color: #dc2626;
            }

            .dropdown-item i {
                font-size: 0.875rem;
            }

            .menu-backdrop {
                position: fixed;
                inset: 0;
                z-index: 1050;
            }

            .layout-menu-button {
                width: 2.5rem;
                height: 2.5rem;
                border-radius: 0.5rem;
                background: transparent;
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background-color 0.2s ease;
                margin-left: 3rem;
            }

            .layout-menu-button:hover {
                background: white;
            }

            .layout-menu-button svg {
                color: #374151;
            }

            @media (max-width: 768px) {
                .asset-selection,
                .next-run-wrapper,
                .user-details {
                    display: none;
                }
            }
            .main-title {
                font-family: 'Degular Display', sans-serif;
                font-size: 22px;
                font-weight: 500;
                letter-spacing: -0.02em;
            }

            .secondary-title {
                font-family: 'Degular Display', sans-serif;
                font-size: 20px;
                font-weight: 400;
                color: var(--text-color-secondary);
            }
        `
    ]
})
export class AppTopbar implements OnInit, OnDestroy {
    items!: MenuItem[];
    nextRunTimer = '--:--:--';

    assetOptions: { name: string; value: string }[] = [];

    selectedAsset: { name: string; value: string } | null = null;

    mainAssetType: string = 'Asset Class'; // Default display value

    showUserMenu = false;
    isTableExpanded = false;
    isAutomationRunning = false;

    isHomeRoute = false;
    private routerSub!: Subscription;
    private timerSub!: Subscription;
    private assetSub!: Subscription;
    private mainTypeSub!: Subscription;
    private subsSub!: Subscription;
    private tableExpandedSub!: Subscription;
    private automationSub!: Subscription;

    get isMenuButtonDisabled(): boolean {
        return this.isTableExpanded && this.isHomeRoute;
    }

    get showRunningIndicator(): boolean {
        return this.isAutomationRunning || this.nextRunTimer === 'Running...';
    }

    constructor(
        public layoutService: LayoutService,
        private router: Router,
        private assetStateService: AssetStateService,
        private automationStatusService: AutomationStatusService,
        private nextRunService: NextRunService,
        private tableStateService: TableStateService
    ) {}

    ngOnInit(): void {
        this.updateHomeRoute(this.router.url);

        this.routerSub = this.router.events.pipe(filter((event) => event instanceof NavigationEnd)).subscribe((event: NavigationEnd) => {
            const wasHomeRoute = this.isHomeRoute;
            this.updateHomeRoute(event.urlAfterRedirects);

            // Reset table expansion state when navigating away from home
            if (wasHomeRoute && !this.isHomeRoute && this.isTableExpanded) {
                this.tableStateService.setTableExpanded(false);
            }
        });

        // Subscribe to main asset type
        this.mainTypeSub = this.assetStateService.mainType$.subscribe((mainType) => {
            if (mainType && mainType.display_name) {
                this.mainAssetType = mainType.display_name;
            }
        });

        // Subscribe to dynamic sub-asset options from AssetStateService
        this.subsSub = this.assetStateService.subAssets$.subscribe((subs) => {
            this.assetOptions = subs;
        });
        this.assetSub = this.assetStateService.asset$.subscribe((asset) => {
            this.selectedAsset = asset;
        });

        // Subscribe to table expansion state
        this.tableExpandedSub = this.tableStateService.isTableExpanded$.subscribe((expanded) => {
            this.isTableExpanded = expanded;
        });

        // Start and subscribe to the shared countdown service
        this.nextRunService.init();
        this.timerSub = this.nextRunService.timer$.subscribe((val) => {
            this.nextRunTimer = val;
        });

        this.automationSub = this.automationStatusService.isRunning$.subscribe((running) => {
            this.isAutomationRunning = running;
        });
    }

    private updateHomeRoute(url: string): void {
        this.isHomeRoute = url === '/' || url.startsWith('/home');
    }

    onMenuToggle(event: Event) {
        event.stopPropagation();
        event.preventDefault();
        this.layoutService.onMenuToggle();
    }

    onLogoClick(): void {
        // Reset table expansion when navigating to home
        if (this.isTableExpanded) {
            this.tableStateService.setTableExpanded(false);
        }
    }

    onAssetChange(asset: any) {
        this.assetStateService.setAsset(asset);
    }

    onLogout(): void {
        this.showUserMenu = false;
        localStorage.removeItem('selectedAssetState');
        localStorage.removeItem('userMainAssetType');
        this.router.navigate(['/login']);
    }

    ngOnDestroy(): void {
        this.routerSub?.unsubscribe();
        this.timerSub?.unsubscribe();
        this.assetSub?.unsubscribe();
        this.mainTypeSub?.unsubscribe();
        this.subsSub?.unsubscribe();
        this.tableExpandedSub?.unsubscribe();
        this.automationSub?.unsubscribe();
    }
}
