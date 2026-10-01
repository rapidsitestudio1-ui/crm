<template>
  <section class="ov-card flex min-w-0 flex-col px-[18px] pb-4 pt-[15px]">
    <CardHeading :title="__('Tasks due today')" align="center">
      <ViewAllLink :to="{ name: 'Tasks' }" />
    </CardHeading>
    <div class="flex flex-col gap-[15px] pt-[14px]">
      <p v-if="!tasks.length" class="ov-empty pl-[10px]">{{ __('No tasks due today') }}</p>
      <div
        v-for="task in tasks"
        :key="task.name"
        class="flex items-start gap-4 pl-[10px]"
        :class="{ 'opacity-50': done.has(task.name) }"
      >
        <div class="flex pt-[6px]">
          <input
            type="checkbox"
            class="ov-checkbox"
            :checked="done.has(task.name)"
            :aria-label="__('Mark {0} as done', [task.title])"
            @change="markDone(task)"
          />
        </div>
        <button type="button" class="flex min-w-0 flex-1 flex-col text-left" @click="open(task)">
          <span
            class="w-full truncate text-[12px] font-medium leading-[17px]"
            :class="{ 'line-through': done.has(task.name) }"
          >
            {{ task.title || __('Untitled task') }}
          </span>
          <span
            v-if="task.subtitle"
            class="w-full truncate pt-[2px] text-[12px] leading-4"
            style="color: var(--ov-ink-muted)"
          >
            {{ task.subtitle }}
          </span>
        </button>
        <div class="flex pt-[2px]">
          <span
            class="rounded-[6px] px-2 py-[3px] text-[12px] leading-[18px] whitespace-nowrap"
            style="background: var(--ov-task-bg); color: var(--ov-task-ink)"
          >
            {{ dayjsLocal(task.due_date).format('h:mm A') }}
          </span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { call, dayjsLocal, toast } from 'frappe-ui'
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import CardHeading from './CardHeading.vue'
import ViewAllLink from './ViewAllLink.vue'

type Task = {
  name: string
  title: string
  subtitle: string
  due_date: string
  reference_doctype?: string
  reference_docname?: string
}

defineProps<{ tasks: Task[] }>()

const router = useRouter()
const done = reactive(new Set<string>())

async function markDone(task: Task) {
  if (done.has(task.name)) return
  done.add(task.name)
  try {
    await call('frappe.client.set_value', {
      doctype: 'CRM Task',
      name: task.name,
      fieldname: 'status',
      value: 'Done',
    })
  } catch (e) {
    done.delete(task.name)
    toast.error(__('Could not update the task'))
  }
}

function open(task: Task) {
  if (task.reference_doctype === 'CRM Lead') {
    router.push({ name: 'Lead', params: { leadId: task.reference_docname }, hash: '#tasks' })
  } else if (task.reference_doctype === 'CRM Deal') {
    router.push({ name: 'Deal', params: { dealId: task.reference_docname }, hash: '#tasks' })
  } else {
    router.push({ name: 'Tasks' })
  }
}
</script>
