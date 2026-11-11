import React from 'react';
import { Button } from '../ui/Primitives';

export interface PromptOption {
  label: string;
  icon: string;
  question: string;
}

export const SAMPLE_PROMPTS: PromptOption[] = [
  {
    label: 'Active Engineers',
    icon: '👷',
    question: 'How many active civil engineers are there?',
  },
  {
    label: 'GPP Project Staff',
    icon: '📂',
    question: 'Who is working on the GPP project?',
  },
  {
    label: 'Multilingual (Spanish)',
    icon: '🌐',
    question: '¿Cuántos empleados activos trabajan en Dubái?',
  },
  {
    label: 'Test Blocked Salary',
    icon: '🛡️',
    question: 'What is the average salary of employees?',
  },
];

interface SamplePromptsProps {
  onSelectPrompt: (prompt: string) => void;
  disabled?: boolean;
}

export const SamplePrompts: React.FC<SamplePromptsProps> = ({
  onSelectPrompt,
  disabled = false,
}) => {
  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-space-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted">
          Suggested Queries
        </span>
        <span className="text-xs text-secondary">
          Click any prompt to execute
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-space-3">
        {SAMPLE_PROMPTS.map((prompt) => (
          <Button
            key={prompt.label}
            variant="secondary"
            disabled={disabled}
            onClick={() => onSelectPrompt(prompt.question)}
            className="flex items-center justify-start text-left px-space-4 py-space-3 h-auto min-h-[44px] rounded-xl hover:border-accent-primary hover:bg-canvas transition-all group"
          >
            <span className="text-lg mr-space-2 shrink-0 group-hover:scale-110 transition-transform">
              {prompt.icon}
            </span>
            <div className="flex flex-col min-w-0">
              <span className="text-xs font-semibold text-primary truncate">
                {prompt.label}
              </span>
              <span className="text-xs text-secondary truncate">
                {prompt.question}
              </span>
            </div>
          </Button>
        ))}
      </div>
    </div>
  );
};
