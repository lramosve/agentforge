import { Component, HostListener, input, output, signal } from '@angular/core';

@Component({
  selector: 'af-header-bar',
  standalone: true,
  template: `
    <header class="header">
      <div class="header-left">
        <button class="icon-btn" title="Conversations" (click)="toggleSidebar.emit()">
          <span class="material-icons-round">menu</span>
        </button>
        <span class="logo material-icons-round">psychology</span>
        <div class="title-group">
          <h1 class="title">AgentForge</h1>
          <span class="status" [class.connected]="isConnected()">
            <span class="status-dot"></span>
            {{ isConnected() ? 'Connected' : 'Disconnected' }}
          </span>
        </div>
      </div>

      <div class="header-actions">
        <div class="export-wrapper">
          <button
            class="icon-btn"
            title="Export conversation"
            [disabled]="!hasMessages()"
            (click)="toggleExport($event)"
          >
            <span class="material-icons-round">download</span>
          </button>
          @if (exportOpen()) {
            <div class="export-dropdown">
              <button class="export-option" (click)="onExportMd()">
                <span class="material-icons-round">description</span>
                Export as Markdown
              </button>
              <button class="export-option" (click)="onExportCsv()">
                <span class="material-icons-round">table_chart</span>
                Export as CSV
              </button>
            </div>
          }
        </div>
        <button
          class="icon-btn"
          title="Clear conversation"
          (click)="clearChat.emit()"
        >
          <span class="material-icons-round">delete_outline</span>
        </button>
        <button
          class="icon-btn"
          title="Toggle theme"
          (click)="toggleTheme.emit()"
        >
          <span class="material-icons-round">
            {{ isDark() ? 'light_mode' : 'dark_mode' }}
          </span>
        </button>
      </div>
    </header>
  `,
  styles: `
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      background: var(--af-bg-primary);
      border-bottom: 1px solid var(--af-border);
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .logo {
      font-size: 28px;
      color: var(--af-accent);
    }

    .title-group {
      display: flex;
      flex-direction: column;
    }

    .title {
      font-size: 1.05em;
      font-weight: 700;
      color: var(--af-text-primary);
      line-height: 1.2;
    }

    .status {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 0.72em;
      color: var(--af-danger);

      &.connected {
        color: var(--af-success);
      }
    }

    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: currentColor;
    }

    .header-actions {
      display: flex;
      gap: 4px;
    }

    .icon-btn {
      width: 36px;
      height: 36px;
      border: none;
      border-radius: 50%;
      background: transparent;
      color: var(--af-text-secondary);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background var(--af-transition), color var(--af-transition);

      &:hover:not(:disabled) {
        background: var(--af-bg-tertiary);
        color: var(--af-text-primary);
      }

      &:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }

      .material-icons-round {
        font-size: 20px;
      }
    }

    .export-wrapper {
      position: relative;
    }

    .export-dropdown {
      position: absolute;
      top: calc(100% + 6px);
      right: 0;
      min-width: 200px;
      background: var(--af-bg-primary);
      border: 1px solid var(--af-border);
      border-radius: var(--af-radius-sm);
      box-shadow: var(--af-shadow-lg);
      z-index: 100;
      overflow: hidden;
      animation: fadeIn 120ms ease;
    }

    .export-option {
      display: flex;
      align-items: center;
      gap: 8px;
      width: 100%;
      padding: 10px 14px;
      border: none;
      background: none;
      color: var(--af-text-primary);
      font-family: var(--af-font-family);
      font-size: 0.85em;
      cursor: pointer;
      transition: background var(--af-transition);

      .material-icons-round {
        font-size: 18px;
        color: var(--af-text-muted);
      }

      &:hover {
        background: var(--af-accent-bg);
      }

      &:not(:last-child) {
        border-bottom: 1px solid var(--af-border);
      }
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(-4px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `,
})
export class HeaderBarComponent {
  readonly isConnected = input(false);
  readonly isDark = input(false);
  readonly hasMessages = input(false);
  readonly toggleTheme = output<void>();
  readonly clearChat = output<void>();
  readonly toggleSidebar = output<void>();
  readonly exportMarkdown = output<void>();
  readonly exportCsv = output<void>();

  readonly exportOpen = signal(false);

  @HostListener('document:click')
  onDocumentClick(): void {
    if (this.exportOpen()) {
      this.exportOpen.set(false);
    }
  }

  toggleExport(event: Event): void {
    event.stopPropagation();
    this.exportOpen.update((v) => !v);
  }

  onExportMd(): void {
    this.exportOpen.set(false);
    this.exportMarkdown.emit();
  }

  onExportCsv(): void {
    this.exportOpen.set(false);
    this.exportCsv.emit();
  }
}
