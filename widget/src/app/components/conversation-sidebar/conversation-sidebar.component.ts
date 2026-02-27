import { Component, input, output } from '@angular/core';
import { DatePipe } from '@angular/common';
import { Conversation } from '../../services/conversation.service';

@Component({
  selector: 'af-conversation-sidebar',
  standalone: true,
  imports: [DatePipe],
  template: `
    <div class="sidebar-backdrop" [class.open]="isOpen()" (click)="close()"></div>
    <aside class="sidebar" [class.open]="isOpen()">
      <div class="sidebar-header">
        <h3 class="sidebar-title">Conversations</h3>
        <button class="new-btn" (click)="newConversation.emit()">
          <span class="material-icons-round">add</span>
          New
        </button>
      </div>

      <div class="conversation-list">
        @for (conv of conversations(); track conv.id) {
          <button
            class="conversation-item"
            [class.active]="conv.id === activeId()"
            (click)="conversationSelected.emit(conv.id)"
          >
            <div class="conv-info">
              <span class="conv-title">{{ conv.title }}</span>
              <span class="conv-meta">
                {{ conv.updatedAt | date:'shortDate' }}
                · {{ conv.messages.length }} msgs
              </span>
            </div>
            <button
              class="delete-btn"
              (click)="onDelete($event, conv.id)"
              title="Delete conversation"
            >
              <span class="material-icons-round">close</span>
            </button>
          </button>
        } @empty {
          <div class="empty">No conversations yet</div>
        }
      </div>
    </aside>
  `,
  styles: `
    .sidebar-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.3);
      z-index: 199;
      opacity: 0;
      pointer-events: none;
      transition: opacity 200ms ease;

      &.open {
        opacity: 1;
        pointer-events: auto;
      }
    }

    .sidebar {
      position: fixed;
      top: 0;
      left: 0;
      bottom: 0;
      width: 260px;
      background: var(--af-bg-primary);
      border-right: 1px solid var(--af-border);
      z-index: 200;
      display: flex;
      flex-direction: column;
      transform: translateX(-100%);
      transition: transform 200ms ease;

      &.open {
        transform: translateX(0);
      }
    }

    .sidebar-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px;
      border-bottom: 1px solid var(--af-border);
    }

    .sidebar-title {
      font-size: 0.95em;
      font-weight: 700;
      color: var(--af-text-primary);
    }

    .new-btn {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 6px 12px;
      border: 1px solid var(--af-accent);
      border-radius: var(--af-radius-sm);
      background: var(--af-accent-bg);
      color: var(--af-accent);
      font-family: var(--af-font-family);
      font-size: 0.82em;
      font-weight: 600;
      cursor: pointer;
      transition: all var(--af-transition);

      .material-icons-round { font-size: 16px; }

      &:hover {
        background: var(--af-accent);
        color: white;
      }
    }

    .conversation-list {
      flex: 1;
      overflow-y: auto;
      padding: 8px;
    }

    .conversation-item {
      display: flex;
      align-items: center;
      gap: 8px;
      width: 100%;
      padding: 10px 12px;
      border: none;
      border-radius: var(--af-radius-sm);
      background: transparent;
      text-align: left;
      font-family: var(--af-font-family);
      cursor: pointer;
      transition: background var(--af-transition);

      &:hover {
        background: var(--af-bg-tertiary);
      }

      &.active {
        background: var(--af-accent-bg);
        border-left: 3px solid var(--af-accent);
      }

      & + & {
        margin-top: 2px;
      }
    }

    .conv-info {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .conv-title {
      font-size: 0.85em;
      font-weight: 500;
      color: var(--af-text-primary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .conv-meta {
      font-size: 0.72em;
      color: var(--af-text-muted);
    }

    .delete-btn {
      width: 24px;
      height: 24px;
      border: none;
      border-radius: 4px;
      background: transparent;
      color: var(--af-text-muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      opacity: 0;
      transition: all var(--af-transition);

      .material-icons-round { font-size: 14px; }

      &:hover {
        color: var(--af-danger);
        background: rgba(225, 112, 85, 0.1);
      }
    }

    .conversation-item:hover .delete-btn {
      opacity: 1;
    }

    .empty {
      text-align: center;
      padding: 32px 16px;
      font-size: 0.85em;
      color: var(--af-text-muted);
    }
  `,
})
export class ConversationSidebarComponent {
  readonly isOpen = input(false);
  readonly conversations = input<Conversation[]>([]);
  readonly activeId = input<string | null>(null);
  readonly conversationSelected = output<string>();
  readonly newConversation = output<void>();
  readonly deleteConversation = output<string>();

  close(): void {
    // Parent handles closing via sidebarOpen signal
    this.conversationSelected.emit('__close__');
  }

  onDelete(event: Event, id: string): void {
    event.stopPropagation();
    this.deleteConversation.emit(id);
  }
}
