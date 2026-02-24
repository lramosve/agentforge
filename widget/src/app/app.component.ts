import { Component, inject, signal } from '@angular/core';
import { HeaderBarComponent } from './components/header-bar/header-bar.component';
import { ChatContainerComponent } from './components/chat-container/chat-container.component';
import { AgentService } from './services/agent.service';

@Component({
  selector: 'af-root',
  standalone: true,
  imports: [HeaderBarComponent, ChatContainerComponent],
  template: `
    <div class="app-shell" [class.theme-dark]="isDark()">
      <af-header-bar
        [isConnected]="agentService.isConnected()"
        [isDark]="isDark()"
        (toggleTheme)="toggleTheme()"
        (clearChat)="agentService.clearConversation()"
      />
      <af-chat-container />
    </div>
  `,
  styles: `
    .app-shell {
      display: flex;
      flex-direction: column;
      height: 100vh;
      height: 100dvh;
      background: var(--af-bg-primary);
      transition: background-color var(--af-transition);
    }
  `,
})
export class AppComponent {
  readonly agentService = inject(AgentService);
  readonly isDark = signal(
    typeof window !== 'undefined' &&
      window.matchMedia('(prefers-color-scheme: dark)').matches
  );

  toggleTheme(): void {
    this.isDark.update((v) => !v);
  }
}
