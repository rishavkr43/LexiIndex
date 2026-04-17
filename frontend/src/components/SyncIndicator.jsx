import { useState, useEffect, useCallback, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { RefreshCw, CheckCircle2, AlertCircle } from "lucide-react"
import { getSyncStatus } from "@/lib/api"

const POLL_MS = 30_000

function timeAgo(isoString) {
  if (!isoString) return "never"
  const diffMs = Date.now() - new Date(isoString).getTime()
  const s = Math.floor(diffMs / 1000)
  if (s < 5)  return "just now"
  if (s < 60) return `${s}s ago`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ago`
  return `${Math.floor(m / 60)}h ago`
}

export default function SyncIndicator() {
  const [syncs, setSyncs] = useState([])
  const [error, setError] = useState(false)
  const [toast, setToast] = useState(null)
  const [, setTick] = useState(0)
  const prevChangesRef = useRef({})

  const poll = useCallback(async () => {
    try {
      const data = await getSyncStatus()
      setSyncs(data)
      setError(false)

      data.forEach((sync) => {
        const changes = sync.added + sync.updated + sync.deleted
        const prev = prevChangesRef.current[sync.doc_id] ?? -1
        if (prev !== -1 && changes > prev) {
          const key = Date.now()
          setToast({ message: `Knowledge base updated — ${changes} section(s) changed`, key })
          setTimeout(() => setToast(null), 4000)
        }
        prevChangesRef.current[sync.doc_id] = changes
      })
    } catch {
      setError(true)
    }
  }, [])

  useEffect(() => {
    poll()
    const id = setInterval(poll, POLL_MS)
    return () => clearInterval(id)
  }, [poll])

  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 15_000)
    return () => clearInterval(id)
  }, [])

  if (syncs.length === 0 && !error) return null

  const latest = syncs.reduce((newest, s) =>
    !newest || s.synced_at > newest.synced_at ? s : newest, null
  )

  return (
    <>
      <div id="sync-indicator" className="flex items-center gap-1.5 font-body text-xs" style={{ color: "var(--parchment-dim)" }}>
        {error ? (
          <AlertCircle size={11} className="text-red-400" />
        ) : (
          <motion.div animate={{ rotate: [0, 360] }} transition={{ duration: 2, repeat: Infinity, ease: "linear" }} style={{ display: "flex" }}>
            <RefreshCw size={11} className="text-gold-dim" />
          </motion.div>
        )}
        {error ? (
          <span className="text-red-400">Sync error</span>
        ) : latest ? (
          <span>Synced <span style={{ color: "var(--gold)" }}>{timeAgo(latest.synced_at)}</span></span>
        ) : (
          <span>Syncing…</span>
        )}
      </div>

      <AnimatePresence>
        {toast && (
          <motion.div
            key={toast.key}
            initial={{ opacity: 0, y: -12, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.95 }}
            transition={{ duration: 0.3 }}
            className="fixed top-5 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-2.5 rounded-full text-xs font-body"
            style={{
              background: "rgba(20,18,14,0.92)",
              border: "1px solid rgba(201,168,76,0.35)",
              color: "var(--parchment)",
              backdropFilter: "blur(12px)",
              boxShadow: "0 0 24px rgba(201,168,76,0.15)",
              pointerEvents: "none",
            }}
          >
            <CheckCircle2 size={12} className="text-gold" />
            {toast.message}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
