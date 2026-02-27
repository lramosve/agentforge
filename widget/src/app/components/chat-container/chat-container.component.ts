import {
  Component,
  ElementRef,
  effect,
  inject,
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
          <af-chat-message [message]="msg" (feedbackSubmitted)="onFeedback($event)" />
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
      </div>

      <af-chat-input
        [disabled]="agentService.isLoading()"
        (messageSent)="onSend($event)"
      />
    </div>
  `,
  styles: `
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
export class ChatContainerComponent {
  readonly agentService = inject(AgentService);

  private readonly scrollContainer =
    viewChild<ElementRef<HTMLElement>>('scrollContainer');

  readonly suggestions = [
    'Portfolio summary',
    'Performance this year',
    'Tax estimate',
    'Top holdings',
  ];

  constructor() {
    effect(() => {
      this.agentService.messages();
      this.scrollToBottom();
    });
  }

  onSend(message: string): void {
    this.agentService.sendMessage(message);
  }

  onFeedback(event: { messageId: string; traceId: string; score: 'up' | 'down' }): void {
    this.agentService.submitFeedback(event.messageId, event.traceId, event.score);
  }

  sendSuggestion(chip: string): void {
    this.agentService.sendMessage(chip);
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      const el = this.scrollContainer()?.nativeElement;
      if (el) {
        el.scrollTop = el.scrollHeight;
      }
    });
  }
}
