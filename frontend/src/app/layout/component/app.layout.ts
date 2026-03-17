import { Component, Renderer2, ViewChild, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavigationEnd, Router, RouterModule } from '@angular/router';
import { filter, Subscription } from 'rxjs';
import { AppTopbar } from './app.topbar';
import { AppSidebar } from './app.sidebar';
import { LayoutService } from '../service/layout.service';
import { TableStateService } from '../../components/home/table-state.service'; // Adjust path as needed


@Component({
    selector: 'app-layout',
    standalone: true,
    imports: [CommonModule, AppTopbar, AppSidebar, RouterModule],
    template: `<div class="layout-wrapper" [ngClass]="containerClass">
        <app-topbar></app-topbar>
        <app-sidebar></app-sidebar>
        <div
            class="layout-main-container"
            [class.layout-main-container-full]="isTableExpanded"
            [style.marginLeft]="getMainContainerMargin()"
        >
            <div class="layout-main">
                <router-outlet></router-outlet>
            </div>
        </div>
        <div class="layout-mask animate-fadein"></div>
    </div> `,
    styles: [
        `
            .layout-main-container {
                margin-left: 14rem;
                transition: margin-left 0.3s ease;
            }

            .layout-main-container-full {
                margin-left: 4.5rem !important;
                width: calc(100% - 4.5rem) !important;
            }

            /* When sidebar is collapsed - show icon-only sidebar */
            .layout-static-inactive .layout-main-container {
                margin-left: 4.5rem;
            }

            .layout-overlay .layout-main-container {
                margin-left: 0;
            }

        `
    ]
})
export class AppLayout implements OnInit, OnDestroy {
    overlayMenuOpenSubscription: Subscription;
    tableExpansionSubscription: Subscription = new Subscription();
    isTableExpanded: boolean = false;

    menuOutsideClickListener: any;

    @ViewChild(AppSidebar) appSidebar!: AppSidebar;
    @ViewChild(AppTopbar) appTopBar!: AppTopbar;

    constructor(
        public layoutService: LayoutService,
        public renderer: Renderer2,
        public router: Router,
        private tableStateService: TableStateService
    ) {
        this.overlayMenuOpenSubscription = this.layoutService.overlayOpen$.subscribe(() => {
            if (!this.menuOutsideClickListener) {
                this.menuOutsideClickListener = this.renderer.listen('document', 'click', (event) => {
                    if (this.isOutsideClicked(event)) {
                        this.hideMenu();
                    }
                });
            }

            if (this.layoutService.layoutState().staticMenuMobileActive) {
                this.blockBodyScroll();
            }
        });

        this.router.events.pipe(filter((event) => event instanceof NavigationEnd)).subscribe(() => {
            this.hideMenu();
        });
    }

    ngOnInit() {
        this.tableExpansionSubscription = this.tableStateService.isTableExpanded$.subscribe((expanded) => {
            this.isTableExpanded = expanded;
        });
    }

    isOutsideClicked(event: MouseEvent) {
        const sidebarEl = document.querySelector('.layout-sidebar');
        const topbarEl = document.querySelector('.layout-menu-button');
        const eventTarget = event.target as Node;

        return !(sidebarEl?.isSameNode(eventTarget) || sidebarEl?.contains(eventTarget) || topbarEl?.isSameNode(eventTarget) || topbarEl?.contains(eventTarget));
    }

    hideMenu() {
        this.layoutService.layoutState.update((prev) => ({ ...prev, overlayMenuActive: false, staticMenuMobileActive: false, menuHoverActive: false }));
        if (this.menuOutsideClickListener) {
            this.menuOutsideClickListener();
            this.menuOutsideClickListener = null;
        }
        this.unblockBodyScroll();
    }

    blockBodyScroll(): void {
        if (document.body.classList) {
            document.body.classList.add('blocked-scroll');
        } else {
            document.body.className += ' blocked-scroll';
        }
    }

    unblockBodyScroll(): void {
        if (document.body.classList) {
            document.body.classList.remove('blocked-scroll');
        } else {
            document.body.className = document.body.className.replace(new RegExp('(^|\\b)' + 'blocked-scroll'.split(' ').join('|') + '(\\b|$)', 'gi'), ' ');
        }
    }

    getMainContainerMargin(): string {
        if (this.isTableExpanded) return '4.5rem';
        if (this.layoutService.layoutConfig().menuMode !== 'static') return '0';
        return this.layoutService.layoutState().staticMenuDesktopInactive ? '4.5rem' : '15rem';
    }

    get containerClass() {
        return {
            'layout-overlay': this.layoutService.layoutConfig().menuMode === 'overlay',
            'layout-static': this.layoutService.layoutConfig().menuMode === 'static',
            'layout-static-inactive': this.layoutService.layoutState().staticMenuDesktopInactive && this.layoutService.layoutConfig().menuMode === 'static',
            'layout-overlay-active': this.layoutService.layoutState().overlayMenuActive,
            'layout-mobile-active': this.layoutService.layoutState().staticMenuMobileActive
        };
    }

    ngOnDestroy() {
        if (this.overlayMenuOpenSubscription) {
            this.overlayMenuOpenSubscription.unsubscribe();
        }

        if (this.tableExpansionSubscription) {
            this.tableExpansionSubscription.unsubscribe();
        }

        if (this.menuOutsideClickListener) {
            this.menuOutsideClickListener();
        }
    }
}
