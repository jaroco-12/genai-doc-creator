import argparse
import time
from pathlib import Path

MAX_RETRIES = 2
DESCRIPTIONS_DIR = Path("descriptions")
OUTPUT_DIR = Path("output")


def with_retries(operation, label):
    from google.genai import errors

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"{label}: attempt {attempt}/{MAX_RETRIES}")
        try:
            return operation()
        except errors.APIError as e:
            if e.code in (503, 429) and attempt < MAX_RETRIES:
                sleep_time = 2.0 * (2 ** (attempt - 1))
                print(
                    f"[Warning] HTTP {e.code} received. Retrying in {sleep_time}s "
                    f"(Attempt {attempt}/{MAX_RETRIES})..."
                )
                time.sleep(sleep_time)
            else:
                raise


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract ATS keywords from a job description and generate a tailored resume."
    )
    parser.add_argument(
        "job_description",
        nargs="?",
        default=None,
        help="Path to a job description file. Omit to start interactive mode.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to write the generated resume (one-shot mode only).",
    )
    return parser.parse_args()


def resolve_job_path(user_input: str) -> Path:
    """Accepts 'constellation', 'constellation.txt', or 'descriptions/constellation.txt'."""
    p = Path(user_input)
    if p.is_file():
        return p
    for candidate in (DESCRIPTIONS_DIR / user_input, DESCRIPTIONS_DIR / f"{user_input}.txt"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Job description not found: {user_input}")


def read_pasted_jd() -> tuple[str, str]:
    """Reads a multi-line pasted JD until 'END' is entered on its own line."""
    stem = input("Company / role label for filename (e.g. constellation): ").strip() or "tailored"
    print("Paste job description below, then type END on a new line:")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    return stem, "\n".join(lines).strip()


def process_job(client, ats, resw, job_text: str, stem: str, output_override: str | None = None):
    ats_highlights = with_retries(
        lambda: ats.extract_keywords(client, job_text),
        "ATS extraction",
    )
    print("FINISHED ATS EXTRACTION")

    resume = with_retries(
        lambda: resw.resume_creator(client, ats_highlights),
        "Resume generation",
    )

    output_path = (
        Path(output_override)
        if output_override
        else OUTPUT_DIR / f"Jared Ocotlan Garcia - {stem}_resume.md"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(resume, encoding="utf-8")

    print(resume)
    print(f"\nWrote resume to {output_path}\n")


def main():
    args = parse_args()

    import ats_extraction as ats
    import resume_writer as resw
    from dotenv import load_dotenv
    from google import genai

    load_dotenv()
    client = genai.Client(
        http_options=genai.types.HttpOptions(api_version="v1alpha")
    )

    # 1. One-shot mode: `python main.py descriptions/zendar.txt`
    if args.job_description:
        job_path = resolve_job_path(args.job_description)
        job_text = job_path.read_text(encoding="utf-8")
        process_job(client, ats, resw, job_text, job_path.stem, args.output)
        return

    # 2. Persistent interactive mode: `python main.py`
    print("genai-doc-creator active (client initialized).")
    print("Enter a file name in descriptions/ (e.g. 'zendar'), type 'paste', or 'quit' to exit.\n")

    while True:
        try:
            cmd = input("Job file / 'paste' / 'quit' > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not cmd:
            continue
        if cmd.lower() in ("quit", "exit", "q"):
            break

        try:
            if cmd.lower() == "paste":
                stem, job_text = read_pasted_jd()
                if not job_text:
                    print("Empty input, skipped.\n")
                    continue
            else:
                job_path = resolve_job_path(cmd)
                stem = job_path.stem
                job_text = job_path.read_text(encoding="utf-8")

            process_job(client, ats, resw, job_text, stem)

        except KeyboardInterrupt:
            print("\nRun cancelled. Instance still active.\n")
        except Exception as e:
            print(f"[Error] {e}\nInstance still active.\n")


if __name__ == "__main__":
    main()