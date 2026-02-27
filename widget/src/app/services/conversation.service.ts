import { Injectable, inject, signal, computed } from '@angular/core';
import { AgentService } from './agent.service';
import { ChatMessage } from '../models/chat.models';

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  conversationId: string | null;
  createdAt: Date;
  updatedAt: Date;
}

const STORAGE_KEY = 'af_conversations';
const ACTIVE_KEY = 'af_active_conversation';

@Injectable({ providedIn: 'root' })
export class ConversationService {
  private readonly agent = inject(AgentService);

  readonly conversations = signal<Conversation[]>([]);
  readonly activeConversationId = signal<string | null>(null);

  readonly activeConversation = computed(() => {
    const id = this.activeConversationId();
    return this.conversations().find((c) => c.id === id) ?? null;
  });

  constructor() {
    this.loadConversations();
  }

  private loadConversations(): void {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed: Conversation[] = JSON.parse(raw, (_key, value) => {
          if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) {
            const d = new Date(value);
            if (!isNaN(d.getTime())) return d;
          }
          return value;
        });
        this.conversations.set(parsed);
      }
      const activeId = localStorage.getItem(ACTIVE_KEY);
      if (activeId) {
        this.activeConversationId.set(activeId);
      }
    } catch {
      // Start fresh
    }
  }

  private persist(): void {
    const convos = this.conversations();
    if (convos.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(convos));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
    const active = this.activeConversationId();
    if (active) {
      localStorage.setItem(ACTIVE_KEY, active);
    } else {
      localStorage.removeItem(ACTIVE_KEY);
    }
  }

  createConversation(): void {
    // If there are existing messages but no active conversation, save them first
    const currentMessages = this.agent.messages().filter((m) => !m.loading);
    if (!this.activeConversationId() && currentMessages.length > 0) {
      const existing: Conversation = {
        id: crypto.randomUUID(),
        title: this.generateTitle(currentMessages),
        messages: currentMessages,
        conversationId: this.agent.conversationId(),
        createdAt: currentMessages[0]?.timestamp ?? new Date(),
        updatedAt: new Date(),
      };
      this.conversations.update((c) => [existing, ...c]);
    } else {
      this.saveCurrentConversation();
    }

    const conv: Conversation = {
      id: crypto.randomUUID(),
      title: 'New Conversation',
      messages: [],
      conversationId: null,
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    this.conversations.update((c) => [conv, ...c]);
    this.activeConversationId.set(conv.id);
    this.agent.clearConversation();
    this.persist();
  }

  switchConversation(id: string): void {
    if (id === this.activeConversationId()) return;

    this.saveCurrentConversation();

    const target = this.conversations().find((c) => c.id === id);
    if (!target) return;

    this.activeConversationId.set(id);
    this.agent.messages.set(target.messages);
    this.agent.conversationId.set(target.conversationId);
    this.agent.error.set(null);
    this.persist();
  }

  deleteConversation(id: string): void {
    this.conversations.update((c) => c.filter((conv) => conv.id !== id));

    if (this.activeConversationId() === id) {
      const remaining = this.conversations();
      if (remaining.length > 0) {
        this.switchConversation(remaining[0].id);
      } else {
        this.activeConversationId.set(null);
        this.agent.clearConversation();
      }
    }

    this.persist();
  }

  renameConversation(id: string, title: string): void {
    this.conversations.update((c) =>
      c.map((conv) => (conv.id === id ? { ...conv, title } : conv))
    );
    this.persist();
  }

  saveCurrentConversation(): void {
    const activeId = this.activeConversationId();
    if (!activeId) return;

    const messages = this.agent.messages().filter((m) => !m.loading);
    if (messages.length === 0) return;

    this.conversations.update((c) =>
      c.map((conv) => {
        if (conv.id !== activeId) return conv;
        const title = conv.title === 'New Conversation' && messages.length > 0
          ? this.generateTitle(messages)
          : conv.title;
        return {
          ...conv,
          title,
          messages,
          conversationId: this.agent.conversationId(),
          updatedAt: new Date(),
        };
      })
    );
    this.persist();
  }

  private generateTitle(messages: ChatMessage[]): string {
    const firstUser = messages.find((m) => m.role === 'user');
    if (!firstUser) return 'New Conversation';
    const text = firstUser.content.trim();
    return text.length > 40 ? text.slice(0, 40) + '...' : text;
  }
}
