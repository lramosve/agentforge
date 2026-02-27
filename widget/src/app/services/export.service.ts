import { Injectable } from '@angular/core';
import { ChatMessage } from '../models/chat.models';

@Injectable({ providedIn: 'root' })
export class ExportService {
  exportMarkdown(messages: ChatMessage[]): void {
    const lines: string[] = ['# AgentForge Conversation', ''];

    for (const msg of messages) {
      const role = msg.role === 'user' ? 'User' : 'Agent';
      const ts = new Date(msg.timestamp).toLocaleString();
      lines.push(`## ${role} — ${ts}`, '');
      lines.push(msg.content, '');

      if (msg.tools_used?.length) {
        lines.push(`**Tools used:** ${msg.tools_used.join(', ')}`, '');
      }
      if (msg.confidence !== undefined) {
        lines.push(`**Confidence:** ${(msg.confidence * 100).toFixed(0)}%`, '');
      }
      lines.push('---', '');
    }

    this.download(lines.join('\n'), 'agentforge-conversation.md', 'text/markdown');
  }

  exportCsv(messages: ChatMessage[]): void {
    const rows: string[] = ['id,role,content,timestamp,tools_used,confidence'];

    for (const msg of messages) {
      const content = this.escapeCsv(msg.content);
      const tools = this.escapeCsv(msg.tools_used?.join('; ') ?? '');
      const confidence = msg.confidence !== undefined ? msg.confidence.toString() : '';
      const ts = new Date(msg.timestamp).toISOString();
      rows.push(`${msg.id},${msg.role},${content},${ts},${tools},${confidence}`);
    }

    this.download(rows.join('\n'), 'agentforge-conversation.csv', 'text/csv');
  }

  private escapeCsv(value: string): string {
    if (value.includes(',') || value.includes('"') || value.includes('\n')) {
      return `"${value.replace(/"/g, '""')}"`;
    }
    return value;
  }

  private download(content: string, filename: string, mimeType: string): void {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }
}
