import shutil, os
src = r"I:\阿飞说球\文章\20260731\韩K联三场前瞻_头条版.md"
dst = r"I:\阿飞说球\📝文章\20260731\韩K联三场前瞻_头条版.md"
os.makedirs(os.path.dirname(dst), exist_ok=True)
shutil.copy2(src, dst)
print("Copied to:", dst)
print("Size:", os.path.getsize(dst))
