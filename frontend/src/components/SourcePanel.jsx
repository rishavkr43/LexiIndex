import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Layers, FileText, ChevronDown, ChevronUp, Cpu } from "lucide-react"
import { formatScore, getScoreColor, truncateText } from "@/lib/utils"

export default function SourcePanel({ sources, retrievalMeta }) {
  const [expandedIdx, setExpandedIdx] = useState(null)

  const toggle = (i) => setExpandedIdx(expandedIdx === i ? null : i)

  return (
    <div className="flex flex-col gap-4">
      {/* Retrieval Metadata */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="card-lexindex p-4"
      >
        <div className="flex items-center gap-2 mb-3">
          <Cpu size={14} className="text-gold" />
          <h3 className="font-display text-sm font-semibold text-parchment">
            Retrieval Internals
          </h3>
        </div>

        <div className="divider-gold mb-4" />

        <div className="grid grid-cols-3 gap-3 mb-4">
          {[
            { label: "Strategy", value: retrievalMeta?.strategy ?? "—" },
            {
              label: "Pages Scanned",
              value: retrievalMeta?.pages_identified?.length ?? 0,
            },
            {
              label: "Chunks Retrieved",
              value: retrievalMeta?.chunks_retrieved ?? 0,
            },
          ].map(({ label, value }) => (
            <div
              key={label}
              className="flex flex-col gap-1 p-3 rounded-lg text-center"
              style={{
                background: "var(--surface-raised)",
                border: "1px solid var(--border)",
              }}
            >
              <p className="text-xs text-parchment-dim font-body">{label}</p>
              <p className="text-sm font-display text-gold font-semibold">
                {value}
              </p>
            </div>
          ))}
        </div>

        {/* Pages identified in Stage 1 */}
        {retrievalMeta?.pages_identified?.length > 0 && (
          <div>
            <p className="text-xs text-parchment-dim font-body mb-2">
              Stage 1 — Pages identified
            </p>
            <div className="flex flex-wrap gap-2">
              {retrievalMeta.pages_identified.map((page) => (
                <span
                  key={page}
                  className="text-xs font-body px-2 py-1 rounded-md"
                  style={{
                    background: "rgba(201,168,76,0.08)",
                    border: "1px solid rgba(201,168,76,0.2)",
                    color: "var(--parchment-dim)",
                  }}
                >
                  {page}
                </span>
              ))}
            </div>
          </div>
        )}
      </motion.div>

      {/* Source Chunks */}
      <div className="card-lexindex p-4">
        <div className="flex items-center gap-2 mb-3">
          <Layers size={14} className="text-gold" />
          <h3 className="font-display text-sm font-semibold text-parchment">
            Retrieved Chunks
          </h3>
          <span
            className="ml-auto text-xs font-body px-2 py-0.5 rounded-full text-gold"
            style={{
              background: "rgba(201,168,76,0.1)",
              border: "1px solid rgba(201,168,76,0.2)",
            }}
          >
            {sources?.length ?? 0} chunks
          </span>
        </div>

        <div className="divider-gold mb-4" />

        <div className="flex flex-col gap-3">
          {sources?.map((source, i) => {
            const isExpanded = expandedIdx === i
            const scoreColor = getScoreColor(source.score)

            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07 }}
                className="chunk-card p-3"
              >
                {/* Chunk header */}
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-body text-parchment-dim flex items-center gap-1">
                      <FileText size={10} className="text-gold-dim" />
                      {source.source_file}
                    </span>
                    <span
                      className="text-xs font-body px-1.5 py-0.5 rounded"
                      style={{
                        background: "rgba(201,168,76,0.08)",
                        border: "1px solid rgba(201,168,76,0.15)",
                        color: "var(--parchment-dim)",
                      }}
                    >
                      p.{source.page}
                    </span>
                    <span
                      className="text-xs font-body px-1.5 py-0.5 rounded"
                      style={{
                        background: "var(--surface)",
                        border: "1px solid var(--border)",
                        color: "var(--parchment-dim)",
                      }}
                    >
                      chunk #{source.chunk_index}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`text-xs font-body font-semibold ${scoreColor}`}>
                      {formatScore(source.score)}
                    </span>
                    <button
                      onClick={() => toggle(i)}
                      className="text-parchment-dim hover:text-parchment transition-colors"
                    >
                      {isExpanded
                        ? <ChevronUp size={13} />
                        : <ChevronDown size={13} />}
                    </button>
                  </div>
                </div>

                {/* Score bar */}
                <div className="score-bar mb-2">
                  <motion.div
                    className="score-bar-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${source.score * 100}%` }}
                    transition={{ duration: 0.8, delay: i * 0.07, ease: "easeOut" }}
                  />
                </div>

                {/* Chunk text */}
                <p className="text-xs font-body text-parchment-dim leading-relaxed">
                  {isExpanded ? source.text : truncateText(source.text, 180)}
                </p>

                <AnimatePresence>
                  {!isExpanded && source.text.length > 180 && (
                    <motion.button
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      onClick={() => toggle(i)}
                      className="text-xs text-gold-dim hover:text-gold font-body mt-1 transition-colors"
                    >
                      Show more
                    </motion.button>
                  )}
                </AnimatePresence>
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}