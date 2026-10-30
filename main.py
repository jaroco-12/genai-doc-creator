import argparse
import time
from pathlib import Path


MAX_RETRIES = 5
DEFAULT_JOB_DESCRIPTION = Path("descriptions/zendar.txt")


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
        default=str(DEFAULT_JOB_DESCRIPTION),
        help="Path to the job description text file (default: descriptions/zendar.txt)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to write the generated resume (default: output/<job-file-stem>_resume.md)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    job_path = Path(args.job_description)
    if not job_path.is_file():
        raise SystemExit(f"Job description not found: {job_path}")

    import ats_extraction as ats
    import resume_writer as resw
    from dotenv import load_dotenv
    from google import genai

    load_dotenv()
    client = genai.Client(
        http_options=genai.types.HttpOptions(
            api_version="v1alpha"
        )
    )

    job_text = job_path.read_text(encoding="utf-8")

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
        Path(args.output)
        if args.output
        else Path("output") / f"{job_path.stem}_resume.md"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(resume, encoding="utf-8")

    print(resume)
    print(f"\nWrote resume to {output_path}")


if __name__ == "__main__":
    main()
