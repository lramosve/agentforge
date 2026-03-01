import {
  EnvironmentProviders,
  makeEnvironmentProviders,
  SecurityContext,
} from '@angular/core';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { provideMarkdown, SANITIZE } from 'ngx-markdown';
import { AF_CONFIG, AgentForgeConfig } from './agent-forge.config';
import { AgentService } from '../services/agent.service';
import { ConversationService } from '../services/conversation.service';
import { ExportService } from '../services/export.service';

export function provideAgentForge(config: AgentForgeConfig): EnvironmentProviders {
  return makeEnvironmentProviders([
    { provide: AF_CONFIG, useValue: config },
    AgentService,
    ConversationService,
    ExportService,
    provideHttpClient(withInterceptorsFromDi()),
    provideMarkdown({
      sanitize: { provide: SANITIZE, useValue: SecurityContext.HTML },
    }),
  ]);
}
