import type { AiPriority } from '../types/incident'

/**
 * Quiet 5-segment priority meter — filled segments only, one muted tone.
 * The scale runs 1 = CRITICAL … 5 = lowest, so a more urgent level fills MORE
 * segments (level 1 lights all five, level 5 lights one).
 */
export default function PriorityMeter({
  level,
  size = 'sm',
}: {
  level: AiPriority | null
  size?: 'sm' | 'md'
}) {
  const known = level != null
  const filled = level == null ? 0 : Math.max(1, 6 - level)
  return (
    <span
      className={`priority-meter ${size}`}
      title={known ? `Priority ${level} of 5` : 'Priority not set yet'}
      aria-label={known ? `Priority ${level} of 5` : 'Priority not set yet'}
    >
      {[1, 2, 3, 4, 5].map(step => (
        <span
          key={step}
          className={`priority-bar ${known && step <= filled ? 'on' : ''}`}
          data-level={known ? level : undefined}
        />
      ))}
    </span>
  )
}
