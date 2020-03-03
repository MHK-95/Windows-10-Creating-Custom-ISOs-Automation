# First Login Scripts

Windows 10 will start the scripts when the user first logs in.

The autounatted.xml has the tag, <CommandLine>"C:\Users\svc\AppData\Local\Programs\Python\Python38\pythonw.exe" "C:\first-login-scripts\main.py"</CommandLine>.

This will start the main.py script and begin the process.

## main.py
The main.py makes a simple Tkinter GUI. The two most important classes in the main.py file is the Backend and App classes.
The Tkinter app is multi-threaded, so it doesn't freeze when the running background processes.
The Tkinter GUI is there just to show the user the output of the Backend class, which runs system subprocesses.
The App and the Backend communicate with each other with a queue data structure.

The Backend has the run method. This is what the Backend class does when it's initiated and started.




 