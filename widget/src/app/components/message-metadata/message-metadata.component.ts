import { Component, input, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { AgentMetrics } from '../../models/chat.models';

@Component({
  selector: 'af-message-metadata',
  standalone: true,
  imports: [DecimalPipe],
  template: `
    <div class="metadata-wrapper">
      <button class="metadata-toggle" (click)="expanded.set(!expanded())">
        <span class="material-icons-round toggle-icon">
          {{ expanded() ? 'expand_less' : 'expand_more' }}
        </span>
        <span class="metadata-summary">
          @if (confidence() !== undefined) {
            <span class="confidence-badge" [class]="confidenceClass()">
              {{ (confidence()! * 100) | number:'1.0-0' }}% confidence
            </span>
          }
          @if (toolsUsed().length > 0) {
            <span class="tools-count">{{ toolsUsed().length }} tools</span>
          }
          @if (metrics()?.duration_seconds; as duration) {
            <span class="duration">{{ duration | number:'1.1-1' }}s</span>
          }
        </span>
      </button>

      @if (expanded()) {
        <div class="metadata-panel af-fade-in">
          @if (toolsUsed().length > 0) {
            <div class="meta-section">
              <span class="meta-label">Tools Used</span>
              <div class="tools-list">
                @for (tool of toolsUsed(); track tool) {
                  <span class="tool-chip">
                    <span class="material-icons-round">build</span>
                    {{ tool }}
                  </span>
                }
              </div>
            </div>
          }

          @if (metrics(); as m) {
            <div class="meta-section">
              <span class="meta-label">Performance</span>
              <div class="meta-grid">
                <div class="meta-item">
                  <span class="meta-value">{{ m.iterations }}</span>
                  <span class="meta-key">Iterations</span>
                </div>
                <div class="meta-item">
                  <span class="meta-value">{{ m.total_tokens | number }}</span>
                  <span class="meta-key">Tokens</span>
                </div>
                <div class="meta-item">
                  <span class="meta-value">\${{ m.total_cost_usd | number:'1.4-4' }}</span>
                  <span class="meta-key">Cost</span>
                </div>
              </div>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: `
    .metadata-wrapper {
      margin-top: 6px;
    }

    .metadata-toggle {
      display: flex;
      align-items: center;
      gap: 4px;
      background: none;
      border: none;
      cursor: pointer;
      padding: 2px 0;
      color: var(--af-text-muted);
      font-size: 0.8em;
      font-family: var(--af-font-family);
      transition: color var(--af-transition);

      &:hover {
        color: var(--af-text-secondary);
      }
    }

    .toggle-icon {
      font-size: 18px;
    }

    .metadata-summary {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .confidence-badge {
      padding: 1px 6px;
      border-radius: 4px;
      font-weight: 500;

      &.high {
        background: rgba(0, 184, 148, 0.12);
        color: var(--af-success);
      }
      &.medium {
        background: rgba(253, 203, 110, 0.15);
        color: var(--af-warning);
      }
      &.low {
        background: rgba(225, 112, 85, 0.12);
        color: var(--af-danger);
      }
    }

    .metadata-panel {
      margin-top: 8px;
      padding: 10px 12px;
      background: var(--af-bg-secondary);
      border-radius: var(--af-radius-sm);
      border: 1px solid var(--af-border);
    }

    .meta-section {
      & + & {
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid var(--af-border);
      }
    }

    .meta-label {
      display: block;
      font-size: 0.75em;
      font-weight: 600;
      color: var(--af-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 6px;
    }

    .tools-list {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }

    .tool-chip {
      display: inline-flex;
      align-items: center;
      gap: 3px;
      padding: 2px 8px;
      background: var(--af-accent-bg);
      color: var(--af-accent);
      border-radius: 4px;
      font-size: 0.82em;
      font-weight: 500;

      .material-icons-round {
        font-size: 13px;
      }
    }

    .meta-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
    }

    .meta-item {
      text-align: center;
    }

    .meta-value {
      display: block;
      font-size: 0.95em;
      font-weight: 600;
      color: var(--af-text-primary);
    }

    .meta-key {
      display: block;
      font-size: 0.72em;
      color: var(--af-text-muted);
      margin-top: 1px;
    }
  `,
})
export class MessageMetadataComponent {
  readonly toolsUsed = input<string[]>([]);
  readonly confidence = input<number | undefined>(undefined);
  readonly metrics = input<AgentMetrics | undefined>(undefined);

  readonly expanded = signal(false);

  confidenceClass(): string {
    const c = this.confidence();
    if (c === undefined) return '';
    if (c >= 0.8) return 'high';
    if (c >= 0.5) return 'medium';
    return 'low';
  }
}
