<template>
  <Dropdown :options="items" placement="right">
    <button type="button" class="ov-select">
      <span>{{ current?.label }}</span>
      <img :src="chevronIcon" alt="" class="size-[13px]" />
    </button>
  </Dropdown>
</template>

<script setup lang="ts">
import { Dropdown } from 'frappe-ui'
import { computed } from 'vue'
import chevronIcon from './assets/chevron.svg'

const props = defineProps<{ options: { label: string; value: number }[] }>()
const model = defineModel<number>()

const current = computed(() => props.options.find((o) => o.value === model.value))
const items = computed(() =>
  props.options.map((o) => ({ label: o.label, onClick: () => (model.value = o.value) })),
)
</script>
