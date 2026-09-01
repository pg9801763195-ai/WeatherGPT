import React, { useRef, useEffect, useState } from 'react';
import { parseGIF, decompressFrames } from 'gifuct-js';
import { resolveWeatherVisual } from '../utils/weatherVisuals';

export default function WeatherAtmosphere({ condition, isHovered = false, customVisual = null }) {
  const visual = customVisual || resolveWeatherVisual(condition);
  const canvasRef = useRef(null);
  
  // State and refs for frame-accurate playback
  const framesRef = useRef([]);
  const currentFrameIdxRef = useRef(0);
  const animTimerRef = useRef(null);
  const isHoveredRef = useRef(isHovered);
  isHoveredRef.current = isHovered;

  const [isReady, setIsReady] = useState(false);
  const [hasPlayed, setHasPlayed] = useState(false);
  const [loadError, setLoadError] = useState(false);

  // Render a specific frame onto the visible canvas
  const renderFrame = (idx) => {
    const canvas = canvasRef.current;
    const frames = framesRef.current;
    if (!canvas || !frames || frames.length === 0) return;

    const frame = frames[idx % frames.length];
    if (!frame || !frame.canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    if (canvas.width !== frame.width || canvas.height !== frame.height) {
      canvas.width = frame.width;
      canvas.height = frame.height;
    }
    ctx.drawImage(frame.canvas, 0, 0);
  };

  // Load and decode the GIF frames with proper cumulative composition
  useEffect(() => {
    let isMounted = true;
    setIsReady(false);
    setLoadError(false);
    setHasPlayed(false);
    currentFrameIdxRef.current = 0;
    framesRef.current = [];

    if (animTimerRef.current) {
      clearTimeout(animTimerRef.current);
      animTimerRef.current = null;
    }

    if (!visual?.gif) return;

    const loadGifFrames = async () => {
      try {
        const res = await fetch(visual.gif);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const buffer = await res.arrayBuffer();
        const parsed = parseGIF(buffer);
        const rawFrames = decompressFrames(parsed, true);

        if (!rawFrames || rawFrames.length === 0) {
          throw new Error('No frames decoded');
        }

        // Determine full GIF dimensions from header or largest frame
        const gifWidth = parsed.lsd?.width || rawFrames[0].dims.width;
        const gifHeight = parsed.lsd?.height || rawFrames[0].dims.height;

        // Cumulative composition canvas to properly assemble full frames
        const fullCanvas = document.createElement('canvas');
        fullCanvas.width = gifWidth;
        fullCanvas.height = gifHeight;
        const fullCtx = fullCanvas.getContext('2d', { willReadFrequently: true });

        const patchCanvas = document.createElement('canvas');
        const patchCtx = patchCanvas.getContext('2d', { willReadFrequently: true });

        const composedFrames = [];

        for (let i = 0; i < rawFrames.length; i++) {
          const f = rawFrames[i];
          const { top = 0, left = 0, width: fw, height: fh } = f.dims;

          // Put current patch data onto patch canvas
          patchCanvas.width = fw;
          patchCanvas.height = fh;
          const patchImgData = new ImageData(new Uint8ClampedArray(f.patch), fw, fh);
          patchCtx.putImageData(patchImgData, 0, 0);

          // Draw the patch onto the cumulative full canvas
          fullCtx.drawImage(patchCanvas, left, top);

          // Snapshot this fully assembled composite frame
          const frameCanvas = document.createElement('canvas');
          frameCanvas.width = gifWidth;
          frameCanvas.height = gifHeight;
          const frameCtx = frameCanvas.getContext('2d');
          frameCtx.drawImage(fullCanvas, 0, 0);

          composedFrames.push({
            canvas: frameCanvas,
            width: gifWidth,
            height: gifHeight,
            delay: Math.max(40, f.delay || 80)
          });

          // Handle GIF disposal method for subsequent frames
          if (f.disposalType === 2) {
            // Restore to background (clear this frame's region)
            fullCtx.clearRect(left, top, fw, fh);
          }
        }

        if (isMounted) {
          framesRef.current = composedFrames;
          setIsReady(true);
          // Render initial frame immediately so it shows clean, full picture
          renderFrame(0);
        }
      } catch (err) {
        console.warn('GIF frame decoder notice, fallback to native image:', err);
        if (isMounted) {
          setLoadError(true);
        }
      }
    };

    loadGifFrames();

    return () => {
      isMounted = false;
      if (animTimerRef.current) {
        clearTimeout(animTimerRef.current);
      }
    };
  }, [visual?.gif]);

  // Frame-accurate animation loop: plays on hover, freezes on unhover, resumes from exact frame
  useEffect(() => {
    if (!isReady || framesRef.current.length === 0) return;

    if (animTimerRef.current) {
      clearTimeout(animTimerRef.current);
      animTimerRef.current = null;
    }

    if (isHovered) {
      setHasPlayed(true);

      const scheduleNextFrame = () => {
        if (!isHoveredRef.current) return;

        const frames = framesRef.current;
        if (!frames || frames.length === 0) return;

        // Advance to next frame in sequence
        const nextIdx = (currentFrameIdxRef.current + 1) % frames.length;
        currentFrameIdxRef.current = nextIdx;
        renderFrame(nextIdx);

        const delay = frames[nextIdx]?.delay || 80;
        animTimerRef.current = setTimeout(scheduleNextFrame, delay);
      };

      // Play next frame according to current frame delay
      const currentDelay = framesRef.current[currentFrameIdxRef.current]?.delay || 80;
      animTimerRef.current = setTimeout(scheduleNextFrame, currentDelay);
    } else {
      // Unhovered: do nothing, canvas remains displaying that exact frozen frame!
    }

    return () => {
      if (animTimerRef.current) {
        clearTimeout(animTimerRef.current);
      }
    };
  }, [isHovered, isReady]);

  return (
    <div className="absolute inset-0 w-full h-full overflow-hidden select-none pointer-events-none transition-all">
      {/* Base Gradient Layer */}
      <div className={`absolute inset-0 bg-gradient-to-br ${visual.gradient} transition-all duration-700 opacity-95`} />

      {/* Frame-Accurate High-Definition GIF Visual Layer (Natural photo colors, no blend distortions) */}
      {isReady && !loadError ? (
        <div className="absolute inset-0">
          <canvas
            ref={canvasRef}
            className="w-full h-full object-cover"
          />
        </div>
      ) : visual?.gif ? (
        <div className="absolute inset-0">
          <img
            src={visual.gif}
            alt={`${visual.label} weather visual`}
            className="w-full h-full object-cover"
          />
        </div>
      ) : null}

      {/* High-End Dark Vignette Gradient Overlay for Crisp Text Contrast */}
      <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/40 to-slate-900/35" />

      {/* Atmospheric Accent Radial Glow */}
      <div 
        className="absolute inset-0 opacity-20 pointer-events-none"
        style={{
          background: `radial-gradient(circle at 75% 25%, ${visual.accentColor} 0%, transparent 60%)`
        }}
      />

      {/* Subtle Grid Accent Texture */}
      <div 
        className="absolute inset-0 opacity-10 pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(rgba(255, 255, 255, 0.15) 1px, transparent 1px)`,
          backgroundSize: '24px 24px'
        }}
      />
    </div>
  );
}
