import React, { useEffect } from 'react';
import {
  X,
  Copy,
  Check,
  Terminal,
  ShieldCheck,
  ShieldAlert,
  Clock,
  Database,
  Lock,
} from 'lucide-react';
import { AuditLogEntry } from '../../types';
import { Badge, Button } from '../ui/Primitives';

interface TraceDrawerProps {
  trace: AuditLogEntry | null;
  onClose: () => void;
}

export const TraceDrawer: React.FC<TraceDrawerProps> = ({ trace, onClose }) => {
  const [copied, setCopied] = React.useState(false);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!trace) return null;

  const handleCopySql = () => {
    if (!trace.generated_sql) return;
    navigator.clipboard.writeText(trace.generated_sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const statusVariant =
    trace.status === 'ready'
      ? 'success'
      : trace.status === 'refused'
      ? 'warning'
      : 'error';

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-xs transition-opacity animate-in fade-in duration-150"
        onClick={onClose}
      />

      {/* Slide-out Drawer */}
      <div className="relative w-full max-w-xl h-full bg-card border-l border-border-prominent shadow-2xl flex flex-col z-50 animate-in slide-in-from-right duration-200 overflow-hidden">
        {/* Drawer Header */}
        <div className="flex items-center justify-between p-space-4 border-b border-border-subtle bg-canvas/60">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-accent-primary" />
            <h3 className="text-sm font-semibold text-primary">Query Trace Inspection</h3>
            <Badge variant={statusVariant} className="uppercase text-[10px]">
              {trace.status}
            </Badge>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 min-h-[32px] px-2 text-xs text-secondary hover:text-primary gap-1"
          >
            <X className="w-3.5 h-3.5" />
            <span>Dismiss Alert</span>
          </Button>
        </div>

        {/* Drawer Content */}
        <div className="flex-1 overflow-y-auto p-space-6 space-y-space-6">
          {/* Metadata Grid */}
          <div className="grid grid-cols-2 gap-space-3 p-space-3 rounded-xl bg-canvas border border-border-subtle text-xs">
            <div>
              <span className="text-muted block text-[10px] uppercase font-mono">Query ID</span>
              <span className="font-mono text-primary font-medium">{trace.query_id}</span>
            </div>
            <div>
              <span className="text-muted block text-[10px] uppercase font-mono">Timestamp</span>
              <span className="text-primary">{new Date(trace.timestamp).toLocaleString()}</span>
            </div>
            <div>
              <span className="text-muted block text-[10px] uppercase font-mono">AST Validation</span>
              <span className="flex items-center gap-1 font-semibold text-primary">
                {trace.is_valid ? (
                  <>
                    <ShieldCheck className="w-3.5 h-3.5 text-status-success" />
                    <span>Safe (Passed)</span>
                  </>
                ) : (
                  <>
                    <ShieldAlert className="w-3.5 h-3.5 text-status-error" />
                    <span>Rejected / Refused</span>
                  </>
                )}
              </span>
            </div>
            <div>
              <span className="text-muted block text-[10px] uppercase font-mono">Rows Returned</span>
              <span className="font-mono text-primary font-semibold">{trace.rows_returned}</span>
            </div>
          </div>

          {/* User Prompt */}
          <div>
            <h4 className="text-xs font-semibold text-secondary uppercase tracking-wider mb-2">
              Natural Language Prompt
            </h4>
            <div className="p-space-3 rounded-xl bg-canvas border border-border-subtle text-sm text-primary leading-relaxed">
              "{trace.question}"
            </div>
          </div>

          {/* Generated SQL & AST Report */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-semibold text-secondary uppercase tracking-wider">
                Generated SQL & AST Report
              </h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopySql}
                className="h-7 min-h-[28px] px-2 text-[11px] gap-1 text-secondary"
              >
                {copied ? (
                  <>
                    <Check className="w-3 h-3 text-status-success" />
                    <span className="text-status-success">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    <span>Copy SQL</span>
                  </>
                )}
              </Button>
            </div>
            <pre className="p-space-4 rounded-xl bg-canvas border border-border-subtle font-mono text-xs text-primary leading-relaxed overflow-x-auto">
              <code>{trace.generated_sql || '-- No SQL generated'}</code>
            </pre>
          </div>

          {/* Latency Stage Breakdown */}
          <div>
            <h4 className="text-xs font-semibold text-secondary uppercase tracking-wider mb-space-3">
              Lifecycle Stage Latencies
            </h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-2 rounded-lg bg-canvas border border-border-subtle text-xs">
                <span className="text-secondary flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-status-info" />
                  1. Semantic Retrieval (FAISS)
                </span>
                <span className="font-mono font-semibold text-primary">
                  {Math.round(trace.retrieval_latency_ms)}ms
                </span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-canvas border border-border-subtle text-xs">
                <span className="text-secondary flex items-center gap-1.5">
                  <Terminal className="w-3.5 h-3.5 text-accent-primary" />
                  2. LLM Formulation & Synthesis
                </span>
                <span className="font-mono font-semibold text-primary">
                  {Math.round(trace.llm_latency_ms)}ms
                </span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-canvas border border-border-subtle text-xs">
                <span className="text-secondary flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-status-success" />
                  3. AST Verification & DB Execution
                </span>
                <span className="font-mono font-semibold text-primary">
                  {Math.round(trace.exec_latency_ms)}ms
                </span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-card border border-accent-primary/30 text-xs font-semibold">
                <span className="text-primary flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-accent-primary" />
                  Total Pipeline Latency
                </span>
                <span className="font-mono text-accent-primary text-sm">
                  {Math.round(trace.total_latency_ms)}ms
                </span>
              </div>
            </div>
          </div>

          {/* Policy & PII Protection Summary */}
          <div className="p-space-4 rounded-xl bg-status-info/10 border border-status-info/20 text-xs">
            <div className="flex items-center gap-2 text-status-info font-semibold mb-1">
              <Lock className="w-4 h-4" />
              <span>Governance & PII Masking Protection</span>
            </div>
            <p className="text-secondary leading-relaxed">
              Every query is analyzed with AST syntactic trees before execution. Restricted columns (salary, ssn, bonus, compensation) are barred from projection. All executed queries are immutable in query audit logs.
            </p>
          </div>
        </div>

        {/* Drawer Footer */}
        <div className="p-space-4 border-t border-border-subtle bg-canvas/40 flex justify-end">
          <Button variant="outline" onClick={onClose} className="px-space-4">
            Dismiss Alert
          </Button>
        </div>
      </div>
    </div>
  );
};
