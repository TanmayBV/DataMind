import React, { useState, useRef, useEffect } from 'react';
import { CornerDownLeft, Trash2 } from 'lucide-react';
import { Button, Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../ui/Primitives';

interface QueryInputProps {
  onExecute: (question: string) => void;
  onClearHistory: () => void;
  isLoading: boolean;
  hasHistory: boolean;
  value?: string;
  onChangeValue?: (val: string) => void;
}

export const QueryInput: React.FC<QueryInputProps> = ({
  onExecute,
  onClearHistory,
  isLoading,
  hasHistory,
  value: externalValue,
  onChangeValue,
}) => {
  const [internalValue, setInternalValue] = useState('');
  const [clearDialogOpen, setClearDialogOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const queryText = externalValue !== undefined ? externalValue : internalValue;

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    if (onChangeValue) {
      onChangeValue(val);
    } else {
      setInternalValue(val);
    }
  };

  // Auto-grow textarea up to 120px
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 120)}px`;
    }
  }, [queryText]);

  const handleSubmit = () => {
    const trimmed = queryText.trim();
    if (!trimmed || isLoading) return;
    onExecute(trimmed);
    if (onChangeValue) {
      onChangeValue('');
    } else {
      setInternalValue('');
    }
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleConfirmClear = () => {
    onClearHistory();
    setClearDialogOpen(false);
  };

  return (
    <div className="w-full bg-card border-t border-border-subtle p-space-4 transition-colors">
      <div className="max-w-5xl mx-auto flex flex-col gap-space-2">
        <div className="relative flex items-end gap-space-2 bg-input border border-border-subtle rounded-xl p-space-2 focus-within:border-accent-primary focus-within:ring-2 focus-within:ring-accent-primary/20 transition-all">
          <textarea
            ref={textareaRef}
            rows={1}
            value={queryText}
            onChange={handleTextChange}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Ask a question about your database in any language (English, Spanish, Hindi, French, German)..."
            className="flex-1 bg-transparent border-0 text-sm font-normal text-primary placeholder:text-muted resize-none focus:outline-none p-space-2 leading-relaxed min-h-[44px] max-h-[120px]"
          />

          <div className="flex items-center gap-space-2 pb-1 pr-1 shrink-0">
            {hasHistory && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setClearDialogOpen(true)}
                disabled={isLoading}
                title="Clear query history"
                className="w-10 h-10 min-h-[40px] min-w-[40px] text-secondary hover:text-destructive hover:bg-status-error-bg/30 rounded-lg"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            )}

            <Button
              variant="primary"
              onClick={handleSubmit}
              disabled={isLoading || !queryText.trim()}
              isLoading={isLoading}
              className="h-10 min-h-[40px] px-space-4 gap-1.5 text-xs font-semibold rounded-lg shadow-sm"
            >
              <span>Execute Query</span>
              <CornerDownLeft className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>

        <div className="flex items-center justify-between text-[11px] text-muted px-1">
          <span>
            Press <kbd className="px-1.5 py-0.5 rounded bg-canvas border border-border-subtle font-mono text-[10px]">Enter</kbd> to submit, <kbd className="px-1.5 py-0.5 rounded bg-canvas border border-border-subtle font-mono text-[10px]">Shift+Enter</kbd> for new line
          </span>
          <span>5-Stage AST Governance Pipeline Active</span>
        </div>
      </div>

      {/* Confirmation Modal for Clearing History */}
      <Dialog open={clearDialogOpen} onOpenChange={setClearDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Clear Query History?</DialogTitle>
            <DialogDescription>
              This will permanently remove all past queries in this session. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-space-4">
            <Button
              variant="outline"
              onClick={() => setClearDialogOpen(false)}
            >
              Dismiss Alert
            </Button>
            <Button
              variant="destructive"
              onClick={handleConfirmClear}
            >
              Confirm Clear
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
