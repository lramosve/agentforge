import { Component } from '@angular/core';
import { AgentForgeWidgetComponent } from '@lramosve/agentforge-widget';

@Component({
  selector: 'af-root',
  standalone: true,
  imports: [AgentForgeWidgetComponent],
  template: `<af-widget />`,
  styles: `
    :host {
      display: block;
      height: 100vh;
      height: 100dvh;
    }
  `,
})
export class AppComponent {}
