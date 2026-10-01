<template>
  <svg width="90" height="45" viewBox="0 0 90 45" fill="none" overflow="visible" aria-hidden="true">
    <defs>
      <linearGradient :id="gradientId" x1="0" y1="9" x2="0" y2="44.5" gradientUnits="userSpaceOnUse">
        <stop :stop-color="color" stop-opacity="0.22" />
        <stop offset="1" :stop-color="color" stop-opacity="0" />
      </linearGradient>
    </defs>
    <path :d="`${line}V44.5H1Z`" :fill="`url(#${gradientId})`" />
    <path :d="line" :stroke="color" stroke-width="1.6" />
  </svg>
</template>

<script setup lang="ts">
import { computed, useId } from 'vue'
import { bucket, monotonePath, type Point } from './utils'

const props = defineProps<{ series: number[]; color: string }>()
const gradientId = `ov-spark-${useId()}`

// Same frame as the Figma sparkline: x 1..89, line between y 3.5 and 40.5.
const line = computed(() => {
  const values = bucket(props.series || [], 9)
  const pts = values.length > 1 ? values : [0, 0]
  const max = Math.max(...pts)
  const min = Math.min(...pts)
  const span = max - min
  const points: Point[] = pts.map((v, i) => [
    1 + (88 * i) / (pts.length - 1),
    span ? 40.5 - ((v - min) / span) * 37 : 40.5,
  ])
  return monotonePath(points)
})
</script>
