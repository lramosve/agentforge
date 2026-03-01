import { InjectionToken } from '@angular/core';

export interface AgentForgeConfig {
  apiUrl: string;
  storagePrefix?: string;
  suggestions?: string[];
}

export const AF_CONFIG = new InjectionToken<AgentForgeConfig>('AF_CONFIG');
