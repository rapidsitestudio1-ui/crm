import { dayjs } from 'frappe-ui'

export type Point = [number, number]

// Port of d3's curveMonotoneX, which Recharts' "monotone" curve (used in the
// Figma charts) is built on.
export function monotonePath(points: Point[]): string {
  const n = points.length
  if (!n) return ''
  if (n === 1) return `M${points[0][0]},${points[0][1]}`
  if (n === 2) return `M${points[0].join(',')}L${points[1].join(',')}`

  const sign = (x: number) => (x < 0 ? -1 : 1)
  const tangents: number[] = new Array(n)
  for (let i = 1; i < n - 1; i++) {
    const [x0, y0] = points[i - 1]
    const [x1, y1] = points[i]
    const [x2, y2] = points[i + 1]
    const h0 = x1 - x0
    const h1 = x2 - x1
    const s0 = (y1 - y0) / (h0 || 1e-9)
    const s1 = (y2 - y1) / (h1 || 1e-9)
    const p = (s0 * h1 + s1 * h0) / (h0 + h1)
    tangents[i] =
      (sign(s0) + sign(s1)) *
        Math.min(Math.abs(s0), Math.abs(s1), 0.5 * Math.abs(p)) || 0
  }
  const endTangent = (a: Point, b: Point, t: number) => {
    const h = b[0] - a[0]
    return h ? (3 * (b[1] - a[1])) / h / 2 - t / 2 : t
  }
  tangents[0] = endTangent(points[0], points[1], tangents[1])
  tangents[n - 1] = endTangent(points[n - 2], points[n - 1], tangents[n - 2])

  let d = `M${points[0][0]},${points[0][1]}`
  for (let i = 1; i < n; i++) {
    const [x0, y0] = points[i - 1]
    const [x1, y1] = points[i]
    const dx = (x1 - x0) / 3
    d += `C${x0 + dx},${y0 + dx * tangents[i - 1]},${x1 - dx},${y1 - dx * tangents[i]},${x1},${y1}`
  }
  return d
}

// Evenly spaced "nice" ticks from 0, e.g. max 37 -> [0, 10, 20, 30, 40].
export function niceTicks(max: number, count = 4): number[] {
  if (!max || max <= 0) return Array.from({ length: count + 1 }, (_, i) => i)
  const raw = max / count
  const mag = Math.pow(10, Math.floor(Math.log10(raw)))
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) || raw
  return Array.from({ length: count + 1 }, (_, i) => +(i * step).toFixed(10))
}

// Average a long daily series down to `buckets` points for sparklines.
export function bucket(series: number[], buckets = 9): number[] {
  if (series.length <= buckets) return series
  const size = series.length / buckets
  return Array.from({ length: buckets }, (_, i) => {
    const slice = series.slice(Math.floor(i * size), Math.floor((i + 1) * size))
    return slice.reduce((a, b) => a + b, 0) / (slice.length || 1)
  })
}

// "$28 400": thin-space grouping as in the Figma design.
export function formatMoney(value: number, symbol = '$'): string {
  return symbol + Math.round(value || 0).toLocaleString('en-US').replace(/,/g, ' ')
}

// "$12K", "40K", "1.2M"
export function formatCompact(value: number, symbol = ''): string {
  const v = Math.abs(value || 0)
  if (v >= 1e6) return `${symbol}${+(value / 1e6).toFixed(1)}M`
  if (v >= 1e3) return `${symbol}${+(value / 1e3).toFixed(1)}K`
  return `${symbol}${Math.round(value || 0)}`
}

export function formatCount(value: number): string {
  return Math.round(value || 0).toLocaleString('en-US').replace(/,/g, ' ')
}

// "2h ago", "1d ago", as in the Figma activity list and leads table.
export function shortAgo(date: string): string {
  if (!date) return ''
  const mins = Math.max(0, dayjs().diff(dayjs(date), 'minute'))
  if (mins < 1) return __('just now')
  if (mins < 60) return __('{0}m ago', [mins])
  const hours = Math.floor(mins / 60)
  if (hours < 24) return __('{0}h ago', [hours])
  const days = Math.floor(hours / 24)
  if (days < 30) return __('{0}d ago', [days])
  const months = Math.floor(days / 30)
  if (months < 12) return __('{0}mo ago', [months])
  return __('{0}y ago', [Math.floor(months / 12)])
}

export function initials(name: string): string {
  return (name || '?')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()
}
