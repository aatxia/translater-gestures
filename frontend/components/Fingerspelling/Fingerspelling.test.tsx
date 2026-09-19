import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Fingerspelling } from "./Fingerspelling";
import type { LetterPredictionMessage } from "@/types/api";

function letterMsg(overrides: Partial<LetterPredictionMessage>): LetterPredictionMessage {
  return {
    type: "letter_prediction",
    letter: "А",
    confidence: 0.8,
    is_final: false,
    ...overrides,
  };
}

describe("Fingerspelling", () => {
  it("shows a placeholder and no letters before anything is detected", () => {
    render(<Fingerspelling letterMessage={null} />);

    expect(screen.getByText(/Покажи літеру/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Очистити" })).toBeDisabled();
  });

  it("shows an interim (not-yet-confirmed) letter guess distinctly from confirmed ones", () => {
    render(<Fingerspelling letterMessage={letterMsg({ letter: "Б", is_final: false })} />);

    expect(screen.getByText("Б?")).toBeInTheDocument();
  });

  it("appends a confirmed letter to the spelled word", () => {
    const { rerender } = render(<Fingerspelling letterMessage={null} />);

    rerender(<Fingerspelling letterMessage={letterMsg({ letter: "П", is_final: true })} />);
    expect(screen.getByText("П")).toBeInTheDocument();

    rerender(<Fingerspelling letterMessage={letterMsg({ letter: "Р", is_final: true })} />);
    expect(screen.getByText("ПР")).toBeInTheDocument();
  });

  it("does not double-append the exact same confirmed message object on a re-render", () => {
    const confirmed = letterMsg({ letter: "Т", is_final: true });
    const { rerender } = render(<Fingerspelling letterMessage={confirmed} />);
    expect(screen.getByText("Т")).toBeInTheDocument();

    rerender(<Fingerspelling letterMessage={confirmed} />);
    expect(screen.getByText("Т")).toBeInTheDocument();
    expect(screen.queryByText("ТТ")).not.toBeInTheDocument();
  });

  it("labels itself as a real model, not demo", () => {
    render(<Fingerspelling letterMessage={null} />);
    expect(screen.getByText(/реальна модель, не демо/)).toBeInTheDocument();
  });

  it("clears the spelled word when the clear button is clicked", async () => {
    render(<Fingerspelling letterMessage={letterMsg({ letter: "А", is_final: true })} />);
    expect(screen.getByText("А")).toBeInTheDocument();

    const { default: userEvent } = await import("@testing-library/user-event");
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Очистити" }));

    expect(screen.getByText(/Покажи літеру/)).toBeInTheDocument();
  });
});
