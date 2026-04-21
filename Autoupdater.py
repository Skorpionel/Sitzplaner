import os, sys, time, subprocess

def main():
    if len(sys.argv) < 3:
        return
    
    alt_exe = sys.argv[1]
    neue_exe = sys.argv[2]

    base_dir = os.path.dirname(sys.executable)
    alt_path = os.path.join(base_dir, alt_exe)

    time.sleep(2)

    for i in range(10):
        try:
            if os.path.exists(alt_path):
                os.remove(alt_path)
            break
        except PermissionError:
            time.sleep(1)
    else:
        return
    
    try:
        subprocess.Popen([neue_exe])
    except Exception as e:
        pass


if __name__ == "__main__":
    main()
