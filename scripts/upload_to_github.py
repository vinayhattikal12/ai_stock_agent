import subprocess
import os
import sys

def run_cmd(cmd):
    print(f"Executing: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=r"c:\Users\Dell\ai_stock")
    print("STDOUT:", res.stdout.strip())
    if res.stderr:
        print("STDERR:", res.stderr.strip())
    return res.returncode

def main():
    print("--- Uploading Repository to GitHub ---")
    run_cmd("git init")
    run_cmd("git config user.name")
    run_cmd("git config user.email")
    run_cmd("git add .")
    run_cmd('git commit -m "feat: complete AI equity swing decision-support platform with institutional risk engine"')
    run_cmd("git branch -M main")
    run_cmd("git remote remove origin")
    run_cmd("git remote add origin https://github.com/vinayhattikal12/ai_stock_agent.git")
    code = run_cmd("git push -u origin main --force")
    if code == 0:
        print("\n✅ Successfully pushed project to https://github.com/vinayhattikal12/ai_stock_agent")
    else:
        print("\n⚠️ Push encountered an issue (authentication or network).")

if __name__ == "__main__":
    main()
