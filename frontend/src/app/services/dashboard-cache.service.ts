import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { TableRow } from '../components/custom-table/custom-table.component';
import { ApiService } from './api.service';

interface HomeCachePayload {
    rows: TableRow[];
}

interface ChartCachePayload {
    rows: any[];
}

interface CacheEnvelope<T> {
    version: string;
    cloId?: string;
    updatedAt: number;
    payload: T;
}

@Injectable({
    providedIn: 'root'
})
export class DashboardCacheService {
    private readonly homeKey = 'dashboard_home_cache_v1';
    private readonly chartKey = 'dashboard_chart_cache_v1';
    private readonly versionKey = 'dashboard_data_version_v1';
    private readonly pollMs = 15000;
    private pollHandle?: ReturnType<typeof setInterval>;
    private currentVersion: string | null = null;
    private memoryHomeCache: CacheEnvelope<HomeCachePayload> | null = null;
    private memoryChartCache: CacheEnvelope<ChartCachePayload> | null = null;

    readonly versionChanged$ = new Subject<string>();

    constructor(private apiService: ApiService) {
        this.currentVersion = this.readStoredVersion() || this.seedVersionFromCache();
    }

    getHomeRows(version: string, cloId?: string): TableRow[] | null {
        if (
            this.memoryHomeCache &&
            this.memoryHomeCache.version === version &&
            this.normalizeCloId(this.memoryHomeCache.cloId) === this.normalizeCloId(cloId)
        ) {
            return this.memoryHomeCache.payload?.rows || null;
        }

        const env = this.readEnvelope<HomeCachePayload>(this.homeKey);
        if (!env || env.version !== version || this.normalizeCloId(env.cloId) !== this.normalizeCloId(cloId)) {
            return null;
        }
        this.memoryHomeCache = env;
        return env.payload?.rows || null;
    }

    getLatestHomeRows(cloId?: string): TableRow[] | null {
        if (
            this.memoryHomeCache &&
            this.normalizeCloId(this.memoryHomeCache.cloId) === this.normalizeCloId(cloId)
        ) {
            return this.memoryHomeCache.payload?.rows || null;
        }

        const env = this.readEnvelope<HomeCachePayload>(this.homeKey);
        if (!env || this.normalizeCloId(env.cloId) !== this.normalizeCloId(cloId)) {
            return null;
        }
        this.memoryHomeCache = env;
        return env.payload?.rows || null;
    }

    getLatestHomeVersion(cloId?: string): string | null {
        if (
            this.memoryHomeCache &&
            this.normalizeCloId(this.memoryHomeCache.cloId) === this.normalizeCloId(cloId)
        ) {
            return this.memoryHomeCache.version || null;
        }

        const env = this.readEnvelope<HomeCachePayload>(this.homeKey);
        if (!env || this.normalizeCloId(env.cloId) !== this.normalizeCloId(cloId)) {
            return null;
        }
        this.memoryHomeCache = env;
        return env.version || null;
    }

    saveHomeRows(version: string, rows: TableRow[], cloId?: string): void {
        const env: CacheEnvelope<HomeCachePayload> = {
            version,
            cloId: this.normalizeCloId(cloId),
            updatedAt: Date.now(),
            payload: { rows }
        };
        this.memoryHomeCache = env;
        this.writeEnvelope(this.homeKey, env);
    }

    getChartRows(version: string): any[] | null {
        if (this.memoryChartCache && this.memoryChartCache.version === version) {
            return this.memoryChartCache.payload?.rows || null;
        }

        const env = this.readEnvelope<ChartCachePayload>(this.chartKey);
        if (!env || env.version !== version) {
            return null;
        }
        this.memoryChartCache = env;
        return env.payload?.rows || null;
    }

    getLatestChartRows(): any[] | null {
        if (this.memoryChartCache) {
            return this.memoryChartCache.payload?.rows || null;
        }

        const env = this.readEnvelope<ChartCachePayload>(this.chartKey);
        this.memoryChartCache = env;
        return env?.payload?.rows || null;
    }

    getLatestChartVersion(): string | null {
        if (this.memoryChartCache) {
            return this.memoryChartCache.version || null;
        }

        const env = this.readEnvelope<ChartCachePayload>(this.chartKey);
        this.memoryChartCache = env;
        return env?.version || null;
    }

    startVersionMonitor(): void {
        if (this.pollHandle) {
            return;
        }

        this.checkVersion(false);
        this.pollHandle = setInterval(() => this.checkVersion(true), this.pollMs);
    }

    getCurrentVersion(): string | null {
        return this.currentVersion;
    }

    setKnownVersion(version: string | null): void {
        this.currentVersion = version || null;
        try {
            if (this.currentVersion) {
                localStorage.setItem(this.versionKey, this.currentVersion);
            }
        } catch {
            // Ignore localStorage failures for version metadata.
        }
    }

    hasVersionChanged(cachedVersion: string | null | undefined): boolean {
        if (!cachedVersion || !this.currentVersion) {
            return false;
        }
        return cachedVersion !== this.currentVersion;
    }

    saveChartRows(version: string, rows: any[]): void {
        const env: CacheEnvelope<ChartCachePayload> = {
            version,
            updatedAt: Date.now(),
            payload: { rows }
        };
        this.memoryChartCache = env;
        this.writeEnvelope(this.chartKey, env);
    }

    clearAll(): void {
        localStorage.removeItem(this.homeKey);
        localStorage.removeItem(this.chartKey);
        localStorage.removeItem(this.versionKey);
        this.currentVersion = null;
        this.memoryHomeCache = null;
        this.memoryChartCache = null;
    }

    private readEnvelope<T>(key: string): CacheEnvelope<T> | null {
        try {
            const raw = localStorage.getItem(key);
            if (!raw) return null;
            return JSON.parse(raw) as CacheEnvelope<T>;
        } catch {
            return null;
        }
    }

    private writeEnvelope<T>(key: string, envelope: CacheEnvelope<T>): void {
        try {
            localStorage.setItem(key, JSON.stringify(envelope));
        } catch {
            // Ignore cache write failures (e.g. storage quota).
        }
    }

    private normalizeCloId(cloId?: string): string {
        return String(cloId || '').trim().toLowerCase();
    }

    private checkVersion(emitChange: boolean): void {
        this.apiService.getDashboardDataVersion().subscribe({
            next: (response) => {
                const nextVersion = String(response?.version || '').trim();
                if (!nextVersion) {
                    return;
                }

                const previousVersion = this.currentVersion;
                this.setKnownVersion(nextVersion);

                if (emitChange && previousVersion && previousVersion !== nextVersion) {
                    this.versionChanged$.next(nextVersion);
                }
            },
            error: () => {
                // Ignore version polling failures; keep showing saved data.
            }
        });
    }

    private readStoredVersion(): string | null {
        try {
            return localStorage.getItem(this.versionKey);
        } catch {
            return null;
        }
    }

    private seedVersionFromCache(): string | null {
        const homeEnv = this.readEnvelope<HomeCachePayload>(this.homeKey);
        if (homeEnv?.version) {
            return homeEnv.version;
        }
        const chartEnv = this.readEnvelope<ChartCachePayload>(this.chartKey);
        return chartEnv?.version || null;
    }
}
