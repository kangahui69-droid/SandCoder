# Docker Desktop 安装指南 (Windows)

## 第一步：启用 WSL2

以**管理员身份**打开 PowerShell，依次执行：

```powershell
# 1. 启用 WSL 功能
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# 2. 启用虚拟机平台
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 3. 重启电脑
shutdown /r /t 0
```

重启后下载并安装 WSL2 内核更新包：
https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi

安装后在 PowerShell（管理员）中：
```powershell
wsl --set-default-version 2
```

## 第二步：安装 Docker Desktop

1. 下载：https://www.docker.com/products/docker-desktop/
2. 双击安装，**勾选 "Use WSL 2 instead of Hyper-V"**
3. 安装完成后启动 Docker Desktop，等鲸鱼图标稳定
4. 终端验证：
   ```bash
   docker run hello-world
   ```

看到 `Hello from Docker!` 表示成功。

## 常见问题

### WSL2 内核更新失败
- 确保 BIOS 中启用了虚拟化（Intel VT-x / AMD-V）
- 控制面板 → 程序和功能 → 启用或关闭 Windows 功能 → 勾选"虚拟机平台"

### Docker Desktop 启动后一直转圈
- 检查 WSL2 是否正常运行：`wsl --status`
- 尝试重启：`wsl --shutdown` 然后重新打开 Docker Desktop

### Docker 命令提示权限不足
- 将当前用户加入 docker-users 组（安装程序通常自动处理）
