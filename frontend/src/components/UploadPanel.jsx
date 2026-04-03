import { useState, useRef, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Upload, FileText, CheckSquare, Square, X, Loader2, Trash2 } from "lucide-react"
import { uploadDocument, deleteDocument } from "@/lib/api"
import { formatFileSize, getFileIcon, truncateText } from "@/lib/utils"

const ACCEPTED = ["pdf", "txt", "csv", "xlsx", "xls"]

export default function UploadPanel({
  documents,
  selectedIds,
  onUploadSuccess,
  onDeleteSuccess,
  onToggleDocument,
  onSelectAll,
  onClearAll,
}) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadingName, setUploadingName] = useState("")
  const [error, setError] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const inputRef = useRef(null)

  const handleFile = useCallback(async (file) => {
    const ext = file.name.split(".").pop().toLowerCase()
    if (!ACCEPTED.includes(ext)) {
      setError(`Unsupported type .${ext}. Accepted: ${ACCEPTED.join(", ")}`)
      return
    }
    if (file.size > 20 * 1024 * 1024) {
      setError("File exceeds 20MB limit.")
      return
    }

    setError(null)
    setUploading(true)
    setUploadProgress(0)
    setUploadingName(file.name)

    try {
      const result = await uploadDocument(file, setUploadProgress)
      onUploadSuccess(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
      setUploadProgress(0)
      setUploadingName("")
    }
  }, [onUploadSuccess])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])

  const onDragOver = (e) => { e.preventDefault(); setIsDragging(true) }
  const onDragLeave = () => setIsDragging(false)
  const onInputChange = (e) => { if (e.target.files[0]) handleFile(e.target.files[0]) }
  const handleDelete = useCallback(async (uploadId, documentName) => {
    const confirmed = window.confirm(`Delete "${documentName}" from index?`)
    if (!confirmed) return

    setError(null)
    setDeletingId(uploadId)
    try {
      await deleteDocument(uploadId)
      onDeleteSuccess?.(uploadId)
    } catch (err) {
      setError(err.message)
    } finally {
      setDeletingId(null)
    }
  }, [onDeleteSuccess])

  return (
    <div className="flex flex-col gap-4">
      {/* Upload Zone */}
      <div className="card-lexindex p-4">
        <h3 className="font-display text-sm font-semibold text-parchment mb-3 flex items-center gap-2">
          <Upload size={14} className="text-gold" />
          Upload Document
        </h3>

        <div
          className={`upload-zone flex flex-col items-center justify-center gap-3 cursor-pointer py-8 px-4 ${isDragging ? "drag-active" : ""}`}
          onClick={() => !uploading && inputRef.current?.click()}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED.map(e => `.${e}`).join(",")}
            className="hidden"
            onChange={onInputChange}
          />

          <AnimatePresence mode="wait">
            {uploading ? (
              <motion.div
                key="uploading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center gap-3 w-full"
              >
                <Loader2 size={24} className="text-gold animate-spin" />
                <p className="text-xs text-parchment-dim text-center font-body">
                  {truncateText(uploadingName, 32)}
                </p>
                <div className="w-full score-bar">
                  <div
                    className="score-bar-fill"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="text-xs text-gold font-body">{uploadProgress}%</p>
              </motion.div>
            ) : (
              <motion.div
                key="idle"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center gap-2"
              >
                <div
                  className="flex items-center justify-center rounded-full"
                  style={{
                    width: 44,
                    height: 44,
                    background: "rgba(201,168,76,0.08)",
                    border: "1px solid rgba(201,168,76,0.2)",
                  }}
                >
                  <Upload size={18} className="text-gold" />
                </div>
                <p className="text-sm text-parchment font-body text-center">
                  Drop file here or{" "}
                  <span className="text-gold underline underline-offset-2 cursor-pointer">
                    browse
                  </span>
                </p>
                <p className="text-xs text-parchment-dim font-body">
                  PDF, TXT, CSV, XLSX · Max 20MB
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-3 flex items-start gap-2 text-xs text-red-400 font-body"
              style={{
                background: "rgba(239,68,68,0.08)",
                border: "1px solid rgba(239,68,68,0.15)",
                borderRadius: 6,
                padding: "8px 10px",
              }}
            >
              <X size={12} className="mt-0.5 shrink-0" />
              {error}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Indexed Documents */}
      <div className="card-lexindex p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-display text-sm font-semibold text-parchment flex items-center gap-2">
            <FileText size={14} className="text-gold" />
            Indexed Documents
            {documents.length > 0 && (
              <span
                className="text-xs font-body px-1.5 py-0.5 rounded-full text-gold"
                style={{ background: "rgba(201,168,76,0.12)", border: "1px solid rgba(201,168,76,0.2)" }}
              >
                {documents.length}
              </span>
            )}
          </h3>

          {documents.length > 0 && (
            <div className="flex gap-2">
              <button
                onClick={onSelectAll}
                className="text-xs text-gold-dim hover:text-gold font-body transition-colors"
              >
                All
              </button>
              <span className="text-border text-xs">·</span>
              <button
                onClick={onClearAll}
                className="text-xs text-parchment-dim hover:text-parchment font-body transition-colors"
              >
                None
              </button>
            </div>
          )}
        </div>

        {documents.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-xs text-parchment-dim font-body">
              No documents indexed yet.
            </p>
            <p className="text-xs text-parchment-faint font-body mt-1">
              Upload a file to get started.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-2" style={{ maxHeight: 360, overflowY: "auto" }}>
            <AnimatePresence>
              {documents.map((doc, i) => {
                const isSelected = selectedIds.includes(doc.upload_id)
                return (
                  <motion.div
                    key={doc.upload_id}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -12 }}
                    transition={{ delay: i * 0.05 }}
                    onClick={() => onToggleDocument(doc.upload_id)}
                    className="flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-all duration-200"
                    style={{
                      background: isSelected ? "rgba(201,168,76,0.06)" : "var(--surface-raised)",
                      border: `1px solid ${isSelected ? "rgba(201,168,76,0.25)" : "var(--border)"}`,
                    }}
                  >
                    <div className="mt-0.5 shrink-0">
                      {isSelected
                        ? <CheckSquare size={14} className="text-gold" />
                        : <Square size={14} className="text-parchment-dim" />
                      }
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-body text-parchment truncate leading-snug">
                        {getFileIcon(doc.file_type)} {doc.document_name}
                      </p>
                      <p className="text-xs text-parchment-dim font-body mt-1">
                        {doc.pages}p · {doc.chunks} chunks
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDelete(doc.upload_id, doc.document_name)
                      }}
                      disabled={deletingId === doc.upload_id}
                      className="shrink-0 p-1 rounded transition-colors text-parchment-dim hover:text-red-300 disabled:opacity-50"
                      title="Delete document"
                      aria-label={`Delete ${doc.document_name}`}
                    >
                      {deletingId === doc.upload_id ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <Trash2 size={14} />
                      )}
                    </button>
                  </motion.div>
                )
              })}
            </AnimatePresence>
          </div>
        )}

        {documents.length > 0 && (
          <p className="text-xs text-parchment-dim font-body mt-3 text-center">
            {selectedIds.length === 0
              ? "No filter — querying all documents"
              : `Querying ${selectedIds.length} of ${documents.length} document${selectedIds.length > 1 ? "s" : ""}`}
          </p>
        )}
      </div>
    </div>
  )
}
