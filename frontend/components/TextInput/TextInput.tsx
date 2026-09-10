"use client";

interface TextInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
  disabled?: boolean;
}

export function TextInput({ value, onChange, onSubmit, disabled = false }: TextInputProps): React.ReactElement {
  return (
    <form
      className="flex gap-3"
      onSubmit={(event) => {
        event.preventDefault();
        const trimmed = value.trim();
        if (trimmed) onSubmit(trimmed);
      }}
    >
      <input
        type="text"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Введіть текст українською..."
        className="flex-1 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="rounded-lg bg-brand-600 px-5 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400"
      >
        Перекласти
      </button>
    </form>
  );
}
