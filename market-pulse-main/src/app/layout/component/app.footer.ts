import { Component } from '@angular/core';

@Component({
    standalone: true,
    selector: 'app-footer',
    template: `<div class="layout-footer">
        All Rights Reserved By 
        <a href="https://www.linkedin.com/in/zahedhasan" target="_blank" rel="noopener noreferrer" class="text-primary font-bold hover:underline">MarketPulse</a>
    </div>`
})
export class AppFooter {}