import { Component, input } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MarkdownComponent } from 'ngx-markdown';
import { ChatMessage } from '../../models/chat.models';
import { MessageMetadataComponent } from '../message-metadata/message-metadata.component';
import { TypingIndicatorComponent } from '../typing-indicator/typing-indicator.component';

@Component({
  selector: 'af-chat-message',
  standalone: true,
  imports: [
    DatePipe,
    MarkdownComponent,
    MessageMetadataComponent,
    TypingIndicatorComponent,
  ],
  template: `
    <div
      class="message af-fade-in"
      [class.message--user]="message().role === 'user'"
      [class.message--agent]="message().role === 'agent'"
    >
      @if (message().role === 'agent') {
        <div class="avatar">
          <span class="material-icons-round">smart_toy</span>
        </div>
      }

      <div class="bubble">
        @if (message().loading) {
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
            />
          }
        } @else {
          <div class="user-text">{{ message().content }}</div>
        }
      </div>

      <div class="timestamp">
        {{ message().timestamp | date:'shortTime' }}
      </div>
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
}
