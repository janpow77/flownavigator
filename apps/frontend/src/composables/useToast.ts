/**
 * Toast composable for showing notifications
 */

interface ToastOptions {
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
}

export function useToast() {
  function show(options: ToastOptions) {
    const event = new CustomEvent('toast', { detail: options })
    window.dispatchEvent(event)
  }

  function success(title: string, message?: string, duration?: number) {
    show({ type: 'success', title, message, duration })
  }

  function error(title: string, message?: string, duration?: number) {
    show({ type: 'error', title, message, duration: duration ?? 8000 })
  }

  function warning(title: string, message?: string, duration?: number) {
    show({ type: 'warning', title, message, duration })
  }

  function info(title: string, message?: string, duration?: number) {
    show({ type: 'info', title, message, duration })
  }

  return {
    show,
    success,
    error,
    warning,
    info,
  }
}
