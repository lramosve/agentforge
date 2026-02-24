import { Component } from '@angular/core';

@Component({
  selector: 'af-typing-indicator',
  standalone: true,
  template: `
    <div class="typing-indicator">
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    </div>
  `,
  styles: `
    .typing-indicator {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 4px 0;
    }

    .dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--af-text-muted);
      animation: bounce 1.2s infinite;

      &:nth-child(2) {
        animation-delay: 0.15s;
      }

      &:nth-child(3) {
        animation-delay: 0.3s;
      }
    }

    @keyframes bounce {
      0%, 60%, 100% {
        transform: translateY(0);
      }
      30% {
        transform: translateY(-4px);
      }
    }
  `,
})
export class TypingIndicatorComponent {}
