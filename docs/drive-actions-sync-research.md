# Google Drive → GitHub Actions 单向同步：技术核查

结论：可由 GitHub Actions 使用 Drive API 定时读取指定文件夹及其子文件，再写入 GitHub；是否能对目标文件夹实际读写，取决于身份、授权、文件权限和运行时配置，官方能力本身不是该账户的实测证明。同步至公开仓库会向所有人公开文件及 Git 历史，必须单独核对目标与文件范围。

## 身份与权限

- 一个可行方案是创建 Google Cloud 服务账号，将目标文件夹以 Viewer 身份直接共享给该账号，并启用 Drive API。Google 明确说明只访问具体文件/文件夹时可以直接共享，不需要域范围代理或管理员角色；子项仍要逐个实测能否读取。来源：[Google Workspace 凭据](https://developers.google.com/workspace/guides/create-credentials)、[Drive 共享权限](https://developers.google.com/workspace/drive/api/guides/manage-sharing)。
- Actions 通过 GitHub OIDC + Google Workload Identity Federation 绑定服务账号，可避免长期密钥进入仓库；需要在 Cloud 端配置身份池、提供方、受限条件和账号绑定，在 workflow 显式提供 `id-token: write`。OIDC 权限本身不授予 Drive 文件权限，文件还须共享给服务账号。来源：[GitHub OIDC](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-cloud-providers)、[Google Actions 身份验证](https://github.com/google-github-actions/auth/blob/main/README.md)。
- Drive 只读需所选身份具备读取文件内容的 OAuth scope 与对象 ACL；`drive.readonly` 是 Google 定义的 restricted scope，OAuth 验证/安全评估是否适用取决于应用类型与使用方式，不能推定所有个人服务账号使用都需要或都豁免审查。`drive.file` 为指定文件访问设计，不能直接假设它可递归发现和读取任意已有文件。来源：[Google Drive 授权范围](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)。
- OIDC 信任条件应绑定正确的仓库、工作流、分支或环境；有云凭据的工作流不应执行来自不可信 PR 的代码；GitHub token 只授予必要权限，避免长期密钥输出到日志、artifact 或网页。

## 清单与文件内容

- `files.list` 以 `'folder_id' in parents and trashed = false` 列直接子项；每个子文件夹均须继续遍历，并处理 `nextPageToken`。默认返回字段有限，显式请求 id、name、mimeType、modifiedTime、parents、shortcutDetails 与 canDownload 等；快捷方式需确定目标可访问及是否纳入范围，不能假设其等同普通文件。来源：[Drive 文件搜索](https://developers.google.com/workspace/drive/api/guides/search-files)。
- 共享云端硬盘须按需要设置 `supportsAllDrives`、`includeItemsFromAllDrives` 与 `driveId`/`corpora`；`allDrives` 可能标记 `incompleteSearch`，不能当完整列表。来源：[共享云端硬盘支持](https://developers.google.com/workspace/drive/api/guides/enable-shareddrives)。
- 二进制文件可用 `files.get?alt=media`；Google Docs 等 Workspace 原生文件需用 `files.export` 或支持的下载方式导出。普通 `files.export` 内容有 10 MB 限制；先核对 `capabilities.canDownload`，对未支持的类型、导出过大和受限下载明确记录失败，不能静默跳过。导出文本不是原生文档完整保真备份：格式、评论、图片、嵌入对象等须按实际格式另行验证。来源：[Drive 下载与导出](https://developers.google.com/workspace/drive/api/guides/manage-downloads)。

## 更新与删除语义

- 文件以 Drive file ID 做稳定标识，保留路径、原名、mimeType、modifiedTime、提取格式、内容 hash、同步时间和每项状态；重名和移动不能仅靠标题匹配。基于 `modifiedTime` 对比以及安全的全量递归扫描，通常足以支持小规模定期同步；更大规模可评估 Changes API。
- `changes.getStartPageToken` + `changes.list` 可增量跟踪变化，按 `nextPageToken` 分页，末页保存 `newStartPageToken`；返回的 removed 不必然等于源文件被删除，也可能因权限撤销不可见。共享盘变更和账户级 token 有各自边界。来源：[读取变更](https://developers.google.com/workspace/drive/api/guides/manage-changes)。
- 保护历史：任意请求、分页、导出、权限或搜索不完整时，不把未见到的内容认定为已删除；不自动把访问错误扩散为 GitHub 删除。明确同步是否要求对真实删除、移动或撤销共享保留历史，再选择策略。定时任务同步权限最好只读 Drive，GitHub 写入的目标路径需限于专门镜像区。

## 页面与可观测性

- 每次扫描输出完整度报告（已发现、成功、跳过、失败、未知及原因、完成时间），让页面区分未更新、缺失与真实空文件夹。标题使用 Drive 元数据，摘要与状态仅当文档有可识别字段或有明确生成规则时提供，缺失标为未知；标签需用户定义、文档已有标签或可解释的分类映射，不能把模型推断当作人工事实。
- `schedule` 的最短间隔为 5 分钟，默认 UTC，可指定 IANA 时区；调度运行的是默认分支最新版本。公开仓库 60 天无活动，定时工作流可能被 GitHub 自动禁用。来源：[触发工作流](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)、[启用和禁用工作流](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows)。
