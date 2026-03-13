import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { ApiService } from './api.service';

@Injectable({ providedIn: 'root' })
export class NextRunService implements OnDestroy {
    /** Emits the formatted countdown string, e.g. "3H:12M:05S" */
    timer$ = new BehaviorSubject<string>('--:--:--');

    private timerInterval: any = null;
    private nextRunTarget: Date | null = null;
    private refreshTimeout: any = null;
    private pollingInterval: any = null;
    private initialized = false;

    constructor(private apiService: ApiService) {}

    /** Call once from any component — subsequent calls are no-ops */
    init(): void {
        if (this.initialized) return;
        this.initialized = true;
        this.fetchNextRun();

        // Keep countdown aligned with any schedule/job changes made elsewhere in the UI.
        this.pollingInterval = setInterval(() => this.fetchNextRun(), 30000);
    }

    private fetchNextRun(): void {
        this.apiService.getActiveCronJobs().subscribe({
            next: (res) => {
                if (res.jobs && res.jobs.length > 0) {
                    // APScheduler returns ISO timestamps with timezone offset
                    // e.g. "2026-02-15T18:30:00+05:00"
                    // new Date() handles this correctly across timezones
                    const nextRuns = res.jobs
                        .filter((j: any) => j.next_run)
                        .map((j: any) => new Date(j.next_run))
                        .filter((d: Date) => !isNaN(d.getTime()) && d.getTime() > Date.now())
                        .sort((a: Date, b: Date) => a.getTime() - b.getTime());

                    if (nextRuns.length > 0) {
                        this.nextRunTarget = nextRuns[0];
                        this.startCountdown();
                        return;
                    }

                    // Fallback: compute from cron schedule strings
                    const soonest = this.computeNextRunFromSchedules(res.jobs);
                    if (soonest) {
                        this.nextRunTarget = soonest;
                        this.startCountdown();
                        return;
                    }
                }
                this.timer$.next('No jobs');
            },
            error: () => {
                this.timer$.next('N/A');
            }
        });
    }

    private computeNextRunFromSchedules(jobs: any[]): Date | null {
        const now = new Date();
        let soonest: Date | null = null;

        for (const job of jobs) {
            if (!job.schedule || !job.is_active) continue;
            const nextRun = this.getNextCronRun(job.schedule, now);
            if (nextRun && (!soonest || nextRun < soonest)) {
                soonest = nextRun;
            }
        }
        return soonest;
    }

    /**
     * Simple cron parser for "M H * * D" format.
     * Cron jobs on the backend use Asia/Karachi timezone.
     * We construct candidate dates in local time since the cron
     * schedule is authored relative to the server's local TZ
     * (which matches the user's TZ in this deployment).
     */
    private getNextCronRun(cron: string, after: Date): Date | null {
        const parts = cron.trim().split(/\s+/);
        if (parts.length < 5) return null;

        const minute = parseInt(parts[0], 10);
        const hour = parseInt(parts[1], 10);
        if (isNaN(minute) || isNaN(hour)) return null;

        const daysPart = parts[4];
        let allowedDays: number[] | null = null;
        if (daysPart !== '*') {
            allowedDays = daysPart.split(',').map(d => parseInt(d, 10)).filter(d => !isNaN(d));
            if (allowedDays.length === 0) allowedDays = null;
        }

        for (let dayOffset = 0; dayOffset <= 7; dayOffset++) {
            const candidate = new Date(after);
            candidate.setDate(candidate.getDate() + dayOffset);
            candidate.setHours(hour, minute, 0, 0);

            if (candidate.getTime() <= after.getTime()) continue;

            if (allowedDays !== null) {
                const dow = candidate.getDay();
                if (!allowedDays.includes(dow)) continue;
            }

            return candidate;
        }
        return null;
    }

    private startCountdown(): void {
        if (this.timerInterval) clearInterval(this.timerInterval);
        this.updateDisplay();
        this.timerInterval = setInterval(() => this.updateDisplay(), 1000);
    }

    private updateDisplay(): void {
        if (!this.nextRunTarget) {
            this.timer$.next('--:--:--');
            return;
        }

        const diff = this.nextRunTarget.getTime() - Date.now();

        if (diff <= 0) {
            this.timer$.next('Running...');
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
                this.timerInterval = null;
            }
            // Re-fetch after 60s to get the next scheduled run
            this.refreshTimeout = setTimeout(() => this.fetchNextRun(), 60000);
            return;
        }

        const totalSeconds = Math.floor(diff / 1000);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        this.timer$.next(
            `${hours}H:${String(minutes).padStart(2, '0')}M:${String(seconds).padStart(2, '0')}S`
        );
    }

    ngOnDestroy(): void {
        if (this.timerInterval) clearInterval(this.timerInterval);
        if (this.refreshTimeout) clearTimeout(this.refreshTimeout);
        if (this.pollingInterval) clearInterval(this.pollingInterval);
    }
}
