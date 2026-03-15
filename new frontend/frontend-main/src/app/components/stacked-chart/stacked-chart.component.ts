import { Component, OnInit, OnDestroy } from '@angular/core';
import { NgxEchartsDirective } from 'ngx-echarts';
import { CommonModule } from '@angular/common';
import { ApiService, ColorProcessed } from '../../services/api.service';
import { Subscription } from 'rxjs';

@Component({
    selector: 'stacked-chart',
    standalone: true,
    imports: [NgxEchartsDirective, CommonModule],
    templateUrl: './stacked-chart.component.html'
})
export class StackedChartComponent implements OnInit, OnDestroy {
    monthWidth = 120;
    chartWidth = 1440;

    options: any = {};
    isLoading = true;
    hasError = false;
    private dataSub?: Subscription;

    constructor(private apiService: ApiService) {}

    ngOnInit() { this.loadChartData(); }
    ngOnDestroy() { this.dataSub?.unsubscribe(); }
    refreshChart() { this.loadChartData(); }

    // ── data loading ──────────────────────────────────────────────

    private loadChartData() {
        this.isLoading = true;
        this.hasError = false;

        this.dataSub = this.apiService.getColors(0, 500).subscribe({
            next: (response) => {
                this.buildChart(response.colors);
                this.isLoading = false;
            },
            error: (err) => {
                console.error('❌ Error loading colors for chart:', err);
                this.hasError = true;
                this.isLoading = false;
                this.useMockData();
            }
        });
    }

    // ── chart computation ─────────────────────────────────────────

    private buildChart(colors: ColorProcessed[]) {
        if (!colors.length) { this.useMockData(); return; }

        // 1. Group by YYYY-MM and bias
        const monthBiasMap: Map<string, Map<string, number>> = new Map();
        for (const record of colors) {
            if (!record.date) continue;
            const month = record.date.toString().substring(0, 7);
            const bias  = (record.bias || 'UNKNOWN').trim().toUpperCase();
            if (!monthBiasMap.has(month)) monthBiasMap.set(month, new Map());
            const bm = monthBiasMap.get(month)!;
            bm.set(bias, (bm.get(bias) ?? 0) + 1);
        }

        // 2. Sort chronologically, keep last 12
        const sortedMonths = [...monthBiasMap.keys()].sort().slice(-12);
        if (!sortedMonths.length) { this.useMockData(); return; }

        const monthLabels = sortedMonths.map((m) => {
            const [y, mo] = m.split('-');
            return new Date(+y, +mo - 1).toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
        });

        // 3. Compute % per bias, raw counts, and total per month
        const monthTotals: number[] = [];
        const monthCounts: { [bias: string]: number }[] = [];
        const monthPercentages: { [bias: string]: number }[] = sortedMonths.map((month) => {
            const bm    = monthBiasMap.get(month)!;
            const total = [...bm.values()].reduce((a, b) => a + b, 0) || 1;
            monthTotals.push(total);
            const cnt: { [bias: string]: number } = {};
            const pct: { [bias: string]: number } = {};
            bm.forEach((count, bias) => { cnt[bias] = count; pct[bias] = (count / total) * 100; });
            monthCounts.push(cnt);
            return pct;
        });

        // 4. Rank biases: highest avg % → bottom of stack
        const biasAverages: { [bias: string]: number } = {};
        monthPercentages.forEach((mp) =>
            Object.entries(mp).forEach(([bias, pct]) => {
                biasAverages[bias] = (biasAverages[bias] ?? 0) + pct;
            })
        );
        const sortedBiases = Object.entries(biasAverages)
            .map(([bias, sum]) => ({ bias, avg: sum / monthPercentages.length }))
            .sort((a, b) => b.avg - a.avg)
            .map((x) => x.bias);

        // 5. Build stacked series
        const series = sortedBiases.map((bias, index) => ({
            name: bias,
            type: 'bar',
            stack: 'total',
            barMaxWidth: 48,
            data: monthPercentages.map((mp) => parseFloat((mp[bias] ?? 0).toFixed(2))),
            itemStyle: {
                color: this.lightenColor('#334155', index * 30),
                borderColor: '#ffffff',
                borderWidth: 1
            },
            emphasis: { disabled: true }
        }));

        this.options = this.buildOptions(monthLabels, sortedBiases, series, monthTotals, monthCounts);
    }

    // ── shared ECharts config builder ─────────────────────────────

    private buildOptions(months: string[], biasNames: string[], series: any[], monthTotals: number[], monthCounts: { [bias: string]: number }[] = []): any {
        // Invisible series stacked on top — its sole purpose is to render
        // the "total records" label above every bar (value = 0 so bar height unchanged)
        const labelSeries = {
            name: '__total__',
            type: 'bar',
            stack: 'total',
            barMaxWidth: 48,
            data: monthTotals.map(() => 0),
            itemStyle: { color: 'transparent', borderColor: 'transparent' },
            emphasis: { disabled: true },
            label: {
                show: true,
                position: 'top',
                color: '#374151',
                fontSize: 11,
                fontWeight: 500,
                fontFamily: 'Poppins, sans-serif',
                formatter: (params: any) => this.formatK(monthTotals[params.dataIndex])
            },
            tooltip: { show: false }
        };

        return {
            tooltip: {
                trigger: 'item',
                backgroundColor: '#ffffff',
                borderColor: '#e5e7eb',
                borderWidth: 1,
                padding: [12, 16],
                extraCssText: 'box-shadow:0 4px 20px rgba(0,0,0,0.12);border-radius:10px;',
                textStyle: { color: '#111827', fontSize: 13 },
                formatter: (params: any) => {
                    // Suppress tooltip for the invisible label series
                    if (params.seriesName === '__total__') return '';

                    const idx   = params.dataIndex;
                    const month = months[idx];

                    // Collect all bias counts for this month
                    const counts = monthCounts[idx] ?? {};
                    const rows = series
                        .filter((s) => s.name !== '__total__')
                        .map((s) => ({ name: s.name, count: counts[s.name] ?? 0, color: s.itemStyle.color }))
                        .sort((a, b) => b.count - a.count)
                        .filter((x) => x.count > 0)
                        .map(
                            (x) =>
                                `<div style="display:flex;align-items:center;justify-content:space-between;` +
                                `gap:28px;margin:5px 0;">` +
                                `<div style="display:flex;align-items:center;gap:9px;">` +
                                `<span style="display:inline-block;width:13px;height:13px;border-radius:3px;` +
                                `background:${x.color};flex-shrink:0;"></span>` +
                                `<span style="color:#6b7280;">${x.name}</span>` +
                                `</div>` +
                                `<span style="font-weight:700;color:#111827;">${x.count.toLocaleString()}</span>` +
                                `</div>`
                        )
                        .join('');

                    return (
                        `<div style="min-width:210px;">` +
                        `<div style="font-weight:700;font-size:14px;color:#111827;` +
                        `margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #f3f4f6;">${month}</div>` +
                        rows +
                        `</div>`
                    );
                }
            },
            grid: { left: 48, right: 24, top: 32, bottom: 8, containLabel: true },
            xAxis: {
                type: 'category',
                data: months,
                axisLine: { show: false },
                axisTick: { show: false },
                axisLabel: { color: '#6B7280', fontSize: 11, margin: 8, show: true }
            },
            yAxis: { type: 'value', max: 100, show: false },
            series: [...series, labelSeries]
        };
    }

    // ── mock fallback ─────────────────────────────────────────────

    private useMockData() {
        const months     = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const mockTotals = [1200, 2300, 1800, 2700, 3100, 2500, 4200, 3800, 2900, 1500, 3300, 4800];
        const mockData   = [
            { BUY_BIAS: 50, SELL_BIAS: 30, HOLD: 20 }, { BUY_BIAS: 55, SELL_BIAS: 25, HOLD: 20 },
            { BUY_BIAS: 45, SELL_BIAS: 35, HOLD: 20 }, { BUY_BIAS: 52, SELL_BIAS: 28, HOLD: 20 },
            { BUY_BIAS: 48, SELL_BIAS: 32, HOLD: 20 }, { BUY_BIAS: 51, SELL_BIAS: 29, HOLD: 20 },
            { BUY_BIAS: 54, SELL_BIAS: 26, HOLD: 20 }, { BUY_BIAS: 49, SELL_BIAS: 31, HOLD: 20 },
            { BUY_BIAS: 53, SELL_BIAS: 27, HOLD: 20 }, { BUY_BIAS: 50, SELL_BIAS: 30, HOLD: 20 },
            { BUY_BIAS: 55, SELL_BIAS: 25, HOLD: 20 }, { BUY_BIAS: 47, SELL_BIAS: 33, HOLD: 20 }
        ];

        const biasAverages: { [b: string]: number } = {};
        mockData.forEach((m) =>
            Object.entries(m).forEach(([b, v]) => { biasAverages[b] = (biasAverages[b] ?? 0) + v; })
        );
        const biasOrder = Object.entries(biasAverages)
            .map(([bias, sum]) => ({ bias, avg: sum / mockData.length }))
            .sort((a, b) => b.avg - a.avg)
            .map((x) => x.bias);

        const series = biasOrder.map((bias, index) => ({
            name: bias,
            type: 'bar',
            stack: 'total',
            barMaxWidth: 48,
            data: mockData.map((m) => (m as any)[bias] ?? 0),
            itemStyle: { color: this.lightenColor('#334155', index * 30), borderColor: '#ffffff', borderWidth: 1 },
            emphasis: { disabled: true }
        }));

        // Derive counts from percentages × monthly totals for mock data
        const mockCounts: { [bias: string]: number }[] = mockData.map((m, i) =>
            Object.fromEntries(Object.entries(m).map(([bias, pct]) => [bias, Math.round((pct / 100) * mockTotals[i])]))
        );

        this.options    = this.buildOptions(months, biasOrder, series, mockTotals, mockCounts);
    }

    // ── helpers ───────────────────────────────────────────────────

    /** Format a raw count as "1K", "2.5K", "12K" etc. */
    private formatK(n: number): string {
        if (n >= 1000) {
            const k = n / 1000;
            return (k % 1 === 0 ? k.toFixed(0) : k.toFixed(1)) + 'K';
        }
        return n.toString();
    }

    /** Lightens `hex` colour towards white by `percent` (0–100). */
    private lightenColor(hex: string, percent: number): string {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        const f = Math.min(percent, 100) / 100;
        const nr = Math.round(r + (255 - r) * f);
        const ng = Math.round(g + (255 - g) * f);
        const nb = Math.round(b + (255 - b) * f);
        return `#${nr.toString(16).padStart(2, '0')}${ng.toString(16).padStart(2, '0')}${nb.toString(16).padStart(2, '0')}`;
    }
}
