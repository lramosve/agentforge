import {
  Component,
  ElementRef,
  OnDestroy,
  effect,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { ChatMessageComponent } from '../chat-message/chat-message.component';
import { ChatInputComponent } from '../chat-input/chat-input.component';
import { AgentService } from '../../services/agent.service';

@Component({
  selector: 'af-chat-container',
  standalone: true,
  imports: [ChatMessageComponent, ChatInputComponent],
  template: `
    <div class="container">
      <div class="messages" #scrollContainer>
        @if (agentService.hasPinnedMessages() && pinnedOpen()) {
          <div class="pinned-section af-fade-in">
            <button class="pinned-header" (click)="pinnedOpen.set(!pinnedOpen())">
              <span class="material-icons-round pinned-icon">push_pin</span>
              <span>Pinned ({{ agentService.pinnedMessages().length }})</span>
              <span class="material-icons-round chevron">expand_less</span>
            </button>
            <div class="pinned-list">
              @for (pin of agentService.pinnedMessages(); track pin.id) {
                <div class="pinned-card" (click)="scrollToMessage(pin.id)">
                  <span class="material-icons-round pinned-card-icon">
                    {{ pin.role === 'user' ? 'person' : 'smart_toy' }}
                  </span>
                  <span class="pinned-card-text">{{ truncate(pin.content, 100) }}</span>
                  <button
                    class="pinned-card-unpin"
                    (click)="unpin($event, pin.id)"
                    title="Unpin"
                  >
                    <span class="material-icons-round">close</span>
                  </button>
                </div>
              }
            </div>
          </div>
        } @else if (agentService.hasPinnedMessages()) {
          <button class="pinned-collapsed" (click)="pinnedOpen.set(true)">
            <span class="material-icons-round pinned-icon">push_pin</span>
            <span>Pinned ({{ agentService.pinnedMessages().length }})</span>
            <span class="material-icons-round chevron">expand_more</span>
          </button>
        }

        @if (!agentService.hasMessages()) {
          <div class="empty-state af-fade-in">
            <span class="material-icons-round empty-icon">forum</span>
            <h2 class="empty-title">Ask AgentForge</h2>
            <p class="empty-subtitle">
              Your AI financial analyst. Ask about portfolios, markets, and
              more.
            </p>
            <div class="suggestions">
              @for (chip of suggestions; track chip) {
                <button class="chip" (click)="sendSuggestion(chip)">
                  {{ chip }}
                </button>
              }
            </div>
          </div>
        }

        @for (msg of agentService.messages(); track msg.id) {
          <af-chat-message
            [attr.data-message-id]="msg.id"
            [message]="msg"
            (feedbackSubmitted)="onFeedback($event)"
            (pinToggled)="onPinToggle($event)"
          />
        }

        @if (agentService.error(); as err) {
          <div class="error-banner af-fade-in">
            <span class="material-icons-round">error_outline</span>
            <span>{{ err }}</span>
            <button class="retry-btn" (click)="agentService.checkHealth()">
              Retry
            </button>
          </div>
        }

        <div #scrollAnchor class="scroll-anchor"></div>
      </div>

      <af-chat-input
        [disabled]="agentService.isLoading()"
        (messageSent)="onSend($event)"
      />
    </div>
  `,
  styles: `
    :host {
      flex: 1;
      min-height: 0;
      overflow: hidden;
    }

    .container {
      display: flex;
      flex-direction: column;
      height: 100%;
    }

    .messages {
      flex: 1;
      min-height: 0;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
    }

    .scroll-anchor {
      height: 0;
      flex-shrink: 0;
    }

    .pinned-section {
      border: 1px solid var(--af-border);
      border-radius: var(--af-radius-sm);
      margin-bottom: 12px;
      overflow: hidden;
    }

    .pinned-header, .pinned-collapsed {
      display: flex;
      align-items: center;
      gap: 6px;
      width: 100%;
      padding: 8px 12px;
      border: none;
      background: var(--af-accent-bg);
      color: var(--af-accent);
      font-family: var(--af-font-family);
      font-size: 0.82em;
      font-weight: 600;
      cursor: pointer;
      transition: background var(--af-transition);

      &:hover {
        background: var(--af-bg-tertiary);
      }
    }

    .pinned-collapsed {
      border: 1px solid var(--af-border);
      border-radius: var(--af-radius-sm);
      margin-bottom: 12px;
    }

    .pinned-icon {
      font-size: 16px;
      transform: rotate(45deg);
    }

    .chevron {
      margin-left: auto;
      font-size: 18px;
    }

    .pinned-list {
      display: flex;
      flex-direction: column;
    }

    .pinned-card {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      cursor: pointer;
      border-top: 1px solid var(--af-border);
      transition: background var(--af-transition);

      &:hover {
        background: var(--af-bg-tertiary);
      }
    }

    .pinned-card-icon {
      font-size: 16px;
      color: var(--af-text-muted);
      flex-shrink: 0;
    }

    .pinned-card-text {
      flex: 1;
      font-size: 0.82em;
      color: var(--af-text-secondary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .pinned-card-unpin {
      width: 22px;
      height: 22px;
      border: none;
      border-radius: 4px;
      background: transparent;
      color: var(--af-text-muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;

      .material-icons-round { font-size: 14px; }

      &:hover {
        color: var(--af-danger);
        background: rgba(225, 112, 85, 0.1);
      }
    }

    .empty-state {
      margin: auto;
      text-align: center;
      padding: 32px 16px;
      max-width: 400px;
    }

    .empty-icon {
      font-size: 48px;
      color: var(--af-accent);
      opacity: 0.6;
      margin-bottom: 12px;
    }

    .empty-title {
      font-size: 1.3em;
      font-weight: 700;
      color: var(--af-text-primary);
      margin-bottom: 6px;
    }

    .empty-subtitle {
      font-size: 0.9em;
      color: var(--af-text-muted);
      margin-bottom: 20px;
      line-height: 1.5;
    }

    .suggestions {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 8px;
    }

    .chip {
      padding: 8px 14px;
      border-radius: 20px;
      border: 1px solid var(--af-border);
      background: var(--af-bg-secondary);
      color: var(--af-text-secondary);
      font-family: var(--af-font-family);
      font-size: 0.85em;
      cursor: pointer;
      transition: all var(--af-transition);

      &:hover {
        border-color: var(--af-accent);
        color: var(--af-accent);
        background: var(--af-accent-bg);
      }
    }

    .error-banner {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 8px 0;
      padding: 10px 14px;
      border-radius: var(--af-radius-sm);
      background: rgba(225, 112, 85, 0.1);
      color: var(--af-danger);
      font-size: 0.88em;

      .material-icons-round {
        font-size: 18px;
      }
    }

    .retry-btn {
      margin-left: auto;
      padding: 4px 12px;
      border-radius: 4px;
      border: 1px solid var(--af-danger);
      background: none;
      color: var(--af-danger);
      font-family: var(--af-font-family);
      font-size: 0.85em;
      cursor: pointer;

      &:hover {
        background: rgba(225, 112, 85, 0.15);
      }
    }
  `,
})
export class ChatContainerComponent implements OnDestroy {
  readonly agentService = inject(AgentService);

  private readonly scrollContainer =
    viewChild<ElementRef<HTMLElement>>('scrollContainer');

  private readonly scrollAnchor =
    viewChild<ElementRef<HTMLElement>>('scrollAnchor');

  private readonly chatInput = viewChild(ChatInputComponent);

  readonly pinnedOpen = signal(false);

  readonly suggestions = [
    'Portfolio summary',
    'Performance this year',
    'Tax estimate',
    'Top holdings',
  ];

  private scrollObserver?: MutationObserver;

  constructor() {
    // Set up MutationObserver once the scroll container is available
    effect(() => {
      const container = this.scrollContainer()?.nativeElement;
      if (container && !this.scrollObserver) {
        this.scrollObserver = new MutationObserver(() => {
          this.doScroll();
        });
        this.scrollObserver.observe(container, {
          childList: true,
          subtree: true,
          characterData: true,
        });
      }
    });

    // Also scroll when messages or loading state change
    effect(() => {
      this.agentService.messages();
      this.agentService.isLoading();
      setTimeout(() => this.doScroll(), 50);
    });
  }

  ngOnDestroy(): void {
    this.scrollObserver?.disconnect();
  }

  private doScroll(): void {
    const anchor = this.scrollAnchor()?.nativeElement;
    if (anchor) {
      anchor.scrollIntoView({ block: 'end', behavior: 'instant' });
    }
  }

  focusInput(): void {
    this.chatInput()?.focusTextarea();
  }

  onSend(message: string): void {
    this.agentService.sendMessageStreaming(message);
  }

  onFeedback(event: { messageId: string; traceId: string; score: 'up' | 'down' }): void {
    this.agentService.submitFeedback(event.messageId, event.traceId, event.score);
  }

  onPinToggle(messageId: string): void {
    this.agentService.togglePin(messageId);
  }

  sendSuggestion(chip: string): void {
    this.agentService.sendMessageStreaming(chip);
  }

  scrollToMessage(messageId: string): void {
    const el = this.scrollContainer()?.nativeElement?.querySelector(
      `[data-message-id="${messageId}"]`
    ) as HTMLElement | null;
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  truncate(text: string, max: number): string {
    return text.length > max ? text.slice(0, max) + '...' : text;
  }

  unpin(event: Event, messageId: string): void {
    event.stopPropagation();
    this.agentService.togglePin(messageId);
  }
}
