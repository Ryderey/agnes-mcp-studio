/**
 * 使用 ai-figure 生成 Agnes Media MCP 工作流程图 (SVG)
 * 运行: node docs/gen-workflow.mjs
 */
import { fig } from 'ai-figure';
import { writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const svg = fig(`
figure swimlane
title: Agnes Media MCP 工作流程
subtitle: Skill（决策层）+ MCP Server（执行层）+ Agnes API（推理层）

section 用户
  req((发送请求: 包含 agnes 关键词))
  result((获得媒体文件))

section Skill 决策层
  gate{关键字门控: 包含 agnes?}
  reject((不激活, 交给其他工具))
  intent[意图匹配: 图像/编辑/视频]
  tools[选择工具: image_generate / v2 / edit / video]
  prompt[构造 Prompt: 主体+场景+风格+光线+构图]
  present[展示结果: Markdown 图片/路径/URL]

section MCP Server
  process[协议适配: payload构建 / Base64 / 8n+1对齐]
  save[保存文件: outputs/images/ | outputs/videos/]

section Agnes API
  call[/POST api.agnes-ai.cn/v1/]
  media{媒体类型?}
  img_sync[图像: 同步返回 b64_json/url]
  vid_async[视频: 异步轮询 video_id]

req --> gate
gate --> reject: 否
gate --> intent: 是
intent --> tools
tools --> prompt
prompt --> process: MCP 调用
process --> call: HTTPS
call --> media
media --> img_sync: 图像
media --> vid_async: 视频
img_sync --> save
vid_async --> save
save --> present
present --> result
`);

const outPath = join(__dirname, 'workflow.svg');
writeFileSync(outPath, svg, 'utf-8');
console.log(`✅ 流程图已生成: ${outPath}`);
