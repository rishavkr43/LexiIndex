import { useState, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Search, Loader2, Sparkles, AlertCircle } from "lucide-react"
import { queryDocuments } from "@/lib/api"

const SUGGESTIONS = [
  "What are the main topics in this document?",
  "Summarize the key findings.",
  "What dates and deadlines are mentioned?",
  "Who are the key people or entities?",
  "What are the conclusions or recommendations?",
]

export default function QueryInterface({
  selectedIds,
  documentsCount,
  isQuerying,
  setIsQuerying,
  onResult,
}) {
  const [question, setQuestion] = useState("")
  const [error, setError] = useState(null)
  const [charCount, setCharCount] = useState(0)
  const textareaRef = useRef(null)

  const handleChange = (e) => {
    setQuestion(e.target.value)
    setCharCount(e.target.value.length)
    setError(null)
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleSuggestion = (text) => {
    setQuestion(text)
    setCharCount(text.length)
    setError(null)
    textareaRef.current?.focus()
  }

  const handleSubmit = async () => {
    const trimmed = question.trim()
    if (!trimmed) {
      setError("Please enter a question.")
      return
    }
    if (trimmed.length > 1000) {
      setError("Question exceeds 1000 character limit.")
      return
    }
    if (documentsCount === 0) {
      setError("Upload at least one document before querying.")
      return
    }

    setError(null)
    setIsQuerying(true)

    try {
      const ids = selectedIds.length > 0 ? selectedIds : null
      const result = await queryDocuments(trimmed, ids)
      onResult(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsQuerying(false)
    }
  }

  return (
    <div className="card-lexindex p-5">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Search size={15} className="text-gold" />
        <h3 className="font-display text-sm font-semibold text-parchment">
          Ask a Question
        </h3>
        {selectedIds.length > 0 && (
          <span
            className="ml-auto text-xs font-body px-2 py-0.5 rounded-full text-gold"
            style={{
              background: "rgba(201,168,76,0.1)",
              border: "1px solid rgba(201,168,76,0.2)",
            }}
          >
            {selectedIds.length} doc{selectedIds.length > 1 ? "s" : ""} scoped
          </span>
        )}
      </div>

      {/* Textarea */}
      <div
        className="relative rounded-lg overflow-hidden transition-all duration-200"
        style={{
          border: `1px solid ${isQuerying ? "rgba(201,168,76,0.4)" : "var(--border)"}`,
          boxShadow: isQuerying ? "0 0 16px rgba(201,168,76,0.08)" : "none",
        }}
      >
        <textarea
          ref={textareaRef}
          value={question}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={isQuerying}
          placeholder="e.g. What are the main topics covered in these documents?"
          rows={4}
          maxLength={1000}
          className="w-full resize-none font-body text-sm text-parchment placeholder-parchment-dim bg-surface-raised p-4 outline-none transition-colors duration-200"
          style={{ lineHeight: 1.7 }}
        />

        {/* Char counter */}
        <div
          className="flex items-center justify-between px-4 py-2"
          style={{
            background: "var(--surface-raised)",
            borderTop: "1px solid var(--border)",
          }}
        >
          <p className="text-xs text-parchment-dim font-body">
            {charCount > 0
              ? `${charCount}/1000`
              : "Press Enter to submit · Shift+Enter for new line"}
          </p>

          <motion.button
            onClick={handleSubmit}
            disabled={isQuerying || !question.trim()}
            whileHover={{ scale: isQuerying ? 1 : 1.02 }}
            whileTap={{ scale: isQuerying ? 1 : 0.97 }}
            className="btn-gold flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none"
          >
            {isQuerying ? (
              <>
                <Loader2 size={13} className="animate-spin" />
                Retrieving…
              </>
            ) : (
              <>
                <Search size={13} />
                Search
              </>
            )}
          </motion.button>
        </div>
      </div>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-3 flex items-start gap-2 text-xs text-red-400 font-body px-3 py-2 rounded-lg"
            style={{
              background: "rgba(239,68,68,0.08)",
              border: "1px solid rgba(239,68,68,0.15)",
            }}
          >
            <AlertCircle size={12} className="mt-0.5 shrink-0" />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Retrieval indicator */}
      <AnimatePresence>
        {isQuerying && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-4 flex flex-col gap-2"
          >
            {[
              "Stage 1 — Scanning page index…",
              "Stage 2 — Retrieving relevant chunks…",
              "Grounding answer in documents…",
            ].map((step, i) => (
              <motion.div
                key={step}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.6 }}
                className="flex items-center gap-2 text-xs font-body text-parchment-dim"
              >
                <motion.div
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    delay: i * 0.6,
                  }}
                  className="w-1.5 h-1.5 rounded-full bg-gold shrink-0"
                />
                {step}
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Suggestions */}
      {!isQuerying && documentsCount > 0 && (
        <div className="mt-4">
          <p className="text-xs text-parchment-dim font-body mb-2 flex items-center gap-1.5">
            <Sparkles size={11} className="text-gold-dim" />
            Suggested questions
          </p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => handleSuggestion(s)}
                className="text-xs font-body px-3 py-1.5 rounded-full transition-all duration-200 text-left"
                style={{
                  background: "var(--surface-raised)",
                  border: "1px solid var(--border)",
                  color: "var(--parchment-dim)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "rgba(201,168,76,0.3)"
                  e.currentTarget.style.color = "var(--gold)"
                  e.currentTarget.style.background = "rgba(201,168,76,0.05)"
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--border)"
                  e.currentTarget.style.color = "var(--parchment-dim)"
                  e.currentTarget.style.background = "var(--surface-raised)"
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}