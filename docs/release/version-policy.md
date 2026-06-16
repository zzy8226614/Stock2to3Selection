# Release And Version Policy

## Branching

- `main`: 稳定主线，保持 Android 可用与 Spec 对齐
- `feature/*`: 单一功能分支，例如 `feature/api-v1-foundation`
- `release/*`: 需要冻结回归的发布分支
- `hotfix/*`: 主线紧急修复

## Tags

建议保留以下标签类型：

- `android-stable-vX.Y.Z`
- `backend-api-vX.Y.Z`
- `desktop-foundation-vX.Y.Z`

## Spec Governance

- `Spec.md` 作为主规范基线
- 破坏性变更必须先改 Spec，再改代码
- 双端兼容策略必须同步到：
  - `Spec.md`
  - `docs/api/*.md`
  - `docs/architecture/*.md`

## Change Classification

### Safe changes

- 修复 bug
- 新增可选字段
- 新增 `/api/v1`、`/api/v2` 版本路径
- 文档补充

### Breaking changes

- 删除旧字段
- 重命名 JSON key
- 改变错误结构
- 修改 legacy 路由语义

发生 breaking change 时：

1. 升接口版本
2. 更新文档
3. 增加回归验证
4. 记录迁移说明

## Release Checklist

1. Legacy Android 测试通过
2. `/api/v1` 路由可访问
3. 文档已同步更新
4. 关键回归项已执行
5. 发布标签已记录
