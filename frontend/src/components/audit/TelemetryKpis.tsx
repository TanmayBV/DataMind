import React, { useMemo } from 'react';
import { FileText, CheckCircle2, Clock, ShieldAlert } from 'lucide-react';
import { Card } from '../ui/Primitives';
import { AuditLogEntry } from '../../types';

interface TelemetryKpisProps {
  logs: AuditLogEntry[];
  totalLogs: number;
}

export const TelemetryKpis: React.FC<TelemetryKpisProps> = ({ logs, totalLogs }) => {
  const metrics = useMemo(() => {
    const total = totalLogs || logs.length;
    if (logs.length === 0) {
      return {
        total: 0,
        successRate: '100%',
        avgLatencyMs: 0,
        rejectionCount: 0,
      };
    }

    const successes = logs.filter((l) => l.status === 'ready' && l.is_valid === 1).length;
    const rejections = logs.filter(
      (l) => l.status === 'refused' || l.status === 'invalid' || l.is_valid === 0
    ).length;

    const rate = logs.length > 0 ? ((successes / logs.length) * 100).toFixed(1) : '100';

    const sumLatency = logs.reduce((acc, curr) => acc + (curr.total_latency_ms || 0), 0);
    const avgLatency = Math.round(sumLatency / logs.length);

    return {
      total,
      successRate: `${rate}%`,
      avgLatencyMs: avgLatency,
      rejectionCount: rejections,
    };
  }, [logs, totalLogs]);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-space-4 mb-space-6">
      {/* 1. Total Queries Logged */}
      <Card className="p-space-4 bg-card border-border-subtle hover:border-border-prominent transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-secondary uppercase tracking-wider">
            Total Queries Logged
          </span>
          <div className="p-1.5 rounded-lg bg-accent-primary/10 text-accent-primary">
            <FileText className="w-4 h-4" />
          </div>
        </div>
        <div className="text-2xl font-bold text-primary tracking-tight">
          {metrics.total}
        </div>
        <span className="text-[11px] text-muted">Across all sessions</span>
      </Card>

      {/* 2. Success Rate */}
      <Card className="p-space-4 bg-card border-border-subtle hover:border-border-prominent transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-secondary uppercase tracking-wider">
            Success Rate
          </span>
          <div className="p-1.5 rounded-lg bg-status-success-bg text-status-success">
            <CheckCircle2 className="w-4 h-4" />
          </div>
        </div>
        <div className="text-2xl font-bold text-status-success tracking-tight">
          {metrics.successRate}
        </div>
        <span className="text-[11px] text-muted">AST verified safe executions</span>
      </Card>

      {/* 3. Average Latency */}
      <Card className="p-space-4 bg-card border-border-subtle hover:border-border-prominent transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-secondary uppercase tracking-wider">
            Average Latency
          </span>
          <div className="p-1.5 rounded-lg bg-status-info/10 text-status-info">
            <Clock className="w-4 h-4" />
          </div>
        </div>
        <div className="text-2xl font-bold text-primary tracking-tight font-mono">
          {metrics.avgLatencyMs}
          <span className="text-sm font-normal text-muted ml-1">ms</span>
        </div>
        <span className="text-[11px] text-muted">Retrieval + LLM + DB execution</span>
      </Card>

      {/* 4. Policy Refusals & AST Rejections */}
      <Card className="p-space-4 bg-card border-border-subtle hover:border-border-prominent transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-secondary uppercase tracking-wider">
            Blocked & Refused
          </span>
          <div className="p-1.5 rounded-lg bg-status-warning-bg text-status-warning">
            <ShieldAlert className="w-4 h-4" />
          </div>
        </div>
        <div className="text-2xl font-bold text-status-warning tracking-tight">
          {metrics.rejectionCount}
        </div>
        <span className="text-[11px] text-muted">Restricted columns or syntax failures</span>
      </Card>
    </div>
  );
};
