import { Injectable, computed, effect, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { catchError, of } from 'rxjs';
import {
  ChatMessage,
  ChatRequest,
  ChatResponse,
  HealthResponse,
  ToolInfo,
  ToolsResponse,
} from '../models/chat.models';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AgentService {
  private readonly apiUrl = environment.apiUrl;
  private readonly STORAGE_KEY_MESSAGES = 'af_messages';
  private readonly STORAGE_KEY_CONVERSATION = 'af_conversationId';

  private readonly toolPromptMap: Record<string, string> = {
    portfolio_analysis:
      'Analyze my portfolio holdings and allocation breakdown',
    portfolio_performance:
      'Show my portfolio performance and returns over time',
    market_data_lookup:
      'Look up current market data for my top holdings',
    transaction_history:
      'Show my recent transaction history',
    tax_estimate:
      'Estimate my tax liability from portfolio gains',
    compliance_check:
      'Run a compliance check on my portfolio',
    benchmark_comparison:
      'Compare my portfolio performance against common benchmarks',
  };

  readonly messages = signal<ChatMessage[]>([]);
  readonly conversationId = signal<string | null>(null);
  readonly isLoading = signal(false);
  readonly isConnected = signal(false);
  readonly error = signal<string | null>(null);
  readonly tools = signal<ToolInfo[]>([]);
  readonly toolsLoaded = signal(false);

  readonly hasMessages = computed(() => this.messages().length > 0);
  readonly pinnedMessages = computed(() => this.messages().filter((m) => m.pinned));
  readonly hasPinnedMessages = computed(() => this.pinnedMessages().length > 0);

  constructor(private readonly http: HttpClient) {
    this.loadFromStorage();
    this.checkHealth();
    this.loadTools();

    effect(() => {
      const msgs = this.messages();
      const convId = this.conversationId();
      const storable = msgs.filter((m) => !m.loading);
      if (storable.length > 0) {
        localStorage.setItem(this.STORAGE_KEY_MESSAGES, JSON.stringify(storable));
      } else {
        localStorage.removeItem(this.STORAGE_KEY_MESSAGES);
      }
      if (convId) {
        localStorage.setItem(this.STORAGE_KEY_CONVERSATION, convId);
      } else {
        localStorage.removeItem(this.STORAGE_KEY_CONVERSATION);
      }
    });
  }

  private loadFromStorage(): void {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEY_MESSAGES);
      if (raw) {
        const parsed: ChatMessage[] = JSON.parse(raw, (_key, value) => {
          if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) {
            const d = new Date(value);
            if (!isNaN(d.getTime())) return d;
          }
          return value;
        });
        this.messages.set(parsed.filter((m) => !m.loading));
      }
      const convId = localStorage.getItem(this.STORAGE_KEY_CONVERSATION);
      if (convId) this.conversationId.set(convId);
    } catch {
      // Corrupted storage — start fresh
    }
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
            trace_id: res.trace_id,
            tool_results: res.tool_results,
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

  loadTools(): void {
    this.http
      .get<ToolsResponse>(`${this.apiUrl}/api/agent/tools`)
      .pipe(
        catchError(() => {
          this.toolsLoaded.set(false);
          return of(null);
        })
      )
      .subscribe((res) => {
        if (res?.tools) {
          this.tools.set(res.tools);
          this.toolsLoaded.set(true);
        }
      });
  }

  sendMessageStreaming(content: string): void {
    if (!content.trim() || this.isLoading()) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    const streamingMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'agent',
      content: '',
      timestamp: new Date(),
      loading: true,
    };

    this.messages.update((msgs) => [...msgs, userMessage, streamingMessage]);
    this.isLoading.set(true);
    this.error.set(null);

    const body = JSON.stringify({
      message: content.trim(),
      conversation_id: this.conversationId() ?? undefined,
    });

    fetch(`${this.apiUrl}/api/agent/chat-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    })
      .then((response) => {
        if (!response.ok || !response.body) {
          throw new Error(`HTTP ${response.status}`);
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        const processChunk = (): Promise<void> => {
          return reader.read().then(({ done, value }) => {
            if (done) {
              this.isLoading.set(false);
              this.messages.update((msgs) =>
                msgs.map((m) =>
                  m.id === streamingMessage.id ? { ...m, loading: false } : m
                )
              );
              return;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() ?? '';

            let eventType = '';
            for (const line of lines) {
              if (line.startsWith('event: ')) {
                eventType = line.slice(7).trim();
              } else if (line.startsWith('data: ')) {
                const dataStr = line.slice(6);
                try {
                  const data = JSON.parse(dataStr);
                  this.handleSSEEvent(eventType, data, streamingMessage.id);
                } catch {
                  // Skip malformed JSON
                }
                eventType = '';
              }
            }
            return processChunk();
          });
        };

        return processChunk();
      })
      .catch(() => {
        // Fallback to non-streaming
        this.messages.update((msgs) =>
          msgs.filter((m) => m.id !== streamingMessage.id && m.id !== userMessage.id)
        );
        this.isLoading.set(false);
        this.sendMessage(content);
      });
  }

  private handleSSEEvent(type: string, data: any, messageId: string): void {
    switch (type) {
      case 'token':
        this.messages.update((msgs) =>
          msgs.map((m) =>
            m.id === messageId
              ? { ...m, content: m.content + (data.content ?? ''), loading: true }
              : m
          )
        );
        break;

      case 'tool_start':
        // Tool events are informational only; tools_used is set
        // authoritatively by the 'done' event to avoid accumulation
        // across conversation turns.
        break;

      case 'done':
        this.conversationId.set(data.conversation_id ?? null);
        this.messages.update((msgs) =>
          msgs.map((m) =>
            m.id === messageId
              ? {
                  ...m,
                  loading: false,
                  confidence: data.confidence,
                  metrics: data.metrics,
                  trace_id: data.trace_id,
                  tools_used: data.tools_used ?? [],
                  tool_results: data.tool_results,
                }
              : m
          )
        );
        this.isLoading.set(false);
        break;

      case 'error':
        this.error.set(data.message ?? 'Streaming error');
        this.isLoading.set(false);
        break;
    }
  }

  sendToolPrompt(toolName: string): void {
    const prompt =
      this.toolPromptMap[toolName] ?? `Use the ${toolName} tool`;
    this.sendMessageStreaming(prompt);
  }

  submitFeedback(messageId: string, traceId: string, score: 'up' | 'down'): void {
    this.messages.update((msgs) =>
      msgs.map((m) => (m.id === messageId ? { ...m, feedback: score } : m))
    );
    this.http
      .post(`${this.apiUrl}/api/agent/feedback`, {
        trace_id: traceId,
        score: score === 'up' ? 1 : 0,
      })
      .pipe(
        catchError((err) => {
          console.error('Feedback failed:', err);
          return of(null);
        })
      )
      .subscribe();
  }

  togglePin(messageId: string): void {
    this.messages.update((msgs) =>
      msgs.map((m) => (m.id === messageId ? { ...m, pinned: !m.pinned } : m))
    );
  }

  clearConversation(): void {
    this.messages.set([]);
    this.conversationId.set(null);
    this.error.set(null);
    localStorage.removeItem(this.STORAGE_KEY_MESSAGES);
    localStorage.removeItem(this.STORAGE_KEY_CONVERSATION);
  }
}
