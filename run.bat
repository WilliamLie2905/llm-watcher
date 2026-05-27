@echo off
echo Running watcher...
python watcher.py

echo Exporting results...
python export.py

echo Done!
