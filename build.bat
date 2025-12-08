@echo off
chcp 65001 >nul
echo ========================================
echo    文件加密器 - 打包工具
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

:: 安装依赖
echo [1/4] 安装依赖...
pip install cryptography pyinstaller tkinterdnd2 -q

:: 清理旧文件
echo [2/4] 清理旧文件...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "*.spec" del /q *.spec

:: 打包
echo [3/4] 正在打包...
echo       这可能需要几分钟，请耐心等待...
echo.

:: 收集 tkinterdnd2 相关文件
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "文件加密器" ^
    --clean ^
    --noconfirm ^
    --collect-all tkinterdnd2 ^
    main.py

:: 检查结果
if exist "dist\文件加密器.exe" (
    echo.
    echo [4/4] 打包完成！
    echo.
    echo ========================================
    echo    成功！
    echo    EXE 文件位置: dist\文件加密器.exe
    echo    文件大小: 
    for %%A in ("dist\文件加密器.exe") do echo    %%~zA bytes
    echo ========================================
) else (
    echo.
    echo [错误] 打包失败，请检查错误信息
)

echo.
pause

