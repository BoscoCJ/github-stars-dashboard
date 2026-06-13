# GitHub Stars Observatory

把 GitHub Stars 变成一个可搜索、可分类、可自动更新的可视化收藏夹。

默认展示你自己的公开 Stars，也可以配置多个 GitHub 用户，用来观察别人公开收藏了哪些好项目。

## 你能得到什么

- 一个可以公开访问的 GitHub Pages 网站
- 自动分类的 GitHub Stars 项目卡片
- 中文解释、搜索、分类筛选、排序
- 每天自动更新
- 支持多个用户的公开 Stars
- 不需要服务器
- 不需要数据库
- 不需要个人 GitHub Token

## 最快使用步骤

### 1. 创建你自己的仓库

推荐点击 GitHub 页面右上角的 `Use this template`。

如果没有模板按钮，也可以直接 `Fork` 这个仓库。

### 2. 修改配置文件

打开仓库里的 `config.yml`，修改成你想看的用户。

只看自己的 Stars：

```yaml
site_title: My GitHub Stars

users:
  - username: auto
    label: 我的收藏
```

`auto` 表示当前仓库拥有者。也就是说，谁创建了这个仓库，默认就生成谁自己的 Stars 页面。

看多个用户的公开 Stars：

```yaml
site_title: GitHub Stars Observatory

users:
  - username: auto
    label: 我的收藏

  - username: torvalds
    label: Linus Torvalds

  - username: BoscoCJ
    label: BoscoCJ
```

### 3. 开启 GitHub Pages

进入你的仓库：

```text
Settings -> Pages
```

在 `Build and deployment` 里这样选：

```text
Source: GitHub Actions
```

保存即可。

### 4. 手动运行第一次生成

进入：

```text
Actions -> Refresh GitHub Stars Dashboard
```

点击：

```text
Run workflow
```

等待 workflow 运行完成。

### 5. 打开你的网站

GitHub Pages 地址通常是：

```text
https://你的用户名.github.io/你的仓库名/
```

比如：

```text
https://boscocj.github.io/github-stars-dashboard/
```

## 页面路径规则

如果只配置 1 个用户，网站首页就是这个用户的 Stars 收藏夹：

```text
/
```

如果配置多个用户，首页会变成用户入口页，每个用户都有一个直接页面：

```text
/
/torvalds/
/BoscoCJ/
```

不需要 `/u/<username>/` 这种额外目录。

## 自动更新

项目内置 GitHub Actions：

```text
.github/workflows/refresh-stars.yml
```

它会每天自动运行一次：

```yaml
cron: "20 1 * * *"
```

这个时间是 UTC 01:20，也就是中国时间 09:20。

你也可以随时在 `Actions` 页面手动点击 `Run workflow` 立即刷新。

## 是否需要 Token

普通使用不需要你创建任何个人 Token。

本项目只读取 GitHub 公开 API：

```text
https://api.github.com/users/<username>/starred
```

所以它只能看到公开 Stars。

GitHub Actions 运行时会自动提供一个临时的 `GITHUB_TOKEN`。这个 token 属于当前仓库的 workflow，不是你的个人 Token。它在本项目里只用于：

- 减少 GitHub API 限流
- 部署 GitHub Pages

工作流权限已经限制为：

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

它不能读取你的私有仓库，也不能读取你的账号密码。

## 隐私说明

这个项目只处理公开信息：

- 只能读取公开 GitHub Stars
- 不读取 private repository
- 不读取 private stars
- 不要求输入 GitHub 密码
- 不要求输入个人访问 Token

如果你配置了别人的 GitHub 用户名，也只能看到这个用户公开可见的 Stars。

## 本地预览，可选

普通用户不需要本地运行。如果你想开发或调试，可以这样：

```bash
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名
python refresh_stars.py
```

运行后打开：

```text
index.html
```

## 常见问题

### 我改了 `config.yml`，页面没变化怎么办？

去 `Actions -> Refresh GitHub Stars Dashboard`，手动点击 `Run workflow`。

### Pages 打开是 404 怎么办？

检查：

```text
Settings -> Pages -> Source
```

必须选择：

```text
GitHub Actions
```

然后确认 `Actions` 里的 workflow 已经成功运行。

### Actions 里出现 Node.js warning 怎么办？

如果 workflow 是绿色 `Success`，说明部署已经成功。Node.js warning 通常只是 GitHub Actions 运行环境升级提醒。

本项目已经在 workflow 里设置：

```yaml
FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true
```

用于提前切换到 GitHub 推荐的 Node.js 24 运行方式。

### 可以看别人的收藏吗？

可以。把对方 GitHub 用户名写进 `config.yml` 即可。

```yaml
users:
  - username: torvalds
    label: Linus Torvalds
```

只能读取公开 Stars。

### 可以每天自动更新吗？

可以。默认已经配置为每天自动更新一次。

### 可以改成每 3 天更新一次吗？

可以，修改 `.github/workflows/refresh-stars.yml` 里的 cron：

```yaml
cron: "20 1 */3 * *"
```

表示每 3 天 UTC 01:20 运行一次。
