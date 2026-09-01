#!/usr/bin/env python3
"""生成应用图标的各种尺寸"""
from PIL import Image
import os

# 源图片路径
source = "D:/Documents/Pictures/宝宝.png"
output_dir = "static/img"

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)

# 加载源图片
img = Image.open(source)

# 生成各种尺寸
sizes = {
    "icon-16.png": (16, 16),
    "icon-32.png": (32, 32),
    "icon-180.png": (180, 180),  # Apple Touch Icon
    "icon-192.png": (192, 192),  # PWA
    "icon-512.png": (512, 512),  # PWA
}

for filename, size in sizes.items():
    resized = img.resize(size, Image.Resampling.LANCZOS)
    resized.save(os.path.join(output_dir, filename), "PNG")
    print(f"Generated {filename} ({size[0]}x{size[1]})")

# 生成 favicon.ico (包含多个尺寸)
favicon_sizes = [(16, 16), (32, 32)]
favicon_images = [img.resize(size, Image.Resampling.LANCZOS) for size in favicon_sizes]
favicon_images[0].save(
    os.path.join(output_dir, "favicon.ico"),
    format="ICO",
    sizes=favicon_sizes
)
print(f"Generated favicon.ico (16x16, 32x32)")

print(f"\nAll icons generated to {output_dir}/")
