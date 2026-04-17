import { useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Link2, FileText, CheckSquare, Square, X, Loader2, RefreshCw } from "lucide-react"
import { connectGoogleDoc } from "@/lib/api"
import { truncateText } from "@/lib/utils"

export default function UploadPanel({
  documents,
  selectedIds,
  onUploadSuccess,
  onToggleDocument,
  onSelectAll,
  onClearAll,
}) {
  const [docUrl, setDocUrl] = useState("")
  const [connecting, setConnecting] = useState(false)
  const [error, setError] = useState(null)
  const [lastConnected, setLastConnected] = useState(null)

  // Defensive guards — ensure props are always arrays
  const docList = Array.isArray(documents) ? documents : []
  const selList = Array.isArray(selectedIds) ? selectedIds : []

  const handleConnect = useCallback(async () => {
    const url = docUrl.trim()
    if (!url) {
      setError("Please paste a Google Doc URL.")
      return
    }
    if (!url.includes("docs.google.com/document")) {
      setError("URL doesn't look like a Google Docs link.")
      return
    }

    setError(null)
    setConnecting(true)

    try {
      const result = await connectGoogleDoc(url)
      setLastConnected(result)
      setDocUrl("")
      onUploadSuccess({
        upload_id: result.doc_id,
        document_name: `Google Doc (${result.doc_id.slice(0, 8)}…)`,
        pages_processed: result.sections_indexed,
        chunks_created: result.added,
        doc_id: result.doc_id,
        is_gdoc: true,
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setConnecting(false)
    }
  }, [docUrl, onUploadSuccess])

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleConnect()
  }

  return (
    <div className="flex flex-col gap-4">
      {/* ── Connect Google Doc ─────────────────────────────── */}
      <div className="card-lexindex p-4">
        <h3 className="font-display text-sm font-semibold text-parchment mb-3 flex items-center gap-2">
          <Link2 size={14} className="text-gold" />
          Connect Google Doc
        </h3>

        <div className="flex flex-col gap-2">
          <div
            className="flex items-center gap-2 rounded-lg overflow-hidden transition-all duration-200"
            style={{
              border: `1px solid ${connecting ? "rgba(201,168,76,0.5)" : "var(--border)"}`,
              background: "var(--surface-raised)",
              boxShadow: connecting ? "0 0 14px rgba(201,168,76,0.07)" : "none",
            }}
          >
            <Link2 size={13} className="ml-3 text-gold-dim shrink-0" />
            <input
              id="gdoc-url-input"
              type="url"
              value={docUrl}
              onChange={(e) => { setDocUrl(e.target.value); setError(null) }}
              onKeyDown={handleKeyDown}
              disabled={connecting}
              placeholder="Paste Google Doc URL…"
              className="flex-1 bg-transparent text-sm font-body text-parchment placeholder-parchment-dim outline-none py-2.5 pr-2"
            />
          </div>

          <motion.button
            id="connect-gdoc-btn"
            onClick={handleConnect}
            disabled={connecting || !docUrl.trim()}
            whileHover={{ scale: connecting ? 1 : 1.02 }}
            whileTap={{ scale: connecting ? 1 : 0.97 }}
            className="btn-gold w-full flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-body disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none"
          >
            {connecting ? (
              <>
                <Loader2 size={13} className="animate-spin" />
                Indexing sections…
              </>
            ) : (
              <>
                <Link2 size={13} />
                Connect Document
              </>
            )}
          </motion.button>
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

        <AnimatePresence>
          {lastConnected && !error && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-3 text-xs font-body"
              style={{
                background: "rgba(201,168,76,0.07)",
                border: "1px solid rgba(201,168,76,0.2)",
                borderRadius: 6,
                padding: "8px 10px",
                color: "var(--parchment-dim)",
              }}
            >
              ✓ &nbsp;
              <span className="text-gold">
                {lastConnected.sections_indexed} sections
              </span>{" "}
              indexed — live sync active
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Connected Docs ────────────────────────────────────── */}
      <div className="card-lexindex p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-display text-sm font-semibold text-parchment flex items-center gap-2">
            <FileText size={14} className="text-gold" />
            Connected Docs
            {docList.length > 0 && (
              <span
                className="text-xs font-body px-1.5 py-0.5 rounded-full text-gold"
                style={{ background: "rgba(201,168,76,0.12)", border: "1px solid rgba(201,168,76,0.2)" }}
              >
                {docList.length}
              </span>
            )}
          </h3>

          {docList.length > 0 && (
            <div className="flex gap-2">
              <button onClick={onSelectAll} className="text-xs text-gold-dim hover:text-gold font-body transition-colors">All</button>
              <span className="text-border text-xs">·</span>
              <button onClick={onClearAll} className="text-xs text-parchment-dim hover:text-parchment font-body transition-colors">None</button>
            </div>
          )}
        </div>

        {docList.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-xs text-parchment-dim font-body">No documents connected yet.</p>
            <p className="text-xs text-parchment-faint font-body mt-1">Paste a Google Doc URL above to get started.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-2" style={{ maxHeight: 360, overflowY: "auto" }}>
            <AnimatePresence>
              {docList.map((doc, i) => {
                const isSelected = selList.includes(doc.upload_id)
                const isGdoc = doc.is_gdoc || doc.file_type === "gdoc"
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
                      {isSelected ? <CheckSquare size={14} className="text-gold" /> : <Square size={14} className="text-parchment-dim" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-body text-parchment truncate leading-snug">
                        {isGdoc ? "📄" : "📎"} {doc.document_name}
                      </p>
                      <p className="text-xs text-parchment-dim font-body mt-1 flex items-center gap-1.5">
                        {isGdoc ? (
                          <><RefreshCw size={9} className="text-gold-dim" />{doc.pages}s · {doc.chunks} chunks · live sync</>
                        ) : (
                          <>{doc.pages}p · {doc.chunks} chunks</>
                        )}
                      </p>
                    </div>
                  </motion.div>
                )
              })}
            </AnimatePresence>
          </div>
        )}

        {docList.length > 0 && (
          <p className="text-xs text-parchment-dim font-body mt-3 text-center">
            {selList.length === 0
              ? "No filter — querying all documents"
              : `Querying ${selList.length} of ${docList.length} doc${selList.length > 1 ? "s" : ""}`}
          </p>
        )}
      </div>
    </div>
  )
}
