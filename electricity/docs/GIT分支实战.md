# Git 分支管理实战

本文记录在「阶梯电价计算与查询系统」中演示的 Git 分支管理完整流程（对应教学 #23）。
所有命令均为在本仓库实际执行过的命令，可直接复现。

## 目标

掌握 Git 分支的核心操作：创建分支、切换分支、独立开发、合并分支、删除分支。
理解「特性分支」开发模式：**每做一个新功能，就开一个独立分支，开发完成后合并回主分支。**

## 演示场景

给 `lib/summary.py` 新增「单次最高 / 最低用电量」两个汇总指标，全程在独立分支上完成，
不直接改动 `master`，最后合并。

---

## 一、查看当前分支

```bash
git branch            # 列出本地分支，当前分支前有 * 号
```

```
* master
```

## 二、创建并切换到特性分支

```bash
git checkout -b feature/stats-extreme
```

`-b` 表示「创建并切换」。一个命令完成「新建分支 + 切过去」。

```
Switched to a new branch 'feature/stats-extreme'
```

> 命名建议：`feature/功能名`（新功能）、`fix/描述`（修 bug）、`docs/描述`（改文档）。

## 三、在分支上开发并提交

在 `lib/summary.py` 中为汇总新增最高 / 最低用电量字段，然后提交：

```bash
git add electricity/lib/summary.py
git commit -m "feat(stats): 汇总新增单次最高/最低用电量指标（在 feature 分支开发）"
```

```
[feature/stats-extreme 707c705] feat(stats): ...
 1 file changed, 8 insertions(+)
```

现在 `feature` 分支领先于 `master` 一个提交，二者各自独立前进。

## 四、切回 master，模拟另一条线也有进展

实际团队中，master 可能同时被别人改了。这里我们切回 master 更新 README，制造「分叉」：

```bash
git checkout master
git add electricity/docs/README.md
git commit -m "docs: 更新项目目录结构与测试清单（master 上的独立进展）"
```

此时的分支历史呈分叉状：

```
A──B──C          (master)
      \
       D──E      (feature/stats-extreme)
```

## 五、合并特性分支回 master

```bash
git merge feature/stats-extreme
```

因为我们改的是不同文件，Git 自动合并，无需人工处理：

```
Merge made by the 'ort' strategy.
 electricity/lib/summary.py | 8 ++++++++
 1 file changed, 8 insertions(+)
```

> 若两个分支改了**同一个文件同一处**，Git 无法自动决定，会报告「冲突（conflict）」。
> 此时需手动打开冲突文件，保留想要的代码（去掉 `<<<<<<<` / `=======` / `>>>>>>>` 标记），
> 再 `git add` + `git commit` 完成合并。

## 六、删除已合并的分支

```bash
git branch -d feature/stats-extreme
```

```
Deleted branch feature/stats-extreme (was 707c705).
```

`-d` 只允许删除「已合并」的分支；若分支尚未合并，`-d` 会拒绝（安全保护），
需改用 `-D` 强制删除（慎用）。

## 七、验证合并结果

```bash
git branch                # 只剩 master
python -m unittest discover -s electricity/tests -p "test_*.py"   # 全部测试通过
python electricity/check.py                                        # AST 规则无违规
git log --oneline --graph          # 查看合并历史图
```

---

## 常用分支命令速查

| 命令 | 作用 |
| --- | --- |
| `git branch` | 列出本地分支 |
| `git branch <名>` | 创建分支（不切换） |
| `git checkout -b <名>` | 创建并切换到新分支 |
| `git checkout <名>` | 切换到已有分支 |
| `git merge <名>` | 把指定分支合并到当前分支 |
| `git branch -d <名>` | 删除已合并的分支 |
| `git branch -v` | 查看每个分支的最新提交 |
| `git log --oneline --graph --all` | 图形化查看所有分支记录 |

## 小结

- 特性分支让「新功能」和「稳定主线」互不干扰，可随时回退。
- 提交信息用 `feat/ fix/ docs/` 前缀标注类型，历史更清晰（Conventional Commits）。
- 冲突不可怕，手动解决后 `add` + `commit` 即可。
- 合并后删除分支，保持仓库整洁。