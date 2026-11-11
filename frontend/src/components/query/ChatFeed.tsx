import React, { useRef, useEffect } from 'react';
import {
  MessageSquare,
  User,
  Bot,
  CheckCircle2,
  Clock,
  Sparkles,
  Search,
  Code2,
  ShieldCheck,
  Database,
  Loader2,
} from 'lucide-react';
import { QueryTurn } from '../../types';
import { SamplePrompts } from './SamplePrompts';
import { SqlCard } from './SqlCard';
import { DataTable } from './DataTable';
import { Badge, Card } from '../ui/Primitives';

interface ChatFeedProps {
  history: QueryTurn[];
  isQuerying: boolean;
  activeQuestion?: string;
  showSql: boolean;
  dialect?: string;
  onSelectPrompt: (prompt: string) => void;
}

export const ChatFeed: React.FC<ChatFeedProps> = ({
  history,
  isQuerying,
  activeQuestion,
  showSql,
  dialect = 'SQLITE',
  onSelectPrompt,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new turns
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history.length, isQuerying]);

  // Format ISO timestamp to readable time
  const formatTime = (isoString?: string) => {
    if (!isoString) return '';
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  // Render empty state
  if (history.length === 0 && !isQuerying) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-space-6 max-w-4xl mx-auto w-full">
        <Card className="w-full text-center p-space-8 border-dashed bg-card/60">
          <div className="w-16 h-16 rounded-2xl bg-accent-primary/10 border border-accent-primary/20 flex items-center justify-center text-accent-primary mx-auto mb-space-4">
            <MessageSquare className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-semibold tracking-tight text-primary mb-2">
            Ready to Query Your Data
          </h2>
          <p className="text-sm text-secondary max-w-md mx-auto mb-space-6 leading-relaxed">
            Ask questions in plain language across 10+ languages. DataMind translates questions to safe SQL with AST validation.
          </p>
          <SamplePrompts onSelectPrompt={onSelectPrompt} disabled={isQuerying} />
        </Card>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-space-4 space-y-space-6 max-w-5xl mx-auto w-full">
      {/* Sample Prompts Row at the Top */}
      <div className="pt-2 pb-space-2 border-b border-border-subtle">
        <SamplePrompts onSelectPrompt={onSelectPrompt} disabled={isQuerying} />
      </div>

      {/* Query Turns */}
      {history.map((turn, index) => (
        <div key={turn.query_id || index} className="space-y-space-3">
          {/* 1. User Message Bubble */}
          <div className="flex items-start justify-end gap-space-3">
            <div className="flex flex-col items-end max-w-2xl">
              <div className="flex items-center gap-space-2 mb-1">
                <span className="text-[11px] text-muted">{formatTime(turn.timestamp)}</span>
                <span className="text-xs font-semibold text-primary">You</span>
              </div>
              <div className="bg-accent-primary text-white rounded-2xl rounded-tr-sm px-space-4 py-space-3 text-sm shadow-sm leading-relaxed">
                {turn.question}
              </div>
            </div>
            <div className="w-8 h-8 rounded-full bg-accent-primary/20 border border-accent-primary/30 flex items-center justify-center text-accent-primary shrink-0 mt-1">
              <User className="w-4 h-4" />
            </div>
          </div>

          {/* 2. Assistant Response Block */}
          <div className="flex items-start gap-space-3">
            <div className="w-8 h-8 rounded-full bg-status-success-bg border border-status-success/30 flex items-center justify-center text-status-success shrink-0 mt-1">
              <Bot className="w-4 h-4" />
            </div>

            <div className="flex-1 max-w-4xl">
              <div className="flex items-center gap-space-2 mb-1">
                <span className="text-xs font-semibold text-primary">DataMind Governance Engine</span>
                <Badge variant={turn.status === 'ready' ? 'success' : turn.status === 'refused' ? 'warning' : 'error'} className="text-[10px]">
                  {turn.status.toUpperCase()}
                </Badge>
                {turn.telemetry?.total_latency_ms !== undefined && (
                  <span className="text-[11px] text-muted flex items-center gap-1 font-mono">
                    <Clock className="w-3 h-3" />
                    {Math.round(turn.telemetry.total_latency_ms)}ms
                  </span>
                )}
              </div>

              {/* Lifecycle Stage Stepper */}
              <div className="w-full bg-canvas/60 border border-border-subtle rounded-xl p-space-3 my-space-2">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  {/* Stage 1: FAISS Retrieval */}
                  <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-card border border-border-subtle">
                    <CheckCircle2 className="w-3.5 h-3.5 text-status-success shrink-0" />
                    <div className="flex flex-col min-w-0">
                      <span className="text-[11px] font-medium text-primary truncate">1. FAISS Retrieval</span>
                      <span className="text-[10px] text-muted font-mono">
                        {turn.telemetry?.retrieval_latency_ms !== undefined
                          ? `${Math.round(turn.telemetry.retrieval_latency_ms)}ms`
                          : 'cached'}
                      </span>
                    </div>
                  </div>

                  {/* Stage 2: SQL Generation */}
                  <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-card border border-border-subtle">
                    <CheckCircle2 className="w-3.5 h-3.5 text-status-success shrink-0" />
                    <div className="flex flex-col min-w-0">
                      <span className="text-[11px] font-medium text-primary truncate">2. SQL Generation</span>
                      <span className="text-[10px] text-muted font-mono">
                        {turn.telemetry?.llm_latency_ms !== undefined
                          ? `${Math.round(turn.telemetry.llm_latency_ms)}ms`
                          : 'completed'}
                      </span>
                    </div>
                  </div>

                  {/* Stage 3: AST Validation */}
                  <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-card border border-border-subtle">
                    {turn.is_valid ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-status-success shrink-0" />
                    ) : (
                      <div className="w-3.5 h-3.5 rounded-full bg-status-error text-white flex items-center justify-center text-[9px] font-bold">
                        ✕
                      </div>
                    )}
                    <div className="flex flex-col min-w-0">
                      <span className="text-[11px] font-medium text-primary truncate">3. AST Validation</span>
                      <span className="text-[10px] text-muted font-mono">
                        {turn.is_valid ? '5/5 Passed' : 'Rejected'}
                      </span>
                    </div>
                  </div>

                  {/* Stage 4: DB Execution */}
                  <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-card border border-border-subtle">
                    {turn.status === 'ready' ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-status-success shrink-0" />
                    ) : (
                      <div className="w-3.5 h-3.5 rounded-full bg-status-warning text-white flex items-center justify-center text-[9px] font-bold">
                        —
                      </div>
                    )}
                    <div className="flex flex-col min-w-0">
                      <span className="text-[11px] font-medium text-primary truncate">4. DB Execution</span>
                      <span className="text-[10px] text-muted font-mono">
                        {turn.telemetry?.exec_latency_ms !== undefined
                          ? `${Math.round(turn.telemetry.exec_latency_ms)}ms`
                          : 'bypassed'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Generated SQL Card */}
              {showSql && turn.generated_sql && (
                <SqlCard
                  sql={turn.generated_sql}
                  dialect={dialect}
                  status={turn.status}
                  isValid={turn.is_valid}
                  errorMessage={turn.error_message}
                />
              )}

              {/* Result Visualizer (Table, Scalar KPI, or Error/Refusal Callout) */}
              <DataTable
                columns={turn.columns}
                rows={turn.rows}
                status={turn.status}
                errorMessage={turn.error_message}
                latencyMs={turn.telemetry?.total_latency_ms}
              />
            </div>
          </div>
        </div>
      ))}

      {/* 3. In-Progress Stepper when querying */}
      {isQuerying && (
        <div className="space-y-space-3">
          {activeQuestion && (
            <div className="flex items-start justify-end gap-space-3">
              <div className="flex flex-col items-end max-w-2xl">
                <div className="flex items-center gap-space-2 mb-1">
                  <span className="text-[11px] text-muted">Just now</span>
                  <span className="text-xs font-semibold text-primary">You</span>
                </div>
                <div className="bg-accent-primary text-white rounded-2xl rounded-tr-sm px-space-4 py-space-3 text-sm shadow-sm leading-relaxed">
                  {activeQuestion}
                </div>
              </div>
              <div className="w-8 h-8 rounded-full bg-accent-primary/20 border border-accent-primary/30 flex items-center justify-center text-accent-primary shrink-0 mt-1">
                <User className="w-4 h-4" />
              </div>
            </div>
          )}

          <div className="flex items-start gap-space-3">
            <div className="w-8 h-8 rounded-full bg-accent-primary/10 border border-accent-primary/30 flex items-center justify-center text-accent-primary shrink-0 mt-1">
              <Bot className="w-4 h-4" />
            </div>

            <div className="flex-1 max-w-4xl">
              <div className="flex items-center gap-space-2 mb-2">
                <span className="text-xs font-semibold text-primary">DataMind Governance Engine</span>
                <Badge variant="info" className="flex items-center gap-1 text-[10px]">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  <span>Processing Query...</span>
                </Badge>
              </div>

              {/* Animated Live Stepper */}
              <Card className="p-space-4 bg-canvas/80 border-border-subtle">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-card border border-accent-primary/30">
                    <Loader2 className="w-3.5 h-3.5 text-accent-primary animate-spin shrink-0" />
                    <span className="text-[11px] font-medium text-primary">Retrieving FAISS</span>
                  </div>
                  <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-card border border-border-subtle opacity-70">
                    <Sparkles className="w-3.5 h-3.5 text-secondary shrink-0" />
                    <span className="text-[11px] font-medium text-secondary">Generating SQL</span>
                  </div>
                  <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-card border border-border-subtle opacity-70">
                    <ShieldCheck className="w-3.5 h-3.5 text-secondary shrink-0" />
                    <span className="text-[11px] font-medium text-secondary">AST Validation</span>
                  </div>
                  <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-card border border-border-subtle opacity-70">
                    <Database className="w-3.5 h-3.5 text-secondary shrink-0" />
                    <span className="text-[11px] font-medium text-secondary">DB Execution</span>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
