# 架构设计文档: [REQUIRED: 产品/项目名称]

> 文档负责人：Architect
> 文档状态：[REQUIRED: draft | review | approved]
> 创建日期：[REQUIRED: YYYY-MM-DD]
> 版本：[REQUIRED: v0.1]
> 关联 PRD：[REQUIRED: 对应的 PRD 文件路径或产品名]

## 一、系统架构图描述

[REQUIRED: 系统架构图文本描述]

以文字形式描述系统整体架构（前端 / 后端 / 数据层 / 第三方服务 / 数据流向）。
若有图示链接，请附 mermaid 或图片 URL。

## 二、模块拆分清单

每个模块需包含 name / responsibility / interface 三要素。

### 模块 1
- name: [REQUIRED: 模块 1 名称]
- responsibility: [REQUIRED: 模块 1 职责描述]
- interface: [REQUIRED: 模块 1 对外接口（函数签名 / 命令 / 端点）]

### 模块 2
- name: [REQUIRED: 模块 2 名称]
- responsibility: [REQUIRED: 模块 2 职责描述]
- interface: [REQUIRED: 模块 2 对外接口（函数签名 / 命令 / 端点）]

## 三、接口定义

### 接口 1
- API 路径: [REQUIRED: API 路径，如 POST /api/v1/articles]
- 参数: [REQUIRED: 请求参数（含类型与是否必填）]
- 返回值: [REQUIRED: 返回值结构（含成功/失败示例）]

### 接口 2
- API 路径: [REQUIRED: API 路径]
- 参数: [REQUIRED: 请求参数]
- 返回值: [REQUIRED: 返回值结构]

## 四、技术规范

- 编程语言: [REQUIRED: 语言，如 Python 3.11]
- 框架与版本: [REQUIRED: 框架及版本，如 FastAPI 0.110 / React 18]
- 关键依赖: [REQUIRED: 核心第三方库清单及版本约束]
- 运行环境: [REQUIRED: 运行时与系统要求，如 Node 20 / Python 3.11+]

## 五、数据模型

列出核心实体与其字段、类型、关系。

### 实体 1
- 名称: [REQUIRED: 实体 1 名称，如 Article]
- 字段:
  - [REQUIRED: 字段名: 类型 — 说明]
  - [REQUIRED: 字段名: 类型 — 说明]
- 关系: [REQUIRED: 与其他实体的关系，如 belongs_to User]

## 六、部署方案

- 部署方式: [REQUIRED: 部署方式，如 Docker / Vercel / 裸机]
- 环境变量: [REQUIRED: 关键环境变量清单]
- 健康检查: [REQUIRED: 健康检查端点或方式]
- 回滚策略: [REQUIRED: 发布失败时的回滚步骤]

[可选: 其他部署注意事项]
