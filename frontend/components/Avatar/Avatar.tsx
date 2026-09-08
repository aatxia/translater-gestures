"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { GlossPlayer } from "./player";
import { applyRotations, buildPuppet } from "./puppet";

interface AvatarProps {
  /** Confirmed gloss sequence to animate, in order. Empty = idle/neutral. */
  glossSequence: string[];
}

interface PlaybackStatus {
  currentGloss: string | null;
  unanimatedGlosses: string[];
}

const IDLE_STATUS: PlaybackStatus = { currentGloss: null, unanimatedGlosses: [] };

/** Detected once via a throwaway canvas, not the real one -- no effect-time
 * setState needed to gate the fallback UI (jsdom, and real browsers without
 * WebGL, both fail this synchronously before any Three.js object exists). */
function detectWebglSupport(): boolean {
  if (typeof document === "undefined" || typeof window === "undefined") {
    return false;
  }
  try {
    const canvas = document.createElement("canvas");
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext("webgl2") ?? canvas.getContext("webgl"))
    );
  } catch {
    return false;
  }
}

export function Avatar({ glossSequence }: AvatarProps): React.ReactElement {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const playerRef = useRef<GlossPlayer>(new GlossPlayer());
  const [webglUnsupported] = useState(() => !detectWebglSupport());
  const [status, setStatus] = useState<PlaybackStatus>(IDLE_STATUS);

  useEffect(() => {
    playerRef.current.play(glossSequence);
  }, [glossSequence]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || webglUnsupported) {
      return;
    }

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    } catch (err) {
      // Already gated by detectWebglSupport() above; a failure here despite
      // that positive detection is a rare edge case, not worth a second
      // render pass to surface in the UI -- fail silently, no fake canvas.
      console.error("THREE.WebGLRenderer failed to initialize:", err);
      return;
    }

    const width = canvas.clientWidth || 320;
    const height = canvas.clientHeight || 224;
    renderer.setSize(width, height, false);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(35, width / height, 0.1, 10);
    camera.position.set(0, 1, 3.2);
    camera.lookAt(0, 0.7, 0);

    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const keyLight = new THREE.DirectionalLight(0xffffff, 0.8);
    keyLight.position.set(2, 3, 2);
    scene.add(keyLight);

    const puppet = buildPuppet();
    scene.add(puppet.root);

    let frameId: number;
    let lastTime = performance.now();

    function tick(now: number): void {
      const delta = Math.min((now - lastTime) / 1000, 0.1);
      lastTime = now;

      const frame = playerRef.current.update(delta);
      applyRotations(puppet, frame.rotations);
      setStatus({ currentGloss: frame.currentGloss, unanimatedGlosses: frame.unanimatedGlosses });

      renderer.render(scene, camera);
      frameId = requestAnimationFrame(tick);
    }
    frameId = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(frameId);
      renderer.dispose();
    };
  }, [webglUnsupported]);

  if (webglUnsupported) {
    return (
      <div className="flex h-40 items-center justify-center rounded-xl bg-slate-100 px-4 text-center text-sm text-slate-400">
        WebGL не підтримується цим браузером — 3D avatar недоступний.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between text-xs">
        <span className="rounded-full bg-amber-100 px-2 py-0.5 font-semibold text-amber-700">
          ⚠ DEMO — умовні жести, не справжня УЖМ
        </span>
        {status.currentGloss && <span className="text-slate-500">{status.currentGloss}</span>}
      </div>
      <canvas ref={canvasRef} className="h-56 w-full rounded-xl bg-slate-100" />
      {status.unanimatedGlosses.length > 0 && (
        <p className="text-xs text-slate-400">
          Немає анімації для: {status.unanimatedGlosses.join(", ")}
        </p>
      )}
    </div>
  );
}
