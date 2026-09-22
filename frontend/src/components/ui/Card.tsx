import { type HTMLAttributes, forwardRef } from 'react';
import { cn } from '../../utils/cn';


export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'interactive' | 'panel' | 'outline' | 'glow';
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "transition-all duration-200",
          variant === 'default' && "meridian-card p-6",
          variant === 'interactive' && "meridian-card meridian-card-interactive p-6 cursor-pointer",
          variant === 'panel' && "meridian-panel p-4",
          variant === 'glow' && "meridian-card p-6",
          variant === 'outline' && "rounded-[16px] border border-[var(--color-hairline)] bg-transparent p-5",
          className
        )}
        {...props}
      />
    );
  }
);
Card.displayName = "Card";

export { Card };

