import axios from "axios"

const client = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL,
  timeout: 120000,
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "An unexpected error occurred."
    return Promise.reject(new Error(message))
  }
)

export const uploadDocument = async (file, onUploadProgress) => {
  const formData = new FormData()
  formData.append("file", file)

  const { data } = await client.post("/api/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (onUploadProgress && event.total) {
        const percent = Math.round((event.loaded * 100) / event.total)
        onUploadProgress(percent)
      }
    },
  })
  return data
}

export const queryDocuments = async (question, uploadIds = null) => {
  const payload = { question }
  if (uploadIds && uploadIds.length > 0) {
    payload.upload_ids = uploadIds
  }
  const { data } = await client.post("/api/query", payload)
  return data
}

export const fetchDocuments = async () => {
  const { data } = await client.get("/api/documents")
  return data
}

export const checkHealth = async () => {
  const { data } = await client.get("/health")
  return data
}

// ── Google Docs ───────────────────────────────────────────────────────────────

export const connectGoogleDoc = async (url) => {
  const { data } = await client.post("/api/connect-gdoc", { url })
  return data
}

export const getSyncStatus = async () => {
  const { data } = await client.get("/api/sync-status")
  return data
}

export const getSyncStatusForDoc = async (docId) => {
  const { data } = await client.get(`/api/sync-status/${docId}`)
  return data
}
