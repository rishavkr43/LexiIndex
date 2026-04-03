import { useState } from "react"
import { motion } from "framer-motion"
import { Copy, Check, BookOpen } from "lucide-react"

const NOT_FOUND = "The information is not available in the uploaded documents."

export default function AnswerCard({ answer }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(answer)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const isNotFound = answer?.trim() === NOT_FOUND

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="card-lexindex p-5"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BookOpen size={14} className="text-gold" />
          <h3 className="font-display text-sm font-semibold text-parchment">
            Answer
          </h3>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs font-body px-2.5 py-1 rounded-md transition-all duration-200"
          style={{
            background: "var(--surface-raised)",
            border: "1px solid var(--border)",
            color: copied ? "var(--gold)" : "var(--parchment-dim)",
            borderColor: copied ? "rgba(201,168,76,0.3)" : "var(--border)",
          }}
        >
          {copied ? <Check size={11} /> : <Copy size={11} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      <div className="divider-gold mb-4" />

      {/* Answer body */}
      {isNotFound ? (
        <div
          className="flex items-start gap-3 p-4 rounded-lg"
          style={{
            background: "rgba(201,168,76,0.05)",
            border: "1px solid rgba(201,168,76,0.15)",
          }}
        >
          <span className="text-gold text-base mt-0.5">⚠</span>
          <p className="text-sm font-body text-parchment-dim leading-relaxed">
            {NOT_FOUND}
          </p>
        </div>
      ) : (
        <div
          className="font-body text-sm text-parchment leading-relaxed"
          style={{ whiteSpace: "pre-wrap", lineHeight: 1.85 }}
        >
          {answer?.split(/(\[.*?\])/g).map((part, i) =>
            /^\[.*\]$/.test(part) ? (
              <span
                key={i}
                className="font-body text-xs px-1.5 py-0.5 rounded mx-0.5"
                style={{
                  background: "rgba(201,168,76,0.12)",
                  border: "1px solid rgba(201,168,76,0.25)",
                  color: "var(--gold)",
                  fontStyle: "normal",
                  whiteSpace: "nowrap",
                }}
              >
                {part}
              </span>
            ) : (
              <span key={i}>{part}</span>
            )
          )}
        </div>
      )}
    </motion.div>
  )
}