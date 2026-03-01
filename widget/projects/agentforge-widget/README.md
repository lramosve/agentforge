# AgentForge Widget

AI financial agent chat widget for Angular 21+.

## Installation

```bash
npm install @lramosve/agentforge-widget
```

### Peer Dependencies

Ensure these are installed in your project:

```bash
npm install @angular/common @angular/core @angular/forms @angular/platform-browser chart.js marked ngx-markdown rxjs
```

### Material Icons

Add the Material Icons Round font to your `index.html`:

```html
<link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">
```

Optionally add the Inter font for best typography:

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

## Quick Start

### 1. Configure providers

```typescript
// app.config.ts
import { provideAgentForge } from '@lramosve/agentforge-widget';

export const appConfig: ApplicationConfig = {
  providers: [
    provideAgentForge({
      apiUrl: 'https://your-backend-url.com',
    }),
  ],
};
```

### 2. Use the widget

```typescript
// any component
import { AgentForgeWidgetComponent } from '@lramosve/agentforge-widget';

@Component({
  imports: [AgentForgeWidgetComponent],
  template: `<af-widget />`,
  styles: `:host { display: block; height: 100vh; }`,
})
export class MyComponent {}
```

## Configuration

The `provideAgentForge()` function accepts a config object:

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `apiUrl` | `string` | Yes | — | Backend API base URL |
| `storagePrefix` | `string` | No | `'af'` | Prefix for localStorage keys |
| `suggestions` | `string[]` | No | Portfolio prompts | Empty-state suggestion chips |

## CSS Theming

The widget uses CSS custom properties prefixed with `--af-`. Override them to match your brand:

```css
.af-widget {
  --af-accent: #3b82f6;
  --af-accent-bg: rgba(59, 130, 246, 0.08);
  --af-user-bubble: #3b82f6;
  --af-radius: 8px;
}
```

SCSS partials are available at `@lramosve/agentforge-widget/styles/`:

```scss
@use '@lramosve/agentforge-widget/styles/variables';
@use '@lramosve/agentforge-widget/styles/animations';
@use '@lramosve/agentforge-widget/styles/markdown';
```

## Features

- Response streaming via SSE
- Multi-conversation tabs with persistence
- Message pinning and copy-to-clipboard
- Markdown rendering with syntax highlighting
- Inline Chart.js visualizations
- CSV and Markdown export
- Light/dark theme toggle
- Keyboard shortcuts (Ctrl+/, Ctrl+L, Esc)
- Configurable suggestion chips
- Tool selector dropdown

## API Endpoints

The widget expects these backend endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agent/health` | GET | Health check |
| `/api/agent/chat` | POST | Non-streaming chat |
| `/api/agent/chat-stream` | POST | SSE streaming chat |
| `/api/agent/tools` | GET | Available tools |
| `/api/agent/feedback` | POST | Submit feedback |

## License

MIT
