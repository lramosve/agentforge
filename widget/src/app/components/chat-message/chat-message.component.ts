import { Component, input, output, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MarkdownComponent } from 'ngx-markdown';
import { ChatMessage } from '../../models/chat.models';
import { MessageMetadataComponent } from '../message-metadata/message-metadata.component';
import { TypingIndicatorComponent } from '../typing-indicator/typing-indicator.component';
import { ChartRendererComponent } from '../chart-renderer/chart-renderer.component';

@Component({
  selector: 'af-chat-message',
  standalone: true,
  imports: [
    DatePipe,
    MarkdownComponent,
    MessageMetadataComponent,
    TypingIndicatorComponent,
    ChartRendererComponent,
  ],
  template: `
    <div
      class="message af-fade-in"
      [class.message--user]="message().role === 'user'"
      [class.message--agent]="message().role === 'agent'"
      [class.message--pinned]="message().pinned"
    >
      @if (message().role === 'agent') {
        <div class="avatar">
          <span class="material-icons-round">smart_toy</span>
        </div>
      }

      <div class="bubble">
        @if (message().loading && !message().content) {
          <af-typing-indicator />
        } @else if (message().role === 'agent') {
          <div class="af-markdown">
            <markdown [data]="message().content" />
          </div>
          @if (message().tools_used?.length || message().confidence !== undefined) {
            <af-message-metadata
              [toolsUsed]="message().tools_used ?? []"
              [confidence]="message().confidence"
              [metrics]="message().metrics"
              [traceId]="message().trace_id"
              [messageId]="message().id"
              [feedback]="message().feedback"
              (feedbackSubmitted)="feedbackSubmitted.emit($event)"
            />
          }
          @if (message().tool_results?.length) {
            <af-chart-renderer [toolResults]="message().tool_results!" />
          }
        } @else {
          <div class="user-text">{{ message().content }}</div>
        }
      </div>

      @if (!message().loading) {
        <div class="message-actions">
          <button
            class="action-btn"
            [class.copied]="copied()"
            (click)="copyContent()"
            title="Copy to clipboard"
          >
            <span class="material-icons-round">
              {{ copied() ? 'check' : 'content_copy' }}
            </span>
          </button>
          <button
            class="action-btn pin-btn"
            [class.pinned]="message().pinned"
            (click)="pinToggled.emit(message().id)"
            title="{{ message().pinned ? 'Unpin message' : 'Pin message' }}"
          >
            <span class="material-icons-round">push_pin</span>
          </button>
          <div class="timestamp">
            {{ message().timestamp | date:'shortTime' }}
          </div>
        </div>
      } @else {
        <div class="timestamp">
          {{ message().timestamp | date:'shortTime' }}
        </div>
      }
    </div>
  `,
  styles: `
    .message {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      max-width: 85%;
      margin-bottom: 12px;

      &--user {
        margin-left: auto;
        flex-direction: row-reverse;
      }

      &--agent {
        margin-right: auto;
      }

      &--pinned .bubble {
        border-left: 3px solid var(--af-accent);
      }
    }

    .avatar {
      flex-shrink: 0;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: var(--af-accent-bg);
      display: flex;
      align-items: center;
      justify-content: center;
      margin-top: 2px;

      .material-icons-round {
        font-size: 18px;
        color: var(--af-accent);
      }
    }

    .bubble {
      padding: 10px 14px;
      border-radius: var(--af-radius);
      line-height: 1.5;
      font-size: 0.93em;
      min-width: 0;

      .message--user & {
        background: var(--af-user-bubble);
        color: var(--af-user-text);
        border-bottom-right-radius: 4px;
      }

      .message--agent & {
        background: var(--af-agent-bubble);
        color: var(--af-agent-text);
        border-bottom-left-radius: 4px;
      }
    }

    .user-text {
      white-space: pre-wrap;
      word-break: break-word;
    }

    .message-actions {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
      flex-shrink: 0;
      padding-top: 2px;
    }

    .action-btn {
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
      opacity: 0;
      transition: opacity var(--af-transition), color var(--af-transition);

      .material-icons-round {
        font-size: 15px;
      }

      &:hover {
        color: var(--af-text-primary);
      }

      &.copied {
        opacity: 1;
        color: var(--af-success);
      }
    }

    .pin-btn {
      transition: opacity var(--af-transition), color var(--af-transition), transform var(--af-transition);

      &:hover {
        color: var(--af-accent);
      }

      &.pinned {
        opacity: 1;
        color: var(--af-accent);
        transform: rotate(45deg);
      }
    }

    .message:hover .action-btn {
      opacity: 1;
    }

    @media (hover: none) {
      .action-btn {
        opacity: 1;
      }
    }

    .timestamp {
      align-self: flex-end;
      font-size: 0.7em;
      color: var(--af-text-muted);
      white-space: nowrap;
      flex-shrink: 0;
    }
  `,
})
export class ChatMessageComponent {
  readonly message = input.required<ChatMessage>();
  readonly feedbackSubmitted = output<{ messageId: string; traceId: string; score: 'up' | 'down' }>();
  readonly pinToggled = output<string>();

  readonly copied = signal(false);

  copyContent(): void {
    navigator.clipboard.writeText(this.message().content).then(() => {
      this.copied.set(true);
      setTimeout(() => this.copied.set(false), 2000);
    });
  }
}
