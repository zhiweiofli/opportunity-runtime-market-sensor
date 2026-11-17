# 开通 Google Drive 单向同步

完成以下一次性配置后，GitHub Actions 使用独立服务账号只读根目录，每三小时同步到 `drive-mirror/` 并刷新 Pages。无需下载服务账号密钥。目标仓库是公开仓库：**启用后，根目录里现有及未来新增的所有可访问文件都会公开，Git 历史也会保留已提交内容**。请先确认该目录整体适合公开；如有不应公开的文件，先移出该目录。同步不会自动删除已提交的历史。

## 1. 创建 Google 身份和联合认证

在 [Google Cloud Console](https://console.cloud.google.com/) 选择已有项目，打开 Cloud Shell，在终端填写项目 ID 后执行以下命令。执行者需要有启用 API、管理服务账号及工作负载身份池的权限。

```sh
PROJECT_ID='填写已有的 Google Cloud 项目 ID'
gcloud config set project "$PROJECT_ID"
gcloud services enable drive.googleapis.com iam.googleapis.com iamcredentials.googleapis.com sts.googleapis.com
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
POOL_ID='github-drive-sync'
PROVIDER_ID='github-actions'
SERVICE_ACCOUNT="drive-mirror@${PROJECT_ID}.iam.gserviceaccount.com"
gcloud iam service-accounts create drive-mirror --display-name='Drive mirror (read only)'
gcloud iam workload-identity-pools create "$POOL_ID" --location=global --display-name='GitHub Drive mirror'
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
  --location=global --workload-identity-pool="$POOL_ID" \
  --issuer-uri='https://token.actions.githubusercontent.com' \
  --attribute-mapping='google.subject=assertion.sub,attribute.repository_id=assertion.repository_id' \
  --attribute-condition="assertion.repository_id == '1426336809' && assertion.ref == 'refs/heads/main'"
gcloud iam service-accounts add-iam-policy-binding "$SERVICE_ACCOUNT" \
  --role='roles/iam.workloadIdentityUser' \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository_id/1426336809"
printf 'GCP_WORKLOAD_IDENTITY_PROVIDER=projects/%s/locations/global/workloadIdentityPools/%s/providers/%s\nGCP_DRIVE_SERVICE_ACCOUNT=%s\n' "$PROJECT_NUMBER" "$POOL_ID" "$PROVIDER_ID" "$SERVICE_ACCOUNT"
```

若已有同名服务账号或身份池，命令会报已存在；可换用其他 ID 并重新执行对应步骤。权限变更可能需要数分钟生效。此授权限定目标仓库的 `main` 分支；服务账号本身不需要项目所有者权限。

## 2. 授权文件夹

在 [Drive 根文件夹](https://drive.google.com/drive/folders/1GB1AnYCpN8bJgBFAVVTQksvKPZCU_W6z)的“共享”中，将上一步输出的服务账号邮箱加入为**查看者**。检查子文件是否都可由该身份读取；如果组织策略阻止对服务账号共享，需要由 Google Workspace 管理员调整。不要分享编辑权限或发送密钥。

## 3. 配置 GitHub

在 [仓库 Actions Secrets 设置](https://github.com/zhiweiofli/opportunity-runtime-market-sensor/settings/secrets/actions)中新增三个 repository secrets：

| 名称 | 值 |
| --- | --- |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | 第 1 步输出的完整 provider 路径 |
| `GCP_DRIVE_SERVICE_ACCOUNT` | 第 1 步输出的服务账号邮箱 |
| `DRIVE_ROOT_FOLDER_ID` | `1GB1AnYCpN8bJgBFAVVTQksvKPZCU_W6z` |

确认整个目录都可以公开后，在同一设置页的 **Variables** 新建 repository variable：`DRIVE_SYNC_ENABLED` = `true`。仓库已有的 `WORKFLOW_PUBLIC_PROJECTION_APPROVED` 也必须为 `true` 才会刷新看板。

## 4. 启动并核对

在仓库 Actions 里手动运行 **Drive one-way mirror**，查看扫描是否成功及文件、文件夹数量；再确认 **Judge Dashboard** 部署成功并检查页面“历史资料”。若出错，检查上述身份和共享权限、工作流日志中的失败类型；同步失败不会提交不完整扫描。后续会每三小时自动运行，GitHub 调度可能延迟。

将 `DRIVE_SYNC_ENABLED` 改为 `false` 可暂停后续同步；这不会撤销已公开的 Git 历史。如果要移除已公开内容，需要另行处理仓库历史及缓存。

参考：[Google 联合身份设置](https://github.com/google-github-actions/auth#workload-identity-federation-through-a-service-account)、[Google 身份联合与部署流水线](https://cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines)。
