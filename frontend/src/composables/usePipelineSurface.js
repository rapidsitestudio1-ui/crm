import { onMounted, onBeforeUnmount } from 'vue'

// Marks <html data-surface="pipeline"> while the page is mounted, so the
// redesigned pages (and their dialogs) use the indigo accent from kanban.css.
export function usePipelineSurface() {
  onMounted(() => (document.documentElement.dataset.surface = 'pipeline'))
  onBeforeUnmount(() => delete document.documentElement.dataset.surface)
}
