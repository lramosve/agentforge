import { Injectable, computed, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { catchError, of } from 'rxjs';
import {
  ChatMessage,
  ChatRequest,
  ChatResponse,
  HealthResponse,
} from '../models/chat.models';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AgentService {
  private readonly apiUrl = environment.apiUrl;

  readonly messages = signal<ChatMessage[]>([]);
  readonly conversationId = signal<string | null>(null);
  readonly isLoading = signal(false);
  readonly isConnected = signal(false);
  readonly error = signal<string | null>(null);

  readonly hasMessages = computed(() => this.messages().length > 0);

  constructor(private readonly http: HttpClient) {
    this.checkHealth();
  }

  checkHealth(): void {
    this.http
      .get<HealthResponse>(`${this.apiUrl}/api/agent/health`)
      .pipe(
        catchError(() => {
          this.isConnected.set(false);
          return of(null);
        })
      )
      .subscribe((res) => {
        this.isConnected.set(res?.status === 'ok');
      });
  }

  sendMessage(content: string): void {
    if (!content.trim() || this.isLoading()) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    const loadingMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'agent',
      content: '',
      timestamp: new Date(),
      loading: true,
    };

    this.messages.update((msgs) => [...msgs, userMessage, loadingMessage]);
    this.isLoading.set(true);
    this.error.set(null);

    const request: ChatRequest = {
      message: content.trim(),
      conversation_id: this.conversationId() ?? undefined,
    };

    this.http
      .post<ChatResponse>(`${this.apiUrl}/api/agent/chat`, request)
      .pipe(
        catchError((err) => {
          this.error.set(
            err.status === 0
              ? 'Unable to reach the agent. Is the backend running?'
              : `Error: ${err.error?.detail || err.message}`
          );
          return of(null);
        })
      )
      .subscribe((res) => {
        this.isLoading.set(false);

        if (res) {
          this.conversationId.set(res.conversation_id);

          const agentMessage: ChatMessage = {
            id: crypto.randomUUID(),
            role: 'agent',
            content: res.response,
            timestamp: new Date(),
            tools_used: res.tools_used,
            confidence: res.confidence,
            metrics: res.metrics,
          };

          this.messages.update((msgs) =>
            msgs.map((m) => (m.id === loadingMessage.id ? agentMessage : m))
          );
        } else {
          this.messages.update((msgs) =>
            msgs.filter((m) => m.id !== loadingMessage.id)
          );
        }
      });
  }

  clearConversation(): void {
    this.messages.set([]);
    this.conversationId.set(null);
    this.error.set(null);
  }
}
