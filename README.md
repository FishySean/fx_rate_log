# 人民币/美元汇率比较工具

这个项目是一个用于比较中国银行和招商银行人民币/美元汇率的Web应用。

## 功能特点

- 实时抓取中国银行和招商银行的人民币/美元汇率数据
- 将汇率数据存储在SQLite数据库中
- 通过Web界面展示汇率数据的折线图
- 支持多种汇率类型的比较（如现汇买入价、现钞卖出价等）

## 技术栈

- 后端：Python, Flask
- 数据库：SQLite
- 前端：HTML, JavaScript, Chart.js
- 数据抓取：requests, bocfx库

## 安装和运行

1. 克隆仓库：
   ```
   git clone [仓库URL]
   ```

2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

3. 运行应用：
   ```
   python main.py
   ```

4. 在浏览器中访问 `http://127.0.0.1:8881` 查看应用

## 项目结构

- `main.py`: 主应用文件，包含Flask应用和数据抓取逻辑
- `templates/index.html`: 前端页面模板
- `exchange_rates.db`: SQLite数据库文件
- `exchange_rates.log`: 日志文件

## 注意事项

- 确保您的网络环境能够访问中国银行和招商银行的官方网站
- 本应用每分钟更新一次汇率数据
- 请遵守相关网站的使用条款和政策

## 贡献

欢迎提交问题和拉取请求。对于重大更改，请先开issue讨论您想要改变的内容。
