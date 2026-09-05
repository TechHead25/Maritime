import React from 'react';

interface StatusMessageProps {
  type: 'error' | 'warning' | 'info' | 'loading';
  message: string;
  onRetry?: () => void;
}

/**
 * Reusable banner component for displaying status messages.
 * Uses ARIA role="alert" for accessibility and supports a retry button.
 */
const StatusMessage: React.FC<StatusMessageProps> = ({ type, message, onRetry }) => {
  const baseStyles = 'p-4 rounded-md mb-4 text-sm flex items-center';
  const typeStyles: Record<string, string> = {
    error: 'bg-red-100 text-red-800 border border-red-300',
    warning: 'bg-yellow-100 text-yellow-800 border border-yellow-300',
    info: 'bg-blue-100 text-blue-800 border border-blue-300',
    loading: 'bg-gray-100 text-gray-800 border border-gray-300',
  };

  return (
    <div role="alert" className={`${baseStyles} ${typeStyles[type]}`}>
      <span>{message}</span>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="ml-4 underline text-sm"
        >
          Retry
        </button>
      )}
    </div>
  );
};

export default StatusMessage;
