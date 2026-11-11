import React, { useState } from 'react';
import { Copy, Check, Terminal, ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';
import { Badge, Button } from '../ui/Primitives';
import { QueryStatus } from '../../types';

interface SqlCardProps {
  sql: string;
  dialect?: string;
  status: QueryStatus;
  isValid: boolean;
  errorMessage?: string | null;
}

export const SqlCard: React.FC<SqlCardProps> = ({
  sql,
  dialect = 'SQLITE',
  status,
  isValid,
  errorMessage,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!sql) return;
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Syntax highlighting tokenization
  const renderHighlightedSql = (rawSql: string) => {
    if (!rawSql) return null;
    const keywords = /\b(SELECT|FROM|WHERE|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|ON|GROUP BY|ORDER BY|HAVING|LIMIT|AND|OR|NOT|IN|AS|COUNT|SUM|AVG|MAX|MIN|DISTINCT|LIKE|BETWEEN|CASE|WHEN|THEN|ELSE|END|IS|NULL)\b/gi;
    const parts = rawSql.split(keywords);

    return parts.map((part, index) => {
      if (keywords.test(part)) {
        return (
          <span key={index} className="text-accent-primary font-semibold">
            {part.toUpperCase()}
          </span>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className="w-full rounded-xl bg-canvas border border-border-subtle overflow-hidden my-space-3">
      {/* Top Header Bar */}
      <div className="flex items-center justify-between px-space-4 py-2 bg-card border-b border-border-subtle text-xs">
        <div className="flex items-center gap-space-2">
          <Terminal className="w-3.5 h-3.5 text-secondary" />
          <span className="font-semibold text-secondary uppercase tracking-wider text-xs">
            Generated SQL
          </span>
          <Badge variant="neutral" className="uppercase font-mono text-[10px] tracking-wide">
            {dialect}
          </Badge>
        </div>

        <div className="flex items-center gap-space-2">
          {/* AST Status Pill */}
          {status === 'ready' && isValid && (
            <Badge variant="success" className="flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" />
              <span>AST Validated Safe</span>
            </Badge>
          )}

          {status === 'refused' && (
            <Badge variant="warning" className="flex items-center gap-1">
              <ShieldAlert className="w-3 h-3" />
              <span>Policy Refusal</span>
            </Badge>
          )}

          {(status === 'invalid' || (!isValid && status !== 'refused')) && (
            <Badge variant="error" className="flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              <span>AST Syntax Error</span>
            </Badge>
          )}

          {/* Copy SQL Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="h-8 min-h-[32px] px-2 text-xs text-secondary hover:text-primary gap-1"
            title="Copy SQL to clipboard"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-status-success" />
                <span className="text-status-success font-medium">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy SQL</span>
              </>
            )}
          </Button>
        </div>
      </div>

      {/* SQL Query Body */}
      <div className="p-space-4 overflow-x-auto font-mono text-xs leading-relaxed text-primary">
        <code>{renderHighlightedSql(sql || '-- No SQL generated')}</code>
      </div>

      {/* Validation Error Footnote if present */}
      {errorMessage && (status === 'invalid' || !isValid) && (
        <div className="px-space-4 py-2 bg-status-error-bg/60 border-t border-status-error/20 text-xs text-status-error flex items-start gap-2">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
};
