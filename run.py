"""
TrendRadar - Orchestrator

Usage:
  python run.py           # scrape + generate prompt
  python run.py --render  # just render existing briefing to HTML
"""

import datetime
import os
import subprocess
import sys
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run_step(name, script, extra_args=None):
    print(f"\n{'='*50}")
    print(f" {name}")
    print(f"{'='*50}\n")
    cmd = [sys.executable, os.path.join(BASE_DIR, script)]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"\n[ERROR] {name} failed (exit code {result.returncode})")
        sys.exit(1)


def main():
    render_only = "--render" in sys.argv

    today = datetime.date.today().isoformat()

    if render_only:
        md_path = os.path.join(BASE_DIR, "output", f"briefing-{today}.md")
        if os.path.exists(md_path):
            run_step("Rendering HTML", "render.py", [md_path])
        else:
            output_dir = os.path.join(BASE_DIR, "output")
            if os.path.exists(output_dir):
                md_files = sorted(
                    [f for f in os.listdir(output_dir) if f.endswith(".md")],
                    reverse=True,
                )
                if md_files:
                    md_path = os.path.join(output_dir, md_files[0])
                    print(f"Using most recent: {md_path}")
                    run_step("Rendering HTML", "render.py", [md_path])
                else:
                    print("No briefing files found in output/")
            else:
                print(f"No briefing found at {md_path}")
    else:
        run_step("Scraping", "scrape.py")
        run_step("Generating Prompt", "briefing.py")

        prompt_path = os.path.join(BASE_DIR, "prompt.md")
        if os.path.exists(prompt_path):
            print(f"\nDone! Prompt saved to {prompt_path}")
            print("\nNext steps:")
            print("  1. Copy the content of prompt.md")
            print("  2. Paste into Claude chat")
            print("  3. Save Claude's response to output/briefing-{}.md".format(today))
            print("  4. Run: python render.py")
            webbrowser.open(prompt_path)


if __name__ == "__main__":
    main()
