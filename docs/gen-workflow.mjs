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
palette: default
title: Agnes Media MCP 工作流程
subtitle: 不含 agnes 关键词时不激活

req((用户请求))
gate{含 agnes?}
stop((跳过))
skill[Skill: 决策+构造]
mcp[MCP: 适配+调用]
api[/Agnes API/]
branch{图像/视频?}
img[同步返回]
vid[异步轮询]
save[保存+展示]
done((完成))

req --> gate
gate --> skill: 是
gate --> stop: 否
skill --> mcp
mcp --> api
api --> branch
branch --> img: 图像
branch --> vid: 视频
img --> save
vid --> save
save --> done
`);

const outPath = join(__dirname, 'workflow.svg');
writeFileSync(outPath, svg, 'utf-8');
console.log(`✅ 流程图已生成: ${outPath}`);
