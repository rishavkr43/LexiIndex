import { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Scale } from "lucide-react"
import CanvasBackground from "@/components/CanvasBackground"
import UploadPanel from "@/components/UploadPanel"
import QueryInterface from "@/components/QueryInterface"
import AnswerCard from "@/components/AnswerCard"
import SourcePanel from "@/components/SourcePanel"
import SyncIndicator from "@/components/SyncIndicator"
import { fetchDocuments } from "@/lib/api"

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, delay: i * 0.1, ease: "easeOut" },
  }),
}

export default function App() {
  const [documents, setDocuments] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [queryResult, setQueryResult] = useState(null)
  const [isQuerying, setIsQuerying] = useState(false)
  const [activeTab, setActiveTab] = useState("answer")

  // Load existing documents on mount
  useEffect(() => {
    fetchDocuments()
      .then((data) => setDocuments(Array.isArray(data) ? data : []))
      .catch(() => {})
  }, [])

  const handleUploadSuccess = useCallback((uploadResponse) => {
    const newDoc = {
      upload_id: uploadResponse.upload_id,
      document_name: uploadResponse.document_name,
      file_type: uploadResponse.is_gdoc ? "gdoc" : uploadResponse.document_name.split(".").pop().toLowerCase(),
      pages: uploadResponse.pages_processed,
      chunks: uploadResponse.chunks_created,
      is_gdoc: uploadResponse.is_gdoc ?? false,
      doc_id: uploadResponse.doc_id ?? null,
    }
    setDocuments((prev) => {
      const exists = prev.find((d) => d.upload_id === newDoc.upload_id)
      return exists ? prev : [newDoc, ...prev]
    })
  }, [])

  const handleQueryResult = useCallback((result) => {
    setQueryResult(result)
    setActiveTab("answer")
  }, [])

  const handleDeleteSuccess = useCallback((uploadId) => {
    setDocuments((prev) => prev.filter((d) => d.upload_id !== uploadId))
    setSelectedIds((prev) => prev.filter((id) => id !== uploadId))
    setQueryResult(null)
  }, [])

  const toggleDocumentSelection = useCallback((uploadId) => {
    setSelectedIds((prev) =>
      prev.includes(uploadId)
        ? prev.filter((id) => id !== uploadId)
        : [...prev, uploadId]
    )
  }, [])

  const selectAll = useCallback(() => {
    setSelectedIds(documents.map((d) => d.upload_id))
  }, [documents])

  const clearAll = useCallback(() => setSelectedIds([]), [])

  return (
    <div className="relative min-h-screen bg-background overflow-hidden">
      <CanvasBackground />

      {/* Main layout */}
      <div
        className="relative z-10 flex flex-col min-h-screen"
        style={{ maxWidth: "1400px", margin: "0 auto", padding: "0 24px" }}
      >
        {/* ── Header ───────────────────────────────────── */}
        <motion.header
          initial="hidden"
          animate="visible"
          variants={fadeUp}
          custom={0}
          className="flex items-center justify-between py-6 border-b border-border"
        >
          <div className="flex items-center gap-3">
            <div
              className="flex items-center justify-center rounded-lg glow-gold"
              style={{
                width: 38,
                height: 38,
                background: "linear-gradient(135deg, #c9a84c22, #c9a84c11)",
                border: "1px solid rgba(201,168,76,0.3)",
              }}
            >
              <Scale size={18} className="text-gold" />
            </div>
            <div>
              <h1 className="font-display text-xl font-semibold text-parchment leading-none">
                LexIndex
              </h1>
              <p className="text-xs text-parchment-dim mt-0.5 font-body">
                Live Google Docs RAG
              </p>
            </div>
          </div>

          <SyncIndicator />

        </motion.header>

        {/* ── Hero ─────────────────────────────────────── */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={fadeUp}
          custom={1}
          className="py-10 text-center"
        >
          <p className="text-xs uppercase tracking-widest text-gold-dim font-body mb-3">
            Live Google Docs RAG
          </p>
          <h2
            className="font-display text-gradient-gold mb-3"
            style={{ fontSize: "clamp(2rem, 4vw, 3.2rem)", lineHeight: 1.15 }}
          >
            Connect. Sync. Understand.
          </h2>
          <p
            className="font-body text-parchment-dim mx-auto"
            style={{ maxWidth: 480, fontSize: "0.95rem", lineHeight: 1.7 }}
          >
            Paste a Google Doc URL and ask questions. Your knowledge base
            stays live — re-indexed automatically every minute.
          </p>
        </motion.div>

        {/* ── Three-column layout ───────────────────────── */}
        <div
          className="flex gap-6 pb-12"
          style={{ alignItems: "flex-start" }}
        >
          {/* Left — Upload + Documents */}
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            custom={2}
            style={{ width: "320px", flexShrink: 0 }}
          >
            <UploadPanel
              documents={documents}
              selectedIds={selectedIds}
              onUploadSuccess={handleUploadSuccess}
              onDeleteSuccess={handleDeleteSuccess}
              onToggleDocument={toggleDocumentSelection}
              onSelectAll={selectAll}
              onClearAll={clearAll}
            />
          </motion.div>

          {/* Center — Query + Results */}
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            custom={3}
            className="flex-1 flex flex-col gap-5"
            style={{ minWidth: 0 }}
          >
            <QueryInterface
              selectedIds={selectedIds}
              documentsCount={documents.length}
              isQuerying={isQuerying}
              setIsQuerying={setIsQuerying}
              onResult={handleQueryResult}
            />

            <AnimatePresence mode="wait">
              {queryResult && (
                <motion.div
                  key="result"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.4 }}
                >
                  {/* Tab switcher */}
                  <div className="flex gap-1 mb-4 p-1 rounded-lg"
                    style={{ background: "var(--surface)", border: "1px solid var(--border)", width: "fit-content" }}
                  >
                    {["answer", "sources"].map((tab) => (
                      <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className="px-4 py-1.5 rounded-md text-sm font-body capitalize transition-all duration-200"
                        style={{
                          background: activeTab === tab ? "var(--surface-raised)" : "transparent",
                          color: activeTab === tab ? "var(--parchment)" : "var(--parchment-dim)",
                          border: activeTab === tab ? "1px solid var(--border-gold)" : "1px solid transparent",
                          boxShadow: activeTab === tab ? "0 0 12px rgba(201,168,76,0.08)" : "none",
                        }}
                      >
                        {tab === "answer" ? "Answer" : `Sources (${queryResult.sources?.length ?? 0})`}
                      </button>
                    ))}
                  </div>

                  <AnimatePresence mode="wait">
                    {activeTab === "answer" && (
                      <motion.div
                        key="answer"
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 8 }}
                        transition={{ duration: 0.25 }}
                      >
                        <AnswerCard answer={queryResult.answer} />
                      </motion.div>
                    )}
                    {activeTab === "sources" && (
                      <motion.div
                        key="sources"
                        initial={{ opacity: 0, x: 8 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -8 }}
                        transition={{ duration: 0.25 }}
                      >
                        <SourcePanel
                          sources={queryResult.sources}
                          retrievalMeta={queryResult.retrieval_meta}
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
