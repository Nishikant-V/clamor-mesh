import { useEffect, useRef, useState } from 'react'
import { sendMessage } from '../api/messages'
import { createReport } from '../api/reports'
import type { PortalLink } from '../hooks/useLivePortal'
import type { NetworkNode } from '../types/network'

type SosFeedback = {
  kind: 'loading' | 'success' | 'error'
  text: string
}

const RESPONDER_SOS_USER_ID = 65001

function pickTargetOrigin(nodes: NetworkNode[]): number {
  const validNode = (node: NetworkNode) => {
    const id = Number(node.id)
    return Number.isInteger(id) && id >= 1 && id <= 254
  }
  const online = nodes.find(node => node.status === 'ONLINE' && validNode(node))
  if (online) return Number(online.id)
  const any = nodes.find(validNode)
  return any ? Number(any.id) : 1
}

export default function Header({
  nodes,
  link = 'live',
  onSosCreated,
}: {
  nodes: NetworkNode[]
  link?: PortalLink
  onSosCreated?: () => void
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

  const [sosLoading, setSosLoading] = useState(false)
  const [sosFeedback, setSosFeedback] = useState<SosFeedback | null>(null)
  const submittingRef = useRef(false)

  useEffect(() => {
    if (!sosFeedback || sosFeedback.kind === 'loading') return
    const timer = window.setTimeout(() => {
      setSosFeedback(null)
    }, 8000)
    return () => window.clearTimeout(timer)
  }, [sosFeedback])

  async function handleSosTrigger() {
    if (submittingRef.current || sosLoading) return
    submittingRef.current = true
    setSosLoading(true)
    setSosFeedback({ kind: 'loading', text: 'Sending SOS…' })

    const origin = pickTargetOrigin(nodes)
    try {
      const report = await createReport({
        user_id: RESPONDER_SOS_USER_ID,
        origin,
        path: [origin],
        category: 8,
        people: 1,
        location: 'Responder Center',
        message: 'SOS alert activated from Responder Center',
        status: 'received',
        name: 'Responder Center',
      })

      onSosCreated?.()

      let text = `SOS #${report.id} saved (${report.status ?? 'received'})`
      try {
        const downlink = await sendMessage({
          user_id: report.user_id,
          text: `SOS #${report.msg_id} activated from Responder Center.`,
          sender: 'Responder Center',
          reply_to: report.msg_id,
        })
        text =
          downlink.status === 'sent'
            ? `SOS #${report.id} sent to mesh (Node ${origin})`
            : `SOS #${report.id} saved (${report.status ?? 'received'}); mesh downlink ${downlink.status}`
      } catch (downlinkErr) {
        const reason =
          downlinkErr instanceof Error && downlinkErr.message.trim()
            ? downlinkErr.message.trim()
            : 'downlink failed'
        text = `SOS #${report.id} saved (${report.status ?? 'received'}); downlink error: ${reason}`
      }

      setSosFeedback({ kind: 'success', text })
    } catch (err) {
      const message =
        err instanceof Error && err.message.trim()
          ? err.message.trim()
          : 'Failed to send SOS'
      setSosFeedback({ kind: 'error', text: `SOS failed: ${message}` })
    } finally {
      submittingRef.current = false
      setSosLoading(false)
    }
  }

  return (
    <header className="portal-header">
      <div className="portal-brand">
        <h1>sos help</h1>
        <span className="portal-name">Responder Center</span>
      </div>

      <div className="header-status">
        {sosFeedback && (
          <span
            className={`sos-feedback ${sosFeedback.kind}`}
            role={sosFeedback.kind === 'error' ? 'alert' : 'status'}
            aria-live="polite"
          >
            {sosFeedback.text}
          </span>
        )}

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
          disabled={sosLoading}
          aria-busy={sosLoading}
          onClick={() => void handleSosTrigger()}
        >
          {sosLoading ? 'Sending…' : 'SOS'}
        </button>
      </div>
    </header>
  )
}
