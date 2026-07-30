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
figure flow
direction: TB
palette: antv
title: Agnes Media MCP 工作流程
subtitle: Skill（决策层）+ MCP Server（执行层）+ Agnes API（推理层）

user1((用户发送请求))
gate{包含 agnes 关键字?}
reject((不激活，交给其他工具))
intent[意图匹配: 图像 / 编辑 / 视频]
decision{决策规则: 选择工具}
tool_img[agnes_image_generate]
tool_imgv2[agnes_image_generate_v2]
tool_edit[agnes_image_edit]
tool_video[agnes_video_generate]
prompt[构造 Prompt]
mcp[MCP Server 处理]
api[/Agnes API 请求/]
type_dec{媒体类型?}
sync_img[图像同步返回 b64/url]
async_vid[视频异步轮询 video_id]
save[保存文件到 outputs/]
present[Agent 展示结果]
user2((用户获得媒体文件))

user1 --> gate
gate --> reject: 否
gate --> intent: 是
intent --> decision
decision --> tool_img: 标准图像
decision --> tool_imgv2: 高分辨率
decision --> tool_edit: 编辑/合成
decision --> tool_video: 视频
tool_img --> prompt
tool_imgv2 --> prompt
tool_edit --> prompt
tool_video --> prompt
prompt --> mcp: MCP 调用
mcp --> api: HTTPS POST
api --> type_dec
type_dec --> sync_img: 图像
type_dec --> async_vid: 视频
sync_img --> save
async_vid --> save
save --> present
present --> user2

group 用户层: user1, user2
group Skill 决策层: gate, intent, decision, prompt, present
group 工具选择: tool_img, tool_imgv2, tool_edit, tool_video
group MCP 执行层: mcp, save
group Agnes API 层: api, type_dec, sync_img, async_vid
`);

const outPath = join(__dirname, 'workflow.svg');
writeFileSync(outPath, svg, 'utf-8');
console.log(`✅ 流程图已生成: ${outPath}`);
