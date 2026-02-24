import {
  Component,
  ElementRef,
  output,
  viewChild,
  input,
} from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'af-chat-input',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="input-wrapper">
      <textarea
        #textarea
        class="chat-textarea"
        [(ngModel)]="value"
        [disabled]="disabled()"
        placeholder="Ask about your portfolio..."
        rows="1"
        (keydown.enter)="onEnter($event)"
        (input)="autoResize()"
      ></textarea>
      <button
        class="send-btn"
        [disabled]="disabled() || !value.trim()"
        (click)="send()"
      >
        <span class="material-icons-round">send</span>
      </button>
    </div>
  `,
  styles: `
    .input-wrapper {
      display: flex;
      align-items: flex-end;
      gap: 8px;
      padding: 12px 16px;
      background: var(--af-bg-primary);
      border-top: 1px solid var(--af-border);
    }

    .chat-textarea {
      flex: 1;
      resize: none;
      border: 1px solid var(--af-border);
      border-radius: var(--af-radius);
      padding: 10px 14px;
      font-family: var(--af-font-family);
      font-size: 0.93em;
      line-height: 1.5;
      color: var(--af-text-primary);
      background: var(--af-bg-secondary);
      outline: none;
      max-height: 120px;
      transition: border-color var(--af-transition);

      &:focus {
        border-color: var(--af-accent);
      }

      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }

      &::placeholder {
        color: var(--af-text-muted);
      }
    }

    .send-btn {
      flex-shrink: 0;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      border: none;
      background: var(--af-accent);
      color: white;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: opacity var(--af-transition), transform var(--af-transition);

      &:hover:not(:disabled) {
        opacity: 0.9;
        transform: scale(1.05);
      }

      &:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }

      .material-icons-round {
        font-size: 20px;
      }
    }
  `,
})
export class ChatInputComponent {
  readonly disabled = input(false);
  readonly messageSent = output<string>();

  readonly textarea = viewChild<ElementRef<HTMLTextAreaElement>>('textarea');

  value = '';

  onEnter(event: Event): void {
    const keyEvent = event as KeyboardEvent;
    if (!keyEvent.shiftKey) {
      keyEvent.preventDefault();
      this.send();
    }
  }

  send(): void {
    const trimmed = this.value.trim();
    if (!trimmed || this.disabled()) return;

    this.messageSent.emit(trimmed);
    this.value = '';

    const el = this.textarea()?.nativeElement;
    if (el) {
      el.style.height = 'auto';
    }
  }

  autoResize(): void {
    const el = this.textarea()?.nativeElement;
    if (el) {
      el.style.height = 'auto';
      el.style.height = el.scrollHeight + 'px';
    }
  }
}
