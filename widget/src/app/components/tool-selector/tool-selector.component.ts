import { Component, HostListener, inject, signal } from '@angular/core';
import { AgentService } from '../../services/agent.service';

@Component({
  selector: 'af-tool-selector',
  standalone: true,
  template: `
    <div class="tool-selector">
      <button
        class="tool-btn"
        [disabled]="agent.isLoading() || !agent.toolsLoaded()"
        (click)="toggle($event)"
        title="Select a tool"
      >
        <span class="material-icons-round">handyman</span>
      </button>

      @if (isOpen()) {
        <div class="dropdown">
          @for (tool of agent.tools(); track tool.name) {
            <button class="dropdown-item" (click)="selectTool(tool.name)">
              <span class="tool-name">{{ formatName(tool.name) }}</span>
              <span class="tool-desc">{{ truncateDesc(tool.description) }}</span>
            </button>
          }
        </div>
      }
    </div>
  `,
  styles: `
    .tool-selector {
      position: relative;
    }

    .tool-btn {
      flex-shrink: 0;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      border: 1px solid var(--af-border);
      background: var(--af-bg-secondary);
      color: var(--af-text-secondary);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--af-transition);

      &:hover:not(:disabled) {
        border-color: var(--af-accent);
        color: var(--af-accent);
        background: var(--af-accent-bg);
      }

      &:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }

      .material-icons-round {
        font-size: 20px;
      }
    }

    .dropdown {
      position: absolute;
      bottom: calc(100% + 8px);
      left: 0;
      min-width: 280px;
      background: var(--af-bg-primary);
      border: 1px solid var(--af-border);
      border-radius: var(--af-radius);
      box-shadow: var(--af-shadow-lg);
      overflow: hidden;
      z-index: 100;
      animation: fadeInUp 150ms ease;
    }

    .dropdown-item {
      display: flex;
      flex-direction: column;
      gap: 2px;
      width: 100%;
      padding: 10px 14px;
      border: none;
      background: none;
      cursor: pointer;
      text-align: left;
      font-family: var(--af-font-family);
      transition: background var(--af-transition);

      &:hover {
        background: var(--af-accent-bg);
      }

      &:not(:last-child) {
        border-bottom: 1px solid var(--af-border);
      }
    }

    .tool-name {
      font-size: 0.88em;
      font-weight: 600;
      color: var(--af-text-primary);
    }

    .tool-desc {
      font-size: 0.78em;
      color: var(--af-text-muted);
      line-height: 1.3;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(4px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `,
})
export class ToolSelectorComponent {
  readonly agent = inject(AgentService);
  readonly isOpen = signal(false);

  @HostListener('document:click')
  onDocumentClick(): void {
    if (this.isOpen()) {
      this.isOpen.set(false);
    }
  }

  toggle(event: Event): void {
    event.stopPropagation();
    this.isOpen.update((v) => !v);
  }

  selectTool(name: string): void {
    this.isOpen.set(false);
    this.agent.sendToolPrompt(name);
  }

  formatName(name: string): string {
    return name
      .split('_')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  }

  truncateDesc(description: string): string {
    const first = description.split('.')[0];
    return first.length > 80 ? first.slice(0, 77) + '...' : first;
  }
}
