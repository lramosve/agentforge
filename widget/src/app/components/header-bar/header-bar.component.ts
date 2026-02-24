import { Component, input, output } from '@angular/core';

@Component({
  selector: 'af-header-bar',
  standalone: true,
  template: `
    <header class="header">
      <div class="header-left">
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

      &:hover {
        background: var(--af-bg-tertiary);
        color: var(--af-text-primary);
      }

      .material-icons-round {
        font-size: 20px;
      }
    }
  `,
})
export class HeaderBarComponent {
  readonly isConnected = input(false);
  readonly isDark = input(false);
  readonly toggleTheme = output<void>();
  readonly clearChat = output<void>();
}
