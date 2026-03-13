import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class AutomationStatusService {
    private activeRuns = 0;
    private readonly runningSubject = new BehaviorSubject<boolean>(false);

    readonly isRunning$ = this.runningSubject.asObservable();

    beginRun(): void {
        this.activeRuns += 1;
        this.sync();
    }

    endRun(): void {
        this.activeRuns = Math.max(0, this.activeRuns - 1);
        this.sync();
    }

    clear(): void {
        this.activeRuns = 0;
        this.sync();
    }

    private sync(): void {
        this.runningSubject.next(this.activeRuns > 0);
    }
}