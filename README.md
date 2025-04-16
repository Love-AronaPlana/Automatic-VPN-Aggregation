# VLESS 链接聚合器

本项目旨在聚合来自多个来源的 VLESS 链接，包括直接链接和订阅 URL，并将它们去重后输出到一个统一的文件中。

## 项目结构

- `.github/workflows/vless_aggregator.yml`: GitHub Actions 工作流配置文件，用于定时自动执行聚合脚本并将结果推送到仓库。
- `aggregate.py`: 主要的 Python 脚本，负责获取、解析和聚合 VLESS 链接。
- `requirements.txt`: Python 依赖文件，列出了脚本运行所需的库 (例如 `requests`)。
- `sources.txt`: 配置文件，用于指定 VLESS 链接的来源（直接链接或订阅 URL）。
- `aggregated_vless.txt`: 脚本运行后生成的输出文件，包含所有去重和排序后的 VLESS 链接。

## 配置

1.  **安装依赖**: 在运行脚本前，需要安装 `requirements.txt` 中列出的依赖。
    ```bash
    pip install -r requirements.txt
    ```
2.  **配置来源**: 编辑 `sources.txt` 文件，添加你的 VLESS 链接或订阅 URL。
    - 每行一个条目。
    - 以 `#` 开头的行将被忽略。
    - 可以直接粘贴 VLESS 链接 (以 `vless://` 开头)。
    - 可以添加订阅链接的 URL。

    **示例 `sources.txt`:**
    ```
    # 这是一个示例 sources.txt 文件
    # 请将下面的链接替换为你自己的 VLESS 链接或订阅 URL

    # 示例 VLESS 链接:
    # vless://your-uuid@your-domain:443?encryption=none&security=tls&sni=your-domain&type=ws&host=your-domain&path=%2F#Example-Node

    # 示例订阅 URL:
    https://raw.githubusercontent.com/user/repo/branch/path/to/sub
    https://another-example.com/subscription
    ```

## 使用

配置好 `sources.txt` 文件并安装依赖后，可以直接运行 Python 脚本：

```bash
python aggregate.py
```

脚本将读取 `sources.txt`，获取所有链接，处理（包括 Base64 解码），去重，然后将结果写入 `aggregated_vless.txt` 文件。

## GitHub Actions

仓库中包含一个 GitHub Actions 工作流 (`.github/workflows/vless_aggregator.yml`)，它会定时（例如每天）自动执行以下操作：

1.  签出代码。
2.  设置 Python 环境。
3.  安装依赖。
4.  运行 `aggregate.py` 脚本生成 `aggregated_vless.txt`。
5.  将更新后的 `aggregated_vless.txt` 文件提交并推送到仓库。

这样可以确保聚合链接始终保持最新状态。

## 输出

最终聚合的、去重且排序后的 VLESS 链接列表保存在项目根目录下的 `aggregated_vless.txt` 文件中，每行一个链接。