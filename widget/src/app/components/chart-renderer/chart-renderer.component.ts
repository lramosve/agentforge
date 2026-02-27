import {
  Component,
  ElementRef,
  OnDestroy,
  afterNextRender,
  input,
  signal,
} from '@angular/core';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

interface ChartConfig {
  title: string;
  type: 'pie' | 'bar';
  labels: string[];
  datasets: { label: string; data: number[]; backgroundColor?: string[] }[];
  indexAxis?: 'x' | 'y';
}

@Component({
  selector: 'af-chart-renderer',
  standalone: true,
  template: `
    @for (chart of charts(); track $index) {
      <div class="chart-card">
        <h4 class="chart-title">{{ chart.title }}</h4>
        <div class="chart-canvas-wrapper">
          <canvas></canvas>
        </div>
      </div>
    }
  `,
  styles: `
    :host {
      display: block;
      margin-top: 8px;
    }

    .chart-card {
      border: 1px solid var(--af-border);
      border-radius: var(--af-radius-sm);
      padding: 12px;
      margin-bottom: 8px;
      background: var(--af-bg-secondary);
    }

    .chart-title {
      font-size: 0.82em;
      font-weight: 600;
      color: var(--af-text-primary);
      margin-bottom: 8px;
    }

    .chart-canvas-wrapper {
      position: relative;
      max-height: 280px;
    }

    canvas {
      width: 100% !important;
      max-height: 260px;
    }
  `,
})
export class ChartRendererComponent implements OnDestroy {
  readonly toolResults = input<any[]>([]);
  readonly isDark = input(false);

  readonly charts = signal<ChartConfig[]>([]);
  private chartInstances: Chart[] = [];
  private el: ElementRef;

  constructor(el: ElementRef) {
    this.el = el;
    afterNextRender(() => {
      this.buildCharts();
    });
  }

  ngOnDestroy(): void {
    this.chartInstances.forEach((c) => c.destroy());
  }

  private buildCharts(): void {
    const results = this.toolResults() ?? [];
    const configs: ChartConfig[] = [];

    for (const result of results) {
      if (!result || result.status !== 'success' || !result.data) continue;
      const data = result.data;

      // Portfolio analysis — sector allocation → pie chart
      if (data.sector_allocation && Array.isArray(data.sector_allocation)) {
        const sectors = data.sector_allocation.slice(0, 8);
        configs.push({
          title: 'Sector Allocation',
          type: 'pie',
          labels: sectors.map((s: any) => s.sector || s.name || 'Unknown'),
          datasets: [{
            label: 'Allocation %',
            data: sectors.map((s: any) => s.allocation_percent ?? s.percentage ?? s.value ?? 0),
            backgroundColor: this.getColorPalette(sectors.length),
          }],
        });
      }

      // Portfolio analysis — top holdings → horizontal bar
      if (data.top_holdings && Array.isArray(data.top_holdings)) {
        const holdings = data.top_holdings.slice(0, 10);
        configs.push({
          title: 'Top Holdings',
          type: 'bar',
          indexAxis: 'y',
          labels: holdings.map((h: any) => h.name || h.symbol || 'Unknown'),
          datasets: [{
            label: 'Allocation %',
            data: holdings.map((h: any) => h.allocation_percent ?? h.percentage ?? h.value ?? 0),
            backgroundColor: this.getColorPalette(holdings.length),
          }],
        });
      }

      // Benchmark comparison → grouped bar
      if (data.benchmarks && Array.isArray(data.benchmarks)) {
        const benchmarks = data.benchmarks;
        const portfolioReturn = data.portfolio_return ?? data.portfolio_return_percent ?? 0;
        configs.push({
          title: 'Portfolio vs Benchmarks',
          type: 'bar',
          labels: benchmarks.map((b: any) => b.name || b.symbol || 'Benchmark'),
          datasets: [
            {
              label: 'Portfolio',
              data: benchmarks.map(() => portfolioReturn),
              backgroundColor: ['rgba(99, 102, 241, 0.7)'],
            },
            {
              label: 'Benchmark',
              data: benchmarks.map((b: any) => b.return_percent ?? b.return ?? 0),
              backgroundColor: ['rgba(168, 162, 158, 0.7)'],
            },
          ],
        });
      }
    }

    this.charts.set(configs);

    // Render after DOM updates
    setTimeout(() => this.renderCanvases(), 0);
  }

  private renderCanvases(): void {
    this.chartInstances.forEach((c) => c.destroy());
    this.chartInstances = [];

    const canvases = this.el.nativeElement.querySelectorAll('canvas');
    const configs = this.charts();
    const textColor = this.isDark() ? '#a8a29e' : '#57534e';

    configs.forEach((cfg, i) => {
      if (!canvases[i]) return;

      const chart = new Chart(canvases[i], {
        type: cfg.type,
        data: {
          labels: cfg.labels,
          datasets: cfg.datasets,
        },
        options: {
          indexAxis: cfg.indexAxis ?? 'x',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: cfg.type === 'pie' || cfg.datasets.length > 1,
              labels: { color: textColor, font: { size: 11 } },
            },
          },
          scales: cfg.type === 'pie' ? {} : {
            x: { ticks: { color: textColor, font: { size: 10 } }, grid: { display: false } },
            y: { ticks: { color: textColor, font: { size: 10 } }, grid: { color: this.isDark() ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' } },
          },
        },
      });
      this.chartInstances.push(chart);
    });
  }

  private getColorPalette(count: number): string[] {
    const palette = [
      'rgba(99, 102, 241, 0.7)',
      'rgba(244, 114, 182, 0.7)',
      'rgba(34, 197, 94, 0.7)',
      'rgba(251, 146, 60, 0.7)',
      'rgba(14, 165, 233, 0.7)',
      'rgba(168, 85, 247, 0.7)',
      'rgba(234, 179, 8, 0.7)',
      'rgba(239, 68, 68, 0.7)',
      'rgba(20, 184, 166, 0.7)',
      'rgba(107, 114, 128, 0.7)',
    ];
    return Array.from({ length: count }, (_, i) => palette[i % palette.length]);
  }
}
