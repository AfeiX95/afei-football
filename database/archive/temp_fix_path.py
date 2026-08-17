import os, shutil

src_dir = r"I:\阿fei说球\assets\charts\20260731"
dst_dir = r"I:\阿飞说球\assets\charts\20260731"
os.makedirs(dst_dir, exist_ok=True)

for f in os.listdir(src_dir):
    src = os.path.join(src_dir, f)
    dst = os.path.join(dst_dir, f)
    shutil.copy2(src, dst)
    print(f"Copied: {f} ({os.path.getsize(dst)} bytes)")

# Remove old dir
shutil.rmtree(r"I:\阿fei说球", ignore_errors=True)
print("Done - all charts in correct path")
