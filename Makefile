win32:
	pyinstaller --name="MyApplication" --hidden-import PySide2.QtXml mygui.py