"""All-in-one program that calculates charge capacity by counting coulombs and strips C8000 all real
time data into usable data with voltage and current columns. Can be updated to include more programs
in the future.

- Oscar Tu 2018

"""

from tkinter import *
from tkinter import filedialog, messagebox
import os

class UI(Frame):
	
	def __init__(self, master=None):
		super().__init__(master)
		self.grid()
		self.init_UI()

	def init_UI(self):
		"""Initializes the User Interface with all the buttons, labels, and entries
		"""


		self.winfo_toplevel().title('File Analyzer')

		# File types to be read
		self.ftypes = [('Text Files', '*.txt'), ('.csv Files', '*.csv'), ('All Files', '*.*')]

		self.inputf = Button(self, text='Input File: ', command=self.open_template)
		self.inputf.grid(row=1, column=0, padx=20, pady=10)

		self.input_file = StringVar()
		self.input_file_entry = self.path_box_init(self.input_file, 1)

		self.outputf = Button(self, text='Output File: ', command=self.save_template)
		self.outputf.grid(row=2, column=0, padx=20, pady=10)

		self.output_file = StringVar()
		self.output_file_entry = self.path_box_init(self.output_file, 2)

		self.output_destination = self.output_file.get()

		self.pg_label = Label(self, text='Select Program: ')
		self.pg_label.grid(row=4, column=0, padx=20)
		
		# Programs to run--add functions and the label for it here to add functionality
		self.programs = {'Strip data from C8000': self.strip_data, 'Calculate Charge Capacity': self.calculate_charge_capacity}

		self.program_var = StringVar()
		self.program_var.set('Strip data from C8000')
		
		# First few rows are static, after that we want to move it if we add programs in the future
		self.base = 4

		# Add radio buttons for each program
		for program in self.programs:
			rb = Radiobutton(self, text=program, variable=self.program_var, value=program)
			rb.grid(row=self.base, column=1, pady=1)
			self.base += 1

		self.title = Label(self, text='Please enter battery info:')
		self.title.grid(row=self.base, column=0, columnspan=2, pady=10)
		
		self.base += 1

		self.rcap_label = Label(self, text='Rated Capacity (mAh)')
		self.rcap_label.grid(row=self.base, column=0, padx=9, pady=10)
		self.rcap_var = StringVar()
		self.rcap_var.set('0.0')
		self.rcap_entry = Entry(self, textvariable=self.rcap_var, width=25)
		self.rcap_entry.grid(row=self.base, column=1, padx=12, pady=10)
		self.base += 1

		self.sample_rate_label = Label(self, text='Sampling Rate of file (s)')
		self.sample_rate_label.grid(row=self.base, column=0, padx=9, pady=10)
		self.sample_rate_var = StringVar()
		self.sample_rate_var.set('0.0')
		self.sample_rate_entry = Entry(self, textvariable=self.sample_rate_var, width=25)
		self.sample_rate_entry.grid(row=self.base, column=1, padx=12, pady=10)
		
		self.base += 1
		self.run_button = self.run_button_init()
		self.quit_button = self.quit_button_init()

	def run(self, program, input_file, output_file):
		"""This function runs after the user presses the "Run" button; processes the program selected
		
		Args:
			program (function): Program that we will be running
			input_file (str): Directory of our input file
			output_file (str): Directory of our output file

		Throws:
			OSError: Based on the program, if required files are not specified will alert the user
		"""
		try:
			open(input_file, 'r')
			if program != self.calculate_charge_capacity:
				try:
					if output_file == '.txt':
						messagebox.showwarning('Specify output file', 'Please specify output file')
						return
					else:
						open(output_file, 'w+')
						result = program(input_file, output_file)
				except OSError:
					messagebox.showwarning('Specify output file', 'Please specify output file')
			else:
				result = program(input_file)
		except OSError:
			messagebox.showwarning('Specify input file', 'Please specify input file')
		return

	def calculate_charge_capacity(self, input_file):
		"""This function calculates the State of Health of the battery based on the input file.
			Loops through entire file and calculates the coulombs at each point in time--calculating the integral of
			the current w.r.t dt from t=0 to t=t_f

		Args:
			input_file (str): Directory of the input file, to be opened
		Throws:
			ValueError: If any of the boxes are 0 or invalid (characters), user is alerted to re-enter
		"""
		try:
			rated_capacity = float(self.rcap_var.get())
			if rated_capacity <= 0:
				messagebox.showwarning('Invalid Value', 'Make sure capacity is not 0')
				return
			try:
				sampling_rate = float(self.sample_rate_var.get())
				if sampling_rate <= 0:
					messagebox.showwarning('Invalid Value', 'Make sure sampling rate is not 0')
					return
				rated_capacity *= 3.6 # Convert from mAh to Amp Seconds
				coulombs = 0
				input_file = open(input_file).read().split("\n")
				if len(input_file[0].split('\t')) == 3:
					for line in input_file:
						line = line.split("\t")
						try:
							coulombs += float(line[2])/1000 * sampling_rate
						except IndexError:
							pass
					messagebox.showinfo('SoH %', "{0:.2f}".format((coulombs/rated_capacity)*100) + "%")
				else:
					messagebox.showwarning('Input File', 'Make sure input file is in correct format!')
					return
			except ValueError:
				messagebox.showwarning('Invalid Value', 'Make sure sampling rate is a number')
		except ValueError:
			messagebox.showwarning('Invalid Value', 'Make sure capacity is a number')
		return

	def strip_data(self, input_file, output_file):
		"""This function strips all the unnecessary outputs from the C8000's all real time data and spits out
			a readable two-coulmn file with current and voltage.
		
		Args:
			input_file (str): Directory of our input file
			output_file (str): Directory of our output file
		"""
		file = open(input_file).read().split('\n')	
		output = open(output_file, 'w')

		# file[0] is first line with column headers, need to check if it is correct/is in the format of "all realtime data"
		try:
			if file[0].split('\t')[1] != 'Status code':
				messagebox.showerror('Wrong File Format', 'This is not C8000\'s "All Real Time Data", please select the correct file/export again from C8000.')
			else:
				file = file[1:]
				for line in file:
					line = line.split('\t')
					if len(line) < 3:
						pass
					else:
						output.write(str(int(line[0].strip())*1000) + '\t' + str(float(line[8].strip())) + '\t' + str(float(line[9].strip())) + '\n')
				messagebox.showinfo('Status', 'File successfully formatted!')
		except:
			messagebox.showerror('Wrong File Format', 'This is not C8000\'s "All Real Time Data", please select the correct file/export again from C8000.')
		return

	def open_template(self):
		file_name = filedialog.askopenfilename(filetypes=self.ftypes)
		if file_name:
			try:
				self.input_file.set(file_name)			
			except: 
				messagebox.showerror('Open Source File', 'Failed to read file \n\'%s\'' % file_name)
				return

	def save_template(self):
		file_name = filedialog.asksaveasfilename(filetypes=self.ftypes)
		
		if file_name[-4:] != '.txt':
			file_name += '.txt'
		self.output_file.set(file_name)
		
	def path_box_init(self, var, r):
		var.set('R:/Projects/UDC Kalman Filter/')
		e = Entry(self, textvariable=var, width=55)
		e.grid(row=r, column=1)
		return e

	def program_label_menu_init(self, var, items):
		w = OptionMenu(self, var, *items)
		w.grid(row=3, column=0, columnspan=2)
		return w

	def run_button_init(self):
		run_button = Button(self, text='Run', fg='green', command=lambda: self.run(self.programs[self.program_var.get()], self.input_file.get(), self.output_file.get()))
		self.base += 1
		run_button.grid(row=self.base, column=0, padx=20, pady=10, columnspan=2)
		return run_button

	def quit_button_init(self):
		quit_button = Button(self, text='Quit', fg='red', command=root.destroy)
		self.base += 1
		quit_button.grid(row=self.base, column=0, columnspan=2)
		return quit_button

root = Tk()
window = UI(master=root)
root.iconbitmap('Bird.ico')
root.geometry('510x370+650+350')
root.mainloop()


