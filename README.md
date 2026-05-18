# 📐 高中数学错题巩固神器

一个智能的高中数学错题分析和练习工具！

## ✨ 功能特性

- 📷 **拍照识别题目**：支持上传错题图片，自动识别文字
- 🎯 **知识点分析**：智能提取题目涉及的知识点
- 💡 **解题思路**：提供详细的解题思路和答案
- 🔄 **举一反三**：自动生成类似题目，包含高考真题
- 📱 **手机访问**：支持手机拍照上传，在同一WiFi下即可访问

## 🛠️ 技术栈

- **后端**：Python 3
- **OCR**：Tesseract OCR
- **前端**：HTML + JavaScript
- **数学公式**：MathJax

## 📦 安装步骤

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. 安装依赖

```bash
pip install pytesseract pillow
```

### 3. 安装 Tesseract OCR（可选但推荐）

下载地址：https://github.com/UB-Mannheim/tesseract/wiki

安装时勾选 **中文语言包（chi_sim）**

### 4. 运行程序

```bash
python app.py
```

访问：http://localhost:5000

## 📱 手机访问

手机和电脑连接同一WiFi后，访问显示的地址，如：
```
http://192.168.1.100:5000
```

## 📂 项目结构

```
.
├── app.py                  # 主程序
├── math_analyzer.py        # 数学分析引擎
├── ocr_processor.py        # OCR识别模块
├── question_generator.py   # 题目生成器
├── templates/
│   └── index.html         # 前端页面
└── uploads/               # 上传文件（自动创建）
```

## 🎯 使用说明

1. **上传图片**：点击或拖拽上传错题图片
2. **输入文本**：也可以直接输入题目内容
3. **查看分析**：自动分析知识点、解题思路
4. **巩固练习**：查看类似题目，举一反三

## 📝 注意事项

- Tesseract OCR安装后，程序会自动检测
- 支持 LaTeX 公式，如 $x^2$、$\frac{a}{b}$
- 上传目录会自动创建，无需手动操作

## 📄 License

MIT License
