
import type { PortalLink } from '../hooks/useLivePortal'
import type { NetworkNode } from '../types/network'

export default function Header({
  nodes,
  link = 'live',
}: {
  nodes: NetworkNode[]
  link?: PortalLink
}) {
  const onlineCount = nodes.filter(
    node => node.status === 'ONLINE'
  ).length

  const healthy = nodes.length > 0 && onlineCount === nodes.length
  const hasAny = nodes.length > 0

  const statusClass = !hasAny
    ? 'down'
    : healthy
      ? 'up'
      : 'degraded'

  const label = !hasAny
    ? 'No nodes'
    : `${onlineCount}/${nodes.length} nodes`

  return (
    <header className="portal-header">
      <div className="portal-brand">
        <h1>sos help</h1>
        <span className="portal-name">Responder Center</span>
      </div>

      <div className="header-status">
        {link !== 'live' && (
          <span
            className={`node-status ${link === 'connecting' ? 'degraded' : 'down'
              }`}
          >
            <span className="status-dot" aria-hidden="true" />
            {link === 'connecting'
              ? 'Connecting'
              : 'Server unreachable'}
          </span>
        )}

        <span className={`node-status ${statusClass}`}>
          <span className="status-dot" aria-hidden="true" />
          {label}
        </span>

        <button
          className="dispatch-send"
          type="button"
          title="Call SOS"
          onClick={() => alert('SOS activated')}
        >
          SOS
        </button>
      </div>
    </header>
  )
}
