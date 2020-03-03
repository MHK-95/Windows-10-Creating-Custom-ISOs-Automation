import threading
import tkinter as tk
import tkinter.ttk
import tkinter.messagebox
import tkinter.font
import queue as q
import enum
import traceback
from typing import NamedTuple, Optional
import subprocess as sp
import time
import datetime
import math
import os.path as osp


class QueueState(enum.Enum):
    READY = enum.auto()
    RUNNING = enum.auto()
    DONE = enum.auto()
    FAILED = enum.auto()


class QueueElement(NamedTuple):
    queue_state: QueueState
    message: Optional[str]


class Backend(threading.Thread):

    def __init__(self, queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue

        self.file = osp.join('C:\\', 'Users', 'Public', 'Windows_Configuration_Report.txt')
        self.initial_epoch = time.time()
        self.make_header()

    def run(self):
        append_wrapper = lambda message: self.append_file_and_queue(QueueElement(QueueState.RUNNING, message))

        try:
            self.append_file_and_queue(QueueElement(QueueState.READY, 'Starting Process...\n'))
            append_wrapper('Closing this GUI window will not shutdown the background process.\n')
            append_wrapper(f'Log file is located at {self.file}.\n\n')

            for i in range(1, 6):
                append_wrapper(f'Running background process... {i}')
                time.sleep(1)

            # Adding a dummy subprocess for testing.
            append_wrapper('\nLooking at root folder:\n')
            cp = sp.run(['DIR', 'C:\\'], shell=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
            append_wrapper(cp.stdout)

            self.make_tail()
            self.append_file_and_queue(QueueElement(QueueState.DONE, 'Windows Configuration is Complete!\n'))

        except sp.CalledProcessError as e:
            append_wrapper("\nOops, a called system process didn't work. :^(\n")
            stderr = e.stderr
            if stderr:
                if isinstance(stderr, bytes):
                    stderr = stderr.decode()
            append_wrapper(stderr)
            raise

        except Exception as e:
            append_wrapper("\nOops, an exception occurred. :^(\n")
            append_wrapper("Printing Stack Trace.\n")
            append_wrapper(str.join('', traceback.format_exception(None, e, e.__traceback__)))

            err_message = 'An exception has occurred when configuring windows 10.\nPlease check the log file.\n'
            self.make_tail()
            self.append_file_and_queue(QueueElement(QueueState.FAILED, err_message))

    def make_header(self) -> None:
        """
        Meant to be called when the class has been initialized.
        Will create the file at the path, self.file. This function wont work if the folder the file is in doesn't
        exist.
        """
        with open(self.file, 'w') as file:
            file.write('Windows Configuration Report\n')
            file.write(f'UTC TimeStamp: {datetime.datetime.fromtimestamp(self.initial_epoch)}\n')
            file.write(f'Epoch Time: {self.initial_epoch}\n')
            file.write('## END OF HEADER ##\n')

    def make_tail(self) -> None:
        """
        Meant to be called towards the end of self.run(). Will append the queue and file with a message of how long the
        process took. Then this function will add a tail message to the end of the file for parsing purposes.
        """
        final_epoch = time.time()
        epoch_diff = final_epoch - self.initial_epoch
        self.append_file_and_queue(QueueElement(QueueState.RUNNING,
                                                f'\nTime taken in minutes: {math.ceil(epoch_diff / 60)}\n'))
        self.append_file_and_queue(QueueElement(QueueState.RUNNING, f'Time taken in seconds: {epoch_diff}\n'))

        file = open(self.file, 'r')
        last_line = file.readlines()[-1]
        last_character = last_line[-1]
        file.close()

        tail_message = '## END OF FILE ##\n'
        if last_character != '\n':
            tail_message = '\n' + tail_message

        with open(self.file, 'a') as file:
            file.write(tail_message)

    def append_file_and_queue(self, element: QueueElement) -> None:
        """
        Will add a newline character to the end of element.message if there is non. Will append the self.queue data
        structure with element. Will append self.file with element.message.
        """

        # Make sure all messages end in a new line, \n.
        last_character = element.message[-1]
        if last_character != '\n':
            element = QueueElement(element.queue_state, element.message + '\n')

        with open(self.file, 'a') as file:
            file.write(element.message)

        self.queue.put(element)


class App(tk.Tk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Text Status Widget
        self.frame_1 = tk.Frame(self, padx=20, pady=20)
        self.frame_1.pack()
        font_times_18 = tk.font.Font(family='Times New Roman', size=18)
        self.status = tk.StringVar(self, value='Windows Configuration is running')
        tk.Label(self.frame_1, textvariable=self.status, font=font_times_18).pack()

        # Progressbar Widget
        self.frame_2 = tk.Frame(self, padx=20)
        self.frame_2.pack()
        self.progressbar = tk.ttk.Progressbar(self.frame_2, orient=tk.HORIZONTAL, length=300, mode='indeterminate')
        self.progressbar.start()
        self.progressbar.pack()

        # Textbox Frame
        self.frame_3 = tk.Frame(self, padx=20, pady=20)
        self.frame_3.pack()
        self.textbox = TextBoxOutput(self.frame_3)
        self.textbox.pack()

    def go(self) -> None:
        """
        This function will start the background process class, Backend, which is a child of the Thread Class. The
        Backend class will run in its own thread, thus not making the Tkinter GUI freeze. The two threads will
        communicate with a queue. This communication is one way though, as the GUI will simply print out messages
        the Backend sends, and not put anything to the queue.
        """
        queue = q.Queue()
        process = Backend(queue)
        process.start()
        self.after(0, self.check_queue, queue)

    def check_queue(self, queue) -> None:
        """
        This function checks the queue every 100 milliseconds. It also pops the queue if there is an element. The queue
        is expected to be homogeneous of the type, named tuple: QueueElement. This function will keep calling itself
        every 100 milliseconds until it gets QueueElement.queue_state that is QueueState.DONE or QueueState.Failed.
        This function does use the QueueElement.message string to print output to the GUI.
        """
        if not queue.empty():
            element = queue.get()

            if element.queue_state is QueueState.READY or element.queue_state is QueueState.RUNNING:
                self.textbox.print_message(element.message)

            if element.queue_state is QueueState.DONE or element.queue_state is QueueState.FAILED:
                new_progress_bar = tk.ttk.Progressbar(self.frame_2, orient=tk.HORIZONTAL, length=300,
                                                      mode='determinate')
                new_progress_bar['value'] = 100
                self.progressbar.destroy()
                self.progressbar = new_progress_bar
                self.progressbar.pack()

                if element.queue_state is QueueState.DONE:
                    self.status.set('Windows Configuration Succeeded')
                    self.after(0, tk.messagebox.showinfo, 'Configuration Succeeded', element.message)
                elif element.queue_state is QueueState.FAILED:
                    self.status.set('Windows Configuration Failed')
                    self.after(0, tk.messagebox.showerror, 'Configuration Failed', element.message)

                return

        self.after(100, self.check_queue, queue)


class TextBoxOutput(tk.Frame):
    """
    This widget is based of the tk.Text widget. It acts as a sort of pseudo-terminal that only prints output, but
    doesn't accept user input. It will in the state of tk.DISABLED so that the user can't use it, but switch to
    tk.Normal, when the program wants to print something out to the screen.
    """

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        self.text = tk.Text(self, state=tk.DISABLED)
        self.vsb = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side=tk.RIGHT, fill="y")
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def print_message(self, message: str):
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, message)
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)


if __name__ == "__main__":
    app = App()
    app.title('Windows Configuration')
    app.after(1000, app.go)
    app.mainloop()
