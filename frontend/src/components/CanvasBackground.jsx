import { useEffect, useRef } from "react"

const NODE_COUNT = 38
const CONNECTION_DISTANCE = 140
const SPEED = 0.28

function randomBetween(a, b) {
  return a + Math.random() * (b - a)
}

function initNodes(width, height) {
  return Array.from({ length: NODE_COUNT }, () => ({
    x: randomBetween(0, width),
    y: randomBetween(0, height),
    vx: randomBetween(-SPEED, SPEED),
    vy: randomBetween(-SPEED, SPEED),
    radius: randomBetween(1.2, 3.2),
    opacity: randomBetween(0.3, 0.9),
    pulseOffset: randomBetween(0, Math.PI * 2),
  }))
}

export default function CanvasBackground() {
  const canvasRef = useRef(null)
  const nodesRef = useRef([])
  const rafRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
      nodesRef.current = initNodes(canvas.width, canvas.height)
    }

    resize()
    window.addEventListener("resize", resize)

    let frame = 0

    const draw = () => {
      const { width, height } = canvas
      ctx.clearRect(0, 0, width, height)

      frame++
      const time = frame * 0.012

      const nodes = nodesRef.current

      // Update positions
      nodes.forEach((node) => {
        node.x += node.vx
        node.y += node.vy

        if (node.x < -20) node.x = width + 20
        if (node.x > width + 20) node.x = -20
        if (node.y < -20) node.y = height + 20
        if (node.y > height + 20) node.y = -20
      })

      // Draw edges
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i]
          const b = nodes[j]
          const dx = a.x - b.x
          const dy = a.y - b.y
          const dist = Math.sqrt(dx * dx + dy * dy)

          if (dist < CONNECTION_DISTANCE) {
            const alpha = (1 - dist / CONNECTION_DISTANCE) * 0.18
            ctx.beginPath()
            ctx.moveTo(a.x, a.y)
            ctx.lineTo(b.x, b.y)
            ctx.strokeStyle = `rgba(201, 168, 76, ${alpha})`
            ctx.lineWidth = 0.6
            ctx.stroke()
          }
        }
      }

      // Draw nodes
      nodes.forEach((node) => {
        const pulse = Math.sin(time + node.pulseOffset) * 0.3 + 0.7
        const r = node.radius * pulse
        const alpha = node.opacity * pulse

        // Outer glow
        const glow = ctx.createRadialGradient(
          node.x, node.y, 0,
          node.x, node.y, r * 5
        )
        glow.addColorStop(0, `rgba(201, 168, 76, ${alpha * 0.25})`)
        glow.addColorStop(1, `rgba(201, 168, 76, 0)`)
        ctx.beginPath()
        ctx.arc(node.x, node.y, r * 5, 0, Math.PI * 2)
        ctx.fillStyle = glow
        ctx.fill()

        // Core node
        ctx.beginPath()
        ctx.arc(node.x, node.y, r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(201, 168, 76, ${alpha})`
        ctx.fill()
      })

      rafRef.current = requestAnimationFrame(draw)
    }

    rafRef.current = requestAnimationFrame(draw)

    return () => {
      window.removeEventListener("resize", resize)
      cancelAnimationFrame(rafRef.current)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none"
      style={{ zIndex: 0, opacity: 0.55 }}
    />
  )
}