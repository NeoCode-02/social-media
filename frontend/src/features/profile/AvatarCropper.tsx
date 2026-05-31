import { motion } from 'framer-motion'
import { ZoomIn } from 'lucide-react'
import { useCallback, useState } from 'react'
import Cropper from 'react-easy-crop'

import { Button } from '@/components/Button'
import { getCroppedFile, type PixelArea } from '@/lib/cropImage'

interface Props {
  src: string
  onCancel: () => void
  onDone: (file: File) => void
}

export function AvatarCropper({ src, onCancel, onDone }: Props) {
  const [crop, setCrop] = useState({ x: 0, y: 0 })
  const [zoom, setZoom] = useState(1)
  const [area, setArea] = useState<PixelArea | null>(null)
  const [busy, setBusy] = useState(false)

  const onComplete = useCallback((_: unknown, pixels: PixelArea) => setArea(pixels), [])

  async function apply() {
    if (!area) return
    setBusy(true)
    try {
      onDone(await getCroppedFile(src, area))
    } finally {
      setBusy(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[70] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 10 }}
        transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-md overflow-hidden rounded-3xl border border-border bg-elev p-5 shadow-soft"
      >
        <h2 className="mb-4 text-base font-semibold">Adjust your photo</h2>
        <div className="relative h-72 w-full overflow-hidden rounded-2xl bg-black">
          <Cropper
            image={src}
            crop={crop}
            zoom={zoom}
            aspect={1}
            cropShape="round"
            showGrid={false}
            onCropChange={setCrop}
            onZoomChange={setZoom}
            onCropComplete={onComplete}
          />
        </div>
        <div className="mt-4 flex items-center gap-3">
          <ZoomIn size={16} className="shrink-0 text-faint" />
          <input
            type="range"
            min={1}
            max={3}
            step={0.01}
            value={zoom}
            onChange={(e) => setZoom(Number(e.target.value))}
            className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-border accent-accent"
          />
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="ghost" type="button" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={apply} loading={busy} disabled={!area}>
            Apply
          </Button>
        </div>
      </motion.div>
    </motion.div>
  )
}
