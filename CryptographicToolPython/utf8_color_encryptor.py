#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UTF-8字符加解密工具
功能：将文本文件中的每个UTF-8字符转换为随机RGB颜色，并生成对应图片
注意：支持所有UTF-8字符，包括emoji、中文、特殊符号等
"""

import os
import sys
import random
import base64
import argparse
from io import BytesIO
from PIL import Image
import json
import hashlib
import time

def set_random_seed(text):
    """根据文本内容设置随机种子，确保相同文本每次生成相同的颜色映射"""
    text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    seed = int(text_hash[:8], 16)
    random.seed(seed)

def encrypt_file(input_file, output_txt=None, output_image=None):
    """
    加密文件：将文本转换为RGB颜色并生成图片
    
    Args:
        input_file: 输入文本文件路径
        output_txt: 输出txt文件路径（默认：input_file.encrypted.txt）
        output_image: 输出图片文件路径（默认：input_file.color_map.png）
    """
    try:
        # 读取输入文件
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text:
            print("错误：输入文件为空！")
            return False
        
        print(f"读取文件成功，字符数：{len(text)}")
        
        # 设置随机种子（确保相同文本生成相同颜色）
        set_random_seed(text)
        
        # 创建字符到颜色的映射
        char_to_color = {}
        color_sequence = []
        
        for char in text:
            if char not in char_to_color:
                # 为每个字符生成唯一的随机RGB颜色
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)
                char_to_color[char] = (r, g, b)
            
            color_sequence.append(char_to_color[char])
        
        print(f"生成颜色映射成功，唯一字符数：{len(char_to_color)}")
        
        # 生成图片（高度1像素，宽度等于字符数）
        width = len(color_sequence)
        height = 1
        
        image = Image.new('RGB', (width, height))
        pixels = image.load()
        
        for i, (r, g, b) in enumerate(color_sequence):
            pixels[i, 0] = (r, g, b)
        
        # 保存图片
        if not output_image:
            base_name = os.path.splitext(input_file)[0]
            output_image = f"{base_name}.color_map.png"
        
        image.save(output_image, 'PNG')
        print(f"图片已保存：{output_image}")
        print(f"图片尺寸：{width} x {height} 像素")
        
        # 将图片转换为base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # 保存对应关系到txt文件
        if not output_txt:
            base_name = os.path.splitext(input_file)[0]
            output_txt = f"{base_name}.encrypted.txt"
        
        with open(output_txt, 'w', encoding='utf-8') as f:
            # 写入字符到颜色的映射
            f.write("=== 字符到颜色映射表 ===\n")
            for char, (r, g, b) in char_to_color.items():
                # 对特殊字符进行转义
                if char == '\n':
                    char_repr = r"\\n"
                elif char == '\t':
                    char_repr = r"\\t"
                elif char == '\r':
                    char_repr = r"\\r"
                else:
                    char_repr = char
                
                f.write(f"字符: '{char_repr}' -> RGB: ({r}, {g}, {b})\n")
            
            f.write("\n=== 颜色序列（按字符顺序） ===\n")
            f.write(f"字符数: {len(color_sequence)}\n")
            f.write("RGB序列:\n")
            
            # 每10个颜色换行一次
            for i in range(0, len(color_sequence), 10):
                batch = color_sequence[i:i+10]
                rgb_str = ' '.join([f"({r},{g},{b})" for r, g, b in batch])
                f.write(rgb_str + '\n')
            
            # 空8行
            for _ in range(8):
                f.write('\n')
            
            # 写入图片的base64
            f.write("=== 图片Base64编码 ===\n")
            f.write(img_base64)
        
        print(f"加密完成！输出文件：{output_txt}")
        print(f"图片文件：{output_image}")
        
        # 显示一些统计信息
        print(f"\n统计信息：")
        print(f"  - 总字符数: {len(text)}")
        print(f"  - 唯一字符数: {len(char_to_color)}")
        print(f"  - 图片尺寸: {width}x{height}")
        
        return True
        
    except Exception as e:
        print(f"加密过程中发生错误: {e}")
        return False

def decrypt_file(input_file, output_txt=None, output_image=None):
    """
    解密文件：从加密的txt文件中恢复原始文本
    
    Args:
        input_file: 加密的txt文件路径
        output_txt: 解密后的文本文件路径（默认：input_file.decrypted.txt）
        output_image: 恢复的图片文件路径（可选）
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分割文件内容
        lines = content.split('\n')
        
        # 查找连续8个空行的位置
        empty_line_count = 0
        split_index = -1
        
        for i, line in enumerate(lines):
            if not line.strip():
                empty_line_count += 1
                if empty_line_count >= 8:
                    split_index = i
                    break
            else:
                empty_line_count = 0
        
        if split_index == -1:
            print("错误：找不到连续8个空行分隔符！")
            return False
        
        # 提取映射部分和base64部分
        mapping_lines = lines[:split_index-7]  # 去掉连续空行
        base64_lines = lines[split_index+1:]  # 从第一个非空行开始
        
        # 解析字符到颜色的映射
        char_to_color = {}
        color_to_char = {}
        
        for line in mapping_lines:
            if "' -> RGB: (" in line and "字符: '" in line:
                try:
                    # 解析字符和颜色
                    char_part = line.split("字符: '")[1].split("' -> RGB: (")[0]
                    rgb_part = line.split("' -> RGB: (")[1].rstrip(')')
                    
                    # 处理转义字符
                    if char_part == r"\\n":
                        char = '\n'
                    elif char_part == r"\\t":
                        char = '\t'
                    elif char_part == r"\\r":
                        char = '\r'
                    else:
                        char = char_part
                    
                    r, g, b = map(int, rgb_part.split(', '))
                    char_to_color[char] = (r, g, b)
                    color_to_char[(r, g, b)] = char
                    
                except Exception as e:
                    continue
        
        # 查找RGB序列
        rgb_sequence = []
        for line in mapping_lines:
            if line.startswith("RGB序列:") or not line.strip():
                continue
            if "===" in line:
                continue
            
            # 尝试解析RGB序列
            parts = line.strip().split(' ')
            for part in parts:
                if part.startswith('(') and part.endswith(')'):
                    try:
                        rgb_str = part[1:-1]
                        r, g, b = map(int, rgb_str.split(','))
                        rgb_sequence.append((r, g, b))
                    except:
                        pass
        
        # 如果没有找到RGB序列，尝试从base64图片中提取
        if not rgb_sequence:
            print("警告：未找到RGB序列，尝试从base64图片中提取...")
            
            # 解析base64
            base64_content = ''.join(base64_lines[1:])  # 跳过"=== 图片Base64编码 ==="行
            try:
                # 解码base64
                img_data = base64.b64decode(base64_content)
                buffered = BytesIO(img_data)
                image = Image.open(buffered)
                
                # 提取颜色序列
                pixels = image.load()
                width, height = image.size
                
                for x in range(width):
                    r, g, b = pixels[x, 0]
                    rgb_sequence.append((r, g, b))
                
                print(f"从图片中提取了 {len(rgb_sequence)} 个颜色")
                
                # 保存恢复的图片
                if output_image:
                    image.save(output_image, 'PNG')
                    print(f"恢复的图片已保存：{output_image}")
                    
            except Exception as e:
                print(f"从base64提取图片失败: {e}")
                return False
        
        # 从颜色序列恢复文本
        recovered_text = []
        for rgb in rgb_sequence:
            if rgb in color_to_char:
                recovered_text.append(color_to_char[rgb])
            else:
                # 如果没有找到映射，尝试查找最接近的颜色
                found_char = None
                min_distance = float('inf')
                
                for (r2, g2, b2), char in color_to_char.items():
                    distance = abs(r2 - rgb[0]) + abs(g2 - rgb[1]) + abs(b2 - rgb[2])
                    if distance < min_distance:
                        min_distance = distance
                        found_char = char
                
                if found_char:
                    recovered_text.append(found_char)
                else:
                    recovered_text.append('?')
        
        recovered_text = ''.join(recovered_text)
        
        # 保存解密结果
        if not output_txt:
            base_name = os.path.splitext(input_file)[0]
            output_txt = f"{base_name}.decrypted.txt"
        
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write(recovered_text)
        
        print(f"解密完成！输出文件：{output_txt}")
        print(f"恢复字符数：{len(recovered_text)}")
        
        # 显示恢复的文本前100个字符
        preview = recovered_text[:100]
        if len(recovered_text) > 100:
            preview += "..."
        print(f"预览：{preview}")
        
        return True
        
    except Exception as e:
        print(f"解密过程中发生错误: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='UTF-8字符加解密工具 - 将文本转换为RGB颜色映射',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 加密文件
  python utf8_color_encryptor.py encrypt input.txt
  
  # 加密文件并指定输出文件名
  python utf8_color_encryptor.py encrypt input.txt --output-txt encoded.txt --output-image colors.png
  
  # 解密文件
  python utf8_color_encryptor.py decrypt encoded.txt
  
  # 解密文件并指定输出
  python utf8_color_encryptor.py decrypt encoded.txt --output-txt decoded.txt
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 加密命令
    encrypt_parser = subparsers.add_parser('encrypt', help='加密文件')
    encrypt_parser.add_argument('input_file', help='输入文本文件')
    encrypt_parser.add_argument('--output-txt', help='输出txt文件（加密结果）')
    encrypt_parser.add_argument('--output-image', help='输出图片文件（颜色映射）')
    
    # 解密命令
    decrypt_parser = subparsers.add_parser('decrypt', help='解密文件')
    decrypt_parser.add_argument('input_file', help='加密的txt文件')
    decrypt_parser.add_argument('--output-txt', help='输出txt文件（解密结果）')
    decrypt_parser.add_argument('--output-image', help='输出图片文件（恢复的图片）')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'encrypt':
        if not os.path.exists(args.input_file):
            print(f"错误：文件不存在 - {args.input_file}")
            return
        
        success = encrypt_file(
            args.input_file,
            args.output_txt,
            args.output_image
        )
        
        if success:
            print("\n✓ 加密成功！")
        else:
            print("\n✗ 加密失败！")
            sys.exit(1)
    
    elif args.command == 'decrypt':
        if not os.path.exists(args.input_file):
            print(f"错误：文件不存在 - {args.input_file}")
            return
        
        success = decrypt_file(
            args.input_file,
            args.output_txt,
            args.output_image
        )
        
        if success:
            print("\n✓ 解密成功！")
        else:
            print("\n✗ 解密失败！")
            sys.exit(1)

if __name__ == "__main__":
    main()
