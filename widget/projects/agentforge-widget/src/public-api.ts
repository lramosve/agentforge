// Configuration
export { AgentForgeConfig, AF_CONFIG } from './lib/config/agent-forge.config';
export { provideAgentForge } from './lib/config/provide-agent-forge';

// Primary component
export { AgentForgeWidgetComponent } from './lib/agent-forge-widget.component';

// Individual components
export { HeaderBarComponent } from './lib/components/header-bar/header-bar.component';
export { ChatContainerComponent } from './lib/components/chat-container/chat-container.component';
export { ChatInputComponent } from './lib/components/chat-input/chat-input.component';
export { ChatMessageComponent } from './lib/components/chat-message/chat-message.component';
export { MessageMetadataComponent } from './lib/components/message-metadata/message-metadata.component';
export { TypingIndicatorComponent } from './lib/components/typing-indicator/typing-indicator.component';
export { ChartRendererComponent } from './lib/components/chart-renderer/chart-renderer.component';
export { ToolSelectorComponent } from './lib/components/tool-selector/tool-selector.component';
export { ConversationSidebarComponent } from './lib/components/conversation-sidebar/conversation-sidebar.component';

// Services
export { AgentService } from './lib/services/agent.service';
export { ConversationService, Conversation } from './lib/services/conversation.service';
export { ExportService } from './lib/services/export.service';

// Models
export {
  ChatRequest,
  AgentMetrics,
  ChatResponse,
  ChatMessage,
  HealthResponse,
  ToolInfo,
  ToolsResponse,
} from './lib/models/chat.models';
