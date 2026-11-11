import React, { useMemo } from 'react';
import { Card } from '../ui/Primitives';
import { AuditLogEntry } from '../../types';

interface LatencyChartProps {
  logs: AuditLogEntry[];
}

export const LatencyChart: React.FC<LatencyChartProps> = ({ logs }) => {
  const breakdown = useMemo(() => {
    if (!logs || logs.length === 0) {
      return {
        retrievalMs: 25,
        llmMs: 550,
        execMs: 5,
        totalMs: 580,
      };
    }

    const n = logs.length;
    const sumRetrieval = logs.reduce((acc, l) => acc + (l.retrieval_latency_ms || 0), 0);
    const sumLlm = logs.reduce((acc, l) => acc + (l.llm_latency_ms || 0), 0);
    const sumExec = logs.reduce((acc, l) => acc + (l.exec_latency_ms || 0), 0);

    const retrievalMs = Math.round(sumRetrieval / n);
    const llmMs = Math.round(sumLlm / n);
    const execMs = Math.round(sumExec / n);
    const totalMs = Math.max(1, retrievalMs + llmMs + execMs);

    return {
      retrievalMs,
      llmMs,
      execMs,
      totalMs,
    };
  }, [logs]);

  const retrievalPct = Math.round((breakdown.retrievalMs / breakdown.totalMs) * 100) || 5;
  const execPct = Math.round((breakdown.execMs / breakdown.totalMs) * 100) || 2;
  const llmPct = Math.max(1, 100 - retrievalPct - execPct);

  return (
    <Card className="p-space-6 bg-card border-border-subtle mb-space-6">
      <div className="flex items-center justify-between mb-space-4">
        <div>
          <h3 className="text-sm font-semibold text-primary">
            Average Latency Stage Breakdown
          </h3>
          <p className="text-xs text-secondary mt-0.5">
            End-to-end stage telemetry across {logs.length} evaluated queries
          </p>
        </div>
        <div className="text-xs font-mono text-primary font-semibold">
          Avg Total: {breakdown.totalMs}ms
        </div>
      </div>

      {/* Stacked Horizontal Bar */}
      <div className="w-full h-8 rounded-xl bg-canvas border border-border-subtle overflow-hidden flex shadow-inner">
        {/* Stage 1: Retrieval */}
        <div
          style={{ width: `${retrievalPct}%` }}
          className="h-full bg-status-info hover:opacity-90 transition-all flex items-center justify-center text-[10px] font-mono font-semibold text-white truncate px-1"
          title={`Retrieval (FAISS): ${breakdown.retrievalMs}ms (${retrievalPct}%)`}
        >
          {retrievalPct > 8 && `${retrievalPct}%`}
        </div>

        {/* Stage 2: LLM Generation */}
        <div
          style={{ width: `${llmPct}%` }}
          className="h-full bg-accent-primary hover:opacity-90 transition-all flex items-center justify-center text-[10px] font-mono font-semibold text-white truncate px-1"
          title={`LLM Generation: ${breakdown.llmMs}ms (${llmPct}%)`}
        >
          {llmPct > 8 && `LLM (${llmPct}%)`}
        </div>

        {/* Stage 3: DB Execution */}
        <div
          style={{ width: `${execPct}%` }}
          className="h-full bg-status-success hover:opacity-90 transition-all flex items-center justify-center text-[10px] font-mono font-semibold text-white truncate px-1"
          title={`DB Execution: ${breakdown.execMs}ms (${execPct}%)`}
        >
          {execPct > 8 && `${execPct}%`}
        </div>
      </div>

      {/* Legend & Breakdown Items */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-space-4 mt-space-4 pt-space-3 border-t border-border-subtle text-xs">
        {/* Retrieval */}
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-sm bg-status-info shrink-0" />
          <div className="flex flex-col">
            <span className="text-secondary text-[11px]">1. Retrieval (FAISS)</span>
            <span className="font-mono text-primary font-semibold">
              {breakdown.retrievalMs}ms{' '}
              <span className="text-muted font-normal">({retrievalPct}%)</span>
            </span>
          </div>
        </div>

        {/* LLM Generation */}
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-sm bg-accent-primary shrink-0" />
          <div className="flex flex-col">
            <span className="text-secondary text-[11px]">2. LLM Synthesis</span>
            <span className="font-mono text-primary font-semibold">
              {breakdown.llmMs}ms{' '}
              <span className="text-muted font-normal">({llmPct}%)</span>
            </span>
          </div>
        </div>

        {/* DB Execution */}
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-sm bg-status-success shrink-0" />
          <div className="flex flex-col">
            <span className="text-secondary text-[11px]">3. DB Execution</span>
            <span className="font-mono text-primary font-semibold">
              {breakdown.execMs}ms{' '}
              <span className="text-muted font-normal">({execPct}%)</span>
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
};
