import { Component, ElementRef } from '@angular/core';
import { AppMenu } from './app.menu';

@Component({
    selector: 'app-sidebar',
    standalone: true,
    imports: [AppMenu],
    template: ` <div class="layout-sidebar">
        <app-menu></app-menu>
    </div>`,
    styles: [`
        .layout-sidebar {
            position: fixed;
            width: 17rem;
            height: calc(100vh - 4rem); /* Adjusted to account for topbar only */
            z-index: 999;
            overflow-y: auto;
            -webkit-user-select: none;
            user-select: none;
            top: 4rem;
            left: 0; /* Remove left gap - stick to left edge */
            transition: transform var(--layout-section-transition-duration), left var(--layout-section-transition-duration);
            background-color: #ffffff;
            border-radius: 0; /* Remove border radius to fill left edge completely */
            padding: 0.5rem 1.5rem;
            border-right: 1px solid var(--surface-border); /* Optional: Add border on right */
        }
    `]
})
export class AppSidebar {
    constructor(public el: ElementRef) {}
}