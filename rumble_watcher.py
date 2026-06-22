import time
import subprocess
import json
import os
import shutil
import glob
import sys

# Paths are relative to the script directory to keep it self-contained
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "rumble_processed_runs.json")
TEMP_BASE_DIR = os.path.join(SCRIPT_DIR, "rumble_temp")
LOG_FILE = os.path.join(SCRIPT_DIR, "rumble_watcher.log")

CREDS = {
    "yt-auto": {
        "email": "gurination24@gmail.com",
        "password": "DM id wale1",
        "channel_id": ""
    },
    "yt-auto-ch2": {
        "email": "gurination14@gmail.com",
        "password": "DM id wale1",
        "channel_id": ""
    },
    "yt-auto-ch3": {
        "email": "ehwtheh@gmail.com",
        "password": "DM id wale1",
        "channel_id": ""
    },
    "yt-auto-ch4": {
        "email": "ytgouner5911@gmail.com",
        "password": "DM id wale1",
        "channel_id": ""
    }
}

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    sys.stdout.flush()
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception as e:
        print(f"Failed to write to log file: {e}")

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"Error loading DB: {e}. Returning empty.")
        return {}

def save_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2)
    except Exception as e:
        log(f"Error saving DB: {e}")

def find_file(directory, pattern):
    search_path = os.path.join(directory, "**", pattern)
    files = glob.glob(search_path, recursive=True)
    return files[0] if files else None

def process_run(repo, run_id, info):
    temp_dir = os.path.join(TEMP_BASE_DIR, str(run_id))
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)

    log(f"Downloading artifacts for run {run_id} in {repo}...")
    cmd_download = f"gh run download {run_id} --dir {temp_dir} -R gurination1/{repo}"
    res = subprocess.run(cmd_download, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        log(f"Failed to download artifacts for run {run_id}. Stderr: {res.stderr.strip()}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return False

    metadata_path = find_file(temp_dir, "metadata.json")
    video_path = find_file(temp_dir, "*.mp4")

    if not metadata_path or not video_path:
        log(f"Metadata or video missing in downloaded artifacts for run {run_id}. Path check: metadata={metadata_path}, video={video_path}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return True  # Mark as processed (corrupt run, no point retrying)

    log(f"Found video: {video_path} and metadata: {metadata_path}")
    
    # Run the Rumble upload script as a subprocess to keep environment clean
    python_cmd = (
        f"import os, sys, json; "
        f"os.environ['RUMBLE_EMAIL'] = {repr(info['email'])}; "
        f"os.environ['RUMBLE_PASSWORD'] = {repr(info['password'])}; "
        f"os.environ['RUMBLE_CHANNEL_ID'] = {repr(info['channel_id'])}; "
        f"sys.path.append('/root/{repo}'); "
        f"from pipeline.phase11_rumble import upload_to_rumble; "
        f"metadata = json.load(open({repr(metadata_path)})); "
        f"metadata['video_path'] = {repr(video_path)}; "
        f"url = upload_to_rumble({repr(video_path)}, metadata); "
        f"print('UPLOAD_SUCCESS_URL:' + str(url))"
    )

    log(f"Triggering Rumble upload subprocess for run {run_id}...")
    res_upload = subprocess.run(
        [sys.executable, "-c", python_cmd],
        capture_output=True,
        text=True
    )

    log(f"Subprocess stdout:\n{res_upload.stdout}")
    if res_upload.stderr:
        log(f"Subprocess stderr:\n{res_upload.stderr}")

    shutil.rmtree(temp_dir, ignore_errors=True)

    if "UPLOAD_SUCCESS_URL:" in res_upload.stdout:
        success_line = [line for line in res_upload.stdout.split("\n") if "UPLOAD_SUCCESS_URL:" in line][0]
        url = success_line.replace("UPLOAD_SUCCESS_URL:", "").strip()
        log(f"Successfully uploaded run {run_id} to Rumble! URL: {url}")
        return True
    else:
        log(f"Rumble upload subprocess failed for run {run_id}.")
        return False

def check_new_runs():
    for repo, info in CREDS.items():
        log(f"Checking runs for {repo}...")
        cmd = f"gh run list -R gurination1/{repo} -L 10 --json databaseId,status,conclusion,name,createdAt"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            log(f"Failed to fetch runs for {repo}. Stderr: {res.stderr.strip()}")
            continue

        try:
            runs = json.loads(res.stdout)
        except Exception as e:
            log(f"Failed to parse runs JSON for {repo}: {e}")
            continue

        for run in runs:
            # Load DB fresh inside the loop so we don't overwrite concurrent changes
            db = load_db()
            run_id = str(run["databaseId"])
            status = run["status"]
            conclusion = run["conclusion"]
            
            # We only process completed success runs
            if status == "completed" and conclusion == "success":
                if run_id not in db:
                    success = process_run(repo, run_id, info)
                    if success:
                        db[run_id] = {
                            "repo": repo,
                            "name": run["name"],
                            "createdAt": run["createdAt"],
                            "status": "uploaded"
                        }
                    else:
                        db[run_id] = {
                            "repo": repo,
                            "name": run["name"],
                            "createdAt": run["createdAt"],
                            "status": "failed_retry"
                        }
                    save_db(db)
                elif db[run_id].get("status") == "failed_retry":
                    # Retry once
                    log(f"Retrying failed run {run_id} for {repo}...")
                    success = process_run(repo, run_id, info)
                    if success:
                        db[run_id]["status"] = "uploaded"
                    else:
                        db[run_id]["status"] = "failed_permanently"
                    save_db(db)

def main():
    log("Rumble Watcher daemon started.")
    while True:
        try:
            check_new_runs()
        except Exception as e:
            log(f"Exception in check_new_runs loop: {e}")
        time.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    main()
