import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TextInput } from "./TextInput";

describe("TextInput", () => {
  it("calls onChange as the user types", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(<TextInput value="" onChange={onChange} onSubmit={vi.fn()} />);

    await user.type(screen.getByPlaceholderText(/Введіть текст/), "П");

    expect(onChange).toHaveBeenCalledWith("П");
  });

  it("calls onSubmit with the trimmed value when the form is submitted", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<TextInput value="  Привіт.  " onChange={vi.fn()} onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: "Перекласти" }));

    expect(onSubmit).toHaveBeenCalledWith("Привіт.");
  });

  it("disables the submit button when the value is empty", () => {
    render(<TextInput value="   " onChange={vi.fn()} onSubmit={vi.fn()} />);

    expect(screen.getByRole("button", { name: "Перекласти" })).toBeDisabled();
  });

  it("disables the submit button when disabled prop is set", () => {
    render(<TextInput value="Привіт" onChange={vi.fn()} onSubmit={vi.fn()} disabled />);

    expect(screen.getByRole("button", { name: "Перекласти" })).toBeDisabled();
  });
});
