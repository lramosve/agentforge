export interface ChatRequest {
  message: string;
  conversation_id?: string;
  ghostfolio_token?: string;
}

export interface AgentMetrics {
  task_id: string;
  duration_seconds: number;
  iterations: number;
  total_tokens: number;
  input_tokens: number;
  output_tokens: number;
  total_cost_usd: number;
  tools_called: string[];
  success: boolean;
  error: string | null;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  tools_used: string[];
  confidence: number;
  metrics: AgentMetrics;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
  tools_used?: string[];
  confidence?: number;
  metrics?: AgentMetrics;
  loading?: boolean;
}

export interface HealthResponse {
  status: string;
  agent: string;
}

export interface ToolInfo {
  name: string;
  description: string;
}

export interface ToolsResponse {
  tools: ToolInfo[];
}
