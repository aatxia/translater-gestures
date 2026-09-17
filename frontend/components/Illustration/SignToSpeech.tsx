/**
 * Original line-art hero illustration: a signer's hand gesture becomes a
 * spoken/written sentence -- the app's actual function, drawn in-house
 * (flat outline style, single red accent) rather than reused third-party
 * stock art, since no source image file was available to embed directly.
 */
export function SignToSpeech(): React.ReactElement {
  return (
    <svg
      viewBox="0 0 420 340"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="h-full w-full"
      role="img"
      aria-label="Ілюстрація: жест руки перетворюється на текст і голос"
    >
      <ellipse cx="205" cy="230" rx="150" ry="95" className="fill-brand-50" />

      {/* speech bubble 1: the sign */}
      <g>
        <rect x="18" y="28" width="118" height="82" rx="20" className="fill-white stroke-slate-800" strokeWidth="2.5" />
        <path d="M70 108 L58 130 L92 108 Z" className="fill-white stroke-slate-800" strokeWidth="2.5" strokeLinejoin="round" />
        <path
          d="M52 78 v-20 a7 7 0 0 1 14 0 v14 m0 -18 a7 7 0 0 1 14 0 v18 m0 -14 a7 7 0 0 1 14 0 v20 m0 -6 a7 7 0 0 1 12 4 v10 a20 20 0 0 1 -20 20 h-6 a20 20 0 0 1 -17 -10 l-11 -18 a6 6 0 0 1 9 -8 l6 6"
          className="stroke-slate-800"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>

      {/* arrow */}
      <path
        d="M144 60 C 190 40, 230 40, 268 58"
        className="stroke-brand-500"
        strokeWidth="3"
        strokeLinecap="round"
        fill="none"
      />
      <path d="M258 48 L272 59 L256 66 Z" className="fill-brand-500" />

      {/* speech bubble 2: the translation */}
      <g>
        <rect x="276" y="20" width="126" height="82" rx="20" className="fill-white stroke-slate-800" strokeWidth="2.5" />
        <path d="M330 100 L342 122 L308 100 Z" className="fill-white stroke-slate-800" strokeWidth="2.5" strokeLinejoin="round" />
        <line x1="296" y1="46" x2="382" y2="46" className="stroke-slate-300" strokeWidth="5" strokeLinecap="round" />
        <line x1="296" y1="62" x2="368" y2="62" className="stroke-slate-300" strokeWidth="5" strokeLinecap="round" />
        <line x1="296" y1="78" x2="352" y2="78" className="stroke-slate-300" strokeWidth="5" strokeLinecap="round" />
        <circle cx="382" cy="80" r="14" className="fill-brand-500" />
        <path
          d="M377 74 v12 M377 76 l-4 3 v4 l4 3 M382 73 a8 8 0 0 1 0 14 M385 70 a13 13 0 0 1 0 20"
          className="stroke-white"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      </g>

      {/* person */}
      <g>
        {/* raised signing arm, drawn first so the torso overlaps its shoulder */}
        <path
          d="M180 210 C 150 200, 130 175, 118 140"
          className="stroke-brand-400"
          strokeWidth="20"
          strokeLinecap="round"
        />
        <circle cx="115" cy="134" r="13" className="fill-brand-400" />
        <path d="M104 116 l-6 -10 M114 112 l-2 -12 M126 114 l2 -12" className="stroke-slate-800" strokeWidth="2.5" strokeLinecap="round" />

        {/* motion lines by the hand */}
        <path d="M78 108 q-10 6 -8 16" className="stroke-slate-300" strokeWidth="2.5" strokeLinecap="round" fill="none" />
        <path d="M86 92 q-14 0 -16 12" className="stroke-slate-300" strokeWidth="2.5" strokeLinecap="round" fill="none" />

        {/* other arm, resting */}
        <path d="M220 215 C 245 225, 255 250, 250 278" className="stroke-brand-400" strokeWidth="20" strokeLinecap="round" />

        {/* torso */}
        <path
          d="M150 200 Q205 175 260 200 L272 320 L138 320 Z"
          className="fill-brand-600"
        />
        <path d="M188 202 L205 230 L222 202 L205 195 Z" className="fill-white" />

        {/* head + hair */}
        <circle cx="205" cy="150" r="34" className="fill-[#ffd9b8]" />
        <path
          d="M171 150 a34 34 0 0 1 68 0 c0 -22 -14 -36 -34 -36 s-34 14 -34 36 Z"
          className="fill-slate-800"
        />
        <circle cx="192" cy="152" r="2.5" className="fill-slate-800" />
        <circle cx="218" cy="152" r="2.5" className="fill-slate-800" />
        <path d="M196 166 q9 7 18 0" className="stroke-slate-800" strokeWidth="2.2" strokeLinecap="round" fill="none" />
      </g>

      {/* small potted plant, bottom right */}
      <g>
        <path d="M362 320 l6 -34 h20 l6 34 Z" className="fill-brand-500" />
        <path
          d="M372 286 q-4 -18 -16 -22 q4 16 14 24 M372 286 q4 -22 20 -26 q-2 18 -18 28 M372 286 v-10"
          className="stroke-slate-800"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      </g>
    </svg>
  );
}
