# 语音绘图

语音绘图是一个通过自然语言语音指令创建和编辑 SVG 图形的 Web 应用。浏览器负责录音、画布交互和 SVG 渲染，后端负责语音识别代理、绘图指令理解、结构化校验和安全过滤。

用户点击麦克风按钮或按空格键开始录音，再次点击或按空格键结束录音。录音内容会被识别为文本，并由大语言模型转换成可执行的绘图命令，前端将命令应用到 SVG 画布中。

## 功能特性

- 语音创建圆形、矩形、椭圆、线段、多边形、路径和文本
- 语音修改图形的位置、尺寸、颜色、描边和文本内容
- 语音删除图形、清空画布和导出 SVG
- 支持一句话生成多条有序绘图命令
- 前端所有可见提示、状态、错误和辅助标签均为简体中文
- 后端统一保护 ASR 和 LLM 密钥，前端只访问本地 `/api/*` 接口
- 后端和前端双层 SVG 安全校验，阻止脚本、事件属性和外部引用进入画布
- Windows 一键启动脚本，可同时启动 FastAPI 后端和 Vite 前端

## 技术栈

后端：

- Python 3.11+
- FastAPI
- Pydantic / pydantic-settings
- LangChain `init_chat_model`
- OpenAI 兼容的 ASR 与 LLM 服务接口
- httpx
- pytest

前端：

- Vue 3
- Vite
- TypeScript
- Pinia
- DOMPurify
- lucide-vue
- Vitest

## 项目结构

```text
backend/        FastAPI 后端、ASR/LLM 代理、绘图命令校验、后端测试
frontend/       Vue 3 前端、录音流程、SVG 画布、状态管理、前端测试
docs/           架构和设计文档
scripts/        本地开发辅助脚本
start-dev.bat   Windows 一键启动入口
.env.example    环境变量模板
```

## 环境配置

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

然后在 `.env` 中填写服务配置：

```dotenv
ASR_API_URL=https://api.openai.com/v1
ASR_API_KEY=replace-me
ASR_MODEL=gpt-4o-mini-transcribe
ASR_LANGUAGE=zh
ASR_RESPONSE_FORMAT=json

LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=replace-me
LLM_MODEL=gpt-4.1-mini
LLM_STRUCTURED_OUTPUT_METHOD=json_schema
```

配置说明：

- `ASR_API_URL` 可以是 OpenAI 兼容的基础地址，也可以是完整的 `/audio/transcriptions` 地址。
- `ASR_MODEL` 默认使用 `gpt-4o-mini-transcribe`，可按服务商支持情况调整。
- `ASR_LANGUAGE` 默认指定中文 `zh`。
- `ASR_RESPONSE_FORMAT` 默认使用 `json`。
- `LLM_BASE_URL` 是 LangChain `init_chat_model` 使用的 OpenAI 兼容基础地址。
- `LLM_MODEL` 使用当前服务商支持结构化输出的对话模型。
- `LLM_STRUCTURED_OUTPUT_METHOD` 默认使用 `json_schema`。
- `.env` 包含密钥，已被 `.gitignore` 排除，不要提交到 GitHub。

## 启动方式

Windows 一键启动：

```powershell
.\start-dev.bat
```

脚本会打开两个独立命令行窗口，分别启动后端和前端，然后自动打开：

```text
http://127.0.0.1:5173/
```

只检查环境，不启动服务窗口：

```powershell
.\start-dev.bat -Check
```

手动启动后端：

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

手动启动前端：

```powershell
cd frontend
npm install
npm run dev
```

Vite 会把前端的 `/api` 请求代理到 `http://127.0.0.1:8000`。

## 使用方式

1. 启动后端和前端。
2. 打开 `http://127.0.0.1:5173/`。
3. 点击麦克风按钮或按空格键开始录音。
4. 说出绘图指令。
5. 再次点击麦克风按钮或按空格键结束录音。
6. 查看画布结果，也可以通过语音或按钮导出 SVG。

示例语音指令：

- “在画布中央画一个红色圆形。”
- “添加三个蓝色正方形，横向排列。”
- “把最后一个图形改成绿色。”
- “删除红色圆形。”
- “清空画布。”
- “导出当前图形。”

## API 接口

健康检查：

```http
GET /api/health
```

返回：

```json
{ "status": "ok" }
```

语音识别：

```http
POST /api/asr
Content-Type: multipart/form-data
```

字段：

- `audio`：浏览器录制的音频文件

返回：

```json
{ "text": "在画布中央画一个红色圆形" }
```

指令理解：

```http
POST /api/interpret
Content-Type: application/json
```

请求：

```json
{
  "text": "在画布中央画一个红色圆形",
  "elements": []
}
```

返回：

```json
{
  "commands": [
    {
      "action": "add",
      "id": "el_1",
      "tag": "circle",
      "attrs": {
        "cx": 480,
        "cy": 270,
        "r": 60,
        "fill": "red"
      },
      "text": null
    }
  ],
  "reply": "已在画布中央添加红色圆形。",
  "warnings": []
}
```

## 绘图命令

支持的操作：

- `add`：新增图形
- `modify`：修改已有图形
- `delete`：删除已有图形
- `clear`：清空画布
- `export`：导出 SVG

支持的 SVG 标签：

- `circle`
- `rect`
- `ellipse`
- `line`
- `polyline`
- `polygon`
- `path`
- `text`

每个图形都有稳定的 `id`，后续语音指令可以通过自然语言引用它，例如“最后一个图形”“红色圆形”。

## 安全策略

- 第三方服务密钥只存在于后端环境变量中。
- 后端使用 Pydantic 校验 LLM 输出结构。
- 后端会过滤不支持的动作、标签和属性。
- 前端再次过滤 SVG 属性，并使用 DOMPurify 处理渲染与导出内容。
- SVG 不允许脚本、事件属性、外链、`foreignObject`、`javascript:`、`data:` 和 `url(...)` 引用。
- 单条非法绘图命令会被跳过并记录中文警告，不会导致整个画布崩溃。

## 质量检查

后端测试：

```powershell
cd backend
uv run pytest
```

前端测试：

```powershell
cd frontend
npm test
```

前端构建：

```powershell
cd frontend
npm run build
```

启动脚本预检查：

```powershell
.\start-dev.bat -Check
```
