'use client';

import { clsx } from 'clsx';

interface ConnectionStatusProps {
  connected: boolean;
  reconnecting: boolean;
  agentId: string;
}

export function ConnectionStatus({ connected, reconnecting, agentId }: ConnectionStatusProps) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-gray-600">Agent: <span className="font-medium">{agentId}</span></span>
      <div className="flex items-center gap-2">
        <span
          className={clsx(
            'h-2.5 w-2.5 rounded-full',
            connected
              ? 'bg-green-500'
              : reconnecting
              ? 'bg-yellow-500 animate-pulse'
              : 'bg-red-500'
          )}
        />
        <span className="text-sm text-gray-500">
          {connected ? 'Connected' : reconnecting ? 'Reconnecting...' : 'Disconnected'}
        </span>
      </div>
    </div>
  );
}
