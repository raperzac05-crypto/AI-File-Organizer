const btn = document.getElementById('organizeBtn')
const folderInput = document.getElementById('folder')
const log = document.getElementById('log')
const summary = document.getElementById('summary')

btn.addEventListener('click', () => {
    const folder = folderInput.value

    const es = new EventSource(`http://localhost:8000/organize-stream?folder=${encodeURIComponent(folder)}`)

    es.onmessage = (e) => {
        const data = JSON.parse(e.data)

        if(data.type === 'log') {
            const line = document.createElement('div')
            line.textContent = data.text
            log.appendChild(line)
            log.scrollTop = log.scrollHeight
        }

        if(data.type === 'summary') {
            summary.textContent = data.text
            es.close()
        }
    }

    es.onerror = (e) => {
        console.error('stream ended or error', e)
        es.close()
    }
})