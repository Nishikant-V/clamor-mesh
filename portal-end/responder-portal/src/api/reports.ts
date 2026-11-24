import { request } from './client'

export interface ApiReportUser {
  user_id: number
  name?: string | null
  phone?: string | null
  origin?: number | null
}

/** Mirrors `ReportDetail` from portal-end/backend/schemas/report.py. */
export interface ApiReport {
  id: number
  msg_id: number
  attempt?: number | null
  user_id: number
  origin?: number | null
  path?: number[] | null
  category?: number | null
  people?: number | null
  needs?: number | null
  gps_lat?: number | null
  gps_lon?: number | null
  gps_accuracy?: number | null
  location?: string | null
  message?: string | null
  status?: string | null
  resolved?: boolean | null
  ai_priority?: number | null
  priority?: number | null
  ai_category?: number | null
  ai_summary?: string | null
  ai_responders?: string[] | null
  cluster_id?: string | null
  cluster_summary?: string | null
  cluster_responders?: string[] | null
  created_at?: string | null
  acked_at?: string | null
  user?: ApiReportUser | null
}

export function listReports(limit = 500, sort: 'created_at' | 'priority' = 'created_at'): Promise<ApiReport[]> {
  return request(`/api/reports?limit=${limit}&sort=${sort}`)
}

export function updateReport(
  id: number,
  patch: { status?: string; resolved?: boolean },
): Promise<ApiReport> {
  return request(`/api/reports/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  })
}

export interface CreateReportInput {
  msg_id?: number
  attempt?: number
  user_id?: number
  origin?: number
  path?: number[]
  category?: number
  people?: number
  needs?: number
  gps_lat?: number | null
  gps_lon?: number | null
  gps_accuracy?: number | null
  location?: string | null
  message?: string | null
  status?: string
  name?: string
  phone?: string
}

function generateMsgId(): number {
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const buf = new Uint32Array(1)
    crypto.getRandomValues(buf)
    return buf[0] === 0 ? 1 : buf[0]
  }
  return Math.floor(Math.random() * 4294967294) + 1
}

export function createReport(body: CreateReportInput = {}): Promise<ApiReport> {
  const origin = body.origin ?? 1
  const payload = {
    msg_id: body.msg_id ?? generateMsgId(),
    attempt: body.attempt ?? 0,
    user_id: body.user_id ?? 65001,
    origin,
    path: body.path && body.path.length > 0 ? body.path : [origin],
    category: body.category ?? 8,
    people: body.people ?? 1,
    needs: body.needs ?? 0,
    gps_lat: body.gps_lat ?? null,
    gps_lon: body.gps_lon ?? null,
    gps_accuracy: body.gps_accuracy ?? null,
    location: body.location ?? '',
    message: body.message ?? '',
    status: body.status ?? 'received',
    name: body.name ?? '',
    phone: body.phone ?? '',
  }

  return request('/api/reports', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
