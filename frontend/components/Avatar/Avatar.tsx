"use client";

import { Info, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { formatGlossLabel, groupGlossesForDisplay } from "@/lib/glossDisplay";
import { GlossPlayer } from "./player";
import { poseForGloss } from "./poses";
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

const SPEED_OPTIONS = [0.5, 1, 1.5, 2] as const;

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
  const speedRef = useRef(1);
  const [webglUnsupported] = useState(() => !detectWebglSupport());
  const [status, setStatus] = useState<PlaybackStatus>(IDLE_STATUS);
  const [speed, setSpeed] = useState(1);

  useEffect(() => {
    speedRef.current = speed;
  }, [speed]);

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

    // Three-point lighting for contrast: a bright key light casting real
    // shadow-side definition, a dim cool fill so the shadow side isn't pure
    // black, and a rim light behind the puppet to separate it from the dark
    // viewport background.
    scene.add(new THREE.AmbientLight(0xffffff, 0.25));
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.4);
    keyLight.position.set(2, 3, 2);
    scene.add(keyLight);
    const fillLight = new THREE.DirectionalLight(0x8ab4ff, 0.35);
    fillLight.position.set(-2.5, 1, 1.5);
    scene.add(fillLight);
    const rimLight = new THREE.DirectionalLight(0xffffff, 0.6);
    rimLight.position.set(0, 2, -3);
    scene.add(rimLight);

    const puppet = buildPuppet();
    scene.add(puppet.root);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 0.7, 0);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = false;
    controls.minDistance = 1.8;
    controls.maxDistance = 5;
    controls.update();

    let frameId: number;
    let lastTime = performance.now();

    function tick(now: number): void {
      const delta = Math.min((now - lastTime) / 1000, 0.1);
      lastTime = now;

      const frame = playerRef.current.update(delta * speedRef.current);
      applyRotations(puppet, frame.rotations);
      setStatus({ currentGloss: frame.currentGloss, unanimatedGlosses: frame.unanimatedGlosses });

      controls.update();
      renderer.render(scene, camera);
      frameId = requestAnimationFrame(tick);
    }
    frameId = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(frameId);
      controls.dispose();
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

  const displayItems = groupGlossesForDisplay(glossSequence);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between text-xs">
        <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 px-2 py-0.5 font-medium text-slate-500">
          <Info className="h-3 w-3" aria-hidden />
          Демо-жести, не справжня УЖМ
        </span>
        {status.currentGloss && (
          <span className="text-slate-500">{formatGlossLabel(status.currentGloss)}</span>
        )}
      </div>

      <canvas ref={canvasRef} className="h-56 w-full rounded-xl bg-slate-800" />
      <p className="text-center text-[11px] text-slate-400">
        Перетягніть, щоб обертати модель — прокрутіть, щоб наблизити
      </p>

      <div className="flex items-center gap-2 text-xs">
        <span className="font-medium text-slate-500">Швидкість:</span>
        <div className="flex gap-1">
          {SPEED_OPTIONS.map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setSpeed(option)}
              aria-pressed={speed === option}
              className={`rounded-full px-2 py-0.5 font-medium transition-colors ${
                speed === option
                  ? "bg-brand-600 text-white"
                  : "bg-slate-100 text-slate-500 hover:bg-slate-200"
              }`}
            >
              {option}×
            </button>
          ))}
        </div>
      </div>

      {displayItems.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {displayItems.map((item) => {
            const canReplay = item.tokens.some((token) => poseForGloss(token) !== null);
            return (
              <button
                key={item.key}
                type="button"
                disabled={!canReplay}
                onClick={() => playerRef.current.play(item.tokens)}
                title={canReplay ? `Повторити жест «${item.label}»` : "Немає анімації для цього жесту"}
                className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${
                  canReplay
                    ? "border-slate-200 text-slate-600 hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700"
                    : "cursor-not-allowed border-slate-100 text-slate-300"
                }`}
              >
                {canReplay && <RotateCcw className="h-3 w-3" aria-hidden />}
                {item.label}
              </button>
            );
          })}
        </div>
      )}

      {status.unanimatedGlosses.length > 0 && (
        <p className="text-xs text-slate-400">
          Немає анімації для:{" "}
          {groupGlossesForDisplay(status.unanimatedGlosses)
            .map((item) => item.label)
            .join(", ")}
        </p>
      )}
    </div>
  );
}
