[py脚本文件获取](./utf8_color_encryptor.py)


依赖为pillow12.2.0

    
```

pip install pillow==12.2.0 -i https://pypi.tuna.tsinghua.edu.cn/simple

```

    
    
```

解密
# 基本用法
python utf8_color_encryptor.py decrypt encoded.txt

# 指定输出文件名
python utf8_color_encryptor.py decrypt encoded.txt --output-txt decoded.txt

    
    

    
    
加密
# 基本用法
python utf8_color_encryptor.py encrypt input.txt

# 指定输出文件名
python utf8_color_encryptor.py encrypt input.txt --output-txt encoded.txt --output-image colors.png


    
    
```