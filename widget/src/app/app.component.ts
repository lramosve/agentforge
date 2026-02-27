import { Component, HostListener, inject, signal, viewChild } from '@angular/core';
import { HeaderBarComponent } from './components/header-bar/header-bar.component';
import { ChatContainerComponent } from './components/chat-container/chat-container.component';
import { ConversationSidebarComponent } from './components/conversation-sidebar/conversation-sidebar.component';
import { AgentService } from './services/agent.service';
import { ExportService } from './services/export.service';
import { ConversationService } from './services/conversation.service';

@Component({
  selector: 'af-root',
  standalone: true,
  imports: [HeaderBarComponent, ChatContainerComponent, ConversationSidebarComponent],
  template: `
    <div class="app-shell" [class.theme-dark]="isDark()">
      <af-conversation-sidebar
        [isOpen]="sidebarOpen()"
        [conversations]="conversationService.conversations()"
        [activeId]="conversationService.activeConversationId()"
        (conversationSelected)="onConversationSelected($event)"
        (newConversation)="onNewConversation()"
        (deleteConversation)="onDeleteConversation($event)"
      />
      <af-header-bar
        [isConnected]="agentService.isConnected()"
        [isDark]="isDark()"
        [hasMessages]="agentService.hasMessages()"
        (toggleTheme)="toggleTheme()"
        (clearChat)="agentService.clearConversation()"
        (toggleSidebar)="toggleSidebar()"
        (exportMarkdown)="onExportMarkdown()"
        (exportCsv)="onExportCsv()"
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
  readonly conversationService = inject(ConversationService);
  private readonly exportService = inject(ExportService);

  private readonly chatContainer = viewChild(ChatContainerComponent);

  readonly isDark = signal(
    typeof window !== 'undefined' &&
      window.matchMedia('(prefers-color-scheme: dark)').matches
  );
  readonly sidebarOpen = signal(false);

  @HostListener('document:keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    if (event.ctrlKey && event.key === '/') {
      event.preventDefault();
      this.chatContainer()?.focusInput();
    }
    if (event.ctrlKey && event.key === 'l') {
      event.preventDefault();
      this.agentService.clearConversation();
    }
  }

  toggleSidebar(): void {
    this.sidebarOpen.update((v) => !v);
  }

  toggleTheme(): void {
    this.isDark.update((v) => !v);
  }

  onExportMarkdown(): void {
    this.exportService.exportMarkdown(this.agentService.messages());
  }

  onExportCsv(): void {
    this.exportService.exportCsv(this.agentService.messages());
  }

  onConversationSelected(id: string): void {
    if (id === '__close__') {
      this.sidebarOpen.set(false);
      return;
    }
    this.conversationService.switchConversation(id);
    this.sidebarOpen.set(false);
  }

  onNewConversation(): void {
    this.conversationService.createConversation();
    this.sidebarOpen.set(false);
  }

  onDeleteConversation(id: string): void {
    this.conversationService.deleteConversation(id);
  }
}
