import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle } from 'lucide-react';
import { useStore } from '../../context/StoreContext';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  Button,
  Input,
} from '../ui/Primitives';

// ----------------------------------------------------------------------
// Policy & Governance Modal (UI-SPEC 9.1: Save Policy / Dismiss Alert)
// ----------------------------------------------------------------------
export interface PolicyModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const PolicyModal: React.FC<PolicyModalProps> = ({ open, onOpenChange }) => {
  const { blockedColumns, customRules, setBlockedColumns, setCustomRules } = useStore();
  const [columnsInput, setColumnsInput] = useState('');
  const [rulesInput, setRulesInput] = useState('');

  useEffect(() => {
    if (open) {
      setColumnsInput(blockedColumns.join(', '));
      setRulesInput(customRules || '');
    }
  }, [open, blockedColumns, customRules]);

  const handleSave = () => {
    const parsed = columnsInput
      .split(',')
      .map((c) => c.trim().toLowerCase())
      .filter((c) => c.length > 0);
    setBlockedColumns(parsed);
    setCustomRules(rulesInput.trim());
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-space-2 mb-1">
            <div className="p-2 rounded-lg bg-status-warning-bg text-status-warning">
              <Shield className="w-5 h-5" />
            </div>
            <DialogTitle>Configure Data Governance</DialogTitle>
          </div>
          <DialogDescription>
            Specify restricted columns and safety prompt guardrails enforced by sqlglot AST verification.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-space-4 py-space-2">
          <div>
            <label className="block text-xs font-semibold text-secondary mb-1">
              Restricted / Blocked Columns (comma-separated)
            </label>
            <Input
              value={columnsInput}
              onChange={(e) => setColumnsInput(e.target.value)}
              placeholder="salary, bonus, compensation, ssn, ..."
            />
            <p className="mt-1 text-xs text-muted">
              Any query referencing these columns will be refused with an AST policy block before execution.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-secondary mb-1">
              Custom Business Rules & Guardrails
            </label>
            <textarea
              rows={4}
              value={rulesInput}
              onChange={(e) => setRulesInput(e.target.value)}
              placeholder="e.g. Always filter active employees (employee_status = 'active') unless historical records are explicitly requested."
              className="w-full px-space-4 py-space-2 text-sm font-normal bg-input border border-border-subtle rounded-lg text-primary placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-accent-primary transition-all duration-150 resize-none"
            />
          </div>
        </div>

        <div className="flex items-center justify-end gap-space-2 pt-space-4 border-t border-border-subtle">
          <Button
            variant="secondary"
            onClick={() => onOpenChange(false)}
          >
            Dismiss Alert
          </Button>
          <Button
            variant="primary"
            onClick={handleSave}
          >
            Save Policy
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// ----------------------------------------------------------------------
// Clear Query History Modal (UI-SPEC 9.1.1: Destructive Confirmation)
// ----------------------------------------------------------------------
export interface ClearHistoryModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}

export const ClearHistoryModal: React.FC<ClearHistoryModalProps> = ({
  open,
  onOpenChange,
  onConfirm,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-space-2 mb-1">
            <div className="p-2 rounded-lg bg-status-error-bg text-status-error">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <DialogTitle>Clear Query History?</DialogTitle>
          </div>
          <DialogDescription>
            This will permanently remove all past queries in this session. This action cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <div className="flex items-center justify-end gap-space-2 pt-space-4 border-t border-border-subtle">
          <Button
            variant="secondary"
            onClick={() => onOpenChange(false)}
          >
            Dismiss Alert
          </Button>
          <Button
            variant="destructive"
            onClick={() => {
              onConfirm();
              onOpenChange(false);
            }}
          >
            Confirm Clear
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
