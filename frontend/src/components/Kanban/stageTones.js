// Semantic pipeline colors for Kanban columns (Leads and Deals).
// `dot` marks the stage, `bg` tints the column header, `ink` is the header text.

export const TONES = {
  slate: { dot: '#64748B', bg: '#F1F5F9', ink: '#334155' },
  blue: { dot: '#3B82F6', bg: '#EFF6FF', ink: '#1D4ED8' },
  amber: { dot: '#D97706', bg: '#FFFBEB', ink: '#92400E' },
  violet: { dot: '#7C3AED', bg: '#F5F3FF', ink: '#5B21B6' },
  emerald: { dot: '#059669', bg: '#ECFDF5', ink: '#065F46' },
  red: { dot: '#DC6262', bg: '#FEF2F2', ink: '#991B1B' },
  cyan: { dot: '#0891B2', bg: '#ECFEFF', ink: '#155E75' },
  indigo: { dot: '#4F46E5', bg: '#EEF2FF', ink: '#3730A3' },
  gray: { dot: '#9CA3AF', bg: '#F3F4F6', ink: '#4B5563' },
}

// Stage names shipped with Frappe CRM.
const BY_NAME = {
  'CRM Lead': {
    New: 'slate',
    Contacted: 'blue',
    Nurture: 'amber',
    Qualified: 'violet',
    Converted: 'emerald',
    Unqualified: 'red',
    Junk: 'gray',
  },
  'CRM Deal': {
    Qualification: 'slate',
    'Demo/Making': 'blue',
    'Proposal/Quotation': 'violet',
    Negotiation: 'amber',
    'Ready to Close': 'cyan',
    Won: 'emerald',
    Lost: 'red',
  },
}

// In-progress stages that aren't known by name cycle through these by position.
const ONGOING_CYCLE = ['blue', 'violet', 'amber', 'cyan', 'indigo']

// Frappe indicator colors (the column color picker) mapped onto the palette.
const FROM_FRAPPE_COLOR = {
  gray: 'slate',
  blue: 'blue',
  cyan: 'cyan',
  teal: 'emerald',
  green: 'emerald',
  orange: 'amber',
  yellow: 'amber',
  amber: 'amber',
  red: 'red',
  pink: 'red',
  purple: 'violet',
  violet: 'violet',
}

/**
 * @param {string} doctype   'CRM Lead' | 'CRM Deal'
 * @param {object} column    Kanban column ({ name, color, color_custom })
 * @param {object} [status]  Status record ({ type, position }) when available
 */
export function getStageTone(doctype, column, status) {
  if (column?.color_custom && FROM_FRAPPE_COLOR[column.color]) {
    return TONES[FROM_FRAPPE_COLOR[column.color]]
  }
  const named = BY_NAME[doctype]?.[column?.name]
  if (named) return TONES[named]

  switch (status?.type) {
    case 'Won':
      return TONES.emerald
    case 'Lost':
      return TONES.red
    case 'Open':
      return TONES.slate
    case 'Ongoing':
      return TONES[ONGOING_CYCLE[((status.position || 1) - 1) % ONGOING_CYCLE.length]]
  }
  return TONES[FROM_FRAPPE_COLOR[column?.color]] || TONES.slate
}

// Subtle, stable avatar colors for initials fallbacks.
const AVATAR_TONES = [
  ['#EEF2FF', '#4338CA'],
  ['#ECFDF5', '#047857'],
  ['#FFF7ED', '#C2410C'],
  ['#F5F3FF', '#6D28D9'],
  ['#EFF6FF', '#1D4ED8'],
  ['#FDF2F8', '#BE185D'],
  ['#F0FDFA', '#0F766E'],
  ['#FEFCE8', '#A16207'],
]

export function avatarTone(seed = '') {
  let h = 0
  for (const ch of String(seed)) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return AVATAR_TONES[h % AVATAR_TONES.length]
}

export function initialsOf(name = '') {
  const parts = String(name).trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return '?'
  const first = parts[0][0]
  const last = parts.length > 1 ? parts[parts.length - 1][0] : ''
  return (first + last).toUpperCase()
}
