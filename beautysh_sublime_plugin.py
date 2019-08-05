import sublime, sublime_plugin
import subprocess

class BeautyshCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		beautysh_cmd = ['python', sublime.packages_path()+'/beautysh/beautysh/beautysh.py', str(self.view.file_name())]
		p = subprocess.Popen(beautysh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
		stdout, stderr = p.communicate()
		
		## Uncomment follwing lines for printing stdout and stderr, might be
		## helpful in debugging.
		# print(stdout)
		# print(stderr)

		if p.returncode != 0:
			print(p.returncode)
			print(stderr)
			print(stdout)
