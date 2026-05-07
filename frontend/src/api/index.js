import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export async function parseVideo(url) {
  const { data } = await api.post('/parse', { url })
  return data
}

export async function triggerDownload(url, formatId) {
  const { data } = await api.post('/download', { url, format_id: formatId }, {
    timeout: 600000,
  })
  return data
}
