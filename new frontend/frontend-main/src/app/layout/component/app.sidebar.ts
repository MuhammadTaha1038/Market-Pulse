import { Component, ElementRef, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { TooltipModule } from 'primeng/tooltip';
import { AppMenu } from './app.menu';
import { Subscription } from 'rxjs';
import { LayoutService } from '../service/layout.service';
import { TableStateService } from '../../components/home/table-state.service';
import { MenuActiveService } from '../service/menu-active.service';

interface CollapsedMenuItem {
    label: string;
    icon: string;
    routerLink: string[];
    queryParams?: { [key: string]: string };
    disabled?: boolean;
    action?: () => void;
}

interface CollapsedMenuSection {
    label: string;
    items: CollapsedMenuItem[];
}

@Component({
    selector: 'app-sidebar',
    standalone: true,
    imports: [CommonModule, RouterModule, TooltipModule, AppMenu],
    template: `
        <!-- Full sidebar with icons + text -->
        <div *ngIf="!isCollapsed" class="layout-sidebar">
            <app-menu></app-menu>
        </div>

        <!-- Collapsed icon-only sidebar -->
        <div *ngIf="isCollapsed" class="layout-sidebar sidebar-collapsed">
            <ng-container *ngFor="let section of collapsedMenu; let si = index">
                <div *ngIf="si > 0" class="section-divider"></div>
                <ng-container *ngFor="let item of section.items">
                    <!-- Navigation item with optional action -->
                    <a (click)="onItemClick(item)" class="icon-nav-item" [class.active-route]="item.label === activeMenuItem" [class.disabled]="item.disabled" [pTooltip]="item.label" tooltipPosition="right">
                        <img [src]="item.icon" [alt]="item.label" class="nav-icon" />
                    </a>
                </ng-container>
            </ng-container>
        </div>
    `,
    styles: [
        `
            .layout-sidebar {
                position: fixed;
                width: 15rem;
                height: calc(100vh - 4rem);
                z-index: 999;
                overflow-y: auto;
                overflow-x: hidden;
                -webkit-user-select: none;
                user-select: none;
                top: 4rem;
                margin-top: 5px;
                left: 0;
                background-color: #ffffff;
                border-radius: 0;
                padding: 0.5rem 1.5rem;
                border-right: 1px solid var(--surface-border);
                display: block;
            }

            /* Collapsed state */
            .layout-sidebar.sidebar-collapsed {
                width: 4.5rem !important;
                padding: 0.75rem 0.5rem;
                display: flex !important;
                flex-direction: column;
                align-items: center;
                gap: 0.25rem;
                transform: none !important;
                z-index: 999 !important;
            }

            .section-divider {
                width: 70%;
                height: 1px;
                background-color: #e5e7eb;
                margin: 0.5rem 0;
            }

            .icon-nav-item {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 2.75rem;
                height: 2.75rem;
                border-radius: 0.625rem;
                cursor: pointer;
                transition:
                    background-color 0.2s ease,
                    box-shadow 0.2s ease;
                text-decoration: none;
                color: inherit;
            }

            .icon-nav-item:hover {
                background-color: var(--surface-hover, #f3f4f6);
            }

            .icon-nav-item.active-route {
                background-color: #f5f5f5;
                border: 2px solid #374151;
                font-weight: 700;
            }

            .icon-nav-item.active-route .nav-icon {
                filter: brightness(0.6);
            }

            .icon-nav-item.disabled {
                opacity: 0.4;
                cursor: not-allowed;
                pointer-events: none;
            }

            .nav-icon {
                width: 1.25rem;
                height: 1.25rem;
                object-fit: contain;
            }

            /* Scrollbar styling */
            .layout-sidebar::-webkit-scrollbar {
                width: 6px;
            }

            .layout-sidebar::-webkit-scrollbar-track {
                background: transparent;
            }

            .layout-sidebar::-webkit-scrollbar-thumb {
                background: #d1d5db;
                border-radius: 3px;
            }

            .layout-sidebar::-webkit-scrollbar-thumb:hover {
                background: #9ca3af;
            }
        `
    ]
})
export class AppSidebar implements OnInit, OnDestroy {
    collapsedMenu: CollapsedMenuSection[] = [];
    activeMenuItem: string = 'Dashboard';
    private isTableExpanded = false;
    private tableExpandedSub!: Subscription;
    private activeMenuSub!: Subscription;

    constructor(
        public el: ElementRef,
        private layoutService: LayoutService,
        private tableStateService: TableStateService,
        private menuActiveService: MenuActiveService,
        private router: Router
    ) {
        this.collapsedMenu = [
            {
                label: 'Main',
                items: [
                    { label: 'Dashboard', icon: 'assets/icon/dashboard.svg', routerLink: ['/home'] },
                    { label: 'Security Search', icon: 'assets/icon/security.svg', routerLink: ['/home'], action: () => this.toggleTableExpansion() },
                    { label: 'Color Process', icon: 'assets/icon/colorprocess.svg', routerLink: ['/color-type'] },
                    { label: 'Data Statistics', icon: 'assets/icon/data.svg', routerLink: ['/home'], disabled: true }
                ]
            },
            {
                label: 'Settings',
                items: [
                    { label: 'Rules', icon: 'assets/icon/rules.svg', routerLink: ['/settings'], queryParams: { section: 'rules' } },
                    { label: 'Preset', icon: 'assets/icon/presets.svg', routerLink: ['/settings'], queryParams: { section: 'preset' } },
                    { label: 'Cron Jobs', icon: 'assets/icon/cronjob.svg', routerLink: ['/settings'], queryParams: { section: 'cron-jobs' } },
                    { label: 'Sorting', icon: 'assets/icon/sorting.svg', routerLink: ['/settings'], queryParams: { section: 'sorting' } },
                    { label: 'Email & Restore', icon: 'assets/icon/info.svg', routerLink: ['/settings'], queryParams: { section: 'restore-email' } }
                ]
            },
            {
                label: 'Super Admin',
                items: [
                    { label: 'CLO Mappings', icon: 'pi pi-fw pi-shield', routerLink: ['/clo-mappings'] }
                ]
            }
        ];
    }

    ngOnInit() {
        this.activeMenuSub = this.menuActiveService.activeMenuItem$.subscribe((item) => {
            this.activeMenuItem = item;
        });

        this.tableExpandedSub = this.tableStateService.isTableExpanded$.subscribe((expanded) => {
            this.isTableExpanded = expanded;
        });
    }

    toggleTableExpansion() {
        this.tableStateService.setTableExpanded(true);
    }

    onItemClick(item: CollapsedMenuItem) {
        // Prevent navigation if disabled
        if (item.disabled) {
            return;
        }

        // Set this item as active
        this.menuActiveService.setActiveMenuItem(item.label);

        // Handle Dashboard navigation - always collapse table
        if (item.label === 'Dashboard') {
            this.tableStateService.setTableExpanded(false);
            this.router.navigate(item.routerLink, { queryParams: item.queryParams });
            return;
        }

        // Handle other items
        // Execute action if present (e.g., Security Search expansion)
        if (item.action) {
            item.action();
        }

        // Navigate to the route
        if (item.routerLink) {
            this.router.navigate(item.routerLink, { queryParams: item.queryParams });
        }
    }

    get isCollapsed(): boolean {
        if (this.isTableExpanded) return true;
        return this.layoutService.layoutState().staticMenuDesktopInactive === true && this.layoutService.layoutConfig().menuMode === 'static';
    }

    ngOnDestroy() {
        this.tableExpandedSub?.unsubscribe();
        this.activeMenuSub?.unsubscribe();
    }
}
