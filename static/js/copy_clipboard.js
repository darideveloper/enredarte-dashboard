document.addEventListener('DOMContentLoaded', () => {
  const copyText = async (text) => {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = text
      document.body.appendChild(textarea)
      textarea.select()
      const ok = document.execCommand('copy')
      document.body.removeChild(textarea)
      if (!ok) {
        throw new Error('execCommand copy failed')
      }
    }
  }

  document.querySelectorAll('[data-copy-url]').forEach((button) => {
    const url = button.dataset.copyUrl
    const label = button.querySelector('[data-copy-label]')
    const originalLabel = label ? label.textContent.trim() : button.textContent.trim()

    button.addEventListener('click', async () => {
      try {
        await copyText(url)
        if (label) {
          label.textContent = '¡Copiado!'
          setTimeout(() => {
            label.textContent = originalLabel
          }, 2000)
        } else {
          button.textContent = '¡Copiado!'
          setTimeout(() => {
            button.textContent = originalLabel
          }, 2000)
        }
      } catch {
        window.prompt('Copia el link manualmente:', url)
      }
    })
  })
})