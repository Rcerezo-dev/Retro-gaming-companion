import os
import shutil
import zipfile

def main():
    downloads_dir = r"C:\Users\rammu\Downloads"
    target_e = r"E:\Carpetas anbernic\psx"
    target_h = r"H:\psx"

    os.makedirs(target_e, exist_ok=True)
    os.makedirs(target_h, exist_ok=True)

    print(f"Scanning {downloads_dir} for PSX games...")

    for f in os.listdir(downloads_dir):
        # Most of these retro games have regions in the filename
        if "(USA)" in f or "(Europe)" in f or "(Spain)" in f or "Final Fantasy" in f:
            path = os.path.join(downloads_dir, f)
            
            if f.lower().endswith(".zip"):
                print(f"Extracting {f} to {target_e}...")
                try:
                    extracted_files = []
                    with zipfile.ZipFile(path, 'r') as zip_ref:
                        extracted_files = zip_ref.namelist()
                        zip_ref.extractall(target_e)
                    
                    # Log to console just the first file to avoid spam
                    if extracted_files:
                        print(f" -> Found {len(extracted_files)} files. Copying to H:...")
                        
                    for ex_f in extracted_files:
                        src = os.path.join(target_e, ex_f)
                        if os.path.isfile(src):
                            dst = os.path.join(target_h, ex_f)
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                            shutil.copy2(src, dst)
                except Exception as e:
                    print(f"Failed to process {f}: {e}")
                    
            elif f.lower().endswith(('.chd', '.bin', '.cue')):
                print(f"Copying {f} to E: and H:...")
                try:
                    shutil.copy2(path, os.path.join(target_e, f))
                    shutil.copy2(path, os.path.join(target_h, f))
                except Exception as e:
                    print(f"Failed to copy {f}: {e}")
                    
            elif f.lower().endswith(".7z"):
                print(f"Skipping {f}: .7z extraction requires an external app like 7-Zip.")

    print("\nExtraction and copying process completed!")

if __name__ == "__main__":
    main()
