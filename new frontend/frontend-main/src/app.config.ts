import { provideHttpClient, withFetch } from '@angular/common/http';
import { ApplicationConfig } from '@angular/core';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideRouter, withEnabledBlockingInitialNavigation, withInMemoryScrolling } from '@angular/router';
import Aura from '@primeuix/themes/aura';
import { providePrimeNG } from 'primeng/config';
import { provideEchartsCore } from 'ngx-echarts'; // ✅ ADD THIS
import { appRoutes } from './app.routes';

export const appConfig: ApplicationConfig = {
    providers: [
        provideRouter(
            appRoutes,
            withInMemoryScrolling({
                anchorScrolling: 'enabled',
                scrollPositionRestoration: 'enabled'
            }),
            withEnabledBlockingInitialNavigation()
        ),

        provideHttpClient(withFetch()),

        provideAnimationsAsync(),

        providePrimeNG({
            theme: {
                preset: Aura,
                options: { darkModeSelector: '.app-dark' }
            }
        }),

        // ✅ ECharts provider (SAFE with PrimeNG)
        provideEchartsCore({
            echarts: () => import('echarts')
        })
    ]
};
