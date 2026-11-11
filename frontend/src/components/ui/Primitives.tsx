import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Loader2, X } from 'lucide-react';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ----------------------------------------------------------------------
// Button Component (UI-SPEC 2.2: min 44x44px touch target)
// ----------------------------------------------------------------------
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
  size?: 'default' | 'sm' | 'icon';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'default', isLoading, disabled, children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center min-h-[44px] min-w-[44px] rounded-lg text-sm font-semibold transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary disabled:opacity-50 disabled:cursor-not-allowed select-none cursor-pointer';

    const variants = {
      primary: 'bg-accent-primary text-white hover:bg-accent-hover shadow-sm',
      secondary: 'bg-card text-primary border border-border-subtle hover:bg-canvas',
      outline: 'border border-border-prominent text-primary hover:bg-card',
      ghost: 'text-secondary hover:text-primary hover:bg-card',
      destructive: 'bg-destructive text-white hover:bg-destructive-hover shadow-sm',
    };

    const sizes = {
      default: 'px-space-4 py-space-2 gap-space-2',
      sm: 'px-space-2 py-1 gap-1 text-xs',
      icon: 'p-space-2 w-[44px] h-[44px]',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin text-current" />
        ) : null}
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';

// ----------------------------------------------------------------------
// Badge Component (UI-SPEC 3.1: 12px semi-bold font)
// ----------------------------------------------------------------------
export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'success' | 'error' | 'warning' | 'info' | 'neutral';
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'neutral',
  children,
  ...props
}) => {
  const variants = {
    success: 'bg-status-success-bg text-status-success border border-status-success/20',
    error: 'bg-status-error-bg text-status-error border border-status-error/20',
    warning: 'bg-status-warning-bg text-status-warning border border-status-warning/20',
    info: 'bg-status-info/10 text-status-info border border-status-info/20',
    neutral: 'bg-canvas text-secondary border border-border-subtle',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold leading-normal transition-colors select-none',
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};

// ----------------------------------------------------------------------
// Card Component (UI-SPEC 2.1: 8-pt padding space-4)
// ----------------------------------------------------------------------
export const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'bg-card border border-border-subtle rounded-xl p-space-4 shadow-sm text-primary transition-colors',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
);
Card.displayName = 'Card';

// ----------------------------------------------------------------------
// Input Component (UI-SPEC 2.2: 44px height, 14px body text)
// ----------------------------------------------------------------------
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'min-h-[44px] h-[44px] w-full px-space-4 text-sm font-normal bg-input border rounded-lg text-primary placeholder:text-muted transition-all duration-150 focus:outline-none focus:ring-2',
        error
          ? 'border-status-error focus:ring-status-error'
          : 'border-border-subtle focus:border-accent-primary focus:ring-accent-primary/20',
        className
      )}
      {...props}
    />
  )
);
Input.displayName = 'Input';

// ----------------------------------------------------------------------
// Accessible Dialog / Modal Component (UI-SPEC Section 5 & 9)
// ----------------------------------------------------------------------
interface DialogContextType {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const DialogContext = createContext<DialogContextType | undefined>(undefined);

export const Dialog: React.FC<{
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}> = ({ open: controlledOpen, onOpenChange, children }) => {
  const [uncontrolledOpen, setUncontrolledOpen] = useState(false);
  const open = controlledOpen !== undefined ? controlledOpen : uncontrolledOpen;
  const handleOpenChange = onOpenChange || setUncontrolledOpen;

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        handleOpenChange(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, handleOpenChange]);

  return (
    <DialogContext.Provider value={{ open, onOpenChange: handleOpenChange }}>
      {children}
    </DialogContext.Provider>
  );
};

export const DialogTrigger: React.FC<{
  asChild?: boolean;
  children: React.ReactElement<{ onClick?: (e: React.MouseEvent) => void }>;
}> = ({ children }) => {
  const context = useContext(DialogContext);
  if (!context) return children;

  return React.cloneElement(children, {
    onClick: (e: React.MouseEvent) => {
      children.props.onClick?.(e);
      context.onOpenChange(true);
    },
  });
};

export const DialogContent: React.FC<{
  className?: string;
  children: React.ReactNode;
}> = ({ className, children }) => {
  const context = useContext(DialogContext);
  if (!context || !context.open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-space-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          context.onOpenChange(false);
        }
      }}
    >
      <div
        className={cn(
          'relative w-full max-w-lg bg-card border border-border-prominent rounded-xl p-space-6 shadow-2xl text-primary animate-in zoom-in-95 duration-150',
          className
        )}
      >
        <button
          type="button"
          aria-label="Dismiss Alert"
          onClick={() => context.onOpenChange(false)}
          className="absolute top-space-4 right-space-4 p-2 text-secondary hover:text-primary rounded-lg min-w-[36px] min-h-[36px] flex items-center justify-center cursor-pointer transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
        {children}
      </div>
    </div>
  );
};

export const DialogHeader: React.FC<{ className?: string; children: React.ReactNode }> = ({
  className,
  children,
}) => (
  <div className={cn('flex flex-col space-y-1.5 mb-space-4', className)}>
    {children}
  </div>
);

export const DialogTitle: React.FC<{ className?: string; children: React.ReactNode }> = ({
  className,
  children,
}) => (
  <h2 className={cn('text-2xl font-semibold leading-tight tracking-tight text-primary', className)}>
    {children}
  </h2>
);

export const DialogDescription: React.FC<{ className?: string; children: React.ReactNode }> = ({
  className,
  children,
}) => (
  <p className={cn('text-sm font-normal text-secondary leading-relaxed', className)}>
    {children}
  </p>
);

export const DialogFooter: React.FC<{ className?: string; children: React.ReactNode }> = ({
  className,
  children,
}) => (
  <div className={cn('flex items-center justify-end gap-space-2 mt-space-6', className)}>
    {children}
  </div>
);

export const DialogClose: React.FC<{
  asChild?: boolean;
  children: React.ReactElement<{ onClick?: (e: React.MouseEvent) => void }>;
}> = ({ children }) => {
  const context = useContext(DialogContext);
  return React.cloneElement(children, {
    onClick: (e: React.MouseEvent) => {
      children.props.onClick?.(e);
      context?.onOpenChange(false);
    },
  });
};

// ----------------------------------------------------------------------
// Tooltip Component (UI-SPEC 5: 200ms delay tooltip)
// ----------------------------------------------------------------------
export const Tooltip: React.FC<{
  content: string | React.ReactNode;
  children: React.ReactNode;
}> = ({ content, children }) => {
  const [visible, setVisible] = useState(false);
  const timeoutRef = useRef<number | null>(null);

  const show = () => {
    timeoutRef.current = window.setTimeout(() => setVisible(true), 200);
  };

  const hide = () => {
    if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
    setVisible(false);
  };

  return (
    <div
      className="relative inline-flex items-center"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      {visible && (
        <div
          role="tooltip"
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 text-xs font-normal text-white bg-slate-900 border border-slate-700 rounded shadow-lg whitespace-nowrap z-dropdown pointer-events-none"
        >
          {content}
        </div>
      )}
    </div>
  );
};

// ----------------------------------------------------------------------
// Accessible Tabs Component (UI-SPEC 5: Navigation tabs)
// ----------------------------------------------------------------------
interface TabsContextType {
  value: string;
  onValueChange: (value: string) => void;
}

const TabsContext = createContext<TabsContextType | undefined>(undefined);

export const Tabs: React.FC<{
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
  children: React.ReactNode;
}> = ({ value, onValueChange, className, children }) => (
  <TabsContext.Provider value={{ value, onValueChange }}>
    <div className={cn('w-full flex flex-col', className)}>{children}</div>
  </TabsContext.Provider>
);

export const TabsList: React.FC<{ className?: string; children: React.ReactNode }> = ({
  className,
  children,
}) => (
  <div
    role="tablist"
    className={cn(
      'flex items-center gap-space-2 p-1 bg-canvas border border-border-subtle rounded-xl select-none',
      className
    )}
  >
    {children}
  </div>
);

export const TabsTrigger: React.FC<{
  value: string;
  className?: string;
  children: React.ReactNode;
}> = ({ value, className, children }) => {
  const context = useContext(TabsContext);
  if (!context) return null;
  const isSelected = context.value === value;

  return (
    <button
      role="tab"
      aria-selected={isSelected}
      type="button"
      onClick={() => context.onValueChange(value)}
      className={cn(
        'min-h-[44px] px-space-4 py-space-2 rounded-lg text-sm font-semibold transition-all duration-150 cursor-pointer flex items-center gap-2',
        isSelected
          ? 'bg-card text-accent-primary shadow-sm border border-border-subtle'
          : 'text-secondary hover:text-primary hover:bg-card/50',
        className
      )}
    >
      {children}
    </button>
  );
};

export const TabsContent: React.FC<{
  value: string;
  className?: string;
  children: React.ReactNode;
}> = ({ value, className, children }) => {
  const context = useContext(TabsContext);
  if (!context || context.value !== value) return null;

  return (
    <div
      role="tabpanel"
      className={cn('flex-1 focus-visible:outline-none', className)}
    >
      {children}
    </div>
  );
};
