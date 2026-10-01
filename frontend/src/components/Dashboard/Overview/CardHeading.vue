<template>
  <div class="flex w-full justify-between" :class="align === 'center' ? 'items-center' : 'items-start'">
    <div class="flex items-center gap-2">
      <h2 class="ov-card-title">{{ title }}</h2>
      <Tooltip v-if="info" :text="info">
        <img :src="infoIcon" alt="" class="size-3 shrink-0" />
      </Tooltip>
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { Tooltip } from 'frappe-ui'
import infoIcon from './assets/info.svg'

withDefaults(
  defineProps<{ title: string; info?: string; align?: 'start' | 'center' }>(),
  { align: 'start' },
)
</script>
