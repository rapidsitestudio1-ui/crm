<template>
  <svg
    width="56"
    height="40"
    viewBox="0 0 56 40"
    fill="none"
    aria-hidden="true"
    class="shrink-0"
  >
    <template v-if="type === 'bars'">
      <rect x="0" y="14" width="11" height="26" rx="2" :fill="c1" />
      <rect x="14" y="0" width="11" height="40" rx="2" :fill="c1" />
      <rect x="28" y="8" width="11" height="32" rx="2" :fill="c1" />
      <rect x="42" y="4" width="11" height="36" rx="2" :fill="c3" />
    </template>
    <template v-else-if="type === 'line'">
      <path
        d="M2 30 L10 22 L17 27 L25 12 L32 20 L40 8 L47 15 L54 6"
        :stroke="c1"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </template>
    <template v-else-if="type === 'donut'">
      <circle cx="28" cy="20" r="15.5" :stroke="c6" stroke-width="7.5" />
      <circle
        cx="28"
        cy="20"
        r="15.5"
        :stroke="c1"
        stroke-width="7.5"
        :stroke-dasharray="`${circumference * 0.7} ${circumference}`"
        transform="rotate(-90 28 20)"
      />
    </template>
    <template v-else>
      <rect
        v-for="(h, i) in pulse"
        :key="i"
        :x="7 + i * 6"
        :y="(40 - h) / 2"
        width="3"
        :height="h"
        rx="1.5"
        :fill="i === 2 || i === 3 || i === 4 ? c1 : c3"
      />
    </template>
  </svg>
</template>

<script setup>
// Decorative trend glyph for KPI cards (Figma "Mini Chart"). It does not plot
// data; colors come from the theme's --chart-* palette.
defineProps({
  type: {
    type: String,
    default: 'bars',
    validator: (v) => ['bars', 'line', 'donut', 'pulse'].includes(v),
  },
})

const c1 = 'var(--chart-1, #ff5316)'
const c3 = 'var(--chart-3, #ffb799)'
const c6 = 'var(--chart-6, #ffd2bf)'
const circumference = 2 * Math.PI * 15.5
const pulse = [14, 26, 36, 22, 32, 18, 28]
</script>
