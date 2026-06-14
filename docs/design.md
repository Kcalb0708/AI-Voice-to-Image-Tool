# 语音绘图设计文档

## 项目定位

语音绘图是一个面向中文语音交互的 SVG 绘图应用。用户通过语音表达绘图意图，系统将音频转换为文本，再将文本理解为结构化绘图命令，最终在浏览器画布中渲染为安全的 SVG 元素。

录音触发采用显式控制方式：点击麦克风按钮或按空格键开始录音，再次点击或按空格键结束录音。这样可以符合浏览器麦克风权限要求，也能让用户明确知道当前是否正在采集音频。

## 设计目标

- 用自然语言完成主要绘图操作，减少手动编辑 SVG 的成本。
- 保持所有前端界面、状态、错误和辅助提示为简体中文。
- 将 ASR 和 LLM 密钥限制在后端，不暴露给浏览器。
- 将 LLM 输出视为不可信输入，经过结构化校验和 SVG 安全过滤后再渲染。
- 使用稳定、清晰的跨层命令协议连接后端解释结果和前端画布状态。
- 提供简单可靠的本地启动方式，便于开发、演示和调试。

## 系统架构

```text
浏览器 Vue 应用
  MediaRecorder 采集音频
    -> FastAPI /api/asr
      -> 云端 ASR 服务
    <- 识别文本

  识别文本 + 当前画布元素摘要
    -> FastAPI /api/interpret
      -> LangChain init_chat_model
      -> 云端 LLM 服务
    <- 结构化绘图命令

  Pinia 画布状态
    -> 命令执行与二次过滤
    -> SVG 渲染
    -> SVG 导出
```

前端负责录音、交互状态、SVG 画布状态和导出。后端负责第三方服务代理、提示词约束、结构化输出、Pydantic 校验和服务端安全过滤。

## 技术选型

### 前端

- Vue 3：构建单页绘图界面。
- Vite：本地开发服务器和生产构建。
- TypeScript：约束命令、元素和接口类型。
- Pinia：保存画布元素列表、系统回复和导出内容。
- MediaRecorder：使用浏览器原生能力采集音频。
- DOMPurify：对渲染和导出的 SVG 内容做前端安全过滤。
- lucide-vue：提供清晰的一致性图标。
- Vitest：覆盖画布状态和 SVG 安全工具。

### 后端

- FastAPI：提供本地 API 网关。
- Pydantic：定义请求、响应和绘图命令模型。
- pydantic-settings / python-dotenv：读取 `.env` 配置。
- LangChain `init_chat_model`：接入 OpenAI 兼容的对话模型并请求结构化输出。
- httpx：调用 OpenAI 兼容的语音转文字接口。
- pytest：覆盖配置、路由和 SVG 过滤逻辑。

## 配置模型

配置集中放在根目录 `.env`：

```dotenv
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

ASR_API_URL=https://api.openai.com/v1
ASR_API_KEY=replace-me
ASR_MODEL=gpt-4o-mini-transcribe
ASR_LANGUAGE=zh
ASR_RESPONSE_FORMAT=json
ASR_TIMEOUT_SECONDS=45

LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=replace-me
LLM_MODEL=gpt-4.1-mini
LLM_TIMEOUT_SECONDS=45
LLM_STRUCTURED_OUTPUT_METHOD=json_schema
```

关键约定：

- `.env` 不提交到 GitHub，只提交 `.env.example`。
- `ASR_API_URL` 可以配置为基础地址，也可以配置为完整的 `/audio/transcriptions` 地址。
- `ASR_MODEL` 默认使用 `gpt-4o-mini-transcribe`。
- `ASR_LANGUAGE` 默认指定中文 `zh`。
- `ASR_RESPONSE_FORMAT` 默认使用 `json`。
- `LLM_BASE_URL` 使用 OpenAI 兼容基础地址，供 LangChain `init_chat_model` 使用。
- `LLM_API_URL` 仅作为旧配置兼容入口；如果以 `/chat/completions` 结尾，后端会规整为基础地址。
- 所有对用户可见的后端错误详情、LLM 回复和警告都使用简体中文。

## API 设计

### 健康检查

```http
GET /api/health
```

响应：

```json
{
  "status": "ok"
}
```

### 语音识别

```http
POST /api/asr
Content-Type: multipart/form-data
```

请求字段：

- `audio`：浏览器录制的音频文件。

响应：

```json
{
  "text": "在画布中央画一个红色圆形"
}
```

约束：

- `audio` 必须存在且非空。
- ASR 配置缺失返回 `503`。
- ASR 服务调用失败或响应不可读返回 `502`。
- 错误详情使用简体中文。

### 指令理解

```http
POST /api/interpret
Content-Type: application/json
```

请求：

```json
{
  "text": "在画布中央画一个红色圆形",
  "elements": [
    {
      "id": "el_1",
      "tag": "rect",
      "attrs": {
        "x": 120,
        "y": 120,
        "width": 160,
        "height": 80,
        "fill": "blue"
      },
      "text": null
    }
  ]
}
```

响应：

```json
{
  "commands": [
    {
      "action": "add",
      "id": "el_2",
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

约束：

- `text` 必填，最大长度为 2000 字符。
- `elements` 最多包含 200 个当前元素。
- LLM 配置缺失返回 `503`。
- LLM 调用失败、结构化输出不可读或 schema 校验失败返回 `502`。
- 单条非法命令会被跳过并写入 `warnings`，不会影响其他合法命令执行。

## 绘图命令协议

核心模型：

```python
class DrawingElement(BaseModel):
    id: str
    tag: str
    attrs: dict[str, Any]
    text: str | None = None


class DrawingCommand(BaseModel):
    action: Literal["add", "modify", "delete", "clear", "export"]
    id: str | None = None
    tag: str | None = None
    attrs: dict[str, Any] = {}
    text: str | None = None
```

支持动作：

- `add`：新增一个 SVG 元素。
- `modify`：修改现有元素的安全属性或文本。
- `delete`：删除现有元素。
- `clear`：清空画布。
- `export`：请求前端导出 SVG 文件。

支持标签：

- `circle`
- `rect`
- `ellipse`
- `line`
- `polyline`
- `polygon`
- `path`
- `text`

命令执行约定：

- `add` 必须包含安全的 `id`、受支持的 `tag` 和经过过滤的 `attrs`。
- `modify` 和 `delete` 必须定位到已有元素；找不到目标时返回中文警告。
- 重复 `add` 同一 `id` 时，前端用新元素替换旧元素，保证 id 稳定。
- `export` 不直接包含文件内容，只通知前端基于当前画布状态生成 SVG 文件。

## 前端状态模型

Pinia 画布 store 是浏览器侧的绘图状态源：

```typescript
interface CanvasElement {
  id: string
  tag: SvgTag
  attrs: Record<string, string | number>
  text?: string | null
}
```

状态流：

1. 用户录音结束后，前端把音频发送到 `/api/asr`。
2. 前端将识别文本和 `elementSummary` 发送到 `/api/interpret`。
3. 后端返回结构化绘图命令。
4. 前端执行命令并更新 Pinia store。
5. SVG 画布根据 store 中的元素列表重新渲染。
6. 如果命令包含 `export`，前端生成并下载当前 SVG 文档。

## 安全模型

安全边界分为后端校验和前端过滤两层。

后端：

- 使用 Pydantic 校验 LLM 结构化输出。
- 限制 `action`、`tag` 和属性集合。
- 拒绝未知标签、未知动作和明显不安全的属性值。
- 对无法执行的单条命令返回中文警告。

前端：

- 执行命令前再次检查 id、标签和属性。
- 渲染前使用 DOMPurify 清洗 SVG 字符串。
- 导出 SVG 前复用同一套安全转换逻辑。
- 文本节点做转义处理，避免把用户输入当作标记解析。

禁止内容：

- `script`
- `foreignObject`
- `iframe`
- `audio`
- `video`
- `image`
- `a`
- `use`
- `style`
- 事件属性，例如 `onclick`、`onload`
- `href`、`xlink:href`、`src`
- `javascript:`、`data:`、`url(...)`

## 本地启动设计

Windows 入口为根目录的 `start-dev.bat`，实际逻辑在 `scripts/start-dev.ps1`。

脚本职责：

- 检查后端目录和前端目录是否存在。
- 检查 `.env` 是否存在。
- 检查 `uv` 和 `npm` 是否可用。
- 检查 `8000` 和 `5173` 端口是否已被占用。
- 未占用时分别打开后端和前端命令行窗口。
- 自动打开 `http://127.0.0.1:5173/`。

预检查命令：

```powershell
.\start-dev.bat -Check
```

## GitHub 提交约定

应提交：

- `README.md`
- `docs/design.md`
- `.env.example`
- `.gitignore`
- `start-dev.bat`
- `scripts/start-dev.ps1`
- `backend/` 源码、测试、`pyproject.toml` 和 `uv.lock`
- `frontend/` 源码、配置、`package.json` 和 `package-lock.json`

不应提交：

- `.env`
- `node_modules/`
- `dist/`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `.ruff_cache/`
- 日志文件
- Trellis 本地运行状态、任务草稿和工作区截图

## 质量验证

后端：

```powershell
cd backend
uv run pytest
```

前端：

```powershell
cd frontend
npm test
npm run build
```

启动脚本：

```powershell
.\start-dev.bat -Check
```

验证重点：

- API 合同是否稳定。
- 缺失配置和第三方调用失败时是否返回中文错误。
- LLM 输出是否经过结构化校验。
- SVG 渲染和导出是否拒绝危险标签与属性。
- 前端状态、识别文本、系统回复和警告是否符合中文界面要求。
