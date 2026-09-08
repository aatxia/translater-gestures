import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Transcript } from "./Transcript";

describe("Transcript", () => {
  it("shows an idle hint by default", () => {
    render(<Transcript state={{ status: "idle" }} />);
    expect(screen.getByText(/Введи текст або скажи щось голосом/)).toBeInTheDocument();
  });

  it("shows a loading message", () => {
    render(<Transcript state={{ status: "loading" }} />);
    expect(screen.getByText("Перекладаю...")).toBeInTheDocument();
  });

  it("shows the error message", () => {
    render(<Transcript state={{ status: "error", message: "Unrecognized word 'кавун'" }} />);
    expect(screen.getByText("Unrecognized word 'кавун'")).toBeInTheDocument();
  });

  it("renders each gloss token from a successful translation", () => {
    render(<Transcript state={{ status: "success", glossSequence: ["I", "WANT", "WATER"] }} />);

    expect(screen.getByText("I")).toBeInTheDocument();
    expect(screen.getByText("WANT")).toBeInTheDocument();
    expect(screen.getByText("WATER")).toBeInTheDocument();
  });
});
