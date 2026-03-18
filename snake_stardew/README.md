# 星露谷风贪吃蛇

欢迎来到我们的星露谷风贪吃蛇。

这是一个用 `Python 3.10+` 和 `pygame` 打造的像素风小项目：保留了经典贪吃蛇的爽快节奏，同时加入了更温暖的田园视觉、完整中文界面、可保存进度、可切换边界模式与窗口模式，适合拿来直接玩，也适合继续二次开发。

## 项目亮点

- 星露谷灵感视觉：草地、木质 HUD、农场色系、像素风菜单
- 完整中文交互：欢迎页、设置页、暂停页、存档确认页
- 主菜单流程：`新游戏` / `继续游戏` / `设置` / `退出`
- 暂停流程：支持 `空格` / `P` / `ESC`，可选择继续或返回欢迎页
- 存档机制：返回菜单时可选 `保存并返回` / `不保存返回`
- 全局设置即时生效：边界模式、蛇速度、果子生成速度
- 两种边界规则：
  - `撞墙死亡`
  - `穿墙模式`
- 穿墙动画修复：不会出现“蛇身断飞/尾巴跨屏飞线”
- 窗口体验：
  - 右上角按钮切换 `全屏/窗口`
  - 支持 `F11` 快捷切换
  - 支持窗口拉伸，画面自适应缩放
- 工程实现：`deque` 蛇身、`tuple` 坐标、`set` 碰撞检测、`Enum` 状态机、更新与渲染分离

## 项目结构

```text
snake_stardew/
  assets/
    stardew_style_icon.png
    stardew_style_icon.ico
    README_ASSETS.md
  config.py
  food.py
  game.py
  input_handler.py
  main.py
  renderer.py
  snake.py
  state.py
  requirements.txt
  README.md
```

## 运行环境

- Python `3.10+`
- Windows（已针对本地 EXE 打包流程优化）

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 操作说明

- 移动：`WASD` 或方向键
- 菜单选择：`↑/↓` 或 `W/S`
- 菜单确认：`Enter` 或 `Space`
- 游戏中暂停：`Space` / `P` / `ESC`
- 全屏切换：右上角按钮 或 `F11`
- 退出程序：在欢迎界面按 `ESC` 或直接关闭窗口

## 设置项说明

- 边界模式：`撞墙死亡` / `穿墙模式`
- 蛇速度：多档调节
- 果子生成速度：多档调节

说明：设置属于全局配置，会即时生效，不绑定到单个存档。

## 打包 EXE（Windows）

```powershell
python -m PyInstaller --noconfirm --clean --onefile --windowed --name StardewSnake --icon "assets\stardew_style_icon.ico" --add-data "assets;assets" main.py
```

生成文件：

- `dist\StardewSnake.exe`

## 数据与配置文件

运行后会在本地数据目录保存：

- `high_score.json`：最高分
- `settings.json`：全局设置
- `savegame.json`：游戏存档

程序会优先使用 `%LOCALAPPDATA%\stardew_snake`，不可用时自动回退到项目目录下的 `data/`。

## 致谢

感谢你一路迭代到现在这个版本。

如果你希望下一步继续增强，我们可以继续做：

- 像素角色与农场季节主题皮肤
- 背景音乐与音效系统
- 排行榜与成就系统
- 更完整的存档槽位管理
