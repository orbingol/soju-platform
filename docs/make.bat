@ECHO OFF

REM SPDX-License-Identifier: BSD-3-Clause
REM Sphinx documentation (run from docs\ or via ``uv run poe docs`` / ``docs-serve``).

pushd %~dp0

if "%SPHINXBUILD%" == "" (
    set SPHINXBUILD=sphinx-build
)
if "%SPHINXAUTOBUILD%" == "" (
    set SPHINXAUTOBUILD=sphinx-autobuild
)
if "%SPHINX_THEME%" == "" (
    set SPHINX_THEME=furo
)
set SOURCEDIR=soju
set BUILDDIR=_build
REM conf.py lives in docs\ (this directory), not under SOURCEDIR
set SPHINXOPTS=-c . %SPHINXOPTS%

if "%1" == "html" goto html
if "%1" == "clean" goto clean
if "%1" == "serve" goto serve

echo Usage: make.bat [html^|clean^|serve]
echo Theme: set SPHINX_THEME=alabaster (default: furo)
exit /b 1

:html
%SPHINXBUILD% -b html %SOURCEDIR% %BUILDDIR%/html %SPHINXOPTS% %O%
goto end

:clean
if exist %BUILDDIR% rmdir /s /q %BUILDDIR%
goto end

:serve
%SPHINXAUTOBUILD% %SOURCEDIR% %BUILDDIR%/html %SPHINXOPTS% %O% --open-browser
goto end

:end
popd
