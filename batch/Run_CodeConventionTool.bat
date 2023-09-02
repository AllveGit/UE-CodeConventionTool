for %%i in (%~dp0..) do set RootPath=%%~fi
set PATH_SOURCEDIR = %RootPath%\\Source
set PATH_UPROJECTFILE = %RootPath%\\Project.uproject
python %RootPath%\\src\\run_codeconvention.py %PATH_SOURCEDIR% %PATH_UPROJECTFILE%
pause