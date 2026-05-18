#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

class OCRProcessor:
    def __init__(self):
        self.tesseract_available = self._check_tesseract()
    
    def _check_tesseract(self):
        """检查Tesseract OCR是否可用"""
        try:
            import pytesseract
            
            # 尝试设置Tesseract路径（Windows常见安装位置）
            tesseract_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
            
            # 尝试执行tesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            print(f"OCR不可用: {e}")
            return False
    
    def extract_text(self, image_path):
        """从图片中提取文字"""
        if not self.tesseract_available:
            return "__OCR_NOT_AVAILABLE__"
        
        try:
            import pytesseract
            from PIL import Image, ImageFilter, ImageEnhance
            
            # 打开图片并预处理
            img = Image.open(image_path)
            
            # 转换为灰度图提高识别率
            img = img.convert('L')
            
            # 提高对比度
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            
            # 锐化图片
            img = img.filter(ImageFilter.SHARPEN)
            
            # 使用中文+英文识别
            custom_config = r'--oem 3 --psm 6 -l chi_sim+eng'
            text = pytesseract.image_to_string(img, config=custom_config)
            
            # 清理文本
            text = self._clean_text(text)
            
            return text
            
        except Exception as e:
            print(f"OCR识别失败: {e}")
            return f"识别失败: {str(e)}"
    
    def _clean_text(self, text):
        """清理识别结果"""
        lines = text.strip().split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 1:  # 过滤掉太短的行（可能是噪点）
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines)
        
        # 如果清理后为空，返回原始文本
        if not result:
            return text.strip()
        
        return result
    
    def is_available(self):
        """检查OCR是否可用"""
        return self.tesseract_available


if __name__ == '__main__':
    ocr = OCRProcessor()
    print(f"OCR可用: {ocr.is_available()}")
