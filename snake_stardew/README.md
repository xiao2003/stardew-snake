# Stardew Snake（星露谷贪吃蛇）

一个给星露谷爱好者做的像素风贪吃蛇小游戏。

我们把经典贪吃蛇玩法和星露谷视觉元素融合在一起：温暖农场色调、木质面板、像素化菜单、中文交互与完整设置流程。你可以把它当成一个轻量休闲小游戏，也可以继续在此基础上扩展成更完整的像素农场小游戏框架。

## 特色

- 视觉风格：星露谷像素风表达（Logo、农场背景、木质 UI）
- 中文菜单：`新游戏 / 继续游戏 / 设置 / 退出`
- 暂停流程：`继续游戏 / 回到欢迎界面`，并可选择是否保存
- 设置即全局：
  - 边界模式（撞墙死亡 / 穿墙）
  - 蛇速度
  - 果子生成速度
- 存档机制：返回欢迎界面时可保存当前局面
- 窗口能力：
  - 可拉伸窗口
  - 右上角按钮切换全屏/窗口
  - `F11` 快捷切换
- 穿墙动画修复：无“断飞”和尾巴跨屏飞线

## 项目结构

```text
snake_stardew/
  assets/
    fonts/
      LXGWWenKaiGB-Regular.ttf
    stardew/
      stardew_logo.png
      stardew_bg.jpg
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

## 环境要求

- Python 3.10+
- Windows（已适配本地 EXE 打包）

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 操作说明

- 移动：`WASD` 或方向键
- 菜单：`↑/↓` 选择，`Enter/Space` 确认
- 游戏中暂停：`Space` / `P` / `ESC`
- 全屏切换：右上角按钮 或 `F11`
- 关闭程序：欢迎界面按 `ESC` 或直接关闭窗口

## 打包 EXE

```powershell
python -m PyInstaller --noconfirm --clean --onefile --windowed --name StardewSnake --icon "assets\stardew_style_icon.ico" --add-data "assets;assets" main.py
```

生成文件：`dist\StardewSnake.exe`

## 数据文件说明

程序运行后会在本地数据目录保存：

- `high_score.json`：最高分
- `settings.json`：全局设置
- `savegame.json`：存档局面

优先路径：`%LOCALAPPDATA%\stardew_snake`，不可用时自动回退到项目目录 `data/`。

## 资源与授权说明

本项目包含用于学习与爱好者展示的第三方视觉素材，请在二次分发前自行确认对应授权条款：

- 星露谷 Logo 与商店头图（用于风格化表达）
- 中文字体：`LXGW WenKai GB`

如你计划公开商用，请替换为可商用授权素材。
