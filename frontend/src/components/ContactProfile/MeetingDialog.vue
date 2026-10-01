<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Schedule meeting'), size: 'md' }"
  >
    <template #body-content>
      <form class="flex flex-col gap-4" @submit.prevent="save">
        <FormControl
          v-model="form.subject"
          :label="__('Title')"
          :placeholder="__('e.g. Next stage planning')"
          required
        />
        <div class="grid grid-cols-2 gap-3">
          <FormControl v-model="form.date" type="date" :label="__('Date')" required />
          <FormControl v-model="form.time" type="time" :label="__('Start time')" required />
        </div>
        <FormControl
          v-model="form.duration"
          type="select"
          :label="__('Duration')"
          :options="[
            { label: __('15 minutes'), value: 15 },
            { label: __('30 minutes'), value: 30 },
            { label: __('45 minutes'), value: 45 },
            { label: __('1 hour'), value: 60 },
            { label: __('1.5 hours'), value: 90 },
            { label: __('2 hours'), value: 120 },
          ]"
        />
        <FormControl
          v-model="form.description"
          type="textarea"
          :label="__('Notes')"
          :placeholder="__('Agenda or discussion points')"
        />
        <ErrorMessage :message="error" />
      </form>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          class="crm-primary"
          variant="solid"
          :label="__('Schedule')"
          :loading="saving"
          :disabled="!form.subject || !form.date || !form.time"
          @click="save"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Dialog,
  FormControl,
  ErrorMessage,
  call,
  dayjs,
  getConfig,
  toast,
} from 'frappe-ui'

// Local (browser) time -> the server's system timezone, as frappe-ui's own
// dayjsSystem does (not exported by this frappe-ui version).
function toSystem(localString, fmt) {
  const system = getConfig('systemTimezone')
  const local =
    getConfig('localTimezone') || Intl.DateTimeFormat().resolvedOptions().timeZone
  if (!system) return localString
  return dayjs.tz(localString, local).tz(system).format(fmt)
}
import { reactive, ref, watch } from 'vue'

const props = defineProps({ contact: { type: String, required: true } })
const emit = defineEmits(['scheduled'])
const show = defineModel({ type: Boolean, default: false })

const saving = ref(false)
const error = ref('')
const form = reactive({})

function reset() {
  const start = dayjs().add(1, 'day').hour(10).minute(0)
  Object.assign(form, {
    subject: '',
    date: start.format('YYYY-MM-DD'),
    time: start.format('HH:mm'),
    duration: 30,
    description: '',
  })
  error.value = ''
}
watch(show, (open) => open && reset(), { immediate: true })

async function save() {
  if (!form.subject || !form.date || !form.time) return
  saving.value = true
  error.value = ''
  // Entered in the user's timezone; stored in the server's (system) timezone.
  const fmt = 'YYYY-MM-DD HH:mm:ss'
  const start = dayjs(`${form.date} ${form.time}`)
  const end = start.add(Number(form.duration) || 30, 'minute')
  try {
    await call('crm.api.contact_profile.schedule_meeting', {
      contact: props.contact,
      subject: form.subject,
      starts_on: toSystem(start.format(fmt), fmt),
      ends_on: toSystem(end.format(fmt), fmt),
      description: form.description,
    })
    toast.success(__('Meeting scheduled'))
    show.value = false
    emit('scheduled')
  } catch (e) {
    error.value = e?.messages?.[0] || e?.message || __('Could not schedule the meeting')
  } finally {
    saving.value = false
  }
}
</script>
