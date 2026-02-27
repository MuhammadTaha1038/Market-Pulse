import { Component, HostBinding, Input } from '@angular/core';
import { NavigationEnd, Router, RouterModule } from '@angular/router';
import { animate, state, style, transition, trigger } from '@angular/animations';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { CommonModule } from '@angular/common';
import { RippleModule } from 'primeng/ripple';
import { MenuItem } from 'primeng/api';
import { LayoutService } from '../service/layout.service';
import { MenuActiveService } from '../service/menu-active.service';
import { TableStateService } from '../../components/home/table-state.service';
//comment
// Extend MenuItem to support SVG icons
interface MenuItemWithSvg extends MenuItem {
    svgIcon?: string;
}

@Component({
    // eslint-disable-next-line @angular-eslint/component-selector
    selector: '[app-menuitem]',
    imports: [CommonModule, RouterModule, RippleModule],
    template: `
        <ng-container>
            <div *ngIf="root && item.visible !== false" class="layout-menuitem-root-text">{{ item.label }}</div>
            <a *ngIf="(!item.routerLink || item.items) && item.visible !== false" [attr.href]="item.url" (click)="itemClick($event)" [ngClass]="item.styleClass" [attr.target]="item.target" tabindex="0" pRipple>
                <!-- SVG Icon -->
                <img *ngIf="itemWithSvg.svgIcon" [src]="itemWithSvg.svgIcon" class="layout-menuitem-icon svg-icon" alt="" />
                <!-- Fallback to icon font if no SVG -->
                <i *ngIf="!itemWithSvg.svgIcon && item.icon" [ngClass]="item.icon" class="layout-menuitem-icon"></i>
                <span class="layout-menuitem-text">{{ item.label }}</span>
                <i class="pi pi-fw pi-angle-down layout-submenu-toggler" *ngIf="item.items"></i>
            </a>
            <a
                *ngIf="item.routerLink && !item.items && item.visible !== false"
                (click)="itemClick($event)"
                [ngClass]="item.styleClass"
                [routerLink]="item.routerLink"
                [class.active-route]="item.label === activeMenuItem"
                [fragment]="item.fragment"
                [queryParamsHandling]="item.queryParamsHandling"
                [preserveFragment]="item.preserveFragment"
                [skipLocationChange]="item.skipLocationChange"
                [replaceUrl]="item.replaceUrl"
                [state]="item.state"
                [queryParams]="item.queryParams"
                [attr.target]="item.target"
                tabindex="0"
                pRipple
            >
                <!-- SVG Icon -->
                <img *ngIf="itemWithSvg.svgIcon" [src]="itemWithSvg.svgIcon" class="layout-menuitem-icon svg-icon" alt="" />
                <!-- Fallback to icon font if no SVG -->
                <i *ngIf="!itemWithSvg.svgIcon && item.icon" [ngClass]="item.icon" class="layout-menuitem-icon"></i>
                <span class="layout-menuitem-text">{{ item.label }}</span>
                <i class="pi pi-fw pi-angle-down layout-submenu-toggler" *ngIf="item.items"></i>
            </a>

            <!-- Parent menu item with subitems -->
            <a *ngIf="!item.routerLink && item.items && item.visible !== false" (click)="itemClick($event)" [ngClass]="item.styleClass" [class.active-route]="isParentActive()" tabindex="0" pRipple>
                <!-- SVG Icon -->
                <img *ngIf="itemWithSvg.svgIcon" [src]="itemWithSvg.svgIcon" class="layout-menuitem-icon svg-icon" alt="" />
                <!-- Fallback to icon font if no SVG -->
                <i *ngIf="!itemWithSvg.svgIcon && item.icon" [ngClass]="item.icon" class="layout-menuitem-icon"></i>
                <span class="layout-menuitem-text">{{ item.label }}</span>
                <i class="pi pi-fw pi-angle-down layout-submenu-toggler" *ngIf="item.items"></i>
            </a>

            <ul *ngIf="item.items && item.visible !== false" [@children]="submenuAnimation">
                <ng-template ngFor let-child let-i="index" [ngForOf]="item.items">
                    <li app-menuitem [item]="child" [index]="i" [parentKey]="key" [class]="child['badgeClass']"></li>
                </ng-template>
            </ul>
        </ng-container>
    `,
    styles: [
        `
            .svg-icon {
                width: 1.25rem;
                height: 1.25rem;
                object-fit: contain;
            }
            .layout-menuitem-text {
                font-family: 'Degular Display', sans-serif;
                font-size: 16px;
                font-weight: 500;
            }

            :host a.active-route .layout-menuitem-text {
                font-weight: 700;
            }
        `
    ],
    animations: [
        trigger('children', [
            state(
                'collapsed',
                style({
                    height: '0'
                })
            ),
            state(
                'expanded',
                style({
                    height: '*'
                })
            ),
            transition('collapsed <=> expanded', animate('400ms cubic-bezier(0.86, 0, 0.07, 1)'))
        ])
    ],
    providers: [LayoutService]
})
export class AppMenuitem {
    @Input() item!: MenuItem;

    @Input() index!: number;

    @Input() @HostBinding('class.layout-root-menuitem') root!: boolean;

    @Input() parentKey!: string;

    active = false;
    activeMenuItem: string = 'Dashboard';
    isTableExpanded: boolean = false;

    menuSourceSubscription: Subscription;

    menuResetSubscription: Subscription;
    activeMenuSubscription!: Subscription;
    tableExpandedSubscription!: Subscription;

    key: string = '';

    // Getter to access svgIcon property
    get itemWithSvg(): MenuItemWithSvg {
        return this.item as MenuItemWithSvg;
    }

    constructor(
        public router: Router,
        private layoutService: LayoutService,
        private menuActiveService: MenuActiveService,
        private tableStateService: TableStateService
    ) {
        this.menuSourceSubscription = this.layoutService.menuSource$.subscribe((value) => {
            Promise.resolve(null).then(() => {
                if (value.routeEvent) {
                    this.active = value.key === this.key || value.key.startsWith(this.key + '-') ? true : false;
                } else {
                    if (value.key !== this.key && !value.key.startsWith(this.key + '-')) {
                        this.active = false;
                    }
                }
            });
        });

        this.menuResetSubscription = this.layoutService.resetSource$.subscribe(() => {
            this.active = false;
        });

        this.router.events.pipe(filter((event) => event instanceof NavigationEnd)).subscribe((params) => {
            if (this.item.routerLink) {
                this.updateActiveStateFromRoute();
            }
        });
    }

    ngOnInit() {
        this.key = this.parentKey ? this.parentKey + '-' + this.index : String(this.index);

        // Subscribe to active menu item changes
        this.activeMenuSubscription = this.menuActiveService.activeMenuItem$.subscribe((item) => {
            this.activeMenuItem = item;
        });

        // Subscribe to table expansion state
        this.tableExpandedSubscription = this.tableStateService.isTableExpanded$.subscribe((expanded) => {
            this.isTableExpanded = expanded;
        });

        if (this.item.routerLink) {
            this.updateActiveStateFromRoute();
        }
    }

    updateActiveStateFromRoute() {
        let activeRoute = this.router.isActive(this.item.routerLink[0], { paths: 'exact', queryParams: 'ignored', matrixParams: 'ignored', fragment: 'ignored' });

        if (activeRoute) {
            this.layoutService.onMenuStateChange({ key: this.key, routeEvent: true });
        }
    }

    itemClick(event: Event) {
        // avoid processing disabled items
        if (this.item.disabled) {
            event.preventDefault();
            return;
        }

        // Set this item as active in the menu
        if (this.item.label) {
            this.menuActiveService.setActiveMenuItem(this.item.label);
        }

        // Reset table expansion when clicking Dashboard
        if (this.item.label === 'Dashboard' && this.isTableExpanded) {
            this.tableStateService.setTableExpanded(false);
        }

        // execute command
        if (this.item.command) {
            this.item.command({ originalEvent: event, item: this.item });
        }

        // toggle active state
        if (this.item.items) {
            this.active = !this.active;
        }

        this.layoutService.onMenuStateChange({ key: this.key });
    }

    get submenuAnimation() {
        return this.root ? 'expanded' : this.active ? 'expanded' : 'collapsed';
    }

    isParentActive(): boolean {
        // Check if this parent's label matches active item
        if (this.item.label === this.activeMenuItem) {
            return true;
        }
        // Check if any child items match the active item
        if (this.item.items) {
            return this.item.items.some((child) => (child as MenuItemWithSvg).label === this.activeMenuItem);
        }
        return false;
    }

    @HostBinding('class.active-menuitem')
    get activeClass() {
        return this.active && !this.root;
    }

    ngOnDestroy() {
        if (this.menuSourceSubscription) {
            this.menuSourceSubscription.unsubscribe();
        }

        if (this.menuResetSubscription) {
            this.menuResetSubscription.unsubscribe();
        }

        if (this.activeMenuSubscription) {
            this.activeMenuSubscription.unsubscribe();
        }

        if (this.tableExpandedSubscription) {
            this.tableExpandedSubscription.unsubscribe();
        }
    }
}
