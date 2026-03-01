import {
  Component,
  HostListener,
  ViewEncapsulation,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { HeaderBarComponent } from './components/header-bar/header-bar.component';
import { ChatContainerComponent } from './components/chat-container/chat-container.component';
import { ConversationSidebarComponent } from './components/conversation-sidebar/conversation-sidebar.component';
import { AgentService } from './services/agent.service';
import { ExportService } from './services/export.service';
import { ConversationService } from './services/conversation.service';

@Component({
  selector: 'af-widget',
  standalone: true,
  imports: [HeaderBarComponent, ChatContainerComponent, ConversationSidebarComponent],
  encapsulation: ViewEncapsulation.None,
  template: `
    <div class="af-widget" [class.theme-dark]="isDark()">
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
    /* ===== AgentForge Widget — Scoped Global Styles ===== */

    /* --- CSS Variables (Light Theme) --- */
    .af-widget {
      --af-bg-primary: #ffffff;
      --af-bg-secondary: #f5f5f5;
      --af-bg-tertiary: #e8e8e8;
      --af-text-primary: #1a1a2e;
      --af-text-secondary: #555770;
      --af-text-muted: #8e8ea0;
      --af-accent: #6c5ce7;
      --af-accent-light: #a29bfe;
      --af-accent-bg: rgba(108, 92, 231, 0.08);
      --af-user-bubble: #6c5ce7;
      --af-user-text: #ffffff;
      --af-agent-bubble: #f0f0f5;
      --af-agent-text: #1a1a2e;
      --af-border: #e0e0e6;
      --af-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
      --af-shadow-lg: 0 4px 16px rgba(0, 0, 0, 0.1);
      --af-success: #00b894;
      --af-warning: #fdcb6e;
      --af-danger: #e17055;
      --af-radius: 12px;
      --af-radius-sm: 8px;
      --af-radius-lg: 16px;
      --af-font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
        Roboto, sans-serif;
      --af-font-mono: 'JetBrains Mono', 'Fira Code', monospace;
      --af-transition: 200ms ease;
    }

    /* --- Dark Theme --- */
    .af-widget.theme-dark {
      --af-bg-primary: #16161a;
      --af-bg-secondary: #1e1e24;
      --af-bg-tertiary: #2a2a32;
      --af-text-primary: #eeeeee;
      --af-text-secondary: #a0a0b8;
      --af-text-muted: #6c6c80;
      --af-accent: #a29bfe;
      --af-accent-light: #6c5ce7;
      --af-accent-bg: rgba(162, 155, 254, 0.1);
      --af-user-bubble: #6c5ce7;
      --af-user-text: #ffffff;
      --af-agent-bubble: #24242c;
      --af-agent-text: #eeeeee;
      --af-border: #2e2e38;
      --af-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
      --af-shadow-lg: 0 4px 16px rgba(0, 0, 0, 0.4);
      --af-success: #55efc4;
      --af-warning: #ffeaa7;
      --af-danger: #fab1a0;
    }

    /* --- Layout --- */
    .af-widget {
      display: flex;
      flex-direction: column;
      height: 100%;
      background: var(--af-bg-primary);
      font-family: var(--af-font-family);
      font-size: 15px;
      color: var(--af-text-primary);
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      transition: background-color var(--af-transition), color var(--af-transition);
    }

    .af-widget *,
    .af-widget *::before,
    .af-widget *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    /* --- Scrollbar --- */
    .af-widget ::-webkit-scrollbar {
      width: 6px;
    }
    .af-widget ::-webkit-scrollbar-track {
      background: transparent;
    }
    .af-widget ::-webkit-scrollbar-thumb {
      background: var(--af-border);
      border-radius: 3px;
    }
    .af-widget ::-webkit-scrollbar-thumb:hover {
      background: var(--af-text-muted);
    }

    /* --- Animations --- */
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(8px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
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

    @keyframes pulse {
      0%, 100% {
        opacity: 1;
      }
      50% {
        opacity: 0.5;
      }
    }

    .af-widget .af-fade-in {
      animation: fadeInUp 300ms ease forwards;
    }

    /* --- Markdown --- */
    .af-widget .af-markdown {
      line-height: 1.65;
      word-break: break-word;
    }

    .af-widget .af-markdown p {
      margin: 0 0 0.75em;
    }

    .af-widget .af-markdown p:last-child {
      margin-bottom: 0;
    }

    .af-widget .af-markdown h1,
    .af-widget .af-markdown h2,
    .af-widget .af-markdown h3,
    .af-widget .af-markdown h4 {
      margin: 1em 0 0.5em;
      font-weight: 600;
      color: var(--af-text-primary);
    }

    .af-widget .af-markdown h1 { font-size: 1.3em; }
    .af-widget .af-markdown h2 { font-size: 1.15em; }
    .af-widget .af-markdown h3 { font-size: 1.05em; }

    .af-widget .af-markdown ul,
    .af-widget .af-markdown ol {
      margin: 0.5em 0;
      padding-left: 1.5em;
    }

    .af-widget .af-markdown li {
      margin: 0.25em 0;
    }

    .af-widget .af-markdown code {
      font-family: var(--af-font-mono);
      font-size: 0.88em;
      padding: 0.15em 0.4em;
      border-radius: 4px;
      background: var(--af-bg-tertiary);
      color: var(--af-accent);
    }

    .af-widget .af-markdown pre {
      margin: 0.75em 0;
      padding: 0.85em 1em;
      border-radius: var(--af-radius-sm);
      background: var(--af-bg-tertiary);
      overflow-x: auto;
    }

    .af-widget .af-markdown pre code {
      padding: 0;
      background: none;
      color: var(--af-text-primary);
    }

    .af-widget .af-markdown table {
      width: 100%;
      border-collapse: collapse;
      margin: 0.75em 0;
      font-size: 0.9em;
    }

    .af-widget .af-markdown th,
    .af-widget .af-markdown td {
      padding: 0.5em 0.75em;
      text-align: left;
      border-bottom: 1px solid var(--af-border);
    }

    .af-widget .af-markdown th {
      font-weight: 600;
      color: var(--af-text-secondary);
      font-size: 0.85em;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }

    .af-widget .af-markdown tr:last-child td {
      border-bottom: none;
    }

    .af-widget .af-markdown blockquote {
      margin: 0.75em 0;
      padding: 0.5em 1em;
      border-left: 3px solid var(--af-accent);
      background: var(--af-accent-bg);
      border-radius: 0 var(--af-radius-sm) var(--af-radius-sm) 0;
      color: var(--af-text-secondary);
    }

    .af-widget .af-markdown hr {
      border: none;
      height: 1px;
      background: var(--af-border);
      margin: 1em 0;
    }

    .af-widget .af-markdown a {
      color: var(--af-accent);
      text-decoration: none;
    }

    .af-widget .af-markdown a:hover {
      text-decoration: underline;
    }

    .af-widget .af-markdown strong {
      font-weight: 600;
      color: var(--af-text-primary);
    }
  `,
})
export class AgentForgeWidgetComponent {
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
